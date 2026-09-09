use fastchunk_core::{KeepSeparator, RecursiveCharacterTextSplitter as CoreSplitter};
use pyo3::exceptions::{PyNotImplementedError, PyValueError};
use pyo3::prelude::*;

#[pyclass]
pub struct RecursiveCharacterTextSplitter {
    inner: CoreSplitter,
}

#[pymethods]
impl RecursiveCharacterTextSplitter {
    #[new]
    #[pyo3(signature = (
        separators=None,
        chunk_size=4000,
        chunk_overlap=200,
        length_function=None,
        keep_separator=None,
        is_separator_regex=false,
        strip_whitespace=true,
    ))]
    fn new(
        separators: Option<Vec<String>>,
        chunk_size: isize,
        chunk_overlap: isize,
        length_function: Option<PyObject>,
        keep_separator: Option<PyObject>,
        is_separator_regex: bool,
        strip_whitespace: bool,
    ) -> PyResult<Self> {
        if chunk_size <= 0 {
            return Err(PyValueError::new_err("chunk_size must be greater than 0"));
        }
        if chunk_overlap < 0 {
            return Err(PyValueError::new_err(
                "chunk_overlap must be greater than or equal to 0",
            ));
        }
        if chunk_overlap >= chunk_size {
            return Err(PyValueError::new_err(format!(
                "Got a larger chunk overlap ({}) than chunk size ({}), should be smaller.",
                chunk_overlap, chunk_size
            )));
        }

        if length_function.is_some() {
            let is_builtin_len = Python::with_gil(|py| {
                let builtin_len = py
                    .eval_bound("len", None, None)
                    .unwrap()
                    .into_any()
                    .unbind();
                length_function.as_ref().unwrap().is(&builtin_len)
            });
            if !is_builtin_len {
                return Err(PyNotImplementedError::new_err("Custom length_functions are not supported in Phase 1 FastChunk. Only the default character length (len) is supported."));
            }
        }

        let keep_sep = if let Some(ks) = keep_separator {
            Python::with_gil(|py| {
                let bound = ks.into_bound(py);
                if let Ok(s) = bound.extract::<String>() {
                    match s.as_str() {
                        "start" => Ok(KeepSeparator::Start),
                        "end" => Ok(KeepSeparator::End),
                        _ => Err(PyValueError::new_err(
                            "keep_separator must be a boolean or 'start'/'end'",
                        )),
                    }
                } else if let Ok(b) = bound.extract::<bool>() {
                    if b {
                        Ok(KeepSeparator::True)
                    } else {
                        Ok(KeepSeparator::False)
                    }
                } else {
                    Err(PyValueError::new_err(
                        "keep_separator must be a boolean or 'start'/'end'",
                    ))
                }
            })?
        } else {
            KeepSeparator::True // default
        };

        let mut splitter = CoreSplitter::new()
            .with_chunk_size(chunk_size as usize)
            .with_chunk_overlap(chunk_overlap as usize)
            .with_keep_separator(keep_sep)
            .with_is_separator_regex(is_separator_regex)
            .with_strip_whitespace(strip_whitespace);

        if let Some(seps) = separators {
            splitter = splitter.with_separators(seps);
        }

        Ok(Self { inner: splitter })
    }

    fn split_text(&self, text: &str) -> PyResult<Vec<String>> {
        Ok(self.inner.split_text(text))
    }

    #[pyo3(signature = (texts, metadatas=None))]
    fn create_documents(
        &self,
        py: Python<'_>,
        texts: Vec<String>,
        metadatas: Option<Vec<PyObject>>,
    ) -> PyResult<Vec<Document>> {
        let copy_module = py.import_bound("copy")?;
        let deepcopy = copy_module.getattr("deepcopy")?;

        let metadatas_vec: Option<Vec<PyObject>> = if let Some(meta_list) = metadatas {
            Some(meta_list)
        } else {
            None
        };

        let mut documents = Vec::new();

        for (i, text) in texts.iter().enumerate() {
            let chunks = self.inner.split_text(text);
            let meta_to_copy = match &metadatas_vec {
                Some(list) if i < list.len() => list[i].clone_ref(py),
                _ => py.eval_bound("{}", None, None)?.into_any().unbind(),
            };

            for chunk in chunks {
                let copied_meta = deepcopy.call1((meta_to_copy.clone_ref(py),))?.into_any().unbind();
                documents.push(Document {
                    page_content: chunk,
                    metadata: copied_meta,
                });
            }
        }

        Ok(documents)
    }

    fn split_documents(&self, py: Python<'_>, documents: &Bound<'_, PyAny>) -> PyResult<Vec<Document>> {
        let mut texts = Vec::new();
        let mut metadatas = Vec::new();

        for doc in documents.iter()? {
            let doc = doc?;
            let page_content: String = if let Ok(content) = doc.getattr("page_content") {
                content.extract()?
            } else if let Ok(dict) = doc.downcast::<pyo3::types::PyDict>() {
                if let Some(content) = dict.get_item("page_content")? {
                    content.extract()?
                } else {
                    return Err(PyValueError::new_err(
                        "Document dictionary must contain 'page_content'",
                    ));
                }
            } else {
                return Err(PyValueError::new_err(
                    "Document object must have 'page_content' attribute or key",
                ));
            };

            let metadata: PyObject = if let Ok(meta) = doc.getattr("metadata") {
                meta.into_any().unbind()
            } else if let Ok(dict) = doc.downcast::<pyo3::types::PyDict>() {
                if let Some(meta) = dict.get_item("metadata")? {
                    meta.into_any().unbind()
                } else {
                    py.eval_bound("{}", None, None)?.into_any().unbind()
                }
            } else {
                py.eval_bound("{}", None, None)?.into_any().unbind()
            };

            texts.push(page_content);
            metadatas.push(metadata);
        }

        self.create_documents(py, texts, Some(metadatas))
    }
}

#[pyclass]
#[derive(Clone)]
pub struct Document {
    #[pyo3(get, set)]
    pub page_content: String,
    #[pyo3(get, set)]
    pub metadata: PyObject,
}

#[pymethods]
impl Document {
    #[new]
    #[pyo3(signature = (page_content, metadata=None))]
    fn new(py: Python<'_>, page_content: String, metadata: Option<PyObject>) -> PyResult<Self> {
        let meta = match metadata {
            Some(m) => m,
            None => py.eval_bound("{}", None, None)?.into_any().unbind(),
        };
        Ok(Self {
            page_content,
            metadata: meta,
        })
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        let meta_repr = self.metadata.bind(py).repr()?.extract::<String>()?;
        Ok(format!(
            "Document(page_content={:?}, metadata={})",
            self.page_content, meta_repr
        ))
    }

    fn __eq__(&self, other: &Bound<'_, PyAny>, py: Python<'_>) -> PyResult<bool> {
        if let Ok(other_doc) = other.extract::<PyRef<'_, Document>>() {
            if self.page_content != other_doc.page_content {
                return Ok(false);
            }
            let eq = self.metadata.bind(py).eq(other_doc.metadata.bind(py))?;
            return Ok(eq);
        }

        // Duck typing comparison: check page_content and metadata attributes if present
        if let Ok(other_content) = other.getattr("page_content") {
            let content_str: String = other_content.extract()?;
            if self.page_content != content_str {
                return Ok(false);
            }
            if let Ok(other_meta) = other.getattr("metadata") {
                let eq = self.metadata.bind(py).eq(other_meta)?;
                return Ok(eq);
            }
        }

        Ok(false)
    }
}

#[pymodule]
fn fastchunk(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RecursiveCharacterTextSplitter>()?;
    m.add_class::<Document>()?;

    let py = m.py();
    let sys_modules = py.import_bound("sys")?.getattr("modules")?;

    let langchain_code = r#"
import sys
import types

class _LangChainSubmodule(types.ModuleType):
    def __getattr__(self, name):
        if name == "FastChunkTextSplitter":
            try:
                from langchain_text_splitters.base import TextSplitter
            except ImportError:
                raise ImportError(
                    "langchain-text-splitters is required to use fastchunk.langchain. "
                    "Please install it with `pip install langchain-text-splitters`."
                ) from None

            import fastchunk

            class FastChunkTextSplitter(TextSplitter):
                """High-performance LangChain TextSplitter backed by FastChunk's Rust core."""

                def __init__(
                    self,
                    separators: list[str] | None = None,
                    keep_separator: bool | str = True,
                    is_separator_regex: bool = False,
                    **kwargs,
                ):
                    super().__init__(keep_separator=keep_separator, **kwargs)
                    self._separators = separators
                    self._is_separator_regex = is_separator_regex
                    self._fastchunk_splitter = fastchunk.RecursiveCharacterTextSplitter(
                        separators=separators,
                        chunk_size=self._chunk_size,
                        chunk_overlap=self._chunk_overlap,
                        length_function=self._length_function,
                        keep_separator=keep_separator,
                        is_separator_regex=is_separator_regex,
                        strip_whitespace=self._strip_whitespace,
                    )

                def split_text(self, text: str) -> list[str]:
                    return self._fastchunk_splitter.split_text(text)

                @classmethod
                def from_language(cls, language, **kwargs):
                    from langchain_text_splitters import RecursiveCharacterTextSplitter as LCTS
                    separators = LCTS.get_separators_for_language(language)
                    return cls(separators=separators, is_separator_regex=True, **kwargs)

            self.FastChunkTextSplitter = FastChunkTextSplitter
            return FastChunkTextSplitter
        raise AttributeError(f"module '{self.__name__}' has no attribute '{name}'")

langchain_submod = _LangChainSubmodule("fastchunk.langchain")
sys.modules["fastchunk.langchain"] = langchain_submod
"#;

    let submod_locals = pyo3::types::PyDict::new_bound(py);
    py.run_bound(langchain_code, None, Some(&submod_locals))?;
    let langchain_submod = sys_modules.get_item("fastchunk.langchain")?;
    m.setattr("langchain", langchain_submod)?;

    let llamaindex_code = r#"
import sys
import types

class _LlamaIndexSubmodule(types.ModuleType):
    def __getattr__(self, name):
        if name == "FastChunkNodeParser":
            try:
                from llama_index.core.node_parser import TextSplitter
                from pydantic import PrivateAttr
            except ImportError:
                raise ImportError(
                    "llama-index-core is required to use fastchunk.llamaindex. "
                    "Please install it with `pip install llama-index-core`."
                ) from None

            import fastchunk

            class FastChunkNodeParser(TextSplitter):
                """High-performance LlamaIndex NodeParser backed by FastChunk's Rust core."""

                chunk_size: int = 1000
                chunk_overlap: int = 200
                _fastchunk_splitter: fastchunk.RecursiveCharacterTextSplitter = PrivateAttr()

                def __init__(
                    self,
                    chunk_size: int = 1000,
                    chunk_overlap: int = 200,
                    separators: list[str] | None = None,
                    keep_separator: bool | str = True,
                    is_separator_regex: bool = False,
                    strip_whitespace: bool = True,
                    **kwargs,
                ):
                    if "tokenizer" in kwargs and kwargs["tokenizer"] is not None:
                        raise NotImplementedError(
                            "Custom tokenizers/length_functions are not supported in FastChunkNodeParser. "
                            "FastChunk calculates lengths in compiled Rust using standard character length."
                        )
                    if "length_function" in kwargs and kwargs["length_function"] is not None:
                        raise NotImplementedError(
                            "Custom length_functions are not supported in FastChunkNodeParser. "
                            "FastChunk calculates lengths in compiled Rust using standard character length."
                        )
                    super().__init__(
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        **kwargs,
                    )
                    self._fastchunk_splitter = fastchunk.RecursiveCharacterTextSplitter(
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        separators=separators,
                        keep_separator=keep_separator,
                        is_separator_regex=is_separator_regex,
                        strip_whitespace=strip_whitespace,
                    )

                def split_text(self, text: str) -> list[str]:
                    return self._fastchunk_splitter.split_text(text)

                @classmethod
                def class_name(cls) -> str:
                    return "FastChunkNodeParser"

            self.FastChunkNodeParser = FastChunkNodeParser
            return FastChunkNodeParser
        raise AttributeError(f"module '{self.__name__}' has no attribute '{name}'")

llamaindex_submod = _LlamaIndexSubmodule("fastchunk.llamaindex")
sys.modules["fastchunk.llamaindex"] = llamaindex_submod
"#;

    let llamaindex_locals = pyo3::types::PyDict::new_bound(py);
    py.run_bound(llamaindex_code, None, Some(&llamaindex_locals))?;
    let llamaindex_submod = sys_modules.get_item("fastchunk.llamaindex")?;
    m.setattr("llamaindex", llamaindex_submod)?;

    Ok(())
}

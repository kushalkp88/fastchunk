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
}

#[pymodule]
fn fastchunk(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RecursiveCharacterTextSplitter>()?;
    Ok(())
}

# FastChunk Python Bindings

## Architecture
FastChunk exposes its Rust core to Python using [PyO3](https://github.com/PyO3/pyo3) and is built using [maturin](https://github.com/PyO3/maturin).
The `fastchunk-python` crate provides the FFI boundary, keeping the Python-specific code completely separate from `fastchunk-core`.

## Development Setup

To build and test the Python bindings locally:

1. Create and activate a virtual environment.
2. Install `maturin` and `pytest`.
3. Build the developer wheel and install it into the current virtual environment using `maturin develop`.

## Python API Usage

FastChunk provides a drop-in replacement for LangChain's `RecursiveCharacterTextSplitter`.

```python
from fastchunk import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""],
    keep_separator=True,
    strip_whitespace=True,
)

text = "Your long document text goes here..."
chunks = splitter.split_text(text)
print(chunks)
```

## Supported Parameters

- `chunk_size` (int): Maximum length of the chunk. Must be > 0.
- `chunk_overlap` (int): Maximum overlap between chunks. Must be >= 0 and < `chunk_size`.
- `separators` (List[str], optional): Custom list of string separators.
- `keep_separator` (bool | "start" | "end"): Whether to preserve the separators in the resulting chunks and where to attach them.
- `is_separator_regex` (bool): Whether the separators should be evaluated as Rust regex patterns.
- `strip_whitespace` (bool): Whether to trim whitespace from the resulting chunks.

## Known Limitations

- **Custom `length_function`**: Currently restricted to the default character length (`len`). Custom Python callbacks for token counting (e.g., `tiktoken.encode`) are explicitly rejected in Phase 1 to preserve FFI boundary performance.
- **Regex Subset**: The `is_separator_regex` parameter utilizes the Rust `regex` crate, which does not support Python `re` features like lookarounds or backreferences.

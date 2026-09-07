# API Compatibility Matrix

## 1. Target Python API
The target API for FastChunk is a drop-in replacement for LangChain's `RecursiveCharacterTextSplitter`.

To provide the lowest friction for adoption, the public API should expose:
```python
from fastchunk import RecursiveCharacterTextSplitter
```
rather than requiring `FastRecursiveCharacterTextSplitter`. This allows users to simply change their import statement from `langchain.text_splitter` to `fastchunk` without changing their actual code.

```python
class RecursiveCharacterTextSplitter:
    def __init__(
        self,
        separators: Optional[List[str]] = None,
        chunk_size: int = 4000,
        chunk_overlap: int = 200,
        length_function: Callable[[str], int] = len,
        keep_separator: Union[bool, Literal["start", "end"]] = True,
        is_separator_regex: bool = False,
        strip_whitespace: bool = True,
    ):
        ...

    def split_text(self, text: str) -> List[str]:
        ...
```

## 2. Phase 1 `length_function` Support
Handling arbitrary Python callbacks across the FFI boundary (PyO3) inside a tight loop is incredibly slow, destroying the performance benefits of Rust.

**Phase 1 Support**:
- FastChunk Phase 1 will **ONLY support the default character length** (the equivalent of Python's `len()`).
- If a user passes a custom `length_function` (e.g., `tiktoken.encode`), the Python wrapper will intercept it, issue a warning, and fall back to the slow, pure-Python LangChain implementation (or raise a `NotImplementedError` in strict mode).
- *Rust/PyO3 Implications*: To keep Phase 1 fast and simple, the Rust core will hardcode string length calculation (`str::chars().count()`). Supporting token-based chunking requires a dedicated Rust token splitter implementation in future phases, not arbitrary Python callbacks.

## 3. Compatibility Matrix

| Feature | LangChain Behavior | Required FastChunk Behavior | Difficulty | Priority | Test Requirements |
|---------|--------------------|-----------------------------|------------|----------|-------------------|
| `separators` | Uses default `["\n\n", "\n", " ", ""]` or custom list. | Exact match. | Low | High | Custom lists, empty lists. |
| `chunk_size` | Hard limit for chunk length. | Exact match. | Medium | High | Exact byte-for-byte chunk output matching. |
| `chunk_overlap` | Context kept between merged chunks. | Exact match. | High | High | Complex overlap scenarios. |
| `keep_separator=False` | Discards separator. | Exact match. | Low | High | Standard splitting. |
| `keep_separator=True / "start"`| Prepends separator to the next chunk. | Exact match. | Medium | High | Merging logic tests. |
| `keep_separator="end"` | Appends separator to the preceding chunk. | Exact match. | Medium | High | Merging logic tests. |
| `is_separator_regex=False` | Treats separators as string literals. | Exact match. | Low | High | Escaped characters. |
| `is_separator_regex=True` | Uses Python `re`. Supports lookarounds. | Supported subset via Rust `regex`. Fail explicitly if lookarounds/backreferences are used. | High | High | Standard regex, unsupported regex error cases. |
| `strip_whitespace` | Strips leading/trailing whitespace from final chunks. | Exact match using Rust's `str::trim()`. | Low | High | Chunks with tabs/spaces at boundaries. |
| `length_function` | Calls Python `len()` or custom function. | Phase 1 supports `len` only. Rejects custom callbacks. | Low | High | Ensure correct rejection/fallback. |
| Empty separator `""` | Splits by individual character (Unicode Scalar). | Exact match via `str::chars()`. | Medium | High | CJK characters, Emojis. |
| Oversized chunks | Returns a chunk larger than `chunk_size`. | Exact match. | Medium | High | A single continuous string > `chunk_size`. |

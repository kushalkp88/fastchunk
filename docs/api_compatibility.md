# API Compatibility Matrix

## 1. Target Python API
The target API for FastChunk is a drop-in replacement for LangChain's `RecursiveCharacterTextSplitter`.

```python
class FastRecursiveCharacterTextSplitter:
    def __init__(
        self,
        separators: Optional[List[str]] = None,
        chunk_size: int = 4000,
        chunk_overlap: int = 200,
        length_function: Callable[[str], int] = len,
        keep_separator: Union[bool, Literal["start", "end"]] = False,
        is_separator_regex: bool = False,
        strip_whitespace: bool = True,
    ):
        ...

    def split_text(self, text: str) -> List[str]:
        ...
```

## 2. Compatibility Matrix

| Feature | LangChain Behavior | Required FastChunk Behavior | Difficulty | Priority | Test Requirements |
|---------|--------------------|-----------------------------|------------|----------|-------------------|
| `separators` | Uses default `["\n\n", "\n", " ", ""]` or custom list. | Exact match. Accepts and iterates through the list exactly as Python does. | Low | High | Custom lists, empty lists. |
| `chunk_size` | Hard limit for chunk length (except for unbreakable segments). | Exact match. | Medium | High | Exact byte-for-byte chunk output matching. |
| `chunk_overlap` | Amount of context kept between merged chunks. | Exact match. | High | High | Complex overlap scenarios, edge cases where overlap > chunk size. |
| `keep_separator=False` | Discards separator. | Exact match. | Low | High | Standard splitting. |
| `keep_separator=True / "end"`| Appends separator to the chunk. | Exact match. | Medium | High | Merging logic tests. |
| `keep_separator="start"` | Prepends separator to the next chunk. | Exact match. | Medium | High | Merging logic tests. |
| `is_separator_regex=False` | Treats separators as string literals. | Exact match. | Low | High | Escaped characters. |
| `is_separator_regex=True` | Uses Python `re`. Supports lookarounds. | Compile via Rust `regex`. Fail explicitly if lookarounds are used. | High | High | Standard regex, unsupported lookaround regex. |
| `strip_whitespace` | Strips leading/trailing whitespace from final chunks. | Exact match using Rust's `str::trim()`. | Low | High | Chunks with tabs/spaces at boundaries. |
| `length_function` | Calls Python `len()` or custom function. | Call Python function via PyO3, or optimize for standard `len()` (char count). | Medium | High | Custom PyFunc callback overhead. |
| Empty separator `""` | Splits by individual character. | Split by Unicode scalar values or graphemes to match Python. | Medium | High | CJK characters, Emojis. |
| Oversized chunks | Returns a chunk larger than `chunk_size` if unbreakable. | Exact match. | Medium | High | A single continuous string > `chunk_size`. |

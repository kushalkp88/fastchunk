# FastChunk Test Strategy

## 1. Differential Testing Core
The fundamental strategy for FastChunk is **Differential Testing**.

Since the goal is exact compatibility with LangChain, we will not write traditional isolated assertions (e.g., `assert chunk[0] == "Hello"`). Instead, the test suite will dynamically generate chunks using both LangChain and FastChunk, and assert they are identical.

```python
# Conceptual Test Harness
def assert_exact_parity(text, **kwargs):
    lc_splitter = langchain_text_splitters.RecursiveCharacterTextSplitter(**kwargs)
    fc_splitter = fastchunk.FastRecursiveCharacterTextSplitter(**kwargs)

    lc_chunks = lc_splitter.split_text(text)
    fc_chunks = fc_splitter.split_text(text)

    assert lc_chunks == fc_chunks, f"Parity failure for args: {kwargs}"
```

## 2. Test Cases to Cover

The differential tester must be parameterized over a vast array of inputs and configurations.

### 2.1 Configurations to Permute
- `chunk_size`: 10, 50, 100, 1000, 4000
- `chunk_overlap`: 0, 5, 20, 200, (also test `overlap >= chunk_size` as an edge case)
- `keep_separator`: `False`, `True`, `"start"`, `"end"`
- `strip_whitespace`: `True`, `False`
- `is_separator_regex`: `True`, `False`

### 2.2 Input Text Data Types
1. **Normal Paragraphs**: Standard English prose with `\n\n`, `\n`, and spaces.
2. **Newline Separators Only**: Text that only contains `\n` but no `\n\n`.
3. **Custom Separator Hierarchies**: e.g., splitting by HTML tags `["<p>", "<br>", " "]`.
4. **Empty Strings**: `""`.
5. **Whitespace Heavy**: Strings with excessive consecutive spaces, tabs, and newlines.
6. **Unicode Text**: Accented characters (`é`, `ö`).
7. **CJK Text**: Chinese, Japanese, Korean text lacking traditional spaces (tests the `""` fallback).
8. **Emojis**: Multi-byte unicode characters (e.g., 👨‍👩‍👧‍👦). Must ensure we don't slice a byte in half causing Unicode panics.
9. **Very Large Text**: A multi-megabyte string to ensure no stack overflow occurs in the recursive logic.
10. **A Single Continuous Chunk**: A string of 10,000 characters with NO separators. Must yield a single oversized chunk.

### 2.3 Known Edge Cases to Target
- When `chunk_size` is smaller than a single word, forcing fallback to `""` splitting.
- When `strip_whitespace=True` but `keep_separator=True` and the separator IS whitespace.
- Rust `regex` crate failing on Python lookarounds (assert that it correctly raises a `ValueError` or specific exception).

# FastChunk Test Strategy

## 1. Differential Testing Core
The fundamental strategy for FastChunk is **Differential Testing**.

Since the goal is exact compatibility with LangChain, we will dynamically generate chunks using both LangChain and FastChunk, and assert they are identical.

```python
# Conceptual Test Harness
def assert_exact_parity(text, **kwargs):
    lc_splitter = langchain_text_splitters.RecursiveCharacterTextSplitter(**kwargs)
    fc_splitter = fastchunk.RecursiveCharacterTextSplitter(**kwargs)

    lc_chunks = lc_splitter.split_text(text)
    fc_chunks = fc_splitter.split_text(text)

    assert lc_chunks == fc_chunks, f"Parity failure for args: {kwargs}"
```

## 2. Property-Based Randomized Testing (Hypothesis)
To ensure there are absolutely no edge cases where FastChunk deviates from LangChain, we will use **Hypothesis** to generate thousands of random text permutations and configurations.

- **Deterministic Seeds**: Hypothesis runs will use deterministic seeds to ensure reproducible failures.
- **Generated Cases**: Generate text combining words, random whitespaces, varying separator tokens, Unicode symbols, and varying chunk/overlap parameters.
- **Regression Fixtures**: Any mismatch found by Hypothesis must be extracted, saved as a static regression fixture, and added to the standard unit test suite to prevent regressions.

## 3. Specific Test Cases to Cover

### 3.1 Input Text Data Types
1. **Normal Paragraphs**: Standard English prose.
2. **Whitespace Heavy**: Strings with excessive consecutive spaces, tabs, and newlines.
3. **Unicode Text**: Accented characters (`é`, `ö`).
4. **CJK Text**: Chinese, Japanese, Korean text lacking traditional spaces.
5. **Emojis**: Multi-byte unicode characters (e.g., 👨‍👩‍👧‍👦). Must ensure we don't slice a byte in half.
6. **Very Large Text**: Multi-megabyte strings to ensure no stack overflow occurs.

### 3.2 Oversized Chunk Edge Cases
We must test the specific scenarios where a chunk exceeds `chunk_size` and cannot be split.
1. **Separator List Exhausted WITHOUT Empty Separator**: e.g., `separators=["\n"]`, input is `"aaaaabbbbb"`, `chunk_size=3`. LangChain cannot split this further and yields the oversized string. FastChunk must do the exact same.
2. **Explicit Empty Separator**: `separators=["\n", ""]`, input is `"aaaaabbbbb"`, `chunk_size=3`. LangChain *will* split this by characters into `["aaa", "aab", "bbb", "b"]`.
3. **Default Separator Hierarchy**: Using the default `["\n\n", "\n", " ", ""]`, testing behavior when a single word is longer than `chunk_size`.

### 3.3 Known Edge Cases
- When `chunk_size` is smaller than a single word, forcing fallback to `""` splitting.
- When `strip_whitespace=True` but `keep_separator=True` and the separator IS whitespace.
- Rust `regex` crate explicitly rejecting Python lookarounds (assert that it correctly raises a `ValueError`).

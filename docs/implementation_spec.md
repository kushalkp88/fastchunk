# FastChunk Implementation Specification

## 1. Reference Implementation
- **Target Package**: `langchain-text-splitters`
- **Target Version**: `1.1.2`
- **Release Tag / Commit SHA**: `v0.2.2` (Tag for `langchain-text-splitters` 1.1.2 release in the monorepo)
- **Source File Path**: `libs/text-splitters/langchain_text_splitters/character.py` and `libs/text-splitters/langchain_text_splitters/base.py`
- **Reference Class**: `langchain_text_splitters.RecursiveCharacterTextSplitter`**: `langchain_text_splitters.RecursiveCharacterTextSplitter`
- **Key Methods Traced**: `__init__`, `_split_text`, `_merge_splits` (inherited from `TextSplitter`)

## 2. Re-verified LangChain `RecursiveCharacterTextSplitter` Tracing
The primary goal is exact behavioral compatibility with the reference implementation.

### Core Logic Tracing
- **Constructor Defaults**:
  - `separators`: `["\n\n", "\n", " ", ""]`
  - `keep_separator`: `True` (Note: This is `True` by default in LangChain, contrary to older versions which defaulted to `False`!)
  - `is_separator_regex`: `False`
  - `strip_whitespace`: Inherited from `TextSplitter`, defaults to `True`.
- **Separator Selection**:
  - It iterates through the `separators` list.
  - It stops at the first separator that is found in the text using `re.search(re.escape(separator), text)`.
  - If no separator is found, it falls back to the *last* separator in the list (usually `""`).
- **`_split_text` Behavior**:
  - Finds the appropriate separator.
  - Slices the `separators` array to pass down to recursive calls (omitting the current separator and all preceding ones).
  - Splits the text using `_split_text_with_regex`.
  - Iterates through the resulting splits.
  - If a split is smaller than `chunk_size`, it accumulates it in `good_splits`.
  - If a split is larger than `chunk_size`, it first merges the existing `good_splits`, adds them to the final output, and then recurses on the large split using the remaining `new_separators`.
- **`_merge_splits` Logic**:
  - Iterates through `good_splits` building a combined string until `chunk_size` is exceeded.
  - Applies `chunk_overlap` to seed the next chunk with context from the end of the previous chunk.
- **`keep_separator` Behavior in `_split_text_with_regex`**:
  - `True`: Treats as `"start"` if it's the start, but generally prepends the separator to the following text chunk (e.g. splitting "a,b" by "," yields `["a", ",b"]`). *Actually, `True` is treated as `"start"` in newer versions.*
  - `"start"`: Prepends the separator to the following chunk (attached to the start of the next split).
  - `"end"`: Appends the separator to the preceding chunk.
  - `False`: Discards the separator.
- **Empty Separator Fallback**: If the chosen separator is `""`, Python's regex engine effectively splits character by character.
- **Oversized Unbreakable Chunks**: If a segment cannot be split further (because `new_separators` is empty), it is appended directly to `final_chunks` as a single oversized string.

---

## 3. Rust Core Implementation Specification

### 3.1 String Representation & Exact Zero-Copy Boundaries
It is critical to understand where zero-copy happens and where allocations occur.
- **Inside Rust Core**: `FastChunk` operates on `&'a str` (string slices). Splitting and traversing the text requires *zero* string allocations. The output of the core splitting function is a `Vec<&'a str>`. This is true zero-copy.
- **At the PyO3 Boundary**: Python strings are immutable and cannot directly wrap a Rust `&str` safely without extending the lifetime of the underlying Python object (which is unsafe in PyO3 without complex buffer protocols). Therefore, when the `Vec<&str>` is returned to Python, PyO3 **will allocate new Python string objects** for each chunk.
- *Clarification*: The performance gain comes from eliminating the massive amount of intermediate string copying and garbage collection *during* the recursive splitting process, not from returning zero-copy strings to the Python runtime.

### 3.2 Unicode Clarification
- **Python's Empty Separator Behavior**: When Python splits by `""`, it splits by individual Unicode code points (equivalent to iterating through a string).
- **Rust Equivalent**: Rust's native `str::chars()` iterates over Unicode Scalar Values (which map directly to Python's behavior, ignoring surrogate pairs which Rust prevents natively). We do *not* need `unicode-segmentation` (grapheme clusters) unless explicitly requested, as `str::chars()` perfectly mimics Python's `list("string")` behavior.

### 3.3 Exact Regex Compatibility
FastChunk must clearly differentiate between literal separators and regex separators.

- **Literal Separators (`is_separator_regex=False`)**: FastChunk will provide 100% exact compatibility using `memchr` or `str::find`.
- **Regex Separators (`is_separator_regex=True`)**:
  - FastChunk uses the Rust `regex` crate.
  - **Supported Subset**: Standard patterns, character classes, greedy/lazy quantifiers.
  - **Unsupported Python `re` Features**: **Lookarounds** (lookahead `(?=...)`, lookbehind `(?<=...)`) and **Backreferences** (`\1`). The Rust `regex` crate explicitly omits these to guarantee linear execution time.
  - *Mitigation*: We do *not* claim exact regex compatibility. If a user provides an unsupported regex, `regex::Regex::new()` will fail, and FastChunk will throw a `ValueError` in Python explicitly stating lookarounds/backreferences are unsupported.

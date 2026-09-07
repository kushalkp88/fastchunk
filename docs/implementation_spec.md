# FastChunk Implementation Specification

## 1. LangChain `RecursiveCharacterTextSplitter` Tracing
The primary goal is exact behavioral compatibility with LangChain's `RecursiveCharacterTextSplitter`. Here is the traced behavior from the official LangChain repository.

### Core Logic Tracing
- **Separator Selection**: The algorithm iterates through a given list of separators (default `["\n\n", "\n", " ", ""]`).
- **Recursive Splitting**: If splitting by the current separator produces chunks that are still larger than `chunk_size` (measured by `length_function`), it recurses on those oversized chunks using the next separator in the list.
- **`_split_text` Logic**:
  - Finds the first separator that actually exists in the text.
  - Splits the text using that separator.
  - Recurses on any resulting segment that exceeds `chunk_size`.
- **`_merge_splits` Logic**:
  - Takes the recursively split segments and merges them back together up to `chunk_size`.
  - Applies `chunk_overlap` to ensure context is maintained between consecutive merged chunks.
- **`keep_separator` Behavior**:
  - `True` or `"end"`: Appends the separator to the end of the preceding chunk.
  - `"start"`: Prepends the separator to the beginning of the following chunk.
  - `False`: Discards the separator.
- **`strip_whitespace`**: If True, strips leading/trailing whitespace from the merged chunks.
- **`is_separator_regex`**: If True, treats the separator list as Python regex patterns (`re.split`). If False, treats them as exact string literals.
- **Empty Separator Fallback**: If the separator list is exhausted or the current separator is `""`, it splits character by character.
- **Oversized Chunks**: If a segment cannot be split further (e.g., a single word longer than `chunk_size` and no smaller separators exist), it is yielded as a single oversized chunk.

---

## 2. Rust Core Implementation Specification

### 2.1 String Representation
- **Primary type**: `&'a str` (Rust string slices).
- FastChunk will aggressively use zero-copy string slices to represent chunks, tying the lifetime `'a` to the original input string. This avoids heap allocation during the splitting phase.
- **Unicode Support**: Rust's native `char` and `&str` handle Unicode correctly. However, for empty separator (`""`) fallback, we must split by grapheme clusters (via the `unicode-segmentation` crate) or Unicode scalar values to match Python's character iteration exact behavior.

### 2.2 Search Algorithms
- **Exact String Matching (`is_separator_regex = False`)**:
  - Use `memchr` crate for single-byte character separators (e.g., `\n`, ` `). `memchr` uses SIMD and is incredibly fast.
  - Use standard library `str::find` for multi-character literal separators (e.g., `\n\n`).
- **Regex Matching (`is_separator_regex = True`)**:
  - Use the Rust `regex` crate.

### 2.3 Python `re` vs Rust `regex` Incompatibilities
The biggest risk to exact behavioral parity lies in regex engines.
- **Rust `regex` limitations**: The Rust `regex` crate guarantees linear time execution ($O(m \times n)$) and intentionally **omits support for backreferences and lookaround assertions (lookahead/lookbehind)**.
- **Python `re` capabilities**: Python uses a backtracking regex engine that supports lookarounds and backreferences.
- **Mitigation strategy**:
  - If a user passes a regex with lookarounds, the Rust `regex` crate will fail to compile it.
  - FastChunk must catch `regex::Error` on initialization. In Phase 1, we should raise an exception explicitly stating that lookarounds are not supported. If this becomes a major blocker for users, a slower fallback using PyO3 to call Python's `re` module could be considered in later phases.

### 2.4 The `_merge_splits` Algorithm
Merging is the most complex part of LangChain's logic.
The Rust implementation will maintain a sliding window (or buffer) of `&str` slices, accumulating them until `length_function` (usually a simple character count, but sometimes a token count callback via PyO3) exceeds `chunk_size`. It will then calculate the overlap and yield the chunk.

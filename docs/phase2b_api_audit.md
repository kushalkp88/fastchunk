# Phase 2B API Compatibility Audit

## 1. Actual Current FastChunk API
The current FastChunk Python bindings (v0.1.0) via PyO3 expose:
- **Class**: `fastchunk.RecursiveCharacterTextSplitter`
- **Constructor Parameters**:
  - `separators` (Option<Vec<String>>): Default `["\n\n", "\n", " ", ""]`
  - `chunk_size` (isize): Default `4000`, raises `ValueError` if `<= 0`.
  - `chunk_overlap` (isize): Default `200`, raises `ValueError` if `< 0` or `>= chunk_size`.
  - `length_function` (Option<PyObject>): Default `None`. Validates identity against `builtins.len`. Raises `NotImplementedError` otherwise.
  - `keep_separator` (Option<PyObject>): Default `None` (maps to `True`). Accepts boolean or `"start"`/`"end"`. Raises `ValueError` for invalid string literals.
  - `is_separator_regex` (bool): Default `false`.
  - `strip_whitespace` (bool): Default `true`.
- **Methods**:
  - `split_text(text: str) -> List[str]`

## 2. Actual LangChain Reference API
- **Version**: `langchain-text-splitters==1.1.2`
- **Class**: `langchain_text_splitters.RecursiveCharacterTextSplitter`
- **Inherits**: `langchain_text_splitters.base.TextSplitter`
- **Methods**:
  - `split_text(text: str) -> List[str]`
  - `create_documents(texts: List[str], metadatas: Optional[List[dict]]) -> List[Document]`
  - `split_documents(documents: Iterable[Document]) -> List[Document]`
- **Inherited Parameters**: `add_start_index` (bool).

## 3. Feature Compatibility Matrix

| Feature | Classification | Notes |
|---------|----------------|-------|
| `chunk_size` | SUPPORTED EXACTLY | Validated mathematically identically. |
| `chunk_overlap` | SUPPORTED EXACTLY | Overlap loops and deductions mirror LangChain. |
| `separators` | SUPPORTED EXACTLY | Custom hierarchies passed directly to Rust logic. |
| `keep_separator` | SUPPORTED EXACTLY | All modes (True, False, start, end) validated. |
| `strip_whitespace` | SUPPORTED EXACTLY | Mismatches and edge cases resolved in Phase 1. |
| `empty string fallback`| SUPPORTED EXACTLY | Splits by Unicode code points exactly as Python `list()`. |
| `is_separator_regex` | SUPPORTED WITH LIMITATIONS | Rust `regex` crate lacks lookaround/backreference support. |
| `length_function` | SUPPORTED WITH LIMITATIONS | Hardcoded to `str::chars().count()`. Callbacks intercepted. |
| `add_start_index` | NOT SUPPORTED | Parameter does not exist in FastChunk API. |
| `create_documents` | NOT SUPPORTED | Method does not exist in FastChunk API. |
| `split_documents` | NOT SUPPORTED | Method does not exist in FastChunk API. |
| `metadata behavior` | NOT SUPPORTED | Bound to Document objects which are unimplemented. |

## 4. Verified Supported Features
Exact byte-for-byte output parity achieved on:
- `chunk_size`, `chunk_overlap`
- `separators` (default & custom string arrays)
- `keep_separator` (all variants)
- `strip_whitespace`
- `split_text(str) -> List[str]` output.
- Unicode, Emojis, and whitespace blocks handling.

## 5. Unsupported Features
- Document schemas (`langchain_core.documents.Document`).
- Batching methods (`create_documents`, `split_documents`).
- Text tracking metadata (`add_start_index`).

## 6. Features with Partial Compatibility
- **Regex Separators**: Python `re` supports backtracking lookarounds (e.g. `(?=[A-Z])`). FastChunk's Rust engine fails parsing on lookarounds (`error: look-around, including look-ahead and look-behind, is not supported`).
- **Length Function**: Intercepts `len` correctly. Passing tokenizers like `tiktoken.encode` raises an explicit `NotImplementedError` rather than executing the callback.

## 7. Exact Behavioral Differences
- Passing an unsupported regex (lookaround) in LangChain successfully creates chunks. In FastChunk, `is_match` yields `false` silently (as `Regex::new(s)` is ignored on `Err`), effectively treating the lookaround as an unmatched string literal instead of throwing an explicit configuration error to Python or evaluating correctly. *(Note: This requires a bugfix to elevate Rust `Regex::new` compilation errors to Python `ValueError`s).*

## 8. Test Evidence
- **1000/1000** randomized differential tests passed natively through PyO3 bindings.
- **29/29** deterministic tests passed verifying exact boundary/whitespace combinations.
- Isolated Python experiments verified LangChain's `create_documents` and `add_start_index` metadata propagation.
- `exp_features.rs` verified the explicit compilation failure of lookarounds in the Rust `regex` crate.

## 9. Recommended Public API Scope for FastChunk v0.1
For a true v0.1 release, FastChunk should focus *exclusively* on dropping in for `RecursiveCharacterTextSplitter.split_text`.
- Keep `split_documents` and `create_documents` out of scope for v0.1. (Users can wrap `split_text` themselves, or we provide a lightweight Python wrapper rather than passing documents through Rust FFI).
- Explicitly reject invalid Regex separators during `__init__` rather than failing silently at split time.

## 10. Recommended Next Feature (Ranked)

### Ranking
1. **create_documents / split_documents** (High demand, High compatibility importance, Medium difficulty via Python wrapper).
2. **Batch chunking API** (Medium demand, High differentiation, High performance impact).
3. **Token-aware splitting** (High demand, Medium compatibility importance, High differentiation).
4. **add_start_index support** (Low demand, Medium compatibility, Low difficulty).
5. **Regex separator support full coverage** (Low demand, High difficulty, High risk).
6. **Custom length_function** (Medium demand, High performance penalty via FFI).

### Recommendation
**Recommend: `create_documents` / `split_documents`**
*Why*: LangChain users rarely use `split_text` directly. The overwhelming majority of LangChain tutorials and codebases utilize `TextSplitter.split_documents(docs)`. If FastChunk does not expose `split_documents`, it fundamentally fails to act as a drop-in replacement. This feature should be implemented purely in Python (`fastchunk-python` Python wrapper) calling into the fast Rust `split_text` core, avoiding complex metadata struct mappings across the FFI.

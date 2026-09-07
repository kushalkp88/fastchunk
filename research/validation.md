# Competitor and API Compatibility Validation

## 1. Verified Facts
- **LangChain `RecursiveCharacterTextSplitter`**: Python-based text splitter that recursively uses a user-provided or default list of separators (e.g., `["\n\n", "\n", " ", ""]`) to break text down until chunks are under `chunk_size` characters or tokens. It supports overlap (`chunk_overlap`), keeping the separator (`keep_separator=True/False/"start"/"end"`), and regex separators (`is_separator_regex=True/False`).
- **LlamaIndex `SentenceSplitter`**: Python-based splitter focused on keeping sentences intact. It uses a combination of regex (like punctuation) and token limits to build chunks.
- **LlamaIndex `TokenTextSplitter`**: Python-based splitter that chunks text strictly by tokens (e.g., using `tiktoken`) without regard for sentence boundaries, simply slicing the token array.
- **`benbrandt/text-splitter`**: Rust crate providing semantic text chunking. It chunks text by characters or tokens, attempting to preserve semantic boundaries (paragraphs, sentences, words, characters).
- **`semantic-text-splitter`**: Python bindings (via PyO3) for `benbrandt/text-splitter`.

## 2. Source Links
- [LangChain `RecursiveCharacterTextSplitter`](https://github.com/langchain-ai/langchain)
- [LlamaIndex `SentenceSplitter` & `TokenTextSplitter`](https://github.com/run-llama/llama_index)
- [`benbrandt/text-splitter` (Rust)](https://github.com/benbrandt/text-splitter)
- [`semantic-text-splitter` (Python)](https://pypi.org/project/semantic-text-splitter/)

## 3. API Comparison Table

| Feature / Library | LangChain `RecursiveCharacterTextSplitter` | LlamaIndex `SentenceSplitter` | LlamaIndex `TokenTextSplitter` | `benbrandt/text-splitter` (Rust) & `semantic-text-splitter` (Py) |
|-------------------|------------------------------------------|-----------------------------|------------------------------|---------------------------------------------------------------|
| **Core Method** | Recursive fallback on custom separators | Sentence boundary detection + token accumulation | Strict token array slicing | Predefined semantic levels (paragraphs, sentences, words) |
| **Custom Separator Hierarchy** | Yes (`separators=["a", "b"]`) | No (hardcoded/regex based) | N/A | No (uses fixed semantic hierarchy) |
| **Keep Separator Option** | Yes (`keep_separator` bool or "start"/"end") | Implicitly keeps punctuation | N/A | Implicitly keeps delimiters, handles whitespace |
| **Regex Separators** | Yes (`is_separator_regex`) | Uses regex internally, some customization | N/A | No (not arbitrarily customizable via regex) |
| **Exact Output Parity w/ LangChain** | Baseline | No | No | No (due to different splitting algorithms and fixed hierarchy) |

## 4. Feature Comparison Table

| Algorithm / Feature | LangChain `RecursiveCharacterTextSplitter` | `benbrandt/text-splitter` |
|---------------------|--------------------------------------------|---------------------------|
| **Recursive Separator Selection** | User-defined list of strings/regex. | Fixed semantic levels (Unicode standard compliant). |
| **Separator Preservation** | Configurable via `keep_separator`. | Automatically preserved where semantically appropriate. |
| **Merging Behavior** | Accumulates splits until `chunk_size`. | Accumulates splits until `chunk_size` is reached. |
| **Overlap Behavior** | Exact `chunk_overlap` character/token count. | Supports overlap, but implementation differs in exact boundary selection. |
| **Character Counting** | Yes | Yes (Unicode scalar values / grapheme clusters). |
| **Token Counting** | Yes (via external tokenizers) | Yes (integrates with `tiktoken-rs`, HuggingFace tokenizers). |
| **Regex Separators** | Yes | No |
| **Unicode Handling** | Python's internal string representation. | First-class Rust Unicode support (grapheme clusters). |

## 5. Specific Differentiation Opportunities
Currently, `semantic-text-splitter` does **not** provide drop-in compatibility with LangChain. This represents a massive opportunity.

**FastChunk Differentiation:**
1. **Drop-in LangChain Compatibility**: FastChunk could provide an exact 1:1 API match to `RecursiveCharacterTextSplitter` and reproduce its chunk outputs byte-for-byte. This allows users to swap libraries without their RAG evaluations changing.
2. **Custom Separator Hierarchies**: `text-splitter` uses fixed semantic rules. FastChunk would allow arbitrary separator lists (including regex), just like LangChain.
3. **Advanced Separator Placement**: Support LangChain's complex `keep_separator="start" | "end"` logic, which `text-splitter` does not replicate exactly.
4. **Optimized Batch API**: A Rayon-powered parallel batch chunking API exposed to Python (`chunk_batch(list_of_strings)`) to bypass the GIL.
5. **Regex Acceleration**: Offload Python's `re` processing to Rust's `regex` crate for custom separators, providing massive speedups on complex splits.

## 6. Risks
- **Regex Compatibility**: Rust's `regex` crate does not support all features of Python's `re` (e.g., lookarounds). This could break 100% parity if a user provides a lookaround regex as a separator.
- **Python FFI Overhead**: The cost of moving large strings back and forth between Python and Rust could negate performance gains if not carefully managed (e.g., by returning views/slices where possible, though Python strings are immutable).
- **Maintenance Burden**: Keeping exact parity with LangChain requires monitoring their repo for internal algorithm changes.

## 7. Recommended Architecture
- **Core (Rust)**: Implement a highly optimized recursive string splitting algorithm matching LangChain's logic. Support string literals, and (safe) regex.
- **Concurrency (Rust)**: Use `rayon` for data-parallel batch chunking.
- **Bindings (PyO3)**: Provide a Python package (`fastchunk`) that exposes a class `FastRecursiveCharacterTextSplitter` with the exact same constructor signature as LangChain's.
- **Benchmarking (Python/Rust)**: Create a rigorous suite (`pytest-benchmark` or `asv`) comparing `fastchunk` vs LangChain and `semantic-text-splitter` on single document throughput, batch throughput, and peak memory.

## 8. A clear GO / NO-GO decision
**GO - OPTION B: Build FastChunk as a compatibility-focused high-performance implementation.**

**Rationale**: While `benbrandt/text-splitter` is excellent for *semantic* splitting, the AI ecosystem is heavily entrenched in LangChain's `RecursiveCharacterTextSplitter`. Users want faster chunking, but they do *not* want to change their chunk outputs because it invalidates their downstream prompt engineering and RAG evaluations.

By building a strict, high-performance, drop-in replacement for LangChain's algorithm with a batch API, FastChunk solves a very specific, high-value problem that existing Rust libraries ignore.

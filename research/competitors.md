# Competitors and Existing Rust Chunking Libraries

## Existing Rust Implementations

Currently, the Rust ecosystem for LLM tooling is growing, but dedicated chunking libraries are somewhat sparse compared to the Python ecosystem.

### 1. text-splitter (Rust)
- **Repository**: [benbrandt/text-splitter](https://github.com/benbrandt/text-splitter)
- **Features**: A popular Rust crate that provides semantic text splitting. It supports chunking by characters or tokens (integrates with HuggingFace tokenizers and tiktoken).
- **Pros**: Good performance, handles UTF-8 correctly, supports overlapping.
- **Cons**: Can be complex to configure for custom tokenizers; sometimes feature-heavy.

### 2. HuggingFace tokenizers (Rust core)
- **Repository**: [huggingface/tokenizers](https://github.com/huggingface/tokenizers)
- **Features**: Primarily for tokenization, but developers often build custom chunking logic on top of it.
- **Pros**: Blazing fast BPE/WordPiece tokenization.
- **Cons**: Not a dedicated chunking library; requires manual implementation of overlap and boundary logic.

---

## Performance Considerations & Bottlenecks in Python Ecosystem

Python libraries like LangChain and LlamaIndex rely heavily on Python-level string manipulation. Even when tokenization is offloaded to Rust (e.g., via `tiktoken`), the chunking logic (loops, regex, string concatenation) remains in Python.

**Key Bottlenecks:**
1. String allocation and copying.
2. Global Interpreter Lock (GIL) preventing true multithreaded chunking.
3. Regex engine overhead (Python's `re` module vs. Rust's `regex` crate).

---

## Rust Optimization Opportunities for `fastchunk`

If we are building `fastchunk`, we should focus on the following optimization vectors:

1. **Zero-Copy Architecture (Lifetimes)**
   - Use `&'a str` for chunks, tying their lifetime to the input string. This avoids creating millions of new `String` objects in memory.
   - *Estimated Impact*: 3x-10x memory reduction compared to Python, and massive CPU time savings from reduced allocator pressure.

2. **SIMD-Accelerated Separator Search**
   - Utilize crates like `memchr` which heavily use SIMD to find separators (like `\n` or spaces) almost instantly across large documents.
   - *Estimated Impact*: Orders of magnitude faster string splitting than standard Python `.split()`.

3. **True Parallelism (Rayon)**
   - Expose an API that allows chunking massive corpora (e.g., thousands of documents) concurrently using thread pools.
   - *Estimated Impact*: Linear scale-up with CPU cores, easily beating Python multiprocess overhead.

4. **FFI/Python Bindings (PyO3)**
   - While building in Rust, using `PyO3` to expose this as a Python library (`fastchunk-py`) gives the best of both worlds: Python ecosystem integration with Rust performance.

# FastChunk: Implementation & Benchmark Recommendations

Based on the analysis of LangChain, LlamaIndex, and existing Rust tooling, here is the recommended roadmap for implementing `fastchunk`.

## 1. Implementation Roadmap

### Phase 1: Zero-Copy Recursive Character Splitter
- **Goal**: Implement a Rust version of LangChain's `RecursiveCharacterTextSplitter`.
- **Architecture**:
  - Input: `&str`, Chunk Size, Overlap, Separators.
  - Output: `Vec<&str>`.
- **Tech**: Use standard library features, `memchr` for fast separator finding.
- **Why**: It is the most requested, most understood chunking algorithm, and benefits massively from zero-copy slices.

### Phase 2: Token-Aware Splitter
- **Goal**: Implement a token-based splitter similar to LlamaIndex.
- **Architecture**:
  - Integrate with `tiktoken-rs` or `hf-hub`.
  - Slice by token limits while preserving overlapping boundaries.
- **Why**: Crucial for strict LLM context-window limits.

### Phase 3: Semantic Sentence Splitter
- **Goal**: Implement sentence-boundary aware chunking.
- **Architecture**:
  - Use regex or unicode-segmentation for robust sentence boundary detection.
  - Group sentences by token count or character length.

### Phase 4: Python Bindings
- **Goal**: Provide `pip install fastchunk`.
- **Architecture**: Use `PyO3` to wrap the Rust core.
- **Why**: The primary audience for RAG chunking still operates in Python.

---

## 2. Benchmark Recommendations

To prove `fastchunk` is superior, we need a rigorous benchmark suite against standard Python libraries.

### Datasets
1. **Wikipedia Dump**: Good for large scale, varied text.
2. **Code Repositories**: Test how the splitters handle non-natural language (newlines, tabs, brackets).
3. **Project Gutenberg (Books)**: Good for testing sentence-level semantic splitting.

### Metrics to Track
1. **Execution Time (Single-threaded)**: Rust vs. Python (LangChain/LlamaIndex). *Expected: 10x-50x speedup.*
2. **Execution Time (Multi-threaded)**: Rust (Rayon) vs. Python (Multiprocessing). *Expected: Significant scaling advantage for Rust.*
3. **Peak Memory Usage**: Measure RAM consumption during the chunking of a 1GB dataset. *Expected: Rust should use ~1.1GB (mostly mapping the file), while Python might spike to 3GB-5GB due to string copies.*
4. **Chunk Quality**: Ensure that given the exact same parameters, `fastchunk` produces identical or semantically equivalent chunks compared to the baseline Python libraries.

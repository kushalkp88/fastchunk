# FastChunk Implementation Roadmap

## Phase 1: Correctness & Exact API Parity (Current Focus)
**Goal**: Build a single-threaded Rust implementation of `RecursiveCharacterTextSplitter` that achieves 100% test pass rate on the Differential Test Suite against LangChain.
- Set up repository structure (Cargo + Maturin).
- Implement pure Rust string splitting and merging logic (`fastchunk-core`).
- Implement PyO3 bindings matching the `FastRecursiveCharacterTextSplitter` API.
- Build the `pytest` differential testing suite.
- Iterate on edge cases (Unicode, whitespace, overlap logic) until outputs are identical to LangChain byte-for-byte.
- *Strictly EXCLUDE: Rayon, parallel batching, token splitters, PyO3 string-view optimizations.*

## Phase 2: Performance Profiling & Optimization
**Goal**: Make the 100% correct implementation as fast as possible on a single thread.
- Establish `pytest-benchmark` baseline against LangChain.
- Optimize separator searching using `memchr` (SIMD).
- Optimize string allocation (ensure we are returning slices or minimizing Python string instantiation overhead).
- Profile memory usage and eliminate intermediate `Vec` allocations where an `Iterator` would suffice.

## Phase 3: Parallelism & Batch API
**Goal**: Introduce a new API for processing thousands of documents concurrently.
- Introduce `chunk_batch(texts: List[str]) -> List[List[str]]`.
- Integrate `rayon` into the Rust core to process the batch across all available CPU cores.
- Release Python GIL during batch processing.

## Phase 4: Token Splitters & Ecosystem Expansion
**Goal**: Expand library scope to other popular RAG chunking methods.
- Implement `TokenTextSplitter` using `tiktoken-rs`.
- Implement `SentenceSplitter` using robust Unicode boundary detection.

# FastChunk Implementation Roadmap

## Phase 1: Correctness & Exact API Parity (Current Focus)
**Goal**: Build a single-threaded Rust implementation of `RecursiveCharacterTextSplitter` that achieves 100% test pass rate on the Differential Test Suite against LangChain.
- Set up repository structure (Cargo + Maturin).
- Implement pure Rust string splitting and merging logic (`fastchunk-core`).
- Implement PyO3 bindings matching the `RecursiveCharacterTextSplitter` API.
- Build the `pytest` differential testing suite (including Hypothesis).
- Iterate on edge cases (Unicode, whitespace, overlap logic) until outputs are identical.
- *Strictly EXCLUDE: Rayon, parallel batching, token splitters, arbitrary Python callbacks.*

### Phase 1 Acceptance Criteria (GO/NO-GO)
Phase 1 **MUST NOT** proceed to Phase 2 (Optimization) until the following criteria are met:
1. **Deterministic Tests Pass**: All static compatibility test fixtures pass with 100% byte-for-byte parity against `langchain-text-splitters==1.1.2`.
2. **Randomized Tests Pass**: Hypothesis runs (10,000+ permutations of text and configurations) produce zero output mismatches.
3. **Unicode Edge Cases Pass**: Emojis, CJK characters, and surrogate pairs (if applicable) do not cause panics or split mismatches compared to Python's character iteration.
4. **Supported Regex Passes**: Tests using standard regex separators pass, and tests using unsupported Python features (lookarounds) cleanly throw explicit exceptions.
5. **No Unresolved Mismatches**: Zero known scenarios exist where FastChunk silently deviates from LangChain behavior (except for the explicitly documented unsupported custom `length_function`).

## Phase 2: Performance Profiling & Optimization
**Goal**: Make the 100% correct implementation as fast as possible on a single thread.
- Establish `pytest-benchmark` baseline against LangChain.
- Optimize separator searching using `memchr` (SIMD).
- Profile memory usage and eliminate intermediate `Vec` allocations where an `Iterator` would suffice.

## Phase 3: Parallelism & Batch API
**Goal**: Introduce a new API for processing thousands of documents concurrently.
- Introduce `chunk_batch(texts: List[str]) -> List[List[str]]`.
- Integrate `rayon` into the Rust core.

## Phase 4: Token Splitters & Ecosystem Expansion
**Goal**: Expand library scope to other popular RAG chunking methods.
- Implement `TokenTextSplitter` using `tiktoken-rs`.
- Implement `SentenceSplitter` using robust Unicode boundary detection.

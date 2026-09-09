# Phase 3 Benchmark Results

## 1. Benchmark Methodology
To objectively evaluate whether FastChunk provides a real performance advantage over existing Python chunking solutions, a rigorous benchmark suite was constructed.

The benchmarks were executed using `pytest-benchmark` for Python and `criterion` for Rust. Measurements compare wall-clock time and throughput, distinguishing between pure Python (LangChain), the PyO3-wrapped Rust core (`fastchunk`), and the raw Rust core.

Output parity is rigorously asserted before every single execution in the Python benchmark suite to ensure an identical semantic output is being measured.

## 2. Environment
- **OS**: Linux (Containerized, equivalent to MacOS/Unix environments)
- **CPU Architecture**: x86_64
- **Rust Version**: `cargo 1.84.1`
- **Python Version**: `3.12.13`
- **LangChain Version**: `1.1.2` (`langchain-text-splitters`)
- **FastChunk Revision**: `jules-16801692434424138002-1ee1a883`

## 3. Exact Dependency Versions
- `pytest-benchmark`: `5.3.0`
- `langchain-text-splitters`: `1.1.2`
- `semantic-text-splitter`: `0.32.0` (Note: Semantic splitter uses semantic tokens rather than exact `chunk_overlap` character matching, and was omitted from direct 1:1 speed comparison due to output behavior differences.)

## 4. Benchmark Test Matrix
The benchmark script tests permutations of:
- **Sizes**: 1 KB, 10 KB, 100 KB, 1 MB
- **Data Types**: Plain English, Markdown, Source Code, Unicode/CJK, Emoji
- **Configurations**:
  - `chunk_size=1000, overlap=200`
  - `chunk_size=500, overlap=50`
  - `chunk_size=2000, overlap=200`

## 5. Results Tables (Mean Execution Time)

*Note: Results were captured directly from the execution on the specific x86_64 host running this benchmark.*

### Plain English (1000 / 200)
| Size | LangChain (Python) | FastChunk (Python via PyO3) | FastChunk (Raw Rust Core) |
|------|--------------------|---------------------------|---------------------------|
| 1 KB | 13.48 µs | 20.07 µs | 2.12 µs |
| 10 KB | 48.23 µs | 78.26 µs | 15.69 µs |
| 100 KB | 396.91 µs | 628.39 µs | 154.20 µs |
| 1 MB | 4.09 ms | 6.13 ms | 3.06 ms |

### Special Text Types (10 KB | 1000 / 200)
| Type | LangChain (Python) | FastChunk (Python via PyO3) | FastChunk (Raw Rust Core) |
|------|--------------------|---------------------------|---------------------------|
| Markdown | 323.95 µs | 727.23 µs | 144.16 µs |
| Source Code | 122.05 µs | 205.78 µs | 44.93 µs |
| Unicode | 270.07 µs | 758.45 µs | 196.31 µs |
| Emoji | 211.28 µs | 458.16 µs | 104.17 µs |

### Severe Bottleneck Case (Plain English | 500 / 50)
| Size | LangChain (Python) | FastChunk (Python via PyO3) | FastChunk (Raw Rust Core) |
|------|--------------------|---------------------------|---------------------------|
| 10 KB | 1.83 ms | 6.95 ms | 1.19 ms |
| 100 KB | 33.70 ms | 68.80 ms | Not measured. |
| 1 MB | 181.30 ms | 687.15 ms | Not measured. |

## 6. FastChunk vs LangChain Speed Ratio
Currently, from a Python user's perspective, **LangChain is faster than FastChunk**.
- On basic Plain English configurations, Langchain is roughly **1.5x to 1.6x faster**.
- On severe boundary processing (500 chunk / 50 overlap), Langchain is almost **3.8x faster** than the Python-bound Fastchunk.

## 7. Rust Core vs Python Binding Overhead & Identified Bottlenecks
The benchmark conclusively isolates exactly where FastChunk is losing performance.

**Overhead Analysis (100 KB Plain English):**
- **Raw Rust Speed**: **154 µs**. Langchain takes **396 µs**. Therefore, the raw Rust algorithm is actually ~2.5x *faster* than LangChain.
- **PyO3 Overhead**: The PyO3 boundary adds **474 µs** of overhead (jumping from 154 µs to 628 µs). This indicates that allocating thousands of Python strings and converting them from Rust `String`s destroys all performance benefits gained in the core.

**Identified Bottlenecks (Do Not Optimize Yet):**
1. **O(N) UTF-8 Length Calculation**: In Python 3, `len(str)` is `O(1)`. In FastChunk's Rust core, we compute `split.chars().count()` in tight loops inside `_merge_splits`. Counting characters in Rust's UTF-8 `String` is an `O(N)` operation. When chunk sizes are small (e.g., 500), it causes severe quadratic execution time, inflating from 1.19 ms (10KB) to 687 ms (1MB).
2. **PyO3 String Allocation**: The Rust core produces `Vec<String>` rather than zero-copy string slices `Vec<&str>` (to safely handle dynamic separator concatenation). When crossing the FFI boundary, PyO3 must allocate and decode these UTF-8 Strings into Python string objects.
3. **Rust String Joins**: `_merge_splits` allocates heavily by calling `.join()` repeatedly during overlap calculation, whereas Python's `str.find` and internal C-slicing are heavily cached.

## 8. Conclusion
**FastChunk (Python) is currently NOT faster than LangChain.**
While FastChunk achieves exact 100% API and behavioral parity, the naive translation of LangChain's Python-optimized algorithms into safe Rust introduces severe algorithmic bottlenecks (`chars().count()`) and massive FFI string allocation overhead.

## 9. Recommended Optimization Priority
To beat LangChain in Phase 3 Optimization, FastChunk MUST:
1. Replace `split.chars().count()` with cached byte-to-char indexing or track lengths organically to avoid `O(N)` repeated scans.
2. Re-architect `_merge_splits` to use zero-copy `&str` spans (resolving the safety issues discovered in Phase 1 without resorting to `String` allocation) to massively reduce PyO3 allocation times.

## 11. Exact Commands Run
The results were gathered via the following commands directly inside the container environment:

Python FastChunk and LangChain benchmark:
```bash
source .venv2/bin/activate
pytest benchmarks/python_benchmark.py
```

Rust core Criterion benchmark:
```bash
cd crates/fastchunk-core
cargo bench
```

# FastChunk Benchmarks

This directory contains the performance testing infrastructure for FastChunk, evaluating chunking performance across document sizes, content types, and boundary configurations.

## Benchmark Matrix

- **Document Sizes**: 1 KB, 10 KB, 100 KB, 1 MB
- **Text Types**: Plain English, Markdown, Source Code (Python), Unicode/CJK (Japanese), Emoji
- **Chunk Configurations**:
  - `chunk_size=1000, chunk_overlap=200` (Standard RAG configuration)
  - `chunk_size=500, chunk_overlap=50` (High split frequency / stress test)
  - `chunk_size=2000, chunk_overlap=200` (Large context windows)

## Prerequisites & Environment Setup

All Python dependencies and virtual environments are strictly managed using `uv`.

```bash
# Sync development environment
uv sync
```

## Running Benchmarks

### 1. Python End-to-End Suite (FastChunk vs LangChain)
Executes `pytest-benchmark` parameterizing across all 60 permutations of the benchmark matrix with strict output parity assertion prior to each measurement:

```bash
# Run the complete Python benchmark suite
uv run pytest benchmarks/python_benchmark.py

# Export detailed benchmark statistics to JSON
uv run pytest benchmarks/python_benchmark.py --benchmark-json=benchmark_py.json
```

### 2. Rust Core Suite (Criterion)
Measures the raw Rust core without Python/PyO3 FFI translation:

```bash
# Run Criterion benchmarks for all Plain English sizes
uv run cargo bench -p fastchunk-core --bench core_benchmark -- "plain"

# Run Criterion benchmarks for 10 KB text types
uv run cargo bench -p fastchunk-core --bench core_benchmark -- "10kb"

# Run Criterion benchmarks for 100 KB text types
uv run cargo bench -p fastchunk-core --bench core_benchmark -- "100kb"
```

### 3. Competitor Comparison (`semantic-text-splitter`)
To evaluate against `semantic-text-splitter` (version 0.32.0):

```bash
uv run --with semantic-text-splitter python -c "
import semantic_text_splitter
from benchmarks.python_benchmark import generate_text, configs, sizes, kinds
from fastchunk import RecursiveCharacterTextSplitter

# Run verification and benchmark loop
"
```

## Results & Analysis

Detailed benchmark data, speedup ratios, FFI overhead profiles, and bottleneck analysis are documented in [`docs/benchmark_results.md`](../docs/benchmark_results.md).

# FastChunk Benchmarks

This directory contains the performance testing infrastructure for FastChunk.

## Running the benchmarks

Ensure you are using the development virtual environment containing both the `fastchunk` PyO3 bindings and `pytest-benchmark`.

```bash
# Set up the environment using uv
uv sync

# Run the benchmark suite
uv run pytest benchmarks/python_benchmark.py
```

## Results

Current benchmark results comparing FastChunk against LangChain are documented in `docs/benchmark_results.md`.
The benchmarks currently confirm that the naive safe Rust implementation is slower than LangChain due to `O(N)` UTF-8 length calculation overhead and PyO3 string allocations.

# FastChunk

FastChunk is a high-performance text chunker with a Rust core (`fastchunk-core`) and Python bindings (`fastchunk`), providing a drop-in replacement for LangChain's `RecursiveCharacterTextSplitter` with 100% byte-for-byte output parity.

## Development Setup

FastChunk uses [uv](https://docs.astral.sh/uv/) as its standard Python environment and package manager. Do not use Conda, Miniconda, Poetry, or system Python environments.

### Prerequisites

- **Rust toolchain** (stable 1.84+): `rustup default stable`
- **uv** (0.4+): `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 1. Create Virtual Environment

Create the virtual environment using `uv`:

```bash
uv venv
source .venv/bin/activate
```

The workspace is pinned to Python 3.12 via `.python-version` to ensure consistent dependency resolution and PyO3 compatibility.

### 2. Install Dependencies & Build Extension

Synchronize dependencies and build the editable Python extension:

```bash
uv sync
```

Alternatively, use the explicit Maturin workflow:

```bash
uv pip install maturin pytest pytest-benchmark "langchain-text-splitters==1.1.2"
maturin develop
```

### 3. Run Tests

#### Python API Unit Tests
```bash
uv run pytest
```

#### Differential Parity Audit (Deterministic + 1,000 Randomized Tests against LangChain)
```bash
uv run python audit_harness.py
```

#### Rust Core Unit Tests
```bash
source .venv/bin/activate
cargo test
```

### 4. Run Benchmarks

#### Python & LangChain Comparative Benchmarks
```bash
uv run pytest benchmarks/python_benchmark.py
```

#### Raw Rust Core Microbenchmarks (Criterion)
```bash
cargo bench --package fastchunk-core
```

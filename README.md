# FastChunk

FastChunk is a high-performance text chunker with a Rust core (`fastchunk-core`) and Python bindings (`fastchunk`), providing a drop-in replacement for LangChain's `RecursiveCharacterTextSplitter` with 100% byte-for-byte output parity.

## Installation

FastChunk distributes precompiled binary wheels for supported platforms. Users installing prebuilt wheels do **not** need the Rust toolchain installed on their system.

Using `pip`:
```bash
pip install fastchunk
```

Using `uv`:
```bash
uv add fastchunk
```

## Quickstart

### 1. Standalone Text Chunking

Core FastChunk has **zero mandatory third-party dependencies**.

```python
from fastchunk import RecursiveCharacterTextSplitter, Document

text = """
FastChunk is designed as a drop-in replacement for text splitting.
It produces identical chunk boundaries with significant performance speedups.
"""

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

# Split raw text
chunks = splitter.split_text(text)

# Generic Document API (zero dependencies)
docs = splitter.create_documents([text], metadatas=[{"source": "demo"}])
split_docs = splitter.split_documents(docs)
```

### 2. LangChain Integration (Optional)

FastChunk provides an optional adapter for LangChain pipelines:

```bash
pip install "fastchunk[langchain]"
# or: pip install fastchunk langchain-text-splitters
```

```python
from fastchunk.langchain import FastChunkTextSplitter
from langchain_text_splitters import Language

splitter = FastChunkTextSplitter(chunk_size=1000, chunk_overlap=200)

# Works directly with LangChain Document pipelines
docs = splitter.create_documents(["some text"])
split_docs = splitter.split_documents(docs)

# Language-aware code splitting
py_splitter = FastChunkTextSplitter.from_language(Language.PYTHON, chunk_size=500)
```

> **Compatibility Note**:
> - Validated against `langchain-text-splitters==1.1.2` and `langchain-core==1.6.2`.
> - FastChunk does not claim universal 100% LangChain API compatibility because custom `length_function` callables are intentionally unsupported (FastChunk calculates lengths in high-speed compiled Rust using standard character length). Passing a custom `length_function` raises a descriptive `NotImplementedError`.

### 3. LlamaIndex Integration (Optional)

FastChunk provides a high-performance `NodeParser` / `TextSplitter` adapter for LlamaIndex RAG pipelines:

```bash
pip install "fastchunk[llamaindex]"
# or: pip install fastchunk llama-index-core
```

```python
from fastchunk.llamaindex import FastChunkNodeParser
from llama_index.core.schema import Document
from llama_index.core.ingestion import IngestionPipeline

parser = FastChunkNodeParser(chunk_size=1000, chunk_overlap=200)

doc = Document(text="Your document text here...", metadata={"source": "rag_doc"})

# 1. Parse directly into LlamaIndex TextNodes (preserving metadata and node relationships)
nodes = parser.get_nodes_from_documents([doc])

# 2. Use inside an IngestionPipeline or VectorStoreIndex
pipeline = IngestionPipeline(transformations=[parser])
pipeline_nodes = pipeline.run(documents=[doc])
```

> **Compatibility Note**:
> - Validated against `llama-index-core==0.14.24`. Minimum supported version is `llama-index-core>=0.10.0`.
> - FastChunk does not claim universal 100% LlamaIndex compatibility: `FastChunkNodeParser` uses FastChunk's recursive character splitting semantics and is **not** a drop-in replacement for LlamaIndex's `SentenceSplitter` (which implements sentence-boundary regex splitting).
> - Custom tokenizers or callable length functions (`tokenizer`, `length_function`) are currently **unsupported** by the compiled Rust core (character length is used). Passing custom functions raises an explicit `NotImplementedError`.
> - FastChunk delegates all text chunking to its Rust core while LlamaIndex's `TextSplitter` base class automatically constructs standard `TextNode` objects, manages `NodeRelationship.SOURCE` and `NodeRelationship.PREVIOUS`/`NEXT` pointers, and propagates metadata.

## Development Setup

For contributors building from source or running benchmarks:

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

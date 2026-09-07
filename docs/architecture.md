# FastChunk Proposed Repository Architecture

To support a high-performance Rust core, Python bindings, and extensive differential testing against Python libraries, the repository should be structured as a Cargo workspace containing the core library, alongside a Python project managed by PyO3/Maturin.

## Proposed Structure

```text
fastchunk/
├── Cargo.toml                 # Workspace manifest
├── crates/
│   ├── fastchunk-core/        # Pure Rust implementation
│   │   ├── Cargo.toml
│   │   └── src/               # lib.rs, splitter.rs, merger.rs
│   └── fastchunk-python/      # PyO3 bindings
│       ├── Cargo.toml         # Depends on fastchunk-core
│       └── src/               # lib.rs (Python class definitions)
├── python/
│   └── fastchunk/             # Python type hints (.pyi) and Python-side wrappers
├── tests/
│   ├── compatibility/         # Differential tests (Pytest) comparing Rust vs LangChain
│   ├── integration/           # Python API tests
│   └── rust_unit/             # Internal Rust tests for `fastchunk-core`
├── benchmarks/                # pytest-benchmark or asv scripts
├── docs/                      # Implementation specs, roadmaps
└── research/                  # Prior competitor research
```

## Rationale
- **Separation of Concerns**: `fastchunk-core` knows nothing about Python. It accepts `&str` and returns `Vec<&str>`. This makes it highly testable via standard `cargo test` and allows it to be published as a standalone Rust crate in the future.
- **`fastchunk-python`**: Contains all PyO3 boilerplate. It handles converting Python strings to Rust `&str`, executing the split, and converting the `Vec<&str>` back to a Python `List[str]`.
- **`tests/compatibility/`**: By placing the differential tests in a Python-driven `tests` folder, we can easily `pip install langchain` in the test environment and run `pytest` to compare outputs.
- **Maturin Build System**: The root should be configured to use `maturin` for seamless cross-compilation of the Rust code into a Python wheel.

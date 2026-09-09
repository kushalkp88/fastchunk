import pytest
from fastchunk import RecursiveCharacterTextSplitter as FastChunkSplitter
import langchain_text_splitters as ts
import warnings

def generate_text(size_kb, kind="plain"):
    chars = size_kb * 1024
    if kind == "plain":
        paragraph = "This is a simple plain English paragraph used for benchmarking text splitters. It contains average sized words and typical punctuation. " * 5
        paragraph += "\n\n"
        repetitions = (chars // len(paragraph)) + 1
        return (paragraph * repetitions)[:chars]
    elif kind == "markdown":
        block = "## Markdown Heading\n\nHere is a paragraph with some **bold** text and `inline code`.\n\n```python\ndef foo():\n    return 'bar'\n```\n\n"
        repetitions = (chars // len(block)) + 1
        return (block * repetitions)[:chars]
    elif kind == "source_code":
        block = "def recursive_function(n):\n    if n <= 1:\n        return n\n    return recursive_function(n-1) + recursive_function(n-2)\n\n"
        repetitions = (chars // len(block)) + 1
        return (block * repetitions)[:chars]
    elif kind == "unicode":
        block = "これはテスト文書です。ベンチマークの目的で使用されます。テキストを正しく分割できるか確認します。\n\n"
        repetitions = (chars // len(block)) + 1
        return (block * repetitions)[:chars]
    elif kind == "emoji":
        block = "Hello world! 👨‍👩‍👧‍👦 This is a test 🚀 with multi-byte emojis! 🍕🍔\n\n"
        repetitions = (chars // len(block)) + 1
        return (block * repetitions)[:chars]
    else:
        raise ValueError("Unknown kind")

def run_fastchunk(text, chunk_size, chunk_overlap):
    splitter = FastChunkSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

def run_langchain(text, chunk_size, chunk_overlap):
    splitter = ts.RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

def assert_parity(text, chunk_size, chunk_overlap):
    lc = run_langchain(text, chunk_size, chunk_overlap)
    fc = run_fastchunk(text, chunk_size, chunk_overlap)
    if lc != fc:
        warnings.warn(f"Parity failure for chunk_size={chunk_size}, overlap={chunk_overlap}")
        assert lc == fc

# Since `pytest-benchmark` generates individual tests, we use parameterization.
# But for exact reporting mirroring the previous script, we define explicit test functions.

configs = [
    (1000, 200),
    (500, 50),
    (2000, 200)
]

sizes = [1, 10, 100, 1000]
kinds = ["plain", "markdown", "source_code", "unicode", "emoji"]

def pytest_generate_tests(metafunc):
    if "text_params" in metafunc.fixturenames:
        params = []
        ids = []
        for size in sizes:
            for kind in kinds:
                for c_size, c_overlap in configs:
                    params.append((size, kind, c_size, c_overlap))
                    ids.append(f"{size}kb_{kind}_{c_size}_{c_overlap}")
        metafunc.parametrize("text_params", params, ids=ids)

def test_fastchunk_perf(benchmark, text_params):
    size, kind, c_size, c_overlap = text_params
    text = generate_text(size, kind)
    assert_parity(text, c_size, c_overlap)
    benchmark(run_fastchunk, text, c_size, c_overlap)

def test_langchain_perf(benchmark, text_params):
    size, kind, c_size, c_overlap = text_params
    text = generate_text(size, kind)
    assert_parity(text, c_size, c_overlap)
    benchmark(run_langchain, text, c_size, c_overlap)

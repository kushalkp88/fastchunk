import pytest
from fastchunk import RecursiveCharacterTextSplitter as FastChunkSplitter
import langchain_text_splitters as ts

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

# Fixtures
@pytest.fixture(scope="session")
def data_1kb_plain(): return generate_text(1, "plain")

@pytest.fixture(scope="session")
def data_10kb_plain(): return generate_text(10, "plain")

@pytest.fixture(scope="session")
def data_100kb_plain(): return generate_text(100, "plain")

@pytest.fixture(scope="session")
def data_1mb_plain(): return generate_text(1000, "plain")

@pytest.fixture(scope="session")
def data_10kb_markdown(): return generate_text(10, "markdown")

@pytest.fixture(scope="session")
def data_10kb_source(): return generate_text(10, "source_code")

@pytest.fixture(scope="session")
def data_10kb_unicode(): return generate_text(10, "unicode")

@pytest.fixture(scope="session")
def data_10kb_emoji(): return generate_text(10, "emoji")


# Benchmarks
def assert_parity(text, chunk_size, chunk_overlap):
    lc = run_langchain(text, chunk_size, chunk_overlap)
    fc = run_fastchunk(text, chunk_size, chunk_overlap)
    assert lc == fc, 'Output parity failure!'

def run_fastchunk(text, chunk_size, chunk_overlap):
    splitter = FastChunkSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

def run_langchain(text, chunk_size, chunk_overlap):
    splitter = ts.RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

# Conf A: 1000/200
def test_fastchunk_10kb_plain_1000_200(benchmark, data_10kb_plain):
    assert_parity(data_10kb_plain, 1000, 200)
    benchmark(run_fastchunk, data_10kb_plain, 1000, 200)
def test_langchain_10kb_plain_1000_200(benchmark, data_10kb_plain): benchmark(run_langchain, data_10kb_plain, 1000, 200)

def test_fastchunk_10kb_markdown_1000_200(benchmark, data_10kb_markdown):
    assert_parity(data_10kb_markdown, 1000, 200)
    benchmark(run_fastchunk, data_10kb_markdown, 1000, 200)
def test_langchain_10kb_markdown_1000_200(benchmark, data_10kb_markdown): benchmark(run_langchain, data_10kb_markdown, 1000, 200)

def test_fastchunk_10kb_source_1000_200(benchmark, data_10kb_source):
    assert_parity(data_10kb_source, 1000, 200)
    benchmark(run_fastchunk, data_10kb_source, 1000, 200)
def test_langchain_10kb_source_1000_200(benchmark, data_10kb_source): benchmark(run_langchain, data_10kb_source, 1000, 200)

def test_fastchunk_10kb_unicode_1000_200(benchmark, data_10kb_unicode):
    assert_parity(data_10kb_unicode, 1000, 200)
    benchmark(run_fastchunk, data_10kb_unicode, 1000, 200)
def test_langchain_10kb_unicode_1000_200(benchmark, data_10kb_unicode): benchmark(run_langchain, data_10kb_unicode, 1000, 200)

def test_fastchunk_10kb_emoji_1000_200(benchmark, data_10kb_emoji):
    assert_parity(data_10kb_emoji, 1000, 200)
    benchmark(run_fastchunk, data_10kb_emoji, 1000, 200)
def test_langchain_10kb_emoji_1000_200(benchmark, data_10kb_emoji): benchmark(run_langchain, data_10kb_emoji, 1000, 200)

def test_fastchunk_100kb_plain_1000_200(benchmark, data_100kb_plain):
    assert_parity(data_100kb_plain, 1000, 200)
    benchmark(run_fastchunk, data_100kb_plain, 1000, 200)
def test_langchain_100kb_plain_1000_200(benchmark, data_100kb_plain): benchmark(run_langchain, data_100kb_plain, 1000, 200)

# Conf B: 500/50
def test_fastchunk_10kb_plain_500_50(benchmark, data_10kb_plain):
    assert_parity(data_10kb_plain, 500, 50)
    benchmark(run_fastchunk, data_10kb_plain, 500, 50)
def test_langchain_10kb_plain_500_50(benchmark, data_10kb_plain): benchmark(run_langchain, data_10kb_plain, 500, 50)

# Conf C: 2000/200
def test_fastchunk_10kb_plain_2000_200(benchmark, data_10kb_plain):
    assert_parity(data_10kb_plain, 2000, 200)
    benchmark(run_fastchunk, data_10kb_plain, 2000, 200)
def test_langchain_10kb_plain_2000_200(benchmark, data_10kb_plain): benchmark(run_langchain, data_10kb_plain, 2000, 200)

def test_fastchunk_1kb_plain_1000_200(benchmark, data_1kb_plain):
    assert_parity(data_1kb_plain, 1000, 200)
    benchmark(run_fastchunk, data_1kb_plain, 1000, 200)
def test_langchain_1kb_plain_1000_200(benchmark, data_1kb_plain): benchmark(run_langchain, data_1kb_plain, 1000, 200)

def test_fastchunk_1mb_plain_1000_200(benchmark, data_1mb_plain):
    assert_parity(data_1mb_plain, 1000, 200)
    benchmark(run_fastchunk, data_1mb_plain, 1000, 200)
def test_langchain_1mb_plain_1000_200(benchmark, data_1mb_plain): benchmark(run_langchain, data_1mb_plain, 1000, 200)

@pytest.fixture(scope="session")
def data_100kb_unicode_fix(): return generate_text(100, "unicode")

def test_fastchunk_100kb_unicode_1000_200(benchmark, data_100kb_unicode_fix):
    assert_parity(data_100kb_unicode_fix, 1000, 200)
    benchmark(run_fastchunk, data_100kb_unicode_fix, 1000, 200)
def test_langchain_100kb_unicode_1000_200(benchmark, data_100kb_unicode_fix): benchmark(run_langchain, data_100kb_unicode_fix, 1000, 200)

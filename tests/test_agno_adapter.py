import pytest
from agno.knowledge.chunking.strategy import ChunkingStrategy
from agno.knowledge.document.base import Document
from agno.knowledge.reader.text_reader import TextReader
import io

from fastchunk.agno import FastChunking


def test_isinstance_agno_base():
    strategy = FastChunking()
    assert isinstance(strategy, ChunkingStrategy)


def test_basic_chunking():
    text = "First section content here.\n\nSecond section content here which exceeds chunk size limit."
    strategy = FastChunking(chunk_size=35, overlap=5)
    doc = Document(id="doc-1", name="basic_doc", content=text, meta_data={"source": "test"})
    chunks = strategy.chunk(doc)

    assert len(chunks) > 1
    assert all(isinstance(c, Document) for c in chunks)
    assert chunks[0].id.startswith("doc-1_")
    assert chunks[0].name == "basic_doc"
    assert chunks[0].meta_data["source"] == "test"
    assert chunks[0].meta_data["chunk"] == 1
    assert "chunk_size" in chunks[0].meta_data


def test_content_shorter_than_chunk_size():
    doc = Document(id="short-1", content="Short content", meta_data={"k": "v"})
    strategy = FastChunking(chunk_size=100, overlap=0)
    chunks = strategy.chunk(doc)
    assert len(chunks) == 1
    assert chunks[0] == doc


def test_multiple_documents():
    docs = [
        Document(id="d1", content="Alpha beta gamma delta epsilon zeta eta theta", meta_data={"doc": 1}),
        Document(id="d2", content="One two three four five six seven eight nine ten", meta_data={"doc": 2}),
    ]
    strategy = FastChunking(chunk_size=20, overlap=0)
    all_chunks = [c for doc in docs for c in strategy.chunk(doc)]
    assert len(all_chunks) >= 4
    d1_chunks = [c for c in all_chunks if c.meta_data.get("doc") == 1]
    d2_chunks = [c for c in all_chunks if c.meta_data.get("doc") == 2]
    assert len(d1_chunks) >= 2
    assert len(d2_chunks) >= 2


def test_metadata_preservation_and_isolation():
    shared_tags = ["tag1"]
    doc = Document(
        id="d-meta",
        content="Paragraph one to split.\n\nParagraph two to split.",
        meta_data={"tags": shared_tags, "author": "FastChunk"},
    )
    strategy = FastChunking(chunk_size=25, overlap=0)
    chunks = strategy.chunk(doc)
    assert len(chunks) == 2

    # Mutate chunk 0 metadata
    chunks[0].meta_data["tags"].append("mutated")
    assert chunks[1].meta_data["tags"] == ["tag1"]
    assert chunks[0].meta_data["author"] == "FastChunk"
    assert chunks[1].meta_data["author"] == "FastChunk"


def test_chunk_size_and_overlap():
    text = "abcdefghijklmnopqrstuvwxyz"
    strategy = FastChunking(chunk_size=10, overlap=2)
    splits = strategy.split_text(text)
    assert len(splits) > 1
    assert all(len(s) <= 10 for s in splits)


def test_custom_separators():
    text = "item1|item2|item3|item4"
    strategy = FastChunking(separators=["|"], chunk_size=10, overlap=0)
    splits = strategy.split_text(text)
    assert splits == ["item1", "|item2", "|item3", "|item4"]


def test_keep_separator():
    text = "alpha|beta|gamma"
    strat_false = FastChunking(separators=["|"], keep_separator=False, chunk_size=8, overlap=0)
    assert strat_false.split_text(text) == ["alpha", "beta", "gamma"]

    strat_start = FastChunking(separators=["|"], keep_separator="start", chunk_size=8, overlap=0)
    assert strat_start.split_text(text) == ["alpha", "|beta", "|gamma"]


def test_strip_whitespace():
    text = "   leading and trailing whitespace chunk   "
    strat_strip = FastChunking(chunk_size=50, overlap=0, strip_whitespace=True)
    assert strat_strip.split_text(text) == ["leading and trailing whitespace chunk"]

    strat_no_strip = FastChunking(chunk_size=50, overlap=0, strip_whitespace=False)
    assert strat_no_strip.split_text(text) == ["   leading and trailing whitespace chunk   "]


def test_empty_input():
    strategy = FastChunking()
    assert strategy.chunk(Document(content="")) == []


def test_unicode_cjk():
    cjk_text = "自然语言处理是计算机科学领域与人工智能领域中的一个重要方向。\n\n它研究能实现人与计算机之间用自然语言进行有效通信的各种理论和方法。"
    strategy = FastChunking(chunk_size=20, overlap=5)
    doc = Document(content=cjk_text, meta_data={"lang": "zh"})
    chunks = strategy.chunk(doc)
    assert len(chunks) > 1
    assert all(isinstance(c, Document) for c in chunks)
    assert all(c.meta_data["lang"] == "zh" for c in chunks)


def test_custom_tokenizer_rejection():
    with pytest.raises(NotImplementedError, match="Custom tokenizers/length_functions are not supported"):
        FastChunking(tokenizer=lambda x: len(x))

    with pytest.raises(NotImplementedError, match="Custom length_functions are not supported"):
        FastChunking(length_function=lambda x: len(x))


def test_text_reader_integration():
    strategy = FastChunking(chunk_size=30, overlap=5)
    reader = TextReader(chunking_strategy=strategy)
    buf = io.BytesIO(b"Hello world! This is a test for Agno TextReader integration with FastChunking.")
    docs = reader.read(buf)
    assert len(docs) > 1
    assert all(isinstance(d, Document) for d in docs)
    assert docs[0].meta_data["chunk"] == 1


def test_missing_agno_import_error():
    import builtins
    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("agno"):
            raise ImportError(f"No module named {name}")
        return orig_import(name, *args, **kwargs)

    try:
        builtins.__import__ = fake_import
        from fastchunk import fastchunk as m
        agno_sub = m.agno
        if hasattr(agno_sub, "FastChunking"):
            delattr(agno_sub, "FastChunking")

        with pytest.raises(ImportError, match="agno is required"):
            _ = agno_sub.FastChunking
    finally:
        builtins.__import__ = orig_import
        from fastchunk.agno import FastChunking

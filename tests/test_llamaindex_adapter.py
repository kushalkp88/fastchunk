import pytest
from llama_index.core.node_parser import TextSplitter, NodeParser
from llama_index.core.schema import Document, TextNode, NodeRelationship
from llama_index.core.ingestion import IngestionPipeline

from fastchunk.llamaindex import FastChunkNodeParser
import fastchunk


def test_isinstance_llamaindex_base():
    parser = FastChunkNodeParser()
    assert isinstance(parser, TextSplitter)
    assert isinstance(parser, NodeParser)
    assert parser.class_name() == "FastChunkNodeParser"


def test_basic_document_splitting():
    text = "Sentence one is here. Sentence two is longer and exceeds chunk size."
    parser = FastChunkNodeParser(chunk_size=25, chunk_overlap=5)
    doc = Document(text=text, metadata={"file": "test.txt"})
    nodes = parser.get_nodes_from_documents([doc])

    assert len(nodes) > 1
    assert all(isinstance(n, TextNode) for n in nodes)
    assert "".join([n.text for n in nodes]) != ""


def test_multiple_documents():
    docs = [
        Document(text="Document one has some text to split.", metadata={"id": 1}),
        Document(text="Document two has different text to split.", metadata={"id": 2}),
    ]
    parser = FastChunkNodeParser(chunk_size=20, chunk_overlap=0)
    nodes = parser.get_nodes_from_documents(docs)

    assert len(nodes) >= 4
    doc1_nodes = [n for n in nodes if n.metadata.get("id") == 1]
    doc2_nodes = [n for n in nodes if n.metadata.get("id") == 2]
    assert len(doc1_nodes) >= 2
    assert len(doc2_nodes) >= 2


def test_metadata_preservation():
    doc = Document(
        text="A document with rich metadata to verify preservation.",
        metadata={"author": "FastChunk Team", "year": 2026, "tags": ["rag", "rust"]},
    )
    parser = FastChunkNodeParser(chunk_size=30, chunk_overlap=5)
    nodes = parser.get_nodes_from_documents([doc])

    for n in nodes:
        assert n.metadata["author"] == "FastChunk Team"
        assert n.metadata["year"] == 2026
        assert n.metadata["tags"] == ["rag", "rust"]


def test_metadata_isolation():
    shared_tags = ["alpha"]
    doc = Document(
        text="A document testing that mutating node metadata does not leak.",
        metadata={"tags": shared_tags},
    )
    parser = FastChunkNodeParser(chunk_size=25, chunk_overlap=0)
    nodes = parser.get_nodes_from_documents([doc])
    assert len(nodes) >= 2

    # Mutate node 0 metadata
    nodes[0].metadata["tags"] = ["mutated"]
    assert nodes[1].metadata["tags"] == ["alpha"]


def test_chunk_size_and_overlap():
    text = "abcdefghijklmnopqrstuvwxyz"
    parser = FastChunkNodeParser(chunk_size=10, chunk_overlap=2)
    splits = parser.split_text(text)
    assert len(splits) > 1
    assert all(len(s) <= 10 for s in splits)


def test_custom_separators():
    text = "item1|item2|item3|item4"
    parser = FastChunkNodeParser(separators=["|"], chunk_size=10, chunk_overlap=0)
    splits = parser.split_text(text)
    assert splits == ["item1", "|item2", "|item3", "|item4"]


def test_keep_separator():
    text = "alpha|beta|gamma"
    parser_false = FastChunkNodeParser(separators=["|"], keep_separator=False, chunk_size=8, chunk_overlap=0)
    assert parser_false.split_text(text) == ["alpha", "beta", "gamma"]

    parser_start = FastChunkNodeParser(separators=["|"], keep_separator="start", chunk_size=8, chunk_overlap=0)
    assert parser_start.split_text(text) == ["alpha", "|beta", "|gamma"]


def test_strip_whitespace():
    text = "   chunk with leading and trailing spaces   "
    parser_strip = FastChunkNodeParser(chunk_size=50, chunk_overlap=0, strip_whitespace=True)
    assert parser_strip.split_text(text) == ["chunk with leading and trailing spaces"]

    parser_no_strip = FastChunkNodeParser(chunk_size=50, chunk_overlap=0, strip_whitespace=False)
    assert parser_no_strip.split_text(text) == ["   chunk with leading and trailing spaces   "]


def test_empty_documents():
    parser = FastChunkNodeParser()
    assert parser.get_nodes_from_documents([]) == []

    empty_doc = Document(text="")
    assert parser.get_nodes_from_documents([empty_doc]) == []


def test_unicode_cjk():
    cjk_text = "自然语言处理是计算机科学领域与人工智能领域中的一个重要方向。\n\n它研究能实现人与计算机之间用自然语言进行有效通信的各种理论和方法。"
    parser = FastChunkNodeParser(chunk_size=20, chunk_overlap=5)
    doc = Document(text=cjk_text, metadata={"lang": "zh"})
    nodes = parser.get_nodes_from_documents([doc])
    assert len(nodes) > 1
    assert all(isinstance(n, TextNode) for n in nodes)
    assert all(n.metadata["lang"] == "zh" for n in nodes)


def test_markdown():
    md_text = "# FastChunk\n\nHigh performance chunker.\n\n## Subheading\n\nDetails here."
    parser = FastChunkNodeParser(chunk_size=25, chunk_overlap=0)
    doc = Document(text=md_text)
    nodes = parser.get_nodes_from_documents([doc])
    assert len(nodes) > 1


def test_source_and_node_relationships():
    doc = Document(text="Chunk 1 content here.\n\nChunk 2 content here.\n\nChunk 3 content here.", id_="parent-doc-123")
    parser = FastChunkNodeParser(chunk_size=25, chunk_overlap=0)
    nodes = parser.get_nodes_from_documents([doc])

    assert len(nodes) == 3
    # Source relationship check
    for n in nodes:
        assert NodeRelationship.SOURCE in n.relationships
        assert n.relationships[NodeRelationship.SOURCE].node_id == "parent-doc-123"

    # Prev / Next relationship check
    assert NodeRelationship.PREVIOUS not in nodes[0].relationships
    assert NodeRelationship.NEXT in nodes[0].relationships
    assert nodes[0].relationships[NodeRelationship.NEXT].node_id == nodes[1].node_id

    assert NodeRelationship.PREVIOUS in nodes[1].relationships
    assert nodes[1].relationships[NodeRelationship.PREVIOUS].node_id == nodes[0].node_id
    assert NodeRelationship.NEXT in nodes[1].relationships
    assert nodes[1].relationships[NodeRelationship.NEXT].node_id == nodes[2].node_id

    assert NodeRelationship.PREVIOUS in nodes[2].relationships
    assert nodes[2].relationships[NodeRelationship.PREVIOUS].node_id == nodes[1].node_id
    assert NodeRelationship.NEXT not in nodes[2].relationships


def test_ingestion_pipeline_roundtrip():
    doc = Document(text="Pipeline processing test with FastChunkNodeParser transformation.", metadata={"topic": "rag"})
    pipeline = IngestionPipeline(
        transformations=[FastChunkNodeParser(chunk_size=25, chunk_overlap=5)]
    )
    nodes = pipeline.run(documents=[doc])
    assert len(nodes) > 1
    assert all(isinstance(n, TextNode) for n in nodes)
    assert all(n.metadata["topic"] == "rag" for n in nodes)


def test_missing_llamaindex_import_error():
    import builtins
    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("llama_index"):
            raise ImportError(f"No module named {name}")
        return orig_import(name, *args, **kwargs)

    try:
        builtins.__import__ = fake_import
        from fastchunk import fastchunk as m
        llamaindex_sub = m.llamaindex
        if hasattr(llamaindex_sub, "FastChunkNodeParser"):
            delattr(llamaindex_sub, "FastChunkNodeParser")

        with pytest.raises(ImportError, match="llama-index-core is required"):
            _ = llamaindex_sub.FastChunkNodeParser
    finally:
        builtins.__import__ = orig_import
        from fastchunk.llamaindex import FastChunkNodeParser

def test_custom_tokenizer_rejection():
    with pytest.raises(NotImplementedError, match="Custom tokenizers/length_functions are not supported"):
        FastChunkNodeParser(tokenizer=lambda x: len(x))

    with pytest.raises(NotImplementedError, match="Custom length_functions are not supported"):
        FastChunkNodeParser(length_function=lambda x: len(x))

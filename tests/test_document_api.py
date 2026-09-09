import copy
import pytest
from fastchunk import RecursiveCharacterTextSplitter, Document


class CustomDuckDocument:
    def __init__(self, page_content: str, metadata: dict | None = None):
        self.page_content = page_content
        self.metadata = metadata or {}


def test_document_instantiation():
    doc = Document("hello world", {"source": "test"})
    assert doc.page_content == "hello world"
    assert doc.metadata == {"source": "test"}
    assert "Document" in repr(doc)
    assert "hello world" in repr(doc)


def test_document_default_metadata():
    doc = Document("hello")
    assert doc.page_content == "hello"
    assert doc.metadata == {}


def test_document_equality():
    doc1 = Document("abc", {"k": "v"})
    doc2 = Document("abc", {"k": "v"})
    doc3 = Document("abc", {"k": "other"})
    doc4 = Document("def", {"k": "v"})

    assert doc1 == doc2
    assert doc1 != doc3
    assert doc1 != doc4

    # Duck-typed equality with any object providing page_content and metadata
    duck_doc = CustomDuckDocument("abc", {"k": "v"})
    assert doc1 == duck_doc


def test_create_documents_basic():
    splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=0)
    texts = ["abcdef", "123456"]
    metadatas = [{"type": "alpha"}, {"type": "digit"}]
    docs = splitter.create_documents(texts, metadatas=metadatas)

    assert len(docs) == 4
    assert docs[0].page_content == "abcde"
    assert docs[0].metadata == {"type": "alpha"}
    assert docs[1].page_content == "f"
    assert docs[1].metadata == {"type": "alpha"}
    assert docs[2].page_content == "12345"
    assert docs[2].metadata == {"type": "digit"}
    assert docs[3].page_content == "6"
    assert docs[3].metadata == {"type": "digit"}


def test_create_documents_without_metadatas():
    splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=0)
    texts = ["abcdef"]
    docs = splitter.create_documents(texts)
    assert len(docs) == 2
    assert docs[0].page_content == "abcde"
    assert docs[0].metadata == {}
    assert docs[1].page_content == "f"
    assert docs[1].metadata == {}


def test_create_documents_metadata_isolation():
    splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=0)
    shared_meta = {"tags": ["initial"]}
    docs = splitter.create_documents(["abcdef"], metadatas=[shared_meta])

    assert len(docs) == 2
    # Modify original metadata dictionary
    shared_meta["tags"].append("mutated")
    shared_meta["extra"] = True

    # Confirm chunk 0 and chunk 1 were not mutated
    assert docs[0].metadata == {"tags": ["initial"]}
    assert docs[1].metadata == {"tags": ["initial"]}

    # Modify chunk 0 metadata, confirm chunk 1 is isolated
    docs[0].metadata["tags"].append("chunk0_only")
    assert docs[1].metadata == {"tags": ["initial"]}


def test_create_documents_empty_inputs():
    splitter = RecursiveCharacterTextSplitter()
    assert splitter.create_documents([]) == []
    assert splitter.create_documents([""]) == []


def test_create_documents_partial_metadatas():
    splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=0)
    texts = ["abc", "def"]
    metadatas = [{"idx": 0}]  # fewer metadata items than texts
    docs = splitter.create_documents(texts, metadatas=metadatas)
    assert len(docs) == 2
    assert docs[0].metadata == {"idx": 0}
    assert docs[1].metadata == {}


def test_split_documents_duck_typed_objects():
    splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=0)
    input_docs = [
        CustomDuckDocument("abcdef", {"id": 1}),
        Document("123456", {"id": 2}),
    ]
    out_docs = splitter.split_documents(input_docs)
    assert len(out_docs) == 4
    assert [d.page_content for d in out_docs] == ["abcde", "f", "12345", "6"]
    assert out_docs[0].metadata == {"id": 1}
    assert out_docs[1].metadata == {"id": 1}
    assert out_docs[2].metadata == {"id": 2}
    assert out_docs[3].metadata == {"id": 2}


def test_split_documents_dict_inputs():
    splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=0)
    dict_docs = [
        {"page_content": "abcdef", "metadata": {"source": "dict1"}},
        {"page_content": "123456", "metadata": {"source": "dict2"}},
    ]
    out_docs = splitter.split_documents(dict_docs)
    assert len(out_docs) == 4
    assert [d.page_content for d in out_docs] == ["abcde", "f", "12345", "6"]
    assert out_docs[0].metadata == {"source": "dict1"}
    assert out_docs[2].metadata == {"source": "dict2"}


def test_split_documents_dict_missing_metadata():
    splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=0)
    dict_docs = [{"page_content": "abcdef"}]
    out_docs = splitter.split_documents(dict_docs)
    assert len(out_docs) == 2
    assert out_docs[0].metadata == {}
    assert out_docs[1].metadata == {}


def test_split_documents_invalid_input():
    splitter = RecursiveCharacterTextSplitter()
    with pytest.raises(ValueError, match="must have 'page_content'"):
        splitter.split_documents(["invalid string instead of doc"])

    with pytest.raises(ValueError, match="must contain 'page_content'"):
        splitter.split_documents([{"bad_key": "content"}])


def test_split_documents_empty_inputs():
    splitter = RecursiveCharacterTextSplitter()
    assert splitter.split_documents([]) == []
    assert splitter.split_documents([Document("")]) == []
    assert splitter.split_documents([{"page_content": ""}]) == []


def test_split_documents_with_langchain_document():
    try:
        from langchain_core.documents import Document as LCDocument
    except ImportError:
        pytest.skip("langchain_core not installed")

    splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=0)
    lc_docs = [
        LCDocument(page_content="abcdef", metadata={"origin": "langchain"}),
        LCDocument(page_content="xyz123", metadata={"origin": "langchain2"}),
    ]
    res = splitter.split_documents(lc_docs)
    assert len(res) == 4
    assert isinstance(res[0], Document)
    assert res[0].page_content == "abcde"
    assert res[0].metadata == {"origin": "langchain"}
    assert res[1].page_content == "f"
    assert res[1].metadata == {"origin": "langchain"}
    assert res[2].page_content == "xyz12"
    assert res[2].metadata == {"origin": "langchain2"}

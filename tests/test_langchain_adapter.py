import pytest
from langchain_text_splitters import RecursiveCharacterTextSplitter as LangChainSplitter, Language
from langchain_text_splitters.base import TextSplitter
from langchain_core.documents import Document as LCDocument

from fastchunk.langchain import FastChunkTextSplitter


def test_isinstance_langchain_base():
    splitter = FastChunkTextSplitter()
    assert isinstance(splitter, TextSplitter)


def test_split_text_parity():
    text = "Hello world! This is a test document.\n\nIt has multiple paragraphs and sections.\nLet's see how it splits."
    fc_splitter = FastChunkTextSplitter(chunk_size=30, chunk_overlap=5)
    lc_splitter = LangChainSplitter(chunk_size=30, chunk_overlap=5)

    assert fc_splitter.split_text(text) == lc_splitter.split_text(text)


def test_create_documents():
    fc_splitter = FastChunkTextSplitter(chunk_size=20, chunk_overlap=0)
    texts = ["First document content here.", "Second document text."]
    metadatas = [{"source": "doc1.txt"}, {"source": "doc2.txt"}]

    docs = fc_splitter.create_documents(texts, metadatas=metadatas)
    assert len(docs) > 0
    assert all(isinstance(d, LCDocument) for d in docs)
    assert docs[0].metadata["source"] == "doc1.txt"


def test_create_documents_add_start_index():
    fc_splitter = FastChunkTextSplitter(chunk_size=20, chunk_overlap=0, add_start_index=True)
    docs = fc_splitter.create_documents(["First document content here."])
    assert len(docs) > 0
    assert "start_index" in docs[0].metadata
    assert docs[0].metadata["start_index"] == 0


def test_split_documents():
    fc_splitter = FastChunkTextSplitter(chunk_size=20, chunk_overlap=0)
    in_docs = [
        LCDocument(page_content="Alpha beta gamma delta epsilon", metadata={"topic": "greek"}),
        LCDocument(page_content="One two three four five six", metadata={"topic": "numbers"}),
    ]
    out_docs = fc_splitter.split_documents(in_docs)
    assert len(out_docs) > 0
    assert all(isinstance(d, LCDocument) for d in out_docs)
    assert out_docs[0].metadata["topic"] == "greek"


def test_metadata_isolation():
    fc_splitter = FastChunkTextSplitter(chunk_size=15, chunk_overlap=0)
    meta = {"tags": ["v1"]}
    docs = fc_splitter.create_documents(["Multiple parts that definitely exceed chunk size"], metadatas=[meta])
    assert len(docs) >= 2

    # Mutate source dict
    meta["tags"].append("v2")
    assert docs[0].metadata["tags"] == ["v1"]

    # Mutate chunk 0
    docs[0].metadata["tags"].append("chunk0")
    assert docs[1].metadata["tags"] == ["v1"]


def test_separators_and_keep_separator():
    text = "item1|item2|item3|item4"
    fc = FastChunkTextSplitter(separators=["|"], keep_separator=True, chunk_size=10, chunk_overlap=0)
    lc = LangChainSplitter(separators=["|"], keep_separator=True, chunk_size=10, chunk_overlap=0)
    assert fc.split_text(text) == lc.split_text(text)

    fc_false = FastChunkTextSplitter(separators=["|"], keep_separator=False, chunk_size=10, chunk_overlap=0)
    lc_false = LangChainSplitter(separators=["|"], keep_separator=False, chunk_size=10, chunk_overlap=0)
    assert fc_false.split_text(text) == lc_false.split_text(text)


def test_strip_whitespace():
    text = "   leading and trailing whitespace chunk   "
    fc = FastChunkTextSplitter(chunk_size=50, chunk_overlap=0, strip_whitespace=True)
    lc = LangChainSplitter(chunk_size=50, chunk_overlap=0, strip_whitespace=True)
    assert fc.split_text(text) == lc.split_text(text)


def test_from_language_markdown():
    md_text = "# Header 1\n\nSome intro text.\n\n## Header 2\n\n- item 1\n- item 2\n"
    fc = FastChunkTextSplitter.from_language(Language.MARKDOWN, chunk_size=30, chunk_overlap=0)
    lc = LangChainSplitter.from_language(Language.MARKDOWN, chunk_size=30, chunk_overlap=0)
    assert fc.split_text(md_text) == lc.split_text(md_text)


def test_from_language_python():
    py_code = """class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
"""
    fc = FastChunkTextSplitter.from_language(Language.PYTHON, chunk_size=40, chunk_overlap=0)
    lc = LangChainSplitter.from_language(Language.PYTHON, chunk_size=40, chunk_overlap=0)
    assert fc.split_text(py_code) == lc.split_text(py_code)


def test_unicode_cjk():
    cjk_text = "自然语言处理是计算机科学领域与人工智能领域中的一个重要方向。\n\n它研究能实现人与计算机之间用自然语言进行有效通信的各种理论和方法。"
    fc = FastChunkTextSplitter(chunk_size=25, chunk_overlap=5)
    lc = LangChainSplitter(chunk_size=25, chunk_overlap=5)
    assert fc.split_text(cjk_text) == lc.split_text(cjk_text)

def test_all_keep_separator_values():
    text = "alpha\n\nbeta\n\ngamma"
    for ks in [False, True, "start", "end"]:
        fc = FastChunkTextSplitter(chunk_size=8, chunk_overlap=0, keep_separator=ks)
        lc = LangChainSplitter(chunk_size=8, chunk_overlap=0, keep_separator=ks)
        assert fc.split_text(text) == lc.split_text(text)


def test_custom_length_function_rejection():
    with pytest.raises(NotImplementedError, match="Custom length_functions are not supported"):
        FastChunkTextSplitter(length_function=lambda x: len(x))


def test_transform_documents():
    fc = FastChunkTextSplitter(chunk_size=20, chunk_overlap=0)
    in_docs = [
        LCDocument(page_content="Alpha beta gamma delta epsilon", metadata={"topic": "greek"}),
        LCDocument(page_content="One two three four five six", metadata={"topic": "numbers"}),
    ]
    out_docs = fc.transform_documents(in_docs)
    assert len(out_docs) > 0
    assert all(isinstance(d, LCDocument) for d in out_docs)
    assert out_docs[0].metadata["topic"] == "greek"


def test_all_six_languages_parity():
    languages = [
        Language.PYTHON,
        Language.MARKDOWN,
        Language.JS,
        Language.RUST,
        Language.CPP,
        Language.GO,
    ]
    sample_texts = {
        Language.PYTHON: "class Foo:\n    def bar(self):\n        return 42\n",
        Language.MARKDOWN: "# Title\n\nSome text.\n\n## Subtitle\n\nMore text.\n",
        Language.JS: "function foo() {\n    return 42;\n}\n\nclass Bar {}\n",
        Language.RUST: "fn foo() -> i32 {\n    42\n}\n\nstruct Bar;\n",
        Language.CPP: "int foo() {\n    return 42;\n}\n\nclass Bar {};\n",
        Language.GO: "func foo() int {\n    return 42\n}\n\ntype Bar struct{}\n",
    }
    for lang in languages:
        fc = FastChunkTextSplitter.from_language(lang, chunk_size=30, chunk_overlap=0)
        lc = LangChainSplitter.from_language(lang, chunk_size=30, chunk_overlap=0)
        assert fc.split_text(sample_texts[lang]) == lc.split_text(sample_texts[lang])


def test_add_start_index_comprehensive():
    test_cases = [
        "The quick brown fox jumps over the lazy dog.",
        "abc abc abc abc abc abc abc abc abc abc",
        "banana banana banana banana banana",
        "Section 1\nDetails here.\nSection 2\nMore details here.\nSection 3\nFinal details.",
    ]
    for text in test_cases:
        for size, overlap in [(15, 5), (20, 10), (30, 0)]:
            fc = FastChunkTextSplitter(chunk_size=size, chunk_overlap=overlap, add_start_index=True)
            lc = LangChainSplitter(chunk_size=size, chunk_overlap=overlap, add_start_index=True)

            fc_docs = fc.create_documents([text])
            lc_docs = lc.create_documents([text])

            assert len(fc_docs) == len(lc_docs)
            for d1, d2 in zip(fc_docs, lc_docs):
                assert d1.page_content == d2.page_content
                assert d1.metadata["start_index"] == d2.metadata["start_index"]

def test_missing_langchain_import_error():
    import builtins
    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("langchain"):
            raise ImportError(f"No module named {name}")
        return orig_import(name, *args, **kwargs)

    try:
        builtins.__import__ = fake_import
        # Access through a new submodule instance
        from fastchunk import fastchunk as m
        # Trigger __getattr__ when langchain is missing
        langchain_sub = m.langchain
        # Reset cached class if any
        if hasattr(langchain_sub, "FastChunkTextSplitter"):
            delattr(langchain_sub, "FastChunkTextSplitter")

        with pytest.raises(ImportError, match="langchain-text-splitters is required"):
            _ = langchain_sub.FastChunkTextSplitter
    finally:
        builtins.__import__ = orig_import
        # Restore normal FastChunkTextSplitter on langchain_sub
        from fastchunk.langchain import FastChunkTextSplitter

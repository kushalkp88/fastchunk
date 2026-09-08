import pytest
from fastchunk import RecursiveCharacterTextSplitter

def test_import():
    assert RecursiveCharacterTextSplitter is not None

def test_constructor_defaults():
    splitter = RecursiveCharacterTextSplitter()
    assert splitter.split_text("test") == ["test"]

def test_chunk_size_validation():
    with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
        RecursiveCharacterTextSplitter(chunk_size=0)

def test_chunk_overlap_validation():
    with pytest.raises(ValueError, match="chunk_overlap must be greater than or equal to 0"):
        RecursiveCharacterTextSplitter(chunk_overlap=-1)

    with pytest.raises(ValueError, match="Got a larger chunk overlap"):
        RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=15)

def test_length_function_rejection():
    def custom_len(x): return len(x)
    with pytest.raises(NotImplementedError, match="Custom length_functions are not supported"):
        RecursiveCharacterTextSplitter(length_function=custom_len)

def test_keep_separator_validation():
    with pytest.raises(ValueError, match="keep_separator must be a boolean or 'start'/'end'"):
        RecursiveCharacterTextSplitter(keep_separator="middle")

def test_split_text_return_type():
    splitter = RecursiveCharacterTextSplitter()
    res = splitter.split_text("Hello\n\nWorld")
    assert isinstance(res, list)
    assert len(res) > 0
    assert isinstance(res[0], str)

def test_empty_text():
    splitter = RecursiveCharacterTextSplitter()
    assert splitter.split_text("") == []

def test_custom_separators():
    splitter = RecursiveCharacterTextSplitter(separators=["|", ","], chunk_size=3, chunk_overlap=0)
    assert splitter.split_text("a|b,c|d") == ["a", "|b", ",c", "|d"] # Let's see if this exact split behavior asserts correctly

def test_unicode():
    splitter = RecursiveCharacterTextSplitter(chunk_size=3, chunk_overlap=0)
    assert splitter.split_text("こんにちは世界") == ["こんに", "ちは世", "界"]

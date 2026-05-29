import pytest
from chronicle.src.indexer import LibrarianIndexer
from chronicle.src.utils.chunker import Chunker
from chronicle.src.utils.config import AppConfig

@pytest.fixture
def indexer_with_config():
    config = AppConfig(content_root="/tmp")
    return LibrarianIndexer(config=config)

def test_chunk_markdown_logic():
    # Test 1: Single small document
    content = "Small document."
    chunks = Chunker.chunk(content, window_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0]["type"] == "semantic_window"

    # Test 2: Large document with splitting and overlap
    # We use a small window_size (200) and overlap (50) to force multiple chunks
    para1 = "This is the first long paragraph that contains enough text to exceed the small window size we are testing."
    para2 = "This is the second paragraph which provides additional context and should trigger a split with overlap."
    content = f"{para1}\n\n{para2}"
    
    chunks = Chunker.chunk(content, window_size=100, overlap=20)
    
    # It should split into multiple chunks
    assert len(chunks) > 1
    assert chunks[0]["type"] == "semantic_window"
    # Overlap check: second chunk should start with end of first or similar
    assert chunks[0]["text"] != chunks[1]["text"]

def test_calculate_hash_consistency(indexer_with_config):
    # Setup
    text = "consistent content"
    
    # Act
    hash1 = indexer_with_config._calculate_hash(text)
    hash2 = indexer_with_config._calculate_hash(text)
    
    # Assert
    assert hash1 == hash2
    assert hash1 == "1604d02cf3ce7a673838d7e644fa9f4e7d0490844b4e266fe117740afb9bf228"

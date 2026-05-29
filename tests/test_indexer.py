import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock
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

@pytest.mark.asyncio
async def test_date_normalization_from_date_object(tmp_path):
    # Create mock temp blog file with date frontmatter
    blog_root = tmp_path / "blog"
    blog_root.mkdir()
    test_file = blog_root / "test-date.md"
    test_file.write_text("---\ntitle: Date Test\ndate: 2026-01-25\n---\nHello date normalization.")

    config = AppConfig(content_root=str(blog_root), db_path=str(tmp_path / "db"))
    indexer = LibrarianIndexer(config=config)
    indexer.provider = MagicMock()
    indexer.provider.embed_async = AsyncMock(return_value=[0.1, 0.2, 0.3])

    chunks = await indexer.process_file(str(test_file))
    assert len(chunks) > 0
    # Verify that the parsed date has been combined with midnight to become a datetime.datetime
    assert isinstance(chunks[0]["date"], datetime.datetime)
    assert chunks[0]["date"] == datetime.datetime(2026, 1, 25, 0, 0)

import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock
from chronicle.src.indexer import LibrarianIndexer
from chronicle.src.models import SearchResult
from chronicle.src.utils.config import AppConfig

@pytest.fixture
def mock_indexer(tmp_path):
    # Setup indexer with temporary paths and mocked dependencies
    blog_root = str(tmp_path / "blog")
    db_path = str(tmp_path / "db")
    os.makedirs(blog_root)
    
    config = AppConfig(blog_root=blog_root, db_path=db_path)
    
    with patch("lancedb.connect") as mock_connect:
        indexer = LibrarianIndexer(config=config)
        indexer.provider = MagicMock()
        # Mock embed_async to return an awaitable list
        indexer.provider.embed_async = AsyncMock(return_value=[0.1, 0.2, 0.3])
        # Store the mock db for test use
        indexer._mock_db = mock_connect.return_value
        return indexer

def test_search_result_mapping(mock_indexer):
    # Mock data that looks like LanceDB output
    raw_data = {
        "id": "slug_1",
        "text": "sample text",
        "source": "rel/path.md",
        "title": "Title",
        "slug": "slug",
        "content_hash": "abc",
        "chunk_type": "prose",
        "series": [],
        "tags": [],
        "draft": False,
        "file_hash": "file_abc",
        "_distance": 0.5
    }
    
    # Act
    result = mock_indexer._to_result(raw_data, mode="vector")
    
    # Assert
    assert isinstance(result, SearchResult)
    assert result.chunk.id == "slug_1"
    assert result.score == 0.5
    assert result.mode == "vector"

@pytest.mark.asyncio
async def test_rrf_logic_manual(mock_indexer):
    # Setup
    mock_indexer.store._table_exists = MagicMock(return_value=True)
    doc_a = {        "source": "post_a.md", "content_hash": "hash_a", "title": "A", "id": "a_1", 
        "text": "text a", "slug": "a", "chunk_type": "prose", "series": [], "tags": [],
        "draft": False, "file_hash": "h"
    }
    doc_b = {
        "source": "post_b.md", "content_hash": "hash_b", "title": "B", "id": "b_1", 
        "text": "text b", "slug": "b", "chunk_type": "prose", "series": [], "tags": [],
        "draft": False, "file_hash": "h"
    }
    
    vector_results = [doc_a, doc_b]
    fts_results = [doc_b, doc_a]
    
    table = MagicMock()
    mock_indexer.store.get_table = MagicMock(return_value=table)
    table.search.return_value.limit.return_value.to_list.side_effect = [vector_results, fts_results]
    
    # Act
    results = await mock_indexer.search("test query", limit=2, mode="hybrid")
    
    # Assert
    assert len(results) == 2
    assert results[0].chunk.title in ["A", "B"]
    assert results[0].mode == "hybrid"
    assert results[0].score > 0.03

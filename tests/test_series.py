import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from chronicle.src.series_manager import SeriesManager
from chronicle.src.indexer import LibrarianIndexer
from chronicle.src.utils.config import AppConfig
from chronicle.src.providers.base import LLMProvider

@pytest.fixture
def mock_indexer_for_series():
    indexer = MagicMock(spec=LibrarianIndexer)
    indexer.table_name = "blog_chunks"
    indexer.config = AppConfig()
    indexer.store = MagicMock()
    return indexer

@pytest.fixture
def mock_provider():
    return MagicMock(spec=LLMProvider)

@pytest.mark.asyncio
async def test_series_ledger_generation(mock_indexer_for_series, mock_provider):
    # Setup: Mock LanceDB table data
    table = MagicMock()
    mock_indexer_for_series.store.get_table.return_value = table
    
    chunks = [
        {"title": "Post 1", "series": ["Series A"], "text": "Content 1"},
        {"title": "Post 2", "series": ["Series A"], "text": "Content 2"},
    ]
    table.search.return_value.where.return_value.to_list.return_value = chunks
    
    mock_provider.chat_async = AsyncMock()
    mock_provider.chat_async.side_effect = [
        # 1st call for summary
        "Series summary text",
        # 2nd call for promises
        '{"promises": [{"source_post": "Post 1", "promise_text": "Later we will cover X", "topic": "X"}]}'
    ]
    
    manager = SeriesManager(mock_indexer_for_series, provider=mock_provider)
    
    # Act
    ledger = await manager.get_series_ledger("Series A")
    
    # Assert
    assert ledger.series_name == "Series A"
    assert ledger.posts_count == 2
    assert "Series summary" in ledger.summary
    assert ledger.open_promises[0].topic == "X"

@pytest.mark.asyncio
async def test_generate_handoff_brief(mock_indexer_for_series, mock_provider):
    table = MagicMock()
    mock_indexer_for_series.store.get_table.return_value = table
    
    chunks = [
        {"title": "Post 1", "series": ["Series A"], "text": "Content 1", "date": datetime(2026, 1, 1)},
        {"title": "Post 2", "series": ["Series A"], "text": "Content 2", "date": datetime(2026, 1, 2)},
    ]
    table.search.return_value.where.return_value.to_list.return_value = chunks
    
    mock_provider.chat_async = AsyncMock(return_value="""
    {
      "logical_gaps": ["Missing implementation detail of X"],
      "follow_ups": [
        {"title": "Implementing X", "rationale": "Because the previous posts only covered X theoretically.", "transition_hook": "Now that we have the theory..."}
      ]
    }
    """)
    
    manager = SeriesManager(mock_indexer_for_series, provider=mock_provider)
    brief = await manager.generate_handoff_brief("Series A")
    
    assert brief.series_name == "Series A"
    assert brief.last_post_title == "Post 2"
    assert len(brief.logical_gaps) == 1
    assert brief.logical_gaps[0] == "Missing implementation detail of X"
    assert len(brief.follow_ups) == 1
    assert brief.follow_ups[0].title == "Implementing X"

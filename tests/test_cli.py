import pytest
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from chronicle.main import run_main

@pytest.mark.asyncio
async def test_cli_subcommands_search():
    test_args = ["chronicle", "search", "TDD", "--limit", "3"]
    
    with patch("sys.argv", test_args), \
         patch("chronicle.main.load_config", return_value={}), \
         patch("chronicle.main.setup_logging"), \
         patch("chronicle.main.LLMProvider.get_provider") as mock_provider, \
         patch("chronicle.main.LibrarianIndexer") as mock_indexer_cls:
        
        mock_indexer = mock_indexer_cls.return_value
        mock_indexer.check_health.return_value = {"ollama": True}
        mock_indexer.search = AsyncMock(return_value=[])
        
        await run_main()
        
        mock_indexer.search.assert_called_once_with(
            "TDD",
            limit=3,
            mode="hybrid",
            series=None,
            published_only=False,
            per_post_limit=None
        )

@pytest.mark.asyncio
async def test_cli_subcommands_ledger_record():
    test_args = ["chronicle", "ledger", "record", "Topic", "Decision", "Rationale", "--scope", "global"]
    
    with patch("sys.argv", test_args), \
         patch("chronicle.main.load_config", return_value={}), \
         patch("chronicle.main.setup_logging"), \
         patch("chronicle.main.LLMProvider.get_provider"), \
         patch("chronicle.main.LibrarianIndexer") as mock_indexer_cls, \
         patch("chronicle.main.SessionLedger") as mock_ledger_cls:
         
        mock_indexer = mock_indexer_cls.return_value
        mock_indexer.check_health.return_value = {"ollama": True}
        mock_ledger = mock_ledger_cls.return_value
        
        await run_main()
        
        mock_ledger.record_decision.assert_called_once_with(
            "Topic", "Decision", "Rationale", scope="global", series=None
        )

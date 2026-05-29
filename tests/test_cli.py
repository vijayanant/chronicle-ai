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
            published_only=True,
            per_post_limit=None
        )

@pytest.mark.asyncio
async def test_cli_subcommands_search_include_drafts():
    test_args = ["chronicle", "search", "TDD", "--limit", "3", "--include-drafts"]
    
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


@pytest.mark.asyncio
async def test_cli_subcommands_lint():
    test_args = ["chronicle", "lint", "draft.md"]
    from pathlib import Path
    
    original_exists = Path.exists
    original_is_file = Path.is_file
    
    def side_effect_exists(self):
        if "draft.md" in str(self):
            return True
        return original_exists(self)
        
    def side_effect_is_file(self):
        if "draft.md" in str(self):
            return True
        return original_is_file(self)
    
    with patch("sys.argv", test_args), \
         patch("chronicle.main.load_config", return_value={}), \
         patch("chronicle.main.setup_logging"), \
         patch("chronicle.main.LLMProvider.get_provider") as mock_provider, \
         patch("chronicle.main.LibrarianIndexer") as mock_indexer_cls, \
         patch.object(Path, "exists", side_effect_exists), \
         patch.object(Path, "is_file", side_effect_is_file), \
         patch("chronicle.src.linter.ProseLinter") as mock_linter_cls:
         
        mock_indexer = mock_indexer_cls.return_value
        mock_indexer.check_health.return_value = {"ollama": True}
        mock_linter = mock_linter_cls.return_value
        mock_linter.lint_file.return_value = []
        
        await run_main()
        
        mock_linter.lint_file.assert_called_once_with(str(Path("draft.md").resolve()), include_drafts=True)

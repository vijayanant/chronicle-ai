import pytest
import sys
from unittest.mock import patch, MagicMock, AsyncMock, ANY
from chronicle.main import run_main

@pytest.mark.asyncio
async def test_cli_subcommands_search():
    test_args = ["chronicle", "search", "TDD", "--limit", "3"]
    
    with patch("sys.argv", test_args), \
         patch("chronicle.main.load_config", return_value={}), \
         patch("chronicle.main.setup_logging"), \
         patch("chronicle.main.LLMProvider.get_provider") as mock_provider, \
         patch("chronicle.main.api.search_blog_api", new_callable=AsyncMock) as mock_search_api:
        
        mock_search_api.return_value = []
        
        await run_main()
        
        mock_search_api.assert_called_once_with(
            ANY,
            "TDD",
            limit=3,
            mode="hybrid",
            series=None,
            include_drafts=False,
            per_post_limit=None
        )

@pytest.mark.asyncio
async def test_cli_subcommands_search_include_drafts():
    test_args = ["chronicle", "search", "TDD", "--limit", "3", "--include-drafts"]
    
    with patch("sys.argv", test_args), \
         patch("chronicle.main.load_config", return_value={}), \
         patch("chronicle.main.setup_logging"), \
         patch("chronicle.main.LLMProvider.get_provider") as mock_provider, \
         patch("chronicle.main.api.search_blog_api", new_callable=AsyncMock) as mock_search_api:
        
        mock_search_api.return_value = []
        
        await run_main()
        
        mock_search_api.assert_called_once_with(
            ANY,
            "TDD",
            limit=3,
            mode="hybrid",
            series=None,
            include_drafts=True,
            per_post_limit=None
        )

@pytest.mark.asyncio
async def test_cli_subcommands_ledger_record():
    test_args = ["chronicle", "ledger", "record", "Topic", "Decision", "Rationale", "--scope", "global"]
    
    with patch("sys.argv", test_args), \
         patch("chronicle.main.load_config", return_value={}), \
         patch("chronicle.main.setup_logging"), \
         patch("chronicle.main.LLMProvider.get_provider"), \
         patch("chronicle.main.api.record_decision_api") as mock_record_api:
         
        await run_main()
        
        mock_record_api.assert_called_once_with(
            ANY,
            "Topic",
            "Decision",
            "Rationale",
            scope="global",
            series=None
        )


@pytest.mark.asyncio
async def test_cli_subcommands_lint():
    test_args = ["chronicle", "lint", "draft.md"]
    
    with patch("sys.argv", test_args), \
         patch("chronicle.main.load_config", return_value={}), \
         patch("chronicle.main.setup_logging"), \
         patch("chronicle.main.LLMProvider.get_provider") as mock_provider, \
         patch("chronicle.main.api.lint_files_api") as mock_lint_api:
         
        mock_lint_api.return_value = {}
        
        await run_main()
        
        mock_lint_api.assert_called_once_with(
            ANY,
            "draft.md",
            include_drafts=False
        )

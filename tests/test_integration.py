import pytest
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from chronicle.src.indexer import LibrarianIndexer
from chronicle.src.guardian import GuardianAgent
from chronicle.src.session_memory import SessionLedger
from chronicle.src.utils.config import AppConfig

@pytest.mark.asyncio
async def test_full_drafting_lifecycle(tmp_path):
    # 1. Setup Environment
    blog_root = tmp_path / "blog"
    blog_root.mkdir()
    (blog_root / "post1.md").write_text("---\ntitle: Post 1\n---\nContent about TDD.")
    
    db_path = tmp_path / "db"
    ledger_path = tmp_path / "ledger.json"
    const_path = tmp_path / "const.md"
    const_path.write_text("# Constitution\n- Always use TDD.")
    
    config = AppConfig(
        content_root=str(blog_root),
        db_path=str(db_path),
        ledger_path=str(ledger_path),
        constitution_path=str(const_path)
    )
    
    # 2. Mock external dependencies (LLM)
    with patch("lancedb.connect") as mock_connect, \
         patch("ollama.AsyncClient") as mock_ollama_async, \
         patch("ollama.embeddings") as mock_embed:
        
        # Setup mocks
        mock_embed.return_value = {"embedding": [0.1] * 768}
        mock_ollama_async.return_value.embeddings.return_value = {"embedding": [0.1] * 768}
        
        # Initialize Core
        indexer = LibrarianIndexer(config=config)
        # Mock the store for the retrieval test
        indexer.store.get_table = MagicMock()
        indexer.store.get_table.return_value.search.return_value.limit.return_value.to_list.return_value = []

        guardian = GuardianAgent(indexer, config=config)
        ledger = SessionLedger(ledger_path=str(ledger_path))
        
        # Mock the audit response
        guardian.council.peer.audit_async = AsyncMock(return_value="Consistent")
        guardian.council.explorer.audit_async = AsyncMock(return_value="PASS")
        guardian.council.craftsman.audit_async = AsyncMock(return_value="PASS")

        # 3. Simulate Workflow
        
        # A. Retrieval
        search_results = await indexer.search("TDD")
        assert len(search_results) == 0 # Mocked DB is empty initially, that's fine
        
        # B. Decision Recording
        ledger.record_decision("TDD", "Always use Red-Green-Refactor", "Quality mandate")
        assert "Always use Red-Green-Refactor" in ledger.get_decisions()
        
        # C. Logic Gate Audit
        audit_result = await guardian.council.pre_commit_audit_async("I am using TDD correctly.")
        assert audit_result["status"] == "PASS"
        
        # D. Dossier Generation
        dossier = await guardian.council.get_audit_dossier("Draft text", ledger)
        assert "constitution_rules" in dossier
        assert "recent_decisions" in dossier
        assert "TDD" in dossier["recent_decisions"]

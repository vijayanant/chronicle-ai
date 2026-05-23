import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from chronicle.src.guardians.orchestrator import Council
from chronicle.src.indexer import LibrarianIndexer
from chronicle.src.utils.config import AppConfig

@pytest.fixture
def mock_council(tmp_path):
    # Setup
    config = AppConfig(
        constitution_path=str(tmp_path / "constitution.md"),
        db_path=str(tmp_path / "db")
    )
    indexer = MagicMock(spec=LibrarianIndexer)
    
    council = Council(indexer, config)
    
    # Mock the critical guardians with AsyncMocks
    council.peer.audit_async = AsyncMock()
    council.explorer.audit_async = AsyncMock()
    council.craftsman.audit_async = AsyncMock()
    
    return council

@pytest.mark.asyncio
async def test_pre_commit_audit_parallel_pass(mock_council):
    # Setup: All guardians return pass
    mock_council.peer.audit_async.return_value = "Consistent"
    mock_council.explorer.audit_async.return_value = "Sovereign"
    mock_council.craftsman.audit_async.return_value = "Disciplined"
    
    # Act
    result = await mock_council.pre_commit_audit_async("A good draft")
    
    # Assert
    assert result["status"] == "PASS"
    assert result["reason"] == "Consistent"
    mock_council.peer.audit_async.assert_called_once()
    mock_council.explorer.audit_async.assert_called_once()

@pytest.mark.asyncio
async def test_pre_commit_audit_parallel_fail(mock_council):
    # Setup: Peer returns a violation
    mock_council.peer.audit_async.return_value = "VIOLATION: Logic Gap"
    mock_council.explorer.audit_async.return_value = "Sovereign"
    mock_council.craftsman.audit_async.return_value = "Disciplined"
    
    # Act
    result = await mock_council.pre_commit_audit_async("A bad draft")
    
    # Assert
    assert result["status"] == "FAIL"
    assert "VIOLATION" in result["reason"]

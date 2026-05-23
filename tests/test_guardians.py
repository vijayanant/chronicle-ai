import pytest
import os
from pathlib import Path
from chronicle.src.guardians.base import BaseGuardian
from unittest.mock import MagicMock, patch, AsyncMock

class ConcreteGuardian(BaseGuardian):
    def get_mandate(self) -> str:
        return super().get_mandate()

@pytest.fixture
def temp_sop_dir(tmp_path):
    sop_dir = tmp_path / "guardians"
    sop_dir.mkdir()
    return sop_dir

def test_guardian_loads_sop_from_file(temp_sop_dir):
    # Setup
    sop_file = temp_sop_dir / "test_guardian.md"
    sop_file.write_text("Custom Mandate Text")
    
    guardian = ConcreteGuardian(name="test_guardian", sop_dir=str(temp_sop_dir))
    
    # Act
    mandate = guardian.get_mandate()
    
    # Assert
    assert mandate == "Custom Mandate Text"

def test_guardian_fallback_when_sop_missing(temp_sop_dir):
    # Setup
    guardian = ConcreteGuardian(name="missing", sop_dir=str(temp_sop_dir))
    
    # Act
    mandate = guardian.get_mandate()
    
    # Assert
    assert "missing guardian" in mandate
    assert "technical and narrative consistency" in mandate

@pytest.mark.asyncio
async def test_guardian_async_call(temp_sop_dir):
    # Setup
    mock_provider = MagicMock()
    # Use AsyncMock for the async method
    mock_provider.chat_async = AsyncMock(return_value="AI Response")
    
    guardian = ConcreteGuardian(name="test", provider=mock_provider, sop_dir=str(temp_sop_dir))
    
    # Act
    response = await guardian.ask_local_llm_async("Hello")
    
    # Assert
    assert response == "AI Response"
    mock_provider.chat_async.assert_called_once()

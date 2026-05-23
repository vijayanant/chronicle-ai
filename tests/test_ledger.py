import os
import json
import pytest
from chronicle.src.session_memory import SessionLedger

@pytest.fixture
def temp_ledger(tmp_path):
    ledger_file = tmp_path / "ledger.json"
    return SessionLedger(ledger_path=str(ledger_file))

def test_ledger_record_and_scope(temp_ledger):
    # Act
    temp_ledger.record_decision("Topic 1", "Decision 1", "Rationale 1", scope="global")
    temp_ledger.record_decision("Topic 2", "Decision 2", "Rationale 2", scope="series", series="Series A")
    temp_ledger.record_decision("Topic 3", "Decision 3", "Rationale 3", scope="post")
    
    # Assert
    global_decisions = temp_ledger.get_decisions()
    assert "[GLOBAL]" in global_decisions
    
    series_decisions = temp_ledger.get_decisions(series="Series A")
    assert "[SERIES]" in series_decisions
    assert "Topic 2" in series_decisions
    
    # VerifyTopic 3 is visible in default recent decisions
    recent = temp_ledger.get_recent_decisions()
    assert "Topic 3" in recent

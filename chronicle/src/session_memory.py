import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class SessionLedger:
    """
    Records design decisions and drafting intent from CLI sessions.
    Supports tiered scoping: Global, Series, or Post.
    """
    def __init__(self, ledger_path: str = "chronicle/data/session_ledger.json"):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.entries: List[Dict[str, Any]] = self._load_ledger()

    def _load_ledger(self) -> List[Dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        try:
            return json.loads(self.ledger_path.read_text())
        except:
            return []

    def record_decision(self, topic: str, decision: str, rationale: str, scope: str = "post", series: Optional[str] = None):
        """Logs a technical or narrative choice with a specific scope."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "decision": decision,
            "rationale": rationale,
            "scope": scope, # global, series, post
            "series": series
        }
        self.entries.append(entry)
        self._save()

    def _save(self):
        self.ledger_path.write_text(json.dumps(self.entries, indent=4))

    def get_decisions(self, series: Optional[str] = None, limit: int = 10) -> str:
        """Returns summarized decisions, prioritized by relevance."""
        if not self.entries:
            return "No decisions recorded."
        
        # If series is specified, prioritize Global + that Series
        if series:
            relevant = [e for e in self.entries if e.get('scope') == 'global' or e.get('series') == series]
        else:
            # If no series, show everything (Global + all Posts) up to the limit
            relevant = self.entries[-limit:]

        summary = "\n".join([
            f"- [{e.get('scope', 'post').upper()}] {e['topic']}: {e['decision']} (Rationale: {e['rationale']})"
            for e in reversed(relevant)
        ])
        return summary

    def get_recent_decisions(self, limit: int = 5) -> str:
        """Legacy support for backward compatibility."""
        return self.get_decisions(limit=limit)

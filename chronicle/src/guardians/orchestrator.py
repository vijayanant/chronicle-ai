import asyncio
from typing import List, Dict, Any
from .adversarial_peer import AdversarialPeer
from .systems_historian import SystemsHistorian
from .remaining_guardians import (
    SovereignExplorer, MasterCraftsman, PragmaticStrategist, 
    Cartographer, HugoMaster, Curator
)
from chronicle.src.indexer import LibrarianIndexer
from chronicle.src.utils.config import AppConfig
from pathlib import Path

class Council:
    """Orchestrator for parallelized Council Guardian audits, driven by config."""
    
    def __init__(self, indexer: LibrarianIndexer, config: AppConfig):
        self.indexer = indexer
        self.config = config
        
        # Instantiate guardians with configured reasoning model and SOPs
        # Note: We use the sop_dir from config or fallback to default
        sop_dir = getattr(config, "sop_dir", ".chronicle/data/guardians")
        guardian_kwargs = {
            "model_name": config.reasoning_model,
            "sop_dir": sop_dir
        }
        
        self.historian = SystemsHistorian(indexer, **guardian_kwargs)
        self.explorer = SovereignExplorer(**guardian_kwargs)
        self.craftsman = MasterCraftsman(**guardian_kwargs)
        self.strategist = PragmaticStrategist(**guardian_kwargs)
        self.cartographer = Cartographer(**guardian_kwargs)
        self.hugo = HugoMaster(**guardian_kwargs)
        self.curator = Curator(**guardian_kwargs)
        self.peer = AdversarialPeer(**guardian_kwargs)
        
        self.guardians = [
            self.historian, self.explorer, self.craftsman,
            self.strategist, self.cartographer, self.hugo,
            self.curator, self.peer
        ]
        self.constitution_path = Path(config.constitution_path)

    async def get_audit_dossier(self, draft: str, ledger) -> Dict[str, Any]:
        """Surgically bundles local knowledge for cloud auditing (Async)."""
        search_results = await self.indexer.search(draft[:500], limit=3, mode="hybrid")
        constitution = self.constitution_path.read_text() if self.constitution_path.exists() else "No Constitution established."
        recent_decisions = ledger.get_decisions(limit=5)
        
        return {
            "relevant_history": [r.chunk.text for r in search_results],
            "constitution_rules": constitution,
            "recent_decisions": recent_decisions,
            "guardian_mandates": {
                "Peer": self.peer.get_mandate(), 
                "Explorer": self.explorer.get_mandate(), 
                "Historian": self.historian.get_mandate()
            }
        }

    async def pre_commit_audit_async(self, draft: str) -> Dict[str, Any]:
        """Active Interceptor (Async): Runs critical guardians in parallel."""
        constitution = self.constitution_path.read_text() if self.constitution_path.exists() else ""
        
        tasks = [
            self.peer.audit_async(draft, constitution),
            self.explorer.audit_async(draft),
            self.craftsman.audit_async(draft)
        ]
        
        results = await asyncio.gather(*tasks)
        peer_report, explorer_report, craftsman_report = results
        
        is_violation = any(word in peer_report.upper() for word in ["VIOLATION", "CONTRADICTION"])
        
        return {
            "status": "FAIL" if is_violation else "PASS",
            "reason": peer_report if is_violation else "Consistent",
            "explorer_notes": explorer_report,
            "craftsman_notes": craftsman_report
        }

    def generate_constitution(self, seed_context: str) -> str:
        prompt = f"Extract Technical Invariants and Principles from this content:\n{seed_context}"
        return self.peer.ask_local_llm(prompt, "You are a senior technical auditor.")

    def audit_draft(self, draft: str) -> str:
        """Legacy synchronous audit."""
        constitution = self.constitution_path.read_text() if self.constitution_path.exists() else ""
        return self.peer.audit(draft, constitution)

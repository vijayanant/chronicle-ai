from typing import List, Dict, Any, Optional
from .guardians.orchestrator import Council
from .indexer import LibrarianIndexer
from .providers.base import LLMProvider
from .utils.config import AppConfig
from pathlib import Path
from datetime import datetime

from .utils.logging import get_logger

logger = get_logger()

class GuardianAgent:
    """
    The Auditing Engine of Chronicle AI. 
    Orchestrates the modular Council of Guardians to verify draft integrity.
    """
    
    def __init__(self, indexer: LibrarianIndexer, config: AppConfig, provider: Optional[LLMProvider] = None):
        self.config = config
        self.council = Council(indexer, config)
        
        # Apply the provider and model to all guardians
        if provider:
            for guardian in self.council.guardians:
                guardian.provider = provider
                guardian.model_name = config.reasoning_model
        
        self.constitution_path = Path(config.constitution_path)

    async def generate_initial_constitution(self):
        logger.info("Starting Modular Global Constitutional Audit...")
        seed_topics = self.config.constitution_seed_topics
        combined_context = ""
        
        for topic in seed_topics:
            results = await self.council.indexer.search(topic, limit=5)
            combined_context += "\n\n" + "\n".join([r.chunk.text for r in results])

        constitution_content = self.council.generate_constitution(combined_context[:15000])
        
        header = f"# Chronicle: Technical Constitution\n**Version:** 1.0.0\n**Last Updated:** {datetime.now()}\n\n---\n\n"
        self.constitution_path.write_text(header + constitution_content)
        logger.info(f"Constitution successfully updated at: {self.constitution_path}")

    def audit_draft(self, draft_text: str) -> str:
        return self.council.audit_draft(draft_text)

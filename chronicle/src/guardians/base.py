from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import ollama
from pathlib import Path
from ..providers.base import LLMProvider
from ..providers.ollama import OllamaProvider

class BaseGuardian(ABC):
    """Abstract base class for all Council Guardians with external SOP support."""
    
    def __init__(self, name: str, provider: LLMProvider = None, model_name: str = "deepseek-r1:14b", sop_dir: str = "chronicle/data/guardians"):
        self.name = name
        self.provider = provider or OllamaProvider()
        self.model_name = model_name
        self.sop_path = Path(sop_dir) / f"{name}.md"

    def get_mandate(self) -> str:
        """Reads the mandate from the external SOP file or returns a generic default."""
        if self.sop_path.exists():
            return self.sop_path.read_text()
        return f"I am the {self.name} guardian. My job is to ensure technical and narrative consistency."

    async def ask_local_llm_async(self, prompt: str, system_prompt: str = "") -> str:
        """Native asynchronous query to the local reasoning model."""
        return await self.provider.chat_async(self.model_name, [
            {"role": "system", "content": system_prompt or self.get_mandate()},
            {"role": "user", "content": prompt}
        ])

    def ask_local_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Synchronous query to the local reasoning model."""
        return self.provider.chat(self.model_name, [
            {"role": "system", "content": system_prompt or self.get_mandate()},
            {"role": "user", "content": prompt}
        ])

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMProvider(ABC):
    """Abstract interface for LLM providers."""
    
    @staticmethod
    def get_provider(name: str, config: Optional[Any] = None) -> 'LLMProvider':
        """Factory method to return the requested provider."""
        if name.lower() == "mlx":
            from .mlx import MLXProvider
            return MLXProvider()
        elif name.lower() in ("openai", "llamacpp"):
            from .openai import OpenAIProvider
            base_url = getattr(config, "openai_base_url", None)
            return OpenAIProvider(base_url=base_url)
        else:
            from .ollama import OllamaProvider
            return OllamaProvider()
    
    @abstractmethod
    def embed(self, text: str, model_name: str, **kwargs) -> List[float]:
        """Generates embeddings (Synchronous)."""
        pass

    @abstractmethod
    async def embed_async(self, text: str, model_name: str, **kwargs) -> List[float]:
        """Generates embeddings (Asynchronous)."""
        pass

    @abstractmethod
    def chat(self, model_name: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """Sends a chat request (Synchronous)."""
        pass

    @abstractmethod
    async def chat_async(self, model_name: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """Sends a chat request (Asynchronous)."""
        pass

    @abstractmethod
    def check_health(self) -> bool:
        """Verifies if the provider service is running."""
        pass

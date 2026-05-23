import ollama
from ollama import AsyncClient
from typing import List, Dict, Any
from .base import LLMProvider

class OllamaProvider(LLMProvider):
    """Refactored implementation using native Ollama AsyncClient."""
    
    def __init__(self):
        self.async_client = AsyncClient()

    def embed(self, text: str, model_name: str, **kwargs) -> List[float]:
        response = ollama.embeddings(model=model_name, prompt=text)
        return response['embedding']

    async def embed_async(self, text: str, model_name: str, **kwargs) -> List[float]:
        response = await self.async_client.embeddings(model=model_name, prompt=text)
        return response['embedding']

    def chat(self, model_name: str, messages: List[Dict[str, str]], **kwargs) -> str:
        response = ollama.chat(model=model_name, messages=messages)
        return response['message']['content']

    async def chat_async(self, model_name: str, messages: List[Dict[str, str]], **kwargs) -> str:
        response = await self.async_client.chat(model=model_name, messages=messages)
        return response['message']['content']

    def check_health(self) -> bool:
        try:
            ollama.list()
            return True
        except:
            return False

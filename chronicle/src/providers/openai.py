import os
import httpx
from typing import List, Dict, Any, Optional
from .base import LLMProvider

class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider using httpx to support llama.cpp, local servers, or OpenAI."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "http://localhost:8080/v1")).rstrip("/")
        self.api_key = os.environ.get("OPENAI_API_KEY", "no-key")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def embed(self, text: str, model_name: str, **kwargs) -> List[float]:
        url = f"{self.base_url}/embeddings"
        payload = {"model": model_name, "input": text, **kwargs}
        with httpx.Client() as client:
            response = client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]

    async def embed_async(self, text: str, model_name: str, **kwargs) -> List[float]:
        url = f"{self.base_url}/embeddings"
        payload = {"model": model_name, "input": text, **kwargs}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]

    def chat(self, model_name: str, messages: List[Dict[str, str]], **kwargs) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {"model": model_name, "messages": messages, **kwargs}
        with httpx.Client() as client:
            response = client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    async def chat_async(self, model_name: str, messages: List[Dict[str, str]], **kwargs) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {"model": model_name, "messages": messages, **kwargs}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    def check_health(self) -> bool:
        url = f"{self.base_url}/models"
        try:
            with httpx.Client() as client:
                response = client.get(url, headers=self.headers)
                return response.status_code == 200
        except Exception:
            return False

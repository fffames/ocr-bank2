from abc import ABC, abstractmethod
from typing import Dict, Any, List
import os
import httpx
from app.config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate_response(self, prompt: str, context: str) -> str:
        """Generate a response based on the prompt and context."""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""

    def __init__(self):
        import google.generativeai as genai
        self.genai = genai
        self.api_key = settings.gemini_api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider")
        genai.configure(api_key=self.api_key)
        # Use the newer Gemini 3.1 Flash Lite Preview model
        self.model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

    async def generate_response(self, prompt: str, context: str) -> str:
        """Generate response using Gemini API."""
        try:
            full_prompt = f"""Context:
{context}

User Question: {prompt}

Please provide a helpful answer based on the receipt context above."""

            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")


class LocalGemmaProvider(LLMProvider):
    """Local Gemma model via LM Studio API."""

    def __init__(self):
        self.base_url = settings.local_llm_url
        if not self.base_url:
            raise ValueError("LOCAL_LLM_URL is required for local Gemma provider")

    async def generate_response(self, prompt: str, context: str) -> str:
        """Generate response using local Gemma model via LM Studio."""
        try:
            full_prompt = f"""Context:
{context}

User Question: {prompt}

Please provide a helpful answer based on the receipt context above."""

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": "local-model",
                        "messages": [
                            {
                                "role": "user",
                                "content": full_prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            raise Exception(f"Local LLM connection error: {str(e)}")
        except Exception as e:
            raise Exception(f"Local LLM error: {str(e)}")


def get_llm_provider() -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    provider = settings.llm_provider

    if provider == "gemini":
        return GeminiProvider()
    elif provider == "local_gemma":
        return LocalGemmaProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

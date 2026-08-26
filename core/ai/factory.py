import os
from typing import Optional
from core.ai.base import AIProvider
from core.ai.mock_provider import MockAIProvider
from core.ai.real_provider import RealAIProvider


def get_ai_provider(provider_type: Optional[str] = None) -> AIProvider:
    """
    Factory to instantiate configured AI provider.
    Selectable via AI_PROVIDER environment variable:
      - 'mock' (default) -> MockAIProvider
      - 'openai' / 'real' / 'gemini' -> RealAIProvider
    """
    selected = (provider_type or os.getenv("AI_PROVIDER", "mock")).lower().strip()

    if selected in ("openai", "real", "gemini", "anthropic"):
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        model = os.getenv("AI_MODEL", "gpt-4o-mini")
        base_url = os.getenv("AI_API_BASE_URL")
        return RealAIProvider(api_key=api_key, model_name=model, api_base_url=base_url)

    return MockAIProvider()

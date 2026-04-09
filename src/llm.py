from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI


def build_chat_model(
    *,
    provider: str,
    model: str,
    temperature: float,
    api_key: str | None,
    base_url: str | None,
    role: str,
) -> BaseChatModel:
    if provider == "openai":
        if not api_key:
            raise RuntimeError(f"OpenAI API key is required for role '{role}'.")
        return ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=temperature,
            base_url=base_url,
            tags=[f"role:{role}"],
        )

    if provider == "google":
        if not api_key:
            raise RuntimeError(f"Google API key is required for role '{role}'.")
        return ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=model,
            temperature=temperature,
            tags=[f"role:{role}"],
        )

    if provider == "ollama":
        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=base_url,
            tags=[f"role:{role}"],
        )

    raise ValueError(f"Unsupported LLM provider for role '{role}': {provider}")

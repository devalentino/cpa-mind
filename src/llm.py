from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI


@dataclass(frozen=True, slots=True)
class RoleLLMConfig:
    provider: str
    model: str
    temperature: float = 0.0
    api_key: str | None = None


@dataclass(frozen=True, slots=True)
class LLMConfig:
    researcher: RoleLLMConfig
    creator: RoleLLMConfig
    compliance_officer: RoleLLMConfig


class ChatModelFactory(Protocol):
    def create_chat_model(self, role: str) -> BaseChatModel:
        ...


@dataclass(frozen=True, slots=True)
class RoleAwareChatModelFactory:
    config: LLMConfig

    def create_chat_model(self, role: str) -> BaseChatModel:
        role_config = self._get_role_config(role)

        if role_config.provider == "openai":
            return self._create_openai_model(role, role_config)
        if role_config.provider == "google":
            return self._create_google_model(role, role_config)
        raise ValueError(f"Unsupported LLM provider for role '{role}': {role_config.provider}")

    def _get_role_config(self, role: str) -> RoleLLMConfig:
        try:
            return getattr(self.config, role)
        except AttributeError as exc:
            raise ValueError(f"Unsupported role: {role}") from exc

    def _create_openai_model(
        self,
        role: str,
        role_config: RoleLLMConfig,
    ) -> ChatOpenAI:
        if not role_config.api_key:
            raise RuntimeError(f"OpenAI API key is required for role '{role}'.")

        return ChatOpenAI(
            api_key=role_config.api_key,
            model=role_config.model,
            temperature=role_config.temperature,
            tags=[f"role:{role}"],
        )

    def _create_google_model(
        self,
        role: str,
        role_config: RoleLLMConfig,
    ) -> ChatGoogleGenerativeAI:
        if not role_config.api_key:
            raise RuntimeError(f"Google API key is required for role '{role}'.")

        return ChatGoogleGenerativeAI(
            google_api_key=role_config.api_key,
            model=role_config.model,
            temperature=role_config.temperature,
            tags=[f"role:{role}"],
        )

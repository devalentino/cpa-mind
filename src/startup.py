from __future__ import annotations

import os

from llm import build_chat_model
from tools.cpa import (
    OfferReader,
    TerraleadsOfferParserStrategy,
    UnsupportedOfferParserStrategy,
)
from tools.factories import (
    build_facebook_ads_library_reader_tool,
    build_google_trends_reader_tool,
    build_landing_reader_tool,
    build_offer_reader_tool,
)
from workflow import build_graph


def startup():
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    researcher_provider = os.getenv("RESEARCHER_LLM_PROVIDER", "google")
    creator_provider = os.getenv("CREATOR_LLM_PROVIDER", "google")
    compliance_provider = os.getenv("COMPLIANCE_LLM_PROVIDER", "google")

    researcher_model = build_chat_model(
        provider=researcher_provider,
        model=os.getenv("RESEARCHER_LLM_MODEL", "gemini-2.5-flash"),
        temperature=float(os.getenv("RESEARCHER_LLM_TEMPERATURE", "0")),
        api_key=(
            os.getenv("RESEARCHER_LLM_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        ),
        base_url=ollama_base_url if researcher_provider == "ollama" else None,
        role="researcher",
    )
    creator_model = build_chat_model(
        provider=creator_provider,
        model=os.getenv("CREATOR_LLM_MODEL", "gemini-2.5-flash"),
        temperature=float(os.getenv("CREATOR_LLM_TEMPERATURE", "0.7")),
        api_key=(
            os.getenv("CREATOR_LLM_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        ),
        base_url=ollama_base_url if creator_provider == "ollama" else None,
        role="creator",
    )
    compliance_officer_model = build_chat_model(
        provider=compliance_provider,
        model=os.getenv("COMPLIANCE_LLM_MODEL", "gemini-2.5-flash"),
        temperature=float(os.getenv("COMPLIANCE_LLM_TEMPERATURE", "0")),
        api_key=(
            os.getenv("COMPLIANCE_LLM_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        ),
        base_url=ollama_base_url if compliance_provider == "ollama" else None,
        role="compliance_officer",
    )

    offer_reader = OfferReader(
        strategies=(
            TerraleadsOfferParserStrategy(
                login=os.getenv("TERRALEADS_LOGIN", ""),
                password=os.getenv("TERRALEADS_PASSWORD", ""),
                cache_path=os.getenv("CACHE_PATH"),
            ),
            UnsupportedOfferParserStrategy(),
        )
    )

    research_tools = [
        build_offer_reader_tool(offer_reader),
        build_landing_reader_tool(),
        build_facebook_ads_library_reader_tool(),
        build_google_trends_reader_tool(),
    ]

    return build_graph(
        researcher_model=researcher_model,
        creator_model=creator_model,
        compliance_officer_model=compliance_officer_model,
        research_tools=research_tools,
    )

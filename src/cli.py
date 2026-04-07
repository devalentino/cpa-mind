from __future__ import annotations

import argparse
import json
import os

from llm import LLMConfig, RoleLLMConfig
from workflow import run_analysis


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analyze",
        description="Analyze a CPA offer with a LangGraph multi-agent workflow.",
    )
    parser.add_argument(
        "--offer-url",
        required=True,
        help="Offer URL to analyze.",
    )
    parser.add_argument(
        "--traffic-source",
        required=True,
        help="Traffic source for the offer.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    llm_config = LLMConfig(
        researcher=RoleLLMConfig(
            provider=os.getenv("RESEARCHER_LLM_PROVIDER", "openai"),
            model=os.getenv("RESEARCHER_LLM_MODEL", "gpt-4.1-mini"),
            temperature=float(os.getenv("RESEARCHER_LLM_TEMPERATURE", "0")),
            api_key=os.getenv("RESEARCHER_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        ),
        creator=RoleLLMConfig(
            provider=os.getenv("CREATOR_LLM_PROVIDER", "openai"),
            model=os.getenv("CREATOR_LLM_MODEL", "gpt-4.1-mini"),
            temperature=float(os.getenv("CREATOR_LLM_TEMPERATURE", "0.7")),
            api_key=(
                os.getenv("CREATOR_LLM_API_KEY")
                or os.getenv("GOOGLE_API_KEY")
                or os.getenv("OPENAI_API_KEY")
            ),
        ),
        compliance_officer=RoleLLMConfig(
            provider=os.getenv("COMPLIANCE_LLM_PROVIDER", "openai"),
            model=os.getenv("COMPLIANCE_LLM_MODEL", "gpt-4.1-mini"),
            temperature=float(os.getenv("COMPLIANCE_LLM_TEMPERATURE", "0")),
            api_key=os.getenv("COMPLIANCE_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        ),
    )

    result = run_analysis(
        offer_url=args.offer_url,
        traffic_source=args.traffic_source,
        llm_config=llm_config,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

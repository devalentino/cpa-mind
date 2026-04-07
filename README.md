# cpa-mind

LangGraph-based skeleton for a CPA multi-agent console application.

## Agents

- `Researcher`: analyzes the offer, landings, audience, market, and competitors
- `Creator`: drafts text and creative directions
- `Compliance Officer`: checks generated creative ideas against Facebook policy constraints

## Tools

- `OfferReader`
- `LandingReader`
- `FacebookAdsLibraryReader`
- `GoogleTrendsReader`

All tools are placeholders for now and return TODO-backed stub data.

## LLM Configuration

Set these environment variables in the runtime environment:

```bash
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key

RESEARCHER_LLM_PROVIDER=openai
RESEARCHER_LLM_MODEL=gpt-4.1-mini
RESEARCHER_LLM_TEMPERATURE=0

CREATOR_LLM_PROVIDER=google
CREATOR_LLM_MODEL=gemini-2.5-flash
CREATOR_LLM_TEMPERATURE=0.7

COMPLIANCE_LLM_PROVIDER=openai
COMPLIANCE_LLM_MODEL=gpt-4.1-mini
COMPLIANCE_LLM_TEMPERATURE=0
```

The runtime configuration is assembled at the application boundary in [src/cli.py](/Users/valentyn/projects/cpa-mind/src/cli.py). The factory in [src/llm.py](/Users/valentyn/projects/cpa-mind/src/llm.py) then selects the concrete chat model by role, so `Researcher`, `Creator`, and `Compliance Officer` can use different providers and models.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
analyze --offer-url https://example.com --traffic-source facebook
```

## Flow

The CLI runs a LangGraph workflow:

1. `Researcher`
2. `Creator`
3. `Compliance Officer`
4. Back to `Creator` if compliance requests revisions
5. Finish when compliance approves or the revision limit is reached

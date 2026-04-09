# cpa-mind

LangGraph-based skeleton for a CPA multi-agent console application.

## Agents

- `Researcher`: analyzes the offer, landings, audience, market, and competitors
- `Creator`: drafts text and creative directions
- `Compliance Officer`: checks generated creative ideas against Facebook policy constraints

## Tools

- `OfferReader`
- `FacebookAdsLibraryReader`
- `GoogleTrendsReader`

All tools are placeholders for now and return TODO-backed stub data.

## Startup Configuration

Set these environment variables in the runtime environment before running `analyze`:

```bash
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
OLLAMA_BASE_URL=http://localhost:11434

RESEARCHER_LLM_PROVIDER=google
RESEARCHER_LLM_MODEL=gemini-2.5-flash
RESEARCHER_LLM_TEMPERATURE=0

CREATOR_LLM_PROVIDER=google
CREATOR_LLM_MODEL=gemini-2.5-flash
CREATOR_LLM_TEMPERATURE=0.7

COMPLIANCE_LLM_PROVIDER=google
COMPLIANCE_LLM_MODEL=gemini-2.5-flash
COMPLIANCE_LLM_TEMPERATURE=0

TERRALEADS_LOGIN=your_terraleads_login
TERRALEADS_PASSWORD=your_terraleads_password
CACHE_PATH=.cache
```

For fully local development without hosted API limits, run Ollama and switch providers to `ollama`:

```bash
OLLAMA_BASE_URL=http://localhost:11434

RESEARCHER_LLM_PROVIDER=ollama
RESEARCHER_LLM_MODEL=qwen3:8b
RESEARCHER_LLM_TEMPERATURE=0

CREATOR_LLM_PROVIDER=ollama
CREATOR_LLM_MODEL=qwen3:8b
CREATOR_LLM_TEMPERATURE=0.7

COMPLIANCE_LLM_PROVIDER=ollama
COMPLIANCE_LLM_MODEL=qwen3:8b
COMPLIANCE_LLM_TEMPERATURE=0
```

Install and preload the model locally before running the CLI:

```bash
brew install ollama
ollama serve
ollama pull qwen3:8b
```

`qwen3:8b` is a reasonable default for local iteration. Smaller models may be faster but will make the researcher/tool-selection and compliance steps less reliable.

Application composition happens in [src/startup.py](/Users/valentyn/projects/cpa-mind/src/startup.py). At startup, the app:

- builds the three role-specific chat models
- builds the `OfferReader` with platform strategies such as Terraleads
- builds the research tools with those ready dependencies
- compiles the LangGraph workflow

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
2. `Researcher` optionally calls only the tools it decides it needs
3. End early if research blocks the offer, for example disabled/unavailable offers
4. `Creator`
5. `Compliance Officer`
6. Back to `Creator` if compliance requests revisions
7. Finish when compliance approves or the revision limit is reached

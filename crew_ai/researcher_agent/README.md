# Researcher Agent

A single CrewAI agent that researches any topic and writes a structured Markdown report.

```
topic ──▶ Senior Research Analyst ──▶ web search (optional) ──▶ output/report.md
```

## How it works

| Piece | Role |
|---|---|
| **Agent** | A *Senior Research Analyst* with a goal and a backstory that push it to prefer primary sources, cross-check claims and cite where facts come from. |
| **Tool** | `SerperDevTool` for Google search results. It is optional: without a Serper key the agent works from the model's own knowledge. |
| **Task** | Research the topic and return a report with a fixed structure: summary, key findings with sources, main players, open questions and sources. |
| **Crew** | Runs the single task sequentially and saves the result to `output/report.md`. |

## Setup

```bash
cd crew_ai/researcher_agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

**Model:** set `MODEL` in `.env` to a local Ollama model (the default, `ollama/llama3.1:8b`) or to a hosted model with its API key. Both options are explained step by step in [Choosing the model](../README.md#choosing-the-model). The agent calls a search tool, so with Ollama use a 7–8B model or larger; 1–3B models often fail to call it.

**Web search (optional):** get a free key at [serper.dev](https://serper.dev) and set `SERPER_API_KEY`. Without it the agent works from the model's own knowledge.

## Run

```bash
python researcher.py --topic "Small language models"

# use another model for a single run without editing .env
python researcher.py --topic "Small language models" --model gpt-4o-mini
```

If Ollama is not running, the model has not been pulled, or the API key for the chosen provider is missing, the script stops with a message explaining what to do. The model selection lives in `llm.py`.

The agent's reasoning and tool calls are printed to the console, and the final report is written to `output/report.md`.

## Ideas to extend it

- Add a second agent (a *writer* or *fact-checker*) that reviews the researcher's report.
- Give the agent more tools: scraping full pages, reading PDFs or querying an API.
- Move the agent and task definitions to YAML config files to separate prompts from code.

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

cp .env.example .env    # then replace the REPLACE_ME values with your keys
```

You need an API key for one LLM provider (OpenAI, Anthropic or Gemini) and, optionally, a [Serper](https://serper.dev) key for web search. Set the model with the `MODEL` variable in `.env`.

## Run

```bash
python researcher.py --topic "Small language models"
```

The agent's reasoning and tool calls are printed to the console, and the final report is written to `output/report.md`.

## Ideas to extend it

- Add a second agent (a *writer* or *fact-checker*) that reviews the researcher's report.
- Give the agent more tools: scraping full pages, reading PDFs or querying an API.
- Move the agent and task definitions to YAML config files to separate prompts from code.

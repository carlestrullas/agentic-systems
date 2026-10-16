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

Then choose the LLM (option A or B) and, optionally, add the search key.

### Option A: local model with Ollama (no API key)

1. Install Ollama from [ollama.com](https://ollama.com) (on Linux: `curl -fsSL https://ollama.com/install.sh | sh`).
2. Download a model and make sure the server is running:

   ```bash
   ollama pull llama3.1:8b
   ollama serve        # not needed if the Ollama desktop app is already open
   ```

3. In `.env`, keep:

   ```env
   MODEL=ollama/llama3.1:8b
   OLLAMA_BASE_URL=http://localhost:11434
   ```

The agent calls a search tool, and very small models (1–3B) often fail to do that properly. Use `llama3.1:8b`, `qwen2.5:7b` or larger.

### Option B: hosted model with an API key

Comment out the Ollama `MODEL` line, uncomment the one for your provider and fill in its key:

```env
MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

| Provider | `MODEL` example | Key variable |
|---|---|---|
| OpenAI | `gpt-4o-mini` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/claude-sonnet-4-5` | `ANTHROPIC_API_KEY` |
| Google Gemini | `gemini/gemini-2.0-flash` | `GEMINI_API_KEY` |
| Groq | `groq/llama-3.3-70b-versatile` | `GROQ_API_KEY` |

### Web search (optional, both options)

Get a free key at [serper.dev](https://serper.dev) and set `SERPER_API_KEY` in `.env`. Without it the agent works from the model's own knowledge.

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

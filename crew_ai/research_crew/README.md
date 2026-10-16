# Research Crew

A multi-agent system in which three specialised agents research a topic, summarise it and fact-check the result.

```
topic ──▶ Research Specialist ──▶ Content Summarizer ──▶ Fact-Checking Specialist ──▶ final report
          (web search)            (no tools)             (web search)
             │                       │                       │
             ▼                       ▼                       ▼
   1_research_notes.md         2_summary.md          3_final_report.md
```

## How it works

| Agent | Tools | Task |
|---|---|---|
| *Senior Internet Research Specialist* | `SerperDevTool` | Searches the web and writes research notes, each insight with its source. |
| *Senior Content Summarizer* | none | Turns the notes into a structured summary, without adding new facts. |
| *Senior Fact-Checking Specialist* | `SerperDevTool` | Re-checks each claim online, corrects or removes what cannot be verified, and produces the final report. |

Why several agents instead of one? Each agent has a **narrow focus** and only the **tools it needs** (the summarizer cannot search, so it cannot drift away from the notes). Each task receives the previous outputs as `context`, so the fact-checker sees both the raw notes and the summary.

### Prompts in YAML

Roles, goals, backstories and task descriptions live in [`config/agents.yaml`](config/agents.yaml) and [`config/tasks.yaml`](config/tasks.yaml). `crew.py` only wires them together, so you can tune the behaviour of the crew without touching the code and track prompt changes in git separately from logic changes.

Placeholders such as `{topic}` and `{today}` in the YAML are filled in by CrewAI from `crew.kickoff(inputs={...})`.

## Setup

```bash
cd crew_ai/research_crew
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Then choose the LLM (option A or B) and add the search key.

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

This crew relies on **tool calling**, which very small models (1–3B) handle poorly: they tend to skip the search or loop. Use `llama3.1:8b`, `qwen2.5:7b` or larger.

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

### Web search (both options)

Get a free key at [serper.dev](https://serper.dev) and set `SERPER_API_KEY` in `.env`. Without it the crew still runs, but the researcher and fact-checker can only use what the model already knows, which defeats much of the purpose.

## Run

```bash
python crew.py --topic "Small language models"

# use another model for a single run without editing .env
python crew.py --topic "Agentic RAG" --model gpt-4o-mini
```

The agents' reasoning and tool calls are printed to the console. The output of each step is saved in `output/` (git-ignored), so you can see how the text changes from raw notes to the verified report.

## Ideas to extend it

- Switch to `Process.hierarchical` and let a manager agent decide the order of work.
- Add a writer agent that turns the verified report into a blog post (see [`technical_writer_agent`](../technical_writer_agent/)).
- Add `ScrapeWebsiteTool` so the researcher can read full pages, not just search snippets.

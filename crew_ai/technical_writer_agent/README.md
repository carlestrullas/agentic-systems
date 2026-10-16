# Technical Writer Agent

Two single-agent workflows that can be used on their own or chained together:

```
topic ──▶ Senior Technical Writer ──▶ output/article.md ──▶ Senior Document Analyst (FileReadTool) ──▶ output/summary.md
           writer.py                                         summarizer.py
```

| Script | Agent | Tools | What it shows |
|---|---|---|---|
| `writer.py` | *Senior Technical Writer* | none | The minimum CrewAI setup: an agent defined by role, goal and backstory, a task with an `{topic}` input, and a crew run with `kickoff(inputs=...)`. |
| `summarizer.py` | *Senior Document Analyst* | `FileReadTool` | How to give an agent a tool. The tool is bound to a single file, so the agent can only read that document. |

Both scripts work with a **local model through Ollama** or with a **hosted model and an API key**; the choice is a single line in `.env`.

## Setup

```bash
cd crew_ai/technical_writer_agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Then pick one of the two options below.

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

Any model from the [Ollama library](https://ollama.com/library) works by writing `ollama/<name>`. Guidelines:

| Model | RAM needed (approx.) | Notes |
|---|---|---|
| `llama3.2:1b` / `llama3.2:3b` | 2–4 GB | Fine for `writer.py`; often fails to call tools in `summarizer.py`. |
| `llama3.1:8b` / `qwen2.5:7b` | ~6 GB | Default. Good balance and reliable tool calling. |
| `qwen2.5:14b` and larger | 10 GB+ | Better quality if your machine can run it. |

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

If the key for the chosen provider is missing, the script stops with a message telling you which variable to set.

> You can also switch model for a single run without editing `.env`: `python writer.py --model gpt-4o-mini`.

## Run

```bash
# 1. Write an article
python writer.py --topic "Retrieval-augmented generation"

# 2. Summarise it (reads output/article.md by default)
python summarizer.py

# ...or summarise any other document
python summarizer.py --file ../researcher_agent/output/report.md
```

The agents' reasoning and tool calls are printed to the console (`verbose=True`). Results are written to `output/` (git-ignored).

## How the model is chosen

`llm.py` reads `MODEL` (or `--model`) and builds a CrewAI `LLM`:

- If the name starts with `ollama/`, it checks that Ollama is reachable at `OLLAMA_BASE_URL` and that the model has been pulled, then connects to it locally.
- Otherwise it checks that the API key of that provider is set and lets CrewAI call the hosted API.

## Ideas to extend it

- Run both steps in one crew, passing the writer's task as `context` to the summary task.
- Add a reviewer agent that critiques the article before it is summarised.
- Replace `FileReadTool` with `PDFSearchTool` or `DirectoryReadTool` to work with other kinds of documents.

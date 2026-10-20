# Technical Writer Agent

Two single-agent workflows that can be used on their own or chained together.

```
topic ──▶ Senior Technical Writer ──▶ output/article.md ──▶ Senior Document Analyst (FileReadTool) ──▶ output/summary.md
           writer.py                                         summarizer.py
```

## How it works

| Script | Agent | Tools | What it shows |
|---|---|---|---|
| `writer.py` | *Senior Technical Writer* | none | The minimum CrewAI setup: an agent defined by role, goal and backstory, a task with an `{topic}` input, and a crew run with `kickoff(inputs=...)`. |
| `summarizer.py` | *Senior Document Analyst* | `FileReadTool` | How to give an agent a tool. The tool is bound to a single file, so the agent can only read that document. |

## Setup

```bash
cd crew_ai/technical_writer_agent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

**Model:** set `MODEL` in `.env` to a local Ollama model (the default, `ollama/llama3.1:8b`) or to a hosted model with its API key. Both options are explained step by step in [Choosing the model](../README.md#choosing-the-model). `writer.py` works even with small Ollama models (1–3B); `summarizer.py` calls a tool, so use a 7–8B model or larger for it.

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

## Ideas to extend it

- Run both steps in one crew, passing the writer's task as `context` to the summary task.
- Add a reviewer agent that critiques the article before it is summarised.
- Replace `FileReadTool` with `PDFSearchTool` or `DirectoryReadTool` to work with other kinds of documents.

# Docs Assistant

A question-answering assistant over a **folder of documents**: drop text, Markdown, PDF, CSV, JSON or Excel files in a folder and ask questions about them. Answers are grounded in the files, say which documents they come from, and admit when the documents do not cover a question.

```
knowledge/ ──▶ DocumentFolderSource ──▶ chunks labelled "[Document: <file>]" ──▶ crew knowledge
                (built-in loaders)                                                   │
question ──▶ Internal Documentation Assistant ◀──── relevant chunks ─────────────────┘
                      │
                      ▼
               Answer(answer, found_in_documents, documents) ──▶ guardrail ──▶ 💬 + 📄 sources
```

Example session with the sample documents of the fictional company *Lumen Analytics* (answers vary with the model):

```
📚 4 documents: company_info.json, feedback.csv, hr_policy.txt, meeting_notes.pdf

❓ Is mobile performance a problem, and who is fixing it?
💬 Yes: 3 of the 12 September comments say the app is slow on mobile (dashboards, charts, filtering).
   Engineering (Engineering Lead) will profile and fix chart rendering on mobile by 14 November;
   the Mobile team has 4 people.
📄 Sources: feedback.csv, meeting_notes.pdf, company_info.json

❓ What is the company's travel expenses policy?
💬 The documents do not include a travel expenses policy.
🤷 Not found in the documents.
```

## How it works

It combines the ideas of [`knowledge_sources`](../knowledge_sources/) with structured output and guardrails:

| Piece | File | What it does |
|---|---|---|
| A custom source | [`sources.py`](sources.py) | `DocumentFolderSource` loads every supported file with CrewAI's own loaders (`PDFKnowledgeSource`, `CSVKnowledgeSource`…) and **prefixes every chunk with its file name**. The built-in sources do not keep that information, so without it the agent could not cite its sources. |
| Crew knowledge | [`docs_crew.py`](docs_crew.py) | The source is attached to the `Crew`, so it is embedded **once** when the crew is created and reused for every question in interactive mode. |
| Retrieval settings | `docs_crew.py` | `KnowledgeConfig(results_limit=6, score_threshold=0.5)` and 800-character chunks (`main.py`): questions often need pieces from several files. |
| Structured answer | [`models.py`](models.py) | `Answer` with `answer`, `found_in_documents` and `documents`, so code can tell grounded answers from "I don't know". |
| Guardrail | `docs_crew.py` | Rejects answers that cite files that do not exist, or that claim to be grounded without citing any (see [`task_features`](../task_features/)). |
| Embedder and storage | [`knowledge_setup.py`](knowledge_setup.py) | Same file as in `knowledge_sources`: `EMBEDDER` from `.env` (local Ollama by default) and a store of its own. The store is emptied on every start, because the folder may have changed and the documents are embedded again anyway. |

Supported files: `.txt`, `.md`, `.pdf` (with a text layer; scanned PDFs give no text), `.csv`, `.json` and `.xlsx` (needs `pip install pandas`). Other files are listed as skipped.

## Setup

```bash
cd crew_ai/docs_assistant
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
ollama pull nomic-embed-text                        # the default embedder
```

**Model:** set `MODEL` in `.env` to a local Ollama model (the default, `ollama/llama3.1:8b`) or to a hosted model with its API key, as explained in [Choosing the model](../README.md#choosing-the-model). The answer must follow a schema and combine several documents, so 7–8B models are the minimum; a hosted model gives noticeably better answers.

**Embedder:** `EMBEDDER` in `.env`, local by default; see [Choosing the embedder](../knowledge_sources/README.md#choosing-the-embedder).

## Run

```bash
# interactive mode over the sample documents in knowledge/
python main.py

# one question
python main.py --question "When can a new employee start taking paid leave?"

# your own documents, with a hosted model and the agent's reasoning visible
python main.py --folder ~/Documents/team-handbook --model gpt-4o-mini --verbose
```

All the documents are embedded at start-up, so a large folder takes a while the first time you ask (and every time you start the program). For hundreds of documents, a dedicated vector database that you index once and query through a RAG tool scales better than knowledge.

## Ideas to extend it

- Keep the conversation: pass the previous questions and answers as an extra input so follow-up questions ("and for part-time employees?") work.
- Add a second agent that turns an "I don't know" into a draft question for the right department head (their names are in `company_info.json`).
- Watch the folder and rebuild the crew when a file changes, instead of at every start.

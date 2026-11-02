# Knowledge sources

So far every agent worked only with what it received at run time: the prompt, the task inputs and its tools. **Knowledge** gives agents a reference library: your policies, documents, spreadsheets or API data are split into chunks, embedded into a vector store, and the most relevant chunks are added to the agent's prompt before each task. It is RAG built into CrewAI, with no retrieval tool or retrieval agent to write.

```
            ┌─ when the crew starts ──────────────────────────────────────┐
sources ──▶ │ text ──▶ chunks ──▶ embedder ──▶ vector store (ChromaDB)     │
            └──────────────────────────────────────────────┬─────────────┘
            ┌─ before each task ───────────────────────────▼──────────────┐
task ─────▶ │ LLM rewrites the task as a search query ──▶ top chunks      │──▶ agent prompt ──▶ answer
            └──────────────────────────────────────────────────────────────┘
```

## Examples

Short, focused scripts, one concept each. The sample files in [`knowledge/`](knowledge/) belong to a fictional company, *Lumen Analytics*.

| Script | Concept | Key pieces |
|---|---|---|
| [`01_string_knowledge.py`](01_string_knowledge.py) | Knowledge from a string, shared by the whole crew; `--no-knowledge` shows the invented answer you get without it. | `StringKnowledgeSource`, `Crew(knowledge_sources=..., embedder=...)` |
| [`02_file_knowledge.py`](02_file_knowledge.py) | One agent per file type: an HR policy (`.txt`), meeting notes (`.pdf`), user feedback (`.csv`) and the org chart (`.json`). | `TextFileKnowledgeSource`, `PDFKnowledgeSource`, `CSVKnowledgeSource`, `JSONKnowledgeSource` |
| [`03_agent_vs_crew_knowledge.py`](03_agent_vs_crew_knowledge.py) | Shared crew knowledge plus private agent knowledge, and an agent saying "I don't know" when the answer is in another agent's files. | `Agent(knowledge_sources=...)` vs. `Crew(knowledge_sources=...)` |
| [`04_retrieval_tuning.py`](04_retrieval_tuning.py) | What retrieval actually does: the rewritten search query, the chunks and their similarity scores. | `chunk_size`, `chunk_overlap`, `KnowledgeConfig`, `KnowledgeRetrievalCompletedEvent` |
| [`05_custom_source.py`](05_custom_source.py) | Your own source: current weather and forecast from the free Open-Meteo API. | `BaseKnowledgeSource` with `validate_content`, `add`, `aadd` |

[`docs_assistant`](../docs_assistant/) puts all of this together in a complete application that answers questions over a folder of documents.

## Setup

```bash
cd crew_ai/knowledge_sources
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
ollama pull nomic-embed-text                        # the default embedder (small, ~270 MB)
```

**Model:** set `MODEL` in `.env` to a local Ollama model (the default, `ollama/llama3.1:8b`) or to a hosted model with its API key, as explained in [Choosing the model](../README.md#choosing-the-model). No script calls tools; 7–8B models answer from the retrieved chunks well, 1–3B models tend to ignore part of them.

**Embedder:** set with `EMBEDDER` in `.env`, independently from `MODEL` (see [below](#choosing-the-embedder)). The default, `ollama/nomic-embed-text`, runs locally even if your LLM is hosted.

## Run

```bash
python 01_string_knowledge.py
python 01_string_knowledge.py --no-knowledge          # same question, no policy: compare the answers
python 02_file_knowledge.py --source text             # or: pdf | csv | json
python 02_file_knowledge.py --source csv --question "Which plan complains the most?"
python 03_agent_vs_crew_knowledge.py
python 04_retrieval_tuning.py
python 04_retrieval_tuning.py --chunk-size 1000 --limit 1
python 04_retrieval_tuning.py --threshold 0.8         # too strict: no chunk reaches the agent
python 05_custom_source.py --city Manresa --question "Will it rain this weekend?"
```

Every script accepts `--model` to use another LLM for one run, and 01–03 accept `--reset` to embed the sources again from scratch (needed after editing a file, see [Storage](#where-the-knowledge-is-stored)).

## The building blocks

### Sources

| Source | Input | Notes |
|---|---|---|
| `StringKnowledgeSource(content=...)` | A Python string | Quick facts, policies, FAQs written in code. |
| `TextFileKnowledgeSource(file_paths=[...])` | `.txt`, `.md` | Read as is. |
| `PDFKnowledgeSource(file_paths=[...])` | `.pdf` | Text extracted with `pdfplumber` (scanned PDFs without a text layer give nothing). |
| `CSVKnowledgeSource(file_paths=[...])` | `.csv` | Each row becomes a line of values separated by spaces; column names appear only once, in the header line, so keep the columns self-explanatory. |
| `JSONKnowledgeSource(file_paths=[...])` | `.json` | Converted into indented `key: value` text, lists as `- item`. |
| `ExcelKnowledgeSource(file_paths=[...])` | `.xlsx` | Every sheet, needs `pandas` and `openpyxl`. |
| Your own `BaseKnowledgeSource` subclass | Anything | APIs, databases, wikis… (see `05`). |

**File paths.** A string such as `"hr_policy.txt"` is looked up in a `knowledge/` folder **under the directory you run the script from**. A `Path` object is used as is. These scripts pass `KNOWLEDGE_DIR / "hr_policy.txt"` so they work from anywhere.

### Agent or crew knowledge

```python
crew = Crew(
    agents=[hr_assistant, product_analyst],
    tasks=[...],
    knowledge_sources=[company_info],          # every agent can use it
    embedder=embedder,                          # also used by agents without their own
)
hr_assistant = Agent(..., knowledge_sources=[hr_policy])   # only this agent
```

Each agent searches its own collection (named after its role) **and** the crew's (`crew`). Give private knowledge to the agent that needs it: smaller collections mean more relevant chunks and fewer tokens for everyone else.

### Retrieval knobs

| Setting | Where | Default | Effect |
|---|---|---|---|
| `chunk_size`, `chunk_overlap` | Each source | 4000, 200 characters | How text is split. Small files end up as one chunk. Chunks are cut by characters, not sentences. |
| `results_limit` | `Agent(knowledge_config=KnowledgeConfig(...))` | 5 (agent knowledge), 3 (crew knowledge) | How many chunks are added to the prompt. |
| `score_threshold` | Same | 0.6 (agent knowledge), 0.35 (crew knowledge) | Minimum similarity (0–1) for a chunk to be used. |

Without a `KnowledgeConfig`, agent and crew knowledge use different defaults; with one, the agent applies the same values to both.

The search query is **not** the task text: the agent's LLM first rewrites the task into a short query focused on the information needed (`agent.knowledge_search_query`), so a better LLM also retrieves better. `04_retrieval_tuning.py` prints the query and the score of every chunk so you can see the effect of each knob.

### Custom sources

```python
class WeatherKnowledgeSource(BaseKnowledgeSource):
    city: str = Field(description="City to get the weather for")

    def validate_content(self) -> str:           # load the data, return clean text
        ...

    def add(self) -> None:                        # chunk + store
        self.chunks.extend(self._chunk_text(self.validate_content()))
        self._save_documents()

    async def aadd(self) -> None:                 # async version, required by CrewAI
        text = await asyncio.to_thread(self.validate_content)
        self.chunks.extend(self._chunk_text(text))
        await self._asave_documents()
```

Knowledge is loaded **once, when the crew starts**. That suits reference data (documents, catalogues, policies, yesterday's numbers). If the agent needs data that is fresh at the moment it acts, or must decide *whether* to look something up, use a tool instead (see [`currency_converter`](../currency_converter/)).

## Choosing the embedder

The **embedder** turns text into vectors; it is a separate, much smaller model than the LLM. CrewAI uses OpenAI's `text-embedding-3-small` unless told otherwise, which would require an OpenAI key even with a local or Claude LLM. [`knowledge_setup.py`](knowledge_setup.py) reads `EMBEDDER` from `.env` and builds the spec passed to `Crew(embedder=...)` or `Agent(embedder=...)`:

| `EMBEDDER` | Provider spec | Needs |
|---|---|---|
| `ollama/nomic-embed-text` (default) | `{"provider": "ollama", "config": {"model_name": "nomic-embed-text", "url": "http://localhost:11434"}}` | `ollama pull nomic-embed-text` and the `ollama` Python package |
| `openai/text-embedding-3-small` | `{"provider": "openai", "config": {"model_name": "text-embedding-3-small"}}` | `OPENAI_API_KEY` |
| `gemini/gemini-embedding-001` | `{"provider": "google-generativeai", "config": {"model_name": "gemini-embedding-001"}}` | `GEMINI_API_KEY` |

Anthropic has no embedding models, so with Claude as `MODEL` keep a local embedder. Other local options are `ollama/mxbai-embed-large` (larger, more accurate) and `ollama/all-minilm` (tiny, faster).

## Where the knowledge is stored

CrewAI saves the vector store (ChromaDB) in your user data folder and **keeps it between runs**. Every time a crew (or an agent with knowledge) starts, its sources are embedded again and *upserted*: a chunk identical to a stored one replaces it, anything else is added. Three things follow, and `knowledge_setup.py` handles them:

- **Embedders cannot be mixed.** Vectors from different models have different sizes; switching `EMBEDDER` on an existing store fails with *"Embedding dimension mismatch"*. → The store name includes the embedder, so each one gets its own.
- **Collections are shared by name.** Crew knowledge always goes to the `crew` collection, so two scripts in the same folder would read each other's chunks. → Each script gets its own store, through the `CREWAI_STORAGE_DIR` variable (which CrewAI reads when it is imported: that is why `knowledge_setup` is imported first).
- **Edited files leave old chunks behind.** Chunks are stored by content, so the old version of an edited file stays and can still be retrieved. → Run with `--reset` after editing a source (`04` and `05` reset on every run).

The path of each store is printed by `01`; on Linux they are under `~/.local/share/agentic-systems-knowledge-sources-*`, on macOS under `~/Library/Application Support/`.

## Ideas to extend it

- Add an `ExcelKnowledgeSource` with a sales spreadsheet and ask the CSV analyst to compare it with the feedback.
- Write a `MarkdownFolderKnowledgeSource` that loads every `.md` file of a notes folder (an Obsidian vault, a wiki export) as one source.
- Add a guardrail (see [`task_features`](../task_features/)) that rejects answers containing numbers that do not appear in the retrieved knowledge.

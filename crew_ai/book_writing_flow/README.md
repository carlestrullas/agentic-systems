# Book Writing Flow

A **multi-crew flow** that researches a topic and writes a whole book about it. One crew designs the outline; then one crew per chapter writes the chapters **in parallel**; finally the flow joins them into a single Markdown file.

```
generate_outline ──▶ generate_chapters ──────────────▶ save_book
  OutlineCrew          ChapterWriterCrew × N              output/book.md
  (1 run)              (N runs in parallel)               (Python)
```

## How it works

| Step | Kind | What it does |
|---|---|---|
| `generate_outline` | Crew | `OutlineCrew` researches the topic and returns an `Outline` with the chapter titles. |
| `generate_chapters` | Crews in parallel | Starts one `ChapterWriterCrew` per chapter at the same time and waits for all of them. |
| `save_book` | Python | Joins the chapters, in outline order, with a table of contents, into `output/book.md`. |

### The two crews

| Crew | Agents | Output |
|---|---|---|
| [`OutlineCrew`](src/book_writing_flow/crews/outline_crew/outline_crew.py) | *Senior Book Researcher* (web search) → *Senior Book Outline Writer* | `Outline(total_chapters, titles)` |
| [`ChapterWriterCrew`](src/book_writing_flow/crews/chapter_writer_crew/chapter_writer_crew.py) | *Senior Chapter Researcher* (web search) → *Senior Book Writer* | `Chapter(title, content)` |

Each crew lives in its own folder under `crews/`, with its own YAML config, and knows nothing about the flow: it receives inputs and returns a Pydantic object ([`models.py`](src/book_writing_flow/models.py)). The flow is the only place that knows the order of the work.

Every chapter writer receives the **full outline** as `{chapters}`, so it knows what the other chapters cover and avoids repeating them.

### Running crews in parallel

```python
@listen(generate_outline)
async def generate_chapters(self):
    async def write_chapter(number, title):
        crew = ChapterWriterCrew(llm=get_llm()).crew()
        result = await asyncio.to_thread(crew.kickoff, inputs={...})
        return result.pydantic

    self.state.chapters = list(await asyncio.gather(
        *(write_chapter(i, t) for i, t in enumerate(self.state.titles, 1))
    ))
```

A flow step can be `async`. `crew.kickoff()` is a blocking call, so each one runs in its own thread with `asyncio.to_thread`: that is what makes the chapters be written at the same time instead of one after another. `asyncio.gather` returns the results in the order of the outline, whatever order they finish in.

With a hosted model, N chapters take roughly as long as one. With Ollama, the requests are queued by the Ollama server (see `OLLAMA_NUM_PARALLEL` in its docs), so the gain depends on your machine.

## Project structure

```
book_writing_flow/
├── pyproject.toml
├── .env.example
├── tests/
└── src/book_writing_flow/
    ├── main.py                       # BookState, BookFlow and entry points
    ├── models.py                     # Outline, Chapter
    ├── llm.py
    ├── tools/
    │   └── __init__.py               # search_tools(): Serper web search, if a key is set
    └── crews/
        ├── outline_crew/
        │   ├── outline_crew.py
        │   └── config/{agents,tasks}.yaml
        └── chapter_writer_crew/
            ├── chapter_writer_crew.py
            └── config/{agents,tasks}.yaml
```

## Setup

From this folder (`crew_ai/book_writing_flow`):

```bash
cp .env.example .env
```

**Model:** set `MODEL` in `.env` to a local Ollama model (the default, `ollama/llama3.1:8b`) or to a hosted model with its API key. Both options are explained step by step in [Choosing the model](../README.md#choosing-the-model). The researchers call a search tool and both crews return structured output, so with Ollama use a 7–8B model or larger.

**Web search:** get a free key at [serper.dev](https://serper.dev) and set `SERPER_API_KEY`. Without it the flow still runs, but the researchers can only use what the model already knows.

Then install the project with the CrewAI CLI (`pip install crewai uv`, then `crewai install`) or with pip (`python -m venv .venv && source .venv/bin/activate`, then `pip install -e .`).

## Run

```bash
crewai run                                                  # default topic, up to 6 chapters
kickoff --topic "Quantum computing for engineers" --max-chapters 4
kickoff --topic "The history of the internet" --model gpt-4o-mini
plot                                                        # saves and opens book_writing_flow.html
run_with_trigger '{"topic": "Climate tech", "max_chapters": 5}'
```

With `crewai install`, run the other entry points through uv: `uv run kickoff --topic "..."`.

A book means several agents per chapter, so start with `--max-chapters 3` to check the setup before running a long one. The result is saved to `output/book.md` (git-ignored).

## Ideas to extend it

- Add an editor crew after `generate_chapters` that reviews the whole book for consistency and transitions between chapters.
- Add a `@router` that rewrites chapters that are too short or off-topic before saving.
- Export the Markdown to PDF or EPUB in an extra step.

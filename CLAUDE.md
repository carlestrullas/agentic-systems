# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A collection of self-contained, educational examples of LLM agent systems, organised **by framework** (currently only `crew_ai/`). Each example is its own independent Python project with its own venv, dependencies and `.env`. There is no root-level build, no shared package, no linter config and no test suite (the `tests/` folders in CrewAI projects contain only `.gitkeep`). Verifying a change means running the example.

The READMEs form a strict hierarchy: the root `README.md` lists frameworks, `crew_ai/README.md` holds the learning path, shared setup and conventions, and each example's `README.md` explains only its own code. Adding an example should only touch its framework README (add a row to the learning path table, and to "Core concepts" if it introduces a new idea). The root README's example count and coverage summary may also need updating.

## Running examples

From inside an example folder:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py                       # class-based crews
python 01_basic_flow.py              # concept-script folders (flows, task_features, knowledge_sources)
python main.py --model gpt-4o-mini   # every LLM script accepts --model to override MODEL from .env
```

CrewAI CLI projects (`flows/poem_flow`, `content_planner_flow`, `book_writing_flow`) use `pyproject.toml` instead: install with `crewai install` (or `pip install -e .`), run with `crewai run`, or with the `[project.scripts]` entry points `kickoff`, `plot` and `run_with_trigger '<json>'` (use `uv run kickoff ...` after `crewai install`).

The default model is local Ollama (`MODEL=ollama/llama3.1:8b`). Knowledge examples also need `ollama pull nomic-embed-text` (selected with `EMBEDDER`). `quality_inspector` needs a vision model.

## Shared-file invariants (important)

- **`llm.py` is byte-identical in every example** (14 copies, including `src/<pkg>/llm.py` in CLI projects). If you change one, copy it to all of them and confirm with `find . -name llm.py -exec md5 -r {} \;`. It exposes `build_llm(model, temperature)`, which validates Ollama reachability, pulled model and provider API keys and exits with an actionable `SystemExit`, and `get_llm()`, an `lru_cache`d version for flows.
- **`knowledge_setup.py` is identical** in `knowledge_sources/` and `docs_assistant/`. It must be imported **before anything from `crewai`**, because it sets `CREWAI_STORAGE_DIR` (a per-example/script/embedder ChromaDB store) and CrewAI reads that only at import time.
- `.env.example` lists every variable an example reads, with `REPLACE_ME` placeholders. `llm.py` treats `REPLACE_ME` as unset. Copy an existing `.env.example` as the base for new examples.

## Code layouts

Pick the layout that matches the example kind (see `crew_ai/README.md` → Conventions):

- **Single-file scripts**: `researcher_agent`, `technical_writer_agent`.
- **Class-based crew** (default for new examples): `main.py` (argparse CLI, `load_dotenv(HERE / ".env")`, `build_llm(args.model)`) + `<name>_crew.py` with a `@CrewBase` class that takes `llm` in `__init__` and loads `config/agents.yaml` / `config/tasks.yaml`, plus `models.py` (Pydantic schemas for `output_pydantic`) and `tools/` (`BaseTool` subclasses) when needed.
- **Concept scripts**: numbered `01_…py`, `02_…py`, one concept each, sharing one `llm.py`.
- **CrewAI project** (for flows that orchestrate crews): `crewai create flow` layout, with `src/<pkg>/main.py` holding the state model, the `Flow` class and the entry points, and one folder per crew under `crews/<name>/` with its own YAML. Crews know nothing about the flow: they take inputs and return Pydantic objects, and the flow owns the ordering and state. Parallel crews use `async` steps with `asyncio.to_thread(crew.kickoff, ...)` + `asyncio.gather`.

Generated files go in `output/` (git-ignored), and so does `.env`. Every example README follows the same structure: description with a small diagram, how it works, **Setup** (example-specific only, linking to `crew_ai/README.md#choosing-the-model`), **Run**, **Ideas to extend it**.

## Convention tooling

- **`check-conventions` skill** (`.claude/skills/check-conventions/`): runs `scripts/check.py --fix` to repair mechanical drift (shared-file copies, required files, README sections, `.env.example` coverage, tracked secrets/output, learning-path rows, root README counts), then fixes the judgment-based TODOs and asks about ambiguous ones. Run it before committing or after adding, renaming or deleting an example.
- **`code-reviewer` agent** (`.claude/agents/code-reviewer.md`): read-only review of changes. It runs the same checker without `--fix` and adds the checks a script can't do (import order, layout, docs matching code). It reports; the skill fixes.

# Memory

Until now every crew was **stateless**: each `kickoff()` started from a blank slate, so a user who gave the assistant their name five seconds ago had to give it again. **Memory** lets agents remember what happened in earlier tasks and earlier runs: facts users told them, decisions, results. It is different from the two ways we already had to give agents information:

| | What it holds | When it changes |
|---|---|---|
| [Knowledge](../knowledge_sources/) | Reference material you provide: policies, documents, data. | When you change the sources. |
| [Tools](../currency_converter/) | Data fetched on the fly (an API, a search). Not kept afterwards. | Every call. |
| **Memory** | What the agents learn while working: user preferences, facts, outcomes. | After every task. |

```
            ┌─ after each task ───────────────────────────────────────────────────┐
task + ───▶ │ memory LLM ──▶ short facts + scope, categories, importance ──▶ embed │──▶ storage (LanceDB)
result      └──────────────────────────────────────────────────────────────────────┘        │
            ┌─ before each task ───────────────────────────────────────────────▼─────────┐
task ─────▶ │ recall(task description) ──▶ top 5 by similarity, recency and importance   │──▶ agent prompt
            └─────────────────────────────────────────────────────────────────────────────┘
```

## Examples

Short, focused scripts, one concept each:

| Script | Concept | Key pieces |
|---|---|---|
| [`01_memory_on_off.py`](01_memory_on_off.py) | Two kickoffs: the user gives a fact, then asks about it. With `--no-memory`, the second kickoff has no idea. | `Crew(memory=...)` |
| [`02_across_sessions.py`](02_across_sessions.py) | Two separate runs with a new crew and a new agent: what connects them is the storage folder. | `Memory(storage=path)` |
| [`03_what_is_stored.py`](03_what_is_stored.py) | Meeting notes about two companies and two people become separate facts, each filed in a scope per entity. | `memory.tree()`, `list_records()`, `recall()` |
| [`04_recall_tuning.py`](04_recall_tuning.py) | How recall ranks facts: similarity, recency and importance weights; shallow vs. deep recall; filtering by scope or category. | `remember(scope=, categories=, importance=)`, `*_weight`, `depth` |
| [`05_user_memory.py`](05_user_memory.py) | One assistant, two users: each crew sees only its user's branch of the memory. | `memory.scope("/users/<id>")` |
| [`06_reset_memory.py`](06_reset_memory.py) | Delete one person's facts, then wipe the whole memory. | `forget()`, `reset()`, `crew.reset_memories()` |

## Setup

```bash
cd crew_ai/memory
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
ollama pull nomic-embed-text                        # the default embedder (small, ~270 MB)
```

**Model:** set `MODEL` in `.env` to a local Ollama model (the default, `ollama/llama3.1:8b`) or to a hosted model with its API key, as explained in [Choosing the model](../README.md#choosing-the-model). The same model also does the memory analysis (splitting results into facts, choosing scopes), which needs structured output: 7–8B models do it reasonably, 1–3B models often store whole paragraphs instead of clean facts, and a hosted model gives the tidiest memories.

**Embedder:** set with `EMBEDDER` in `.env`, independently from `MODEL`, exactly as in [`knowledge_sources`](../knowledge_sources/README.md#choosing-the-embedder). The default, `ollama/nomic-embed-text`, runs locally.

## Run

```bash
python 01_memory_on_off.py
python 01_memory_on_off.py --no-memory               # same two kickoffs, the colour is forgotten
python 01_memory_on_off.py --fact "I am allergic to peanuts" --question "Suggest a snack for me"
python 02_across_sessions.py --session tell
python 02_across_sessions.py --session ask           # a new run: it still knows
python 02_across_sessions.py --reset
python 03_what_is_stored.py
python 03_what_is_stored.py --question "Who should I call about the Beta Corp renewal?"
python 04_recall_tuning.py
python 04_recall_tuning.py --importance-weight 0     # which diet fact wins now?
python 04_recall_tuning.py --depth deep --query "<a question of more than 200 characters>"
python 05_user_memory.py
python 05_user_memory.py --user carles --message "I'm vegetarian and I live in Manresa."
python 05_user_memory.py --user carles --message "Suggest a restaurant for tonight."
python 06_reset_memory.py
```

Every script accepts `--model` to use another LLM for one run. 01, 03, 04, 05 (demo mode) and 06 empty their memory at the start, so each run is repeatable. 02 and `05 --user` keep it, because remembering between runs is what they show; delete their folders under `output/memory/` (or run `02 --reset`) to start again.

## The building blocks

### One memory, five old names

Older CrewAI versions, and most tutorials, describe five kinds of memory, each with its own class. Since CrewAI 1.x they are all one `Memory` object, and each old name is now a way of using it:

| Old name | What it meant | Now |
|---|---|---|
| Short-term memory | Recent context within one session. | Facts saved after each task are recalled by the next task (`01`). |
| Long-term memory | Learnings kept across sessions. | The storage is a folder on disk, so every run sees what earlier runs saved (`02`). |
| Entity memory | Facts kept per person, company or product. | The memory LLM files each fact in a scope per entity, e.g. `/companies/beta` (`03`). |
| Contextual memory | The three above merged into the prompt. | One `recall()` searches all scopes and ranks the results together (`03`, `04`). |
| User memory | Per-user memory, through the external Mem0 service. | One scope per user: `memory.scope("/users/<id>")` (`05`). |

### Turning it on

```python
crew = Crew(agents=[...], tasks=[...], memory=True)      # defaults: OpenAI embedder, user data folder
crew = Crew(agents=[...], tasks=[...], memory=memory)    # your own Memory, as in these scripts

memory = Memory(
    llm=llm,                                              # analyses what is saved and what is asked
    embedder={"provider": "ollama", "config": {"model_name": "nomic-embed-text"}},
    storage="output/memory/my-crew",                      # LanceDB folder; kept between runs
)
```

[`memory_setup.py`](memory_setup.py) builds this `Memory` for each script: the agents' LLM, the `EMBEDDER` from `.env` and a folder of its own under `output/memory/` (git-ignored), named after the script and the embedder. You can open or delete those folders yourself. Embedders cannot share a folder, because vectors from different models have different sizes.

With memory on, CrewAI does three things on its own:

1. **Before each task** it recalls the 5 memories most relevant to the task description and adds them to the agent's prompt.
2. **After each task** the memory LLM turns the task and its result into short facts and saves them. Saving runs in the background; `memory.drain_writes()` waits for it, and both `recall()` and the end of `kickoff()` do so automatically.
3. It gives the agents two tools, *Search memory* and *Save to memory*, so they can look things up or save facts on purpose.

### What a record looks like

| Field | Set by | Used for |
|---|---|---|
| `content` | The memory LLM (one short fact) or you | What the agent reads. |
| `scope` | The LLM, or `remember(scope=...)` | A path such as `/companies/beta`. Recall and deletion can be limited to a branch. |
| `categories` | The LLM, or you | Tags to filter by: `recall(categories=["diet"])`. |
| `importance` | The LLM, or you (0–1) | Part of the ranking. |
| `created_at` | Automatic | Recency in the ranking. |

If you pass `scope`, `categories` and `importance` to `remember()` yourself, the LLM is not needed to analyse the fact (`04` does this). When a new fact is almost identical to a stored one (similarity above `consolidation_threshold`, 0.85), the LLM decides whether to keep both, update the old one or delete it, so corrections do not pile up as duplicates.

### How recall ranks

```
score = semantic_weight × similarity + recency_weight × 0.5^(age_days / recency_half_life_days) + importance_weight × importance
```

| Setting | Default | Effect |
|---|---|---|
| `semantic_weight` | 0.5 | How much similarity to the query counts. |
| `recency_weight`, `recency_half_life_days` | 0.3, 30 | Newer facts rank higher; the bonus halves every 30 days. |
| `importance_weight` | 0.2 | Important facts rank higher. |
| `recall(depth=...)` | `"deep"` | `"shallow"`: one vector search, no LLM. `"deep"`: the LLM splits the query into targeted searches and picks the scopes; queries shorter than `query_analysis_threshold` (200 characters) skip that step. |

### Scopes: per user, per agent, per crew

`memory.scope(path)` is a view of one branch: everything saved through it goes under `path`, and recall only searches there. Pass it as `Crew(memory=...)` or `Agent(memory=...)`. `memory.slice([path1, path2])` is a read-only view over several branches, for example a support agent that may read the product notes and the current user's notes but write neither. With `Crew(memory=True)`, CrewAI scopes everything under `/crew/<crew name>` and each agent's saves under `.../agent/<role>`.

Scopes match by **prefix**, without stopping at the `/`: `memory.scope("/users/al")` also sees `/users/alice`. Use IDs that are never the start of another ID (UUIDs, fixed-length numbers).

### Forgetting

| Call | Deletes |
|---|---|
| `memory.forget(scope=..., categories=..., older_than=..., record_ids=...)` | Only the matching records; returns how many. |
| `memory.reset(scope)` | A whole branch, or everything without a scope. |
| `crew.reset_memories("memory")` | The crew's whole memory (also `"knowledge"`, `"kickoff_outputs"`, `"all"`). |
| `crewai reset-memories --memory` | The same from the CLI, inside a CrewAI project. |

The same prefix rule applies here: `forget(scope="/people/bob")` also deletes `/people/bobby`, and records saved at the root scope `/` are deleted along with any scope.

`Memory(read_only=True)`, or setting `memory.read_only = True`, lets a crew recall without saving anything new (`06` uses it so that only the seeded facts are in memory).

## Ideas to extend it

- Add memory to [`docs_assistant`](../docs_assistant/) so it remembers which documents each user asked about and can answer follow-up questions.
- Build a small chat loop on top of `05`: read messages with `input()` and keep one crew per user, so you can hold a real conversation with memory.
- Use `memory.slice(...)` to give a team of agents a shared read-only scope with company facts and a private writable scope each, and check with `memory.tree()` who wrote what.
- Write a clean-up job that calls `memory.forget(older_than=...)` to drop facts nobody has needed for months.

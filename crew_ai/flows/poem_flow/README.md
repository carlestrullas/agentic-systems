# Poem Flow

A CrewAI **flow that orchestrates a crew**, organised exactly like a project generated with `crewai create flow`, but running on any LLM (a local model with Ollama or a hosted one with an API key) instead of being tied to OpenAI.

```
generate_sentence_count ──▶ generate_poem ──▶ save_poem
  plain Python (random)      PoemCrew (LLM)     plain Python (file)
```

1. **`generate_sentence_count`** picks how many sentences the poem will have (1–5). Ordinary code, no LLM.
2. **`generate_poem`** runs `PoemCrew`, a `@CrewBase` crew with one *poem writer* agent, passing it the topic and the sentence count.
3. **`save_poem`** writes the poem to `output/poem.txt`.

All three steps share a structured state:

```python
class PoemState(BaseModel):
    topic: str = "learning something new"
    sentence_count: int = 1
    poem: str = ""
```

## Project structure

```
poem_flow/
├── .gitignore
├── .env.example                 # copy to .env and choose the model
├── pyproject.toml               # dependencies and entry points (kickoff, plot, ...)
├── README.md
├── tests/
└── src/poem_flow/
    ├── __init__.py
    ├── main.py                  # PoemState, PoemFlow and the entry points
    ├── llm.py                   # builds the LLM from MODEL (Ollama or hosted)
    ├── crews/
    │   └── poem_crew/
    │       ├── config/
    │       │   ├── agents.yaml  # role, goal and backstory of the poem writer
    │       │   └── tasks.yaml   # the write_poem task
    │       └── poem_crew.py     # PoemCrew (@CrewBase)
    └── tools/
        ├── __init__.py
        └── custom_tool.py       # SentenceCounterTool, an optional custom tool
```

| Folder / file | Role |
|---|---|
| `crews/` | One sub-folder per crew, each with its own YAML config and `@CrewBase` class. To add a crew, add a folder here and one more `@listen` step in `main.py`. |
| `tools/` | Custom tools the agents can use. `SentenceCounterTool` counts sentences; it is not attached by default (see the commented line in `poem_crew.py`). |
| `main.py` | The flow and the entry points listed in `[project.scripts]`. |
| `pyproject.toml` | Makes the folder an installable project; `[tool.crewai] type = "flow"` is what lets `crewai run` recognise it. |

Differences from the generated template: the LLM is injected into the crew from `llm.py` (so `MODEL` in `.env` selects Ollama or a hosted provider), the topic can be passed on the command line, and the output path does not depend on the folder you run it from.

## Setup

All commands run from this folder (`crew_ai/flows/poem_flow`).

```bash
cp .env.example .env
```

**Model:** set `MODEL` in `.env` to a local Ollama model (the default, `ollama/llama3.1:8b`) or to a hosted model with its API key. Both options are explained step by step in [Choosing the model](../../README.md#choosing-the-model). The crew uses no tools, so even a small Ollama model such as `llama3.2:3b` works.

Then install the project, with either of these options.

**Option 1: CrewAI CLI (uses [uv](https://docs.astral.sh/uv/))**

```bash
pip install crewai uv     # if you don't have them yet
crewai install            # creates .venv and installs the project
```

**Option 2: plain pip**

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

## Run

```bash
crewai run                                  # option 1: runs the kickoff entry point
kickoff                                     # option 2 (inside the venv)
kickoff --topic "Monday mornings"
kickoff --topic "Monday mornings" --model gpt-4o-mini
plot                                        # saves and opens poem_flow.html
run_with_trigger '{"topic": "the sea"}'     # start the flow from a JSON payload
```

With option 1, the other entry points also run inside the uv environment: `uv run kickoff --topic "Monday mornings"`, `uv run plot`.

The crew's reasoning is printed to the console, and the poem is saved to `output/poem.txt` (git-ignored).

## Ideas to extend it

- Attach `SentenceCounterTool` to the poem writer and check whether the poems respect the length more often.
- Add a `reviewer_crew` under `crews/` and a `@router` that sends the poem back for a rewrite when the review is negative.
- Replace the random sentence count with a value chosen by an LLM from the topic.

# CrewAI

[CrewAI](https://github.com/crewAIInc/crewAI) is a Python framework for orchestrating role-playing AI agents. You describe each agent by its **role**, **goal** and **backstory**, give it **tools**, assign it **tasks**, and group everything into a **crew** that runs the tasks sequentially or under a manager agent. **Flows** add event-driven workflows on top, mixing plain Python steps with crews.

## Learning path

The examples are ordered so that each one builds on the previous ones. Each row lists only the concepts it adds.

| # | Example | Agents | Introduces |
|---|---|---|---|
| 1 | [`researcher_agent`](researcher_agent/) | 1 | The building blocks: `Agent`, `Task`, `Crew`, a built-in search tool and saving the result to a file. |
| 2 | [`technical_writer_agent`](technical_writer_agent/) | 1 + 1 | Task inputs (`{topic}` + `kickoff(inputs=...)`), an agent without tools vs. one with `FileReadTool`. |
| 3 | [`research_crew`](research_crew/) | 3 | Multi-agent pipelines, `context` between tasks, prompts in YAML and modular `@CrewBase` classes. |
| 4 | [`entity_extractor`](entity_extractor/) | 1 | Structured output: the task returns a validated Pydantic object (`output_pydantic`). |
| 5 | [`currency_converter`](currency_converter/) | 2 | Custom tools (`BaseTool`), and one Pydantic schema shared by an agent's output and a tool's input. |
| 6 | [`flows`](flows/) | – | Flows: `@start`/`@listen`, state, `or_`/`and_`, `@router`, and crews inside a flow project (`poem_flow`). |

## Choosing the model

Every example selects the LLM with one variable, `MODEL`, in its `.env` file. You can run everything on a **local model with Ollama** (free, no API key) or on a **hosted model with an API key**.

### Common setup

Each example is self-contained. From its folder:

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

(`flows/poem_flow` is a CrewAI project with a `pyproject.toml` instead; its README explains how to install it.)

### Option A: local model with Ollama (no API key)

1. Install Ollama from [ollama.com](https://ollama.com) (on Linux: `curl -fsSL https://ollama.com/install.sh | sh`).
2. Download a model and make sure the server is running:

   ```bash
   ollama pull llama3.1:8b
   ollama serve        # not needed if the Ollama desktop app is already open
   ```

3. In `.env`, keep the default lines:

   ```env
   MODEL=ollama/llama3.1:8b
   OLLAMA_BASE_URL=http://localhost:11434
   ```

Any model from the [Ollama library](https://ollama.com/library) works by writing `ollama/<name>`. What matters most is whether the example's agents **call tools**:

| Model | RAM (approx.) | Good for |
|---|---|---|
| `llama3.2:1b` / `llama3.2:3b` | 2–4 GB | Examples without tool calling: `writer.py` and `flows`. Structured output (`entity_extractor`) runs but is less reliable. |
| `llama3.1:8b` / `qwen2.5:7b` | ~6 GB | Default. Reliable tool calling, so it works for every example. |
| `qwen2.5:14b` and larger | 10 GB+ | Better quality if your machine can run it. |

### Option B: hosted model with an API key

In `.env`, comment out the Ollama `MODEL` line, uncomment the one for your provider and fill in its key:

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

### Switching model for one run

Every script that uses an LLM accepts `--model`, which overrides `.env` for that run:

```bash
python main.py --model gpt-4o-mini
```

### How it works

Each example has a copy of the same [`llm.py`](technical_writer_agent/llm.py). It reads `MODEL` and builds a CrewAI `LLM`:

- If the name starts with `ollama/`, it checks that Ollama is reachable at `OLLAMA_BASE_URL` and that the model has been pulled, then connects to it locally.
- Otherwise it checks that the API key of that provider is set and lets CrewAI call the hosted API.

If something is missing, the script stops with a message that says exactly what to do (start Ollama, `ollama pull <model>`, or which key to set).

## Conventions

These rules keep the examples consistent as the folder grows.

### Every example folder has

| File | Purpose |
|---|---|
| `README.md` | What the example does (with a small diagram), how it works, **Setup**, **Run** and **Ideas to extend it**. Setup only lists what is specific to the example and links here for the model. |
| `requirements.txt` | Its dependencies (a `pyproject.toml` for projects created with the `crewai` CLI). |
| `.env.example` | Every variable it reads, with `REPLACE_ME` placeholders. The real `.env` is git-ignored. |
| `llm.py` | The shared model selection. It is **identical in every example**: when you change it, copy it to all of them. |
| `output/` | Created at run time for generated files; git-ignored. |

### Code layout

| Kind of example | Layout | Used in |
|---|---|---|
| Single-file scripts | Everything in one `.py` per agent, to show the basics with no indirection. | `researcher_agent`, `technical_writer_agent` |
| Class-based crew | `main.py` (command line) + `<name>_crew.py` (`@CrewBase` class) + `config/agents.yaml` and `config/tasks.yaml`, plus `models.py` for Pydantic schemas and `tools/` for custom tools when needed. | `research_crew`, `entity_extractor`, `currency_converter` |
| Concept scripts | Numbered scripts (`01_…`, `02_…`), one concept each. | `flows` |
| CrewAI project | The layout generated by `crewai create flow`: `pyproject.toml`, `src/<name>/main.py`, `crews/`, `tools/`. | `flows/poem_flow` |

New examples should use the class-based layout unless they are deliberately teaching something simpler.

### Adding a new example

1. Create a folder with a descriptive `snake_case` name and the files listed above (copy `llm.py` and `.env.example` from an existing example).
2. Add a row to the [learning path](#learning-path) and, if it introduces a new idea, to [core concepts](#core-concepts).
3. Never commit keys or generated files.

## Core concepts

| Concept | In CrewAI |
|---|---|
| **Agent** | `Agent(role, goal, backstory, tools, llm)`: an LLM with a persona and the tools it may use. |
| **Task** | `Task(description, expected_output, agent)`: a unit of work with a clear definition of done. |
| **Tool** | Any function the agent can call, from the `crewai_tools` package or custom-built. |
| **Crew** | `Crew(agents, tasks, process)`: runs the tasks, passing each output as context to the next. |
| **Process** | `sequential` (tasks in order) or `hierarchical` (a manager agent delegates). |
| **CrewBase** | `@CrewBase` class with `@agent`, `@task` and `@crew` methods that load their settings from YAML. |
| **Structured output** | `Task(..., output_pydantic=Model)`: the result is a validated Pydantic object (`result.pydantic`). |
| **Custom tool** | A `BaseTool` subclass with `name`, `description`, `args_schema` (Pydantic) and a `_run` method. |
| **Flow** | A `Flow` class whose methods are steps connected with `@start`, `@listen`, `@router`, `or_` and `and_`, sharing `self.state`. |

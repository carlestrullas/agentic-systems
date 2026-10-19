# CrewAI

[CrewAI](https://github.com/crewAIInc/crewAI) is a Python framework for orchestrating role-playing AI agents. You describe each agent by its **role**, **goal** and **backstory**, give it **tools**, assign it **tasks**, and group everything into a **crew** that runs the tasks sequentially or under a manager agent.

## Examples

| Example | Agents | What it shows |
|---|---|---|
| [`researcher_agent`](researcher_agent/) | 1 | The basic building blocks: an agent with a search tool, a task with a structured expected output, and a crew that saves the result to a file; runs on Ollama or a hosted API. |
| [`technical_writer_agent`](technical_writer_agent/) | 1 + 1 | A writer agent with no tools and a summarizer agent that reads a file with `FileReadTool`; runs on Ollama or a hosted API. |
| [`research_crew`](research_crew/) | 3 | A multi-agent pipeline (research → summary → fact-check) defined as a modular `@CrewBase` class with YAML config; runs on Ollama or a hosted API. |
| [`entity_extractor`](entity_extractor/) | 1 | Structured output: the task returns a validated Pydantic object (`output_pydantic`) with subject-relation-object triplets. |
| [`currency_converter`](currency_converter/) | 2 | A custom tool (`BaseTool` subclass) for live exchange rates, plus a parser agent that turns a free-text question into the tool's Pydantic input. |

## Choosing the model: Ollama or API key

All examples select the LLM with a single `MODEL` variable in `.env`:

| `MODEL` | Runs on | Needs |
|---|---|---|
| `ollama/llama3.1:8b` | Your machine, via [Ollama](https://ollama.com) | `ollama pull llama3.1:8b`, no API key |
| `gpt-4o-mini` | OpenAI | `OPENAI_API_KEY` |
| `anthropic/claude-sonnet-4-5` | Anthropic | `ANTHROPIC_API_KEY` |
| `gemini/gemini-2.0-flash` | Google | `GEMINI_API_KEY` |

Every script also accepts `--model` to override it for one run. Each example's README explains the setup step by step.

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

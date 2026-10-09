# CrewAI

[CrewAI](https://github.com/crewAIInc/crewAI) is a Python framework for orchestrating role-playing AI agents. You describe each agent by its **role**, **goal** and **backstory**, give it **tools**, assign it **tasks**, and group everything into a **crew** that runs the tasks sequentially or under a manager agent.

## Examples

| Example | Agents | What it shows |
|---|---|---|
| [`researcher_agent`](researcher_agent/) | 1 | The basic building blocks: an agent with a search tool, a task with a structured expected output, and a crew that saves the result to a file. |

## Core concepts

| Concept | In CrewAI |
|---|---|
| **Agent** | `Agent(role, goal, backstory, tools, llm)`: an LLM with a persona and the tools it may use. |
| **Task** | `Task(description, expected_output, agent)`: a unit of work with a clear definition of done. |
| **Tool** | Any function the agent can call, from the `crewai_tools` package or custom-built. |
| **Crew** | `Crew(agents, tasks, process)`: runs the tasks, passing each output as context to the next. |
| **Process** | `sequential` (tasks in order) or `hierarchical` (a manager agent delegates). |

# Project Research (hierarchical)

A **hierarchical crew**: a manager agent receives the research of a project idea, delegates market, risk and ROI analysis to three specialists, reviews their work and writes a go / no-go report.

```
                         ┌──▶ Market Demand Analyst ──┐
project ──▶ Manager ─────┼──▶ Risk Analyst ───────────┼──▶ Manager reviews ──▶ final report
        (delegates)      └──▶ ROI Analyst ────────────┘   (can send work back)
```

## Sequential vs. hierarchical

So far every crew in this repo was **sequential**: each task has a fixed agent and the tasks run in the order they are listed. A **hierarchical** crew works like a team with a lead:

| | Sequential | Hierarchical |
|---|---|---|
| Who runs a task | The agent assigned to it | The **manager**, who delegates it to the most suitable agent |
| Order and routing | Fixed in code / YAML | Decided by the manager at run time |
| Quality control | None unless you add it (guardrails, human review) | The manager reviews each answer and can ask for a revision |
| Cost | One agent run per task | Extra LLM calls for the manager's planning, delegation and review |

Use it when the work can be split among specialists but someone should decide who does what and check the result; keep sequential crews when the steps are fixed and cheap.

## How it works

| Agent | Delegation | Tools | Job |
|---|---|---|---|
| *Project Research Manager* | `allow_delegation=True` | Only CrewAI's delegation tools | Assigns each task, reviews the answers, writes the final report. |
| *Market Demand Analyst* | `False` | `SerperDevTool` (optional) | Customers, market size, competitors, demand signals. |
| *Risk Analyst* | `False` | `SerperDevTool` (optional) | Risk table with likelihood, impact and mitigation. |
| *Return on Investment Analyst* | `False` | `SerperDevTool` (optional) | Costs, revenue model, conservative and optimistic scenarios. |

The key lines of [`project_research_crew.py`](project_research_crew.py):

```python
def manager(self) -> Agent:                  # a plain method, NOT @agent
    return Agent(config=self.agents_config["manager"], llm=self.llm, allow_delegation=True)

@agent
def market_analyst(self) -> Agent:           # specialists: @agent, no delegation
    return Agent(config=self.agents_config["market_analyst"], tools=self.search_tools,
                 llm=self.llm, allow_delegation=False)

@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,                  # the specialists only
        tasks=self.tasks,
        process=Process.hierarchical,
        manager_agent=self.manager(),
    )
```

What happens at run time:

1. CrewAI gives **every task to the manager** (the tasks in [`config/tasks.yaml`](config/tasks.yaml) have no `agent:` on purpose) and equips it with two tools: *Delegate work to coworker* and *Ask question to coworker*.
2. The manager picks a specialist for each task and writes them a brief. Specialists know nothing else, so the brief must carry all the context.
3. The specialist's answer comes back to the manager, which accepts it or asks again.
4. The final task receives the three analyses as `context`, and the manager checks them for consistency and writes the report.

Three rules CrewAI enforces or expects:

- The manager **must not** be in `agents`; it goes in `manager_agent`. That is why it is not decorated with `@agent`.
- The manager should **not have tools** of its own: it works through delegation only.
- Placeholders such as `{project}` are filled in for the crew's agents and tasks, **not** for the manager, so the manager's YAML is written without them.

Instead of defining a manager, you can pass `manager_llm=llm` and let CrewAI create a generic one. A custom manager, as here, lets you set its standards (what to check, when to send work back).

## Setup

```bash
cd crew_ai/project_research_hierarchical
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

**Model:** set `MODEL` in `.env` to a local Ollama model (the default, `ollama/llama3.1:8b`) or to a hosted model with its API key. Both options are explained step by step in [Choosing the model](../README.md#choosing-the-model). Delegation is done through tool calls and the manager has to plan and review, so small local models often loop or answer the tasks themselves; use at least a 7–8B model, and a hosted model such as `gpt-4o-mini` for reliable results.

**Web search:** get a free key at [serper.dev](https://serper.dev) and set `SERPER_API_KEY`. Without it the analysts rely on the model's own knowledge, which is fine to see delegation at work but gives outdated market figures.

## Run

```bash
python main.py --project "An AI assistant that answers phone calls and takes orders for small restaurants"

# another model for one run
python main.py --project "A marketplace for second-hand lab equipment" --model gpt-4o-mini

# without web search
python main.py --no-search
```

The console shows the manager's delegation calls (*Delegate work to coworker*) and each specialist's work. Each section and the final report are saved in `output/` (git-ignored).

## Ideas to extend it

- Add a fourth specialist (for example a *Technical Feasibility Analyst*) by adding it to `agents.yaml`, an `@agent` method and a task: the manager will start delegating to it with no other change.
- Add a guardrail to `final_report_task` that rejects the report if it lacks a clear go / no-go recommendation (see [`task_features`](../task_features/)).
- Run the same crew with `Process.sequential` (adding `agent:` to each task) and compare cost, time and quality.

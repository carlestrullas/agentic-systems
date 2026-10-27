# Task features

Options of `Task` and `Crew` that make a crew more **reliable** (guardrails, human review), **faster** (asynchronous tasks) and easier to **integrate and debug** (task outputs, callbacks). Each one is a single parameter, so they can be added to any of the previous examples.

## Examples

Short, focused scripts, one concept each:

| Script | Concept | Key parameters |
|---|---|---|
| [`01_guardrails.py`](01_guardrails.py) | A Python function validates the output; on failure its error message goes back to the agent, which retries. | `guardrail`, `guardrail_max_retries` |
| [`02_structured_guardrails.py`](02_structured_guardrails.py) | Guardrails on top of structured output: a code guardrail and an LLM-based guardrail (a plain string) chained. | `output_pydantic`, `guardrails=[...]` |
| [`03_task_outputs.py`](03_task_outputs.py) | Chaining tasks with `context` and inspecting each task's `TaskOutput` after the run. | `context`, `task.output` |
| [`04_async_tasks.py`](04_async_tasks.py) | Two independent research tasks run at the same time; the writer waits for both. | `async_execution` |
| [`05_callbacks.py`](05_callbacks.py) | Your own code runs when a task finishes: save a digest and log every task. | `callback`, `Crew(task_callback=...)` |
| [`06_human_input.py`](06_human_input.py) | A person reviews each answer in the terminal and can send it back with feedback. | `human_input` |

Two complete examples build on these ideas: [`project_research_hierarchical`](../project_research_hierarchical/) (a manager agent that delegates) and [`quality_inspector`](../quality_inspector/) (an agent that looks at images).

## Setup

```bash
cd crew_ai/task_features
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

**Model:** set `MODEL` in `.env` to a local Ollama model (the default, `ollama/llama3.1:8b`) or to a hosted model with its API key. Both options are explained step by step in [Choosing the model](../README.md#choosing-the-model). No script calls tools, but structured output and guardrails are much more reliable with 7–8B models than with 1–3B ones.

## Run

```bash
python 01_guardrails.py
python 01_guardrails.py --ask-words 250     # ask for more than the 150-word limit: watch the retries
python 02_structured_guardrails.py
python 02_structured_guardrails.py --no-llm-guardrail
python 03_task_outputs.py --topic "Small language models"
python 04_async_tasks.py
python 04_async_tasks.py --sync             # same crew without async, to compare
python 05_callbacks.py                      # writes output/news_digest.md and output/tasks.log
python 06_human_input.py                    # interactive: you review each answer
```

Every script accepts `--model` to use another model for one run. Generated files go to `output/` (git-ignored).

## Guardrails

A guardrail checks a task's output **before** it is passed on. It receives the `TaskOutput` and returns a tuple:

```python
def validate_summary_length(output: TaskOutput) -> tuple[bool, Any]:
    words = len(output.raw.split())
    if words > 150:
        return False, f"The summary has {words} words; rewrite it in at most 150."
    return True, output        # the second value replaces the output (a str or a TaskOutput)

Task(..., guardrail=validate_summary_length, guardrail_max_retries=3)
```

```
agent ──▶ output ──▶ guardrail ──(True, value)──▶ next task
            ▲            │
            └─ (False, error message) ◀── retried up to guardrail_max_retries times, then the task raises
```

- **The error message is a prompt.** The agent reads it to fix its answer, so say *what* to change ("rewrite it in at most 150 words"), not only that it is invalid.
- **Function or string.** A function gives deterministic, free checks (length, counts, formats, forbidden words). A string such as `"Every finding must be specific to this paper"` becomes an **LLM-based guardrail** that uses the agent's model to judge things code cannot.
- **Several in a row.** `guardrails=[check_report, "Every finding must be..."]` runs them in order; each must pass.
- **Shape vs. content.** With `output_pydantic`, CrewAI already parses and validates the fields, so a guardrail that re-checks the JSON keys adds nothing. Use guardrails for the rules the schema cannot express: how many items, how long, how specific.
- **Always keep a retry limit.** `guardrail_max_retries` (3 by default) stops a model that cannot meet the requirement from burning calls forever. It replaces the older `max_retries`, which is deprecated.

Good places for guardrails: length limits (posts, tweets in a thread, summaries), content rules for structured data, and checks before anything is published or sent.

## Task outputs and context

Every task stores its result in `task.output`, a `TaskOutput`:

| Field | Content |
|---|---|
| `raw` | The answer as text. |
| `pydantic` / `json_dict` | The structured answer, when the task uses `output_pydantic` / `output_json`. |
| `agent` | Role of the agent that produced it. |
| `description`, `summary` | The task description and its first words. |
| `output_format` | `raw`, `json` or `pydantic`. |

In a sequential crew each task receives the output of the previous one by default. `context=[task_a, task_b]` chooses exactly which outputs a task receives, so a final writer can combine several earlier results without regenerating them:

```python
blog_task = Task(..., context=[research_task, analysis_task])
...
crew.kickoff()
analysis_task.output.pydantic.key_takeaway   # any intermediate result, after the run
```

## Asynchronous tasks

```python
breakthroughs = Task(..., async_execution=True)
regulation    = Task(..., async_execution=True)
report        = Task(..., context=[breakthroughs, regulation])   # waits for both
```

```
sync:   breakthroughs ████████ regulation ████████ report ████
async:  breakthroughs ████████
        regulation    ████████ report ████
```

Use it for tasks that do not depend on each other. CrewAI enforces two rules: a crew can end with at most one async task, and an async task cannot use as context another async task from the same parallel block. To run whole crews in parallel instead of tasks, see the `async` flow steps in [`book_writing_flow`](../book_writing_flow/).

## Callbacks

```python
def save_news_digest(output: TaskOutput) -> None:
    Path("output/news_digest.md").write_text(output.raw)

Task(..., callback=save_news_digest)        # after this task
Crew(..., task_callback=log_task)           # after every task of the crew
```

Callbacks are plain Python that runs as soon as a task finishes: store results in a file or database, send a notification, start another process, collect metrics. They cannot change the output; that is what guardrails are for.

## Human in the loop

```python
Task(..., human_input=True)
```

After its final answer the agent stops and shows it in the terminal:

- **Type feedback and press Enter** → the agent revises the answer with it and asks again.
- **Press Enter on an empty line** → the answer is approved and the crew continues.

Any text, even "looks good", is treated as feedback and triggers another revision. Use human review where a mistake is expensive: anything published or sent to clients, financial or medical content, decisions that cannot be undone. For human review inside flows (approve/reject branches, asynchronous approvals) CrewAI also has `@human_feedback` for flow steps.

## Ideas to extend it

- Add a guardrail to [`content_planner_flow`](../content_planner_flow/) that rejects any tweet in a thread longer than 280 characters.
- Turn `05_callbacks.py` into a monitor: send the digest to Slack or by email instead of writing a file.
- Combine `async_execution` with the [`research_crew`](../research_crew/) to research two topics in parallel and compare them.

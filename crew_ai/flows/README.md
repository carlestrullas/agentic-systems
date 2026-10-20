# CrewAI Flows

Crews give agents autonomy; **Flows** give you control. A flow is an event-driven workflow written as a Python class: each step is a method, steps are connected with decorators, and all of them share a state. Some steps are ordinary deterministic code, others call an LLM or run a whole crew.

This balances the two worlds: the LLM handles what needs reasoning (understanding a ticket, writing text), while the order of the steps, the branching rules and the data that moves between them stay predictable and testable.

## Examples

Short, focused scripts, one concept each, and a final example that puts a crew inside a flow:

| Script | Concept | Needs an LLM? |
|---|---|---|
| [`01_basic_flow.py`](01_basic_flow.py) | `@start` and `@listen`: two chained LLM calls (random genre → movie recommendation) and intermediate values in `self.state`. | Yes |
| [`02_unstructured_state.py`](02_unstructured_state.py) | State as a free-form dict that steps read and update. | No |
| [`03_structured_state.py`](03_structured_state.py) | State as a Pydantic model with `Flow[TaskState]`, and the error you get when assigning an undeclared field. | No |
| [`04_or_and.py`](04_or_and.py) | `or_()` (run when any trigger finishes) and `and_()` (run when all have finished). | No |
| [`05_router.py`](05_router.py) | `@router()` to choose the next step at run time; the ticket priority can be decided by an LLM. | Optional |
| [`poem_flow/`](poem_flow/) | A complete flow project with the `crewai create flow` structure (`pyproject.toml`, `src/`, `crews/`, `tools/`) that orchestrates a `@CrewBase` crew. It has its own setup: see its [README](poem_flow/README.md). | Yes |

## Setup

```bash
cd crew_ai/flows
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

The LLM is chosen with `MODEL` in `.env`, as in the rest of the repo:

- **Ollama (no API key):** `ollama pull llama3.1:8b` and keep `MODEL=ollama/llama3.1:8b`. For these examples even a small model such as `llama3.2:3b` works, because no tool calling is involved.
- **API key:** set for example `MODEL=gpt-4o-mini` and `OPENAI_API_KEY=sk-...` (also `anthropic/…`, `gemini/…`, `groq/…` with their keys).

See [`technical_writer_agent`](../technical_writer_agent/README.md#setup) for the step-by-step setup of both options. Every script that uses an LLM also accepts `--model` to override it for one run.

## Run

```bash
python 01_basic_flow.py
python 02_unstructured_state.py
python 03_structured_state.py
python 03_structured_state.py --undeclared-field
python 04_or_and.py                     # or: --demo or | --demo and
python 05_router.py                     # random priority, no LLM
python 05_router.py --ticket "Our checkout page is down and customers cannot pay!"
```

`--plot` (in `01` and `05`) saves an interactive HTML diagram of the flow and opens it.

`poem_flow` is an installable project with its own `.env`: follow its [README](poem_flow/README.md) and run it from its folder with `crewai run`.

## The building blocks

### `@start` and `@listen`

```python
class MovieRecommendationFlow(Flow):
    @start()                                  # entry point; several @start methods run in parallel
    def generate_genre(self) -> str:
        return get_llm().call("Give me one random movie genre ...")

    @listen(generate_genre)                   # runs when generate_genre finishes
    def recommend_movie(self, genre: str) -> str:   # receives its return value
        return get_llm().call(f"Recommend one highly rated movie in the {genre} genre ...")

result = MovieRecommendationFlow().kickoff()  # returns the output of the last step
```

`get_llm()` (in [`llm.py`](llm.py)) builds the LLM from `MODEL` once and reuses it in every step; `llm.call(prompt)` is a single LLM call, no agent involved.

### State: unstructured or structured

Every flow has a `self.state` that all steps share, with a unique `id` per run.

| | Unstructured | Structured |
|---|---|---|
| Declaration | `class MyFlow(Flow)` | `class MyFlow(Flow[MyState])` with `MyState(BaseModel)` |
| Access | `self.state["status"]` | `self.state.status` |
| New fields at run time | Allowed (a typo creates a new key) | Error: `"... object has no field 'priority'"` |
| Best for | Prototypes and simple, dynamic state | Real workflows where types and names matter |

With a structured state, `kickoff(inputs={...})` fills the matching fields before the first step runs; this is how `05_router.py` receives the ticket text and `poem_flow` the topic.

### Conditional logic

| Tool | Runs the step when… | Example |
|---|---|---|
| `@listen(or_(a, b))` | **any** of `a` or `b` finishes | Log a request from whichever channel produced it |
| `@listen(and_(a, b))` | **all** of `a` and `b` have finished | Escalate only after the user confirms *and* an agent reviews |
| `@router(a)` + `@listen("label")` | the router method returns `"label"` | Send high-priority tickets to a live agent, the rest to email |

```python
@router(classify_ticket)
def route_ticket(self) -> str:
    return "urgent_support" if self.state.priority == "high" else "email_support"

@listen("urgent_support")
def assign_to_agent(self): ...

@listen("email_support")
def send_to_email_queue(self): ...
```

In `05_router.py` the router itself is deterministic, but the priority it reads can be set by an LLM: AI makes the judgement, plain code decides what happens with it.

### Crews inside flows

[`poem_flow/`](poem_flow/) has the same structure as a project generated with `crewai create flow`, adapted to this repo so it runs on any LLM instead of only OpenAI:

```
poem_flow/
├── pyproject.toml               # dependencies, entry points and [tool.crewai] type = "flow"
├── .env.example
├── README.md
├── tests/
└── src/poem_flow/
    ├── main.py                  # PoemFlow + PoemState and the kickoff / plot entry points
    ├── llm.py
    ├── crews/
    │   └── poem_crew/
    │       ├── poem_crew.py     # PoemCrew, a @CrewBase class
    │       └── config/
    │           ├── agents.yaml
    │           └── tasks.yaml
    └── tools/
        └── custom_tool.py       # place for the project's own tools
```

```python
class PoemState(BaseModel):
    topic: str = "learning something new"
    sentence_count: int = 1
    poem: str = ""

class PoemFlow(Flow[PoemState]):
    @start()
    def generate_sentence_count(self):              # plain Python
        self.state.sentence_count = random.randint(1, 5)

    @listen(generate_sentence_count)
    def generate_poem(self):                         # a crew does the AI work
        result = PoemCrew(llm=get_llm()).crew().kickoff(
            inputs={"topic": self.state.topic, "sentence_count": self.state.sentence_count}
        )
        self.state.poem = result.raw

    @listen(generate_poem)
    def save_poem(self):                             # plain Python
        OUTPUT_FILE.write_text(self.state.poem)
```

Each crew lives in its own folder with its own YAML, so adding a second crew (for example a reviewer that critiques the poem) means adding a folder under `crews/` and one more `@listen` step in the flow.

## Ideas to extend it

- Add a reviewer crew to `poem_flow` and a `@router` that sends the poem back for a rewrite if the review is negative.
- Combine [`research_crew`](../research_crew/) and [`technical_writer_agent`](../technical_writer_agent/) in one flow: research a topic, then write an article from the verified report.
- In `05_router.py`, replace the parsing of the LLM's one-word answer with structured output (a Pydantic model with `priority: Literal["high", "low"]` and a `reason`).

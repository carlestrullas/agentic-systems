# Content Planner Flow

A flow that turns a technical blog post into a **ready-to-publish social media plan**: a Twitter/X thread or a LinkedIn post, written in the author's own style and returned as validated JSON.

```
get_draft ──▶ select_platform ──"twitter"───▶ plan_twitter_thread ──┐
(Firecrawl     (@router)       └─"linkedin"──▶ plan_linkedin_post ───┴─ or_ ──▶ save_plan
 or a file)                                    (PlanningCrew)                   (JSON)
```

## How it works

| Step | Kind | What it does |
|---|---|---|
| `get_draft` | Python | With `--url`, scrapes the post with [Firecrawl](https://www.firecrawl.dev) and saves it as Markdown (images included) in `output/drafts/`. Otherwise uses a local file (by default [`assets/sample_draft.md`](assets/sample_draft.md)). |
| `select_platform` | `@router` | Returns `"twitter"` or `"linkedin"`, so only one branch runs. |
| `plan_twitter_thread` / `plan_linkedin_post` | Crew | Runs `PlanningCrew` for that platform and prints the plan. |
| `save_plan` | `@listen(or_(...))` | Runs after whichever branch finished and saves the plan to `output/<draft>_<platform>.json`. |

### The planning crew

[`PlanningCrew`](src/content_planner_flow/crews/planning_crew/planning_crew.py) defines three agents in YAML. Each run uses two of them:

| Agent | Used for | Task | Output |
|---|---|---|---|
| *Senior Technical Draft Analyst* | both | Reads the draft and extracts the core idea, the sections and the image URLs of each section. | Text (context for the planner) |
| *Senior Twitter Thread Planner* | `twitter` | Reads the example threads and writes a thread in that style. | `Thread` |
| *Senior LinkedIn Post Planner* | `linkedin` | Reads the example posts and writes a post in that style. | `LinkedInPost` |

The crew takes a `platform` argument, and its `@crew` method picks the analyzer plus that platform's planner, so one crew definition serves both platforms and the analyzer is not duplicated. All agents have `FileReadTool` and nothing else: it is the only tool they need.

### Structured output

The planners return Pydantic models ([`models.py`](src/content_planner_flow/models.py)), so the JSON always has the same shape:

```python
class Tweet(BaseModel):
    content: str            # at most 280 characters (the flow warns if a tweet is longer)
    is_hook: bool = False   # True for the first tweet
    media_urls: list[str]   # images from the draft that illustrate the tweet

class Thread(BaseModel):
    topic: str
    tweets: list[Tweet]

class LinkedInPost(BaseModel):
    content: str
    media_url: str = ""
```

### Writing style

The planners imitate the examples in [`assets/example_threads.txt`](assets/example_threads.txt) and [`assets/example_linkedin.txt`](assets/example_linkedin.txt). **Replace them with your own posts** to make the output sound like you.

## Project structure

```
content_planner_flow/
├── pyproject.toml                 # dependencies and entry points
├── .env.example
├── assets/
│   ├── sample_draft.md            # example blog post, used when no --url is given
│   ├── example_threads.txt        # writing-style examples for Twitter/X
│   └── example_linkedin.txt       # writing-style examples for LinkedIn
├── tests/
└── src/content_planner_flow/
    ├── main.py                    # ContentPlanningState, ContentPlanningFlow and entry points
    ├── models.py                  # Tweet, Thread, LinkedInPost
    ├── scraper.py                 # Firecrawl → Markdown
    ├── llm.py
    └── crews/
        └── planning_crew/
            ├── planning_crew.py
            └── config/
                ├── agents.yaml
                └── tasks.yaml
```

## Setup

From this folder (`crew_ai/content_planner_flow`):

```bash
cp .env.example .env
```

**Model:** set `MODEL` in `.env` to a local Ollama model (the default, `ollama/llama3.1:8b`) or to a hosted model with its API key. Both options are explained step by step in [Choosing the model](../README.md#choosing-the-model). The agents read files with a tool and return structured output, so with Ollama use a 7–8B model or larger.

**Scraping (optional):** only needed for `--url`. Firecrawl works without a key at low rate limits; a free key from [firecrawl.dev](https://www.firecrawl.dev) set as `FIRECRAWL_API_KEY` raises them.

Then install the project with the CrewAI CLI (`pip install crewai uv`, then `crewai install`) or with pip (`python -m venv .venv && source .venv/bin/activate`, then `pip install -e .`).

## Run

```bash
crewai run                                              # sample draft → Twitter thread
kickoff --platform linkedin                             # sample draft → LinkedIn post
kickoff --url https://example.com/my-post --platform twitter
kickoff --draft path/to/my_post.md --model gpt-4o-mini
plot                                                    # saves and opens content_planner_flow.html
run_with_trigger '{"url": "https://example.com/my-post", "platform": "linkedin"}'
```

With `crewai install`, run the other entry points through uv: `uv run kickoff --platform linkedin`.

The plan is printed to the console and saved to `output/` (git-ignored), together with any scraped drafts.

## Ideas to extend it

- Add a `"both"` option that runs the two planners in parallel and saves one JSON per platform.
- Add a reviewer agent that checks tone and length before saving, and a `@router` that sends the plan back for a rewrite.
- Publish the plan automatically through the platforms' APIs, after a human approves it.

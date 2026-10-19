# Entity Extractor

A crew that turns unstructured text into a **validated Pydantic object**: a list of `subject → relation → object` triplets, ready to load into a knowledge graph or a database.

```
"Marie Curie was born in Warsaw…" ──▶ Knowledge Graph Engineer ──▶ KnowledgeGraph(triplets=[…]) ──▶ output/triplets.json
```

```
subject      relation          object
----------------------------------------------------
Marie Curie  born_in           Warsaw
Marie Curie  married_to        Pierre Curie
Marie Curie  discovered        polonium
…
```

## Why structured output

By default an agent returns free text. Even if you ask for JSON, the answer often comes wrapped in ```` ```json ```` fences, with extra comments, or with slightly different keys from one run to the next, so it needs another parsing step before code can use it.

With **structured output** you define the shape of the answer as a Pydantic model and attach it to the task. CrewAI asks the model for that shape, validates the answer and returns a Python object:

```python
# models.py
class Triplet(BaseModel):
    subject: str = Field(..., description="The entity the fact is about, e.g. 'Marie Curie'.")
    relation: str = Field(..., description="A short verb phrase in snake_case, e.g. 'born_in'.")
    object: str = Field(..., description="The entity or value related to the subject.")

class KnowledgeGraph(BaseModel):
    triplets: list[Triplet] = Field(..., description="Every fact stated explicitly in the text.")

# extractor_crew.py
Task(config=self.tasks_config["extraction_task"], output_pydantic=KnowledgeGraph)

# main.py
graph = result.pydantic          # a KnowledgeGraph instance
graph.triplets[0].subject        # 'Marie Curie'
```

> **Tip:** always give every field a `description`. The model reads them and uses them as instructions, which matters more than the field names themselves.

`output_json=Model` is the alternative if you prefer a plain dictionary (`result.json_dict`) instead of a Pydantic object.

## Files

| File | Content |
|---|---|
| [`models.py`](models.py) | The Pydantic schema (`Triplet`, `KnowledgeGraph`). |
| [`extractor_crew.py`](extractor_crew.py) | `ExtractorCrew`, a `@CrewBase` class with one agent and one task that uses `output_pydantic`. |
| [`config/`](config/) | Agent and task prompts in YAML. |
| [`main.py`](main.py) | Command-line entry point; prints a table and saves the JSON. |

## Setup

```bash
cd crew_ai/entity_extractor
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Choose the model in `.env`, exactly as in the other examples:

- **Ollama (no API key):** `ollama pull llama3.1:8b` and keep `MODEL=ollama/llama3.1:8b`. Small models (1–3B) often return fewer or malformed triplets; 7–8B models or larger work much better.
- **API key:** set for example `MODEL=gpt-4o-mini` and `OPENAI_API_KEY=sk-...` (also `anthropic/…`, `gemini/…`, `groq/…` with their keys).

See [`technical_writer_agent`](../technical_writer_agent/README.md#setup) for the step-by-step setup of both options.

## Run

```bash
# sample text about Marie Curie
python main.py

# your own text
python main.py --text "Ada Lovelace worked with Charles Babbage on the Analytical Engine."
python main.py --file notes.txt --model gpt-4o-mini
```

The triplets are printed as a table and saved to `output/triplets.json` (git-ignored).

## Ideas to extend it

- Add entity types (`person`, `place`, `organisation`…) to the schema with a `Literal` field.
- Load the triplets into NetworkX or Neo4j and draw the graph.
- Chain it after the [`research_crew`](../research_crew/) to build a knowledge graph of a topic.

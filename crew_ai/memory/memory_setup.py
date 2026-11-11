"""
Memory shared by the scripts in this example: embedder, storage and helpers.

CrewAI memory is one `Memory` object that needs three things besides the
agents' LLM:

* An **LLM for analysis**. When something is saved, this LLM splits it into
  short facts and gives each one a scope, categories and an importance. When
  something is recalled with depth="deep", it turns the query into targeted
  searches. Here it is the same model as the agents (MODEL in .env).
* An **embedder**, the model that turns text into vectors for the similarity
  search. CrewAI uses OpenAI unless told otherwise, so it is chosen with the
  EMBEDDER variable in .env, like MODEL chooses the LLM:

      ollama/nomic-embed-text           local, free (default)
      openai/text-embedding-3-small     needs OPENAI_API_KEY
      gemini/gemini-embedding-001       needs GEMINI_API_KEY

* A **storage** folder where the records live (a LanceDB database). It
  persists between runs. Every script and embedder gets its own folder under
  output/memory/, so the scripts do not read each other's memories, and you
  can open or delete them yourself. Vectors from different embedders have
  different sizes and cannot share a folder.
"""

import os
import re
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")

from crewai.memory import Memory, MemoryMatch, MemoryRecord  # noqa: E402

from llm import check_ollama, is_set  # noqa: E402

DEFAULT_EMBEDDER = "ollama/nomic-embed-text"
EMBEDDER = os.getenv("EMBEDDER") or DEFAULT_EMBEDDER

# EMBEDDER prefix -> (CrewAI provider name, API key variable)
PROVIDERS = {
    "ollama": ("ollama", None),
    "openai": ("openai", "OPENAI_API_KEY"),
    "gemini": ("google-generativeai", "GEMINI_API_KEY"),
}


def build_embedder(name: str | None = None) -> dict:
    """Return the embedder spec to pass as `embedder=` to a Memory."""
    name = name or EMBEDDER
    prefix, _, model = name.partition("/")
    if prefix not in PROVIDERS or not model:
        raise SystemExit(
            f"EMBEDDER '{name}' is not supported. Use one of: ollama/<model>, openai/<model>, gemini/<model>."
        )

    provider, key_var = PROVIDERS[prefix]

    if prefix == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        check_ollama(name, base_url)  # fails early if Ollama is down or the model is not pulled
        print(f"🔢 Embeddings: {model} (Ollama, local)")
        return {"provider": provider, "config": {"model_name": model, "url": base_url}}

    if key_var and not is_set(key_var):
        raise SystemExit(
            f"EMBEDDER is '{name}' but {key_var} is not set. Add the key to .env or use a local "
            f"embedder, e.g. EMBEDDER={DEFAULT_EMBEDDER}."
        )
    print(f"🔢 Embeddings: {model} ({prefix})")
    return {"provider": provider, "config": {"model_name": model}}


def storage_path(name: str | None = None) -> Path:
    """Folder of a script's memory, e.g. output/memory/02-across-sessions-ollama-nomic-embed-text."""
    script = name or Path(sys.argv[0]).stem or "interactive"
    slug = re.sub(r"[^a-z0-9]+", "-", f"{script}-{EMBEDDER}".lower()).strip("-")
    return HERE / "output" / "memory" / slug


def build_memory(llm, name: str | None = None, **settings) -> Memory:
    """Create the Memory for a script: analysis LLM, embedder and its own storage folder.

    `settings` are passed to Memory, e.g. recency_weight=0.5 (see 04_recall_tuning.py).
    """
    path = storage_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    return Memory(llm=llm, embedder=build_embedder(), storage=str(path), **settings)


def reset_store(name: str | None = None) -> None:
    """Delete a script's memory folder, so the next run starts with an empty memory."""
    path = storage_path(name)
    if path.exists():
        shutil.rmtree(path)
        print(f"🧹 Memory deleted: {path.relative_to(HERE)}")


def show_records(records: list[MemoryRecord], title: str = "Stored memories") -> None:
    """Print records the way they are stored: scope, categories, importance and text."""
    print(f"\n📒 {title} ({len(records)})")
    for r in records:
        categories = ", ".join(r.categories) or "-"
        print(f"  [{r.scope}] importance={r.importance:.2f} categories={categories}")
        print(f"      {r.content}")


def show_matches(matches: list[MemoryMatch], query: str) -> None:
    """Print recall results with their composite score and why they matched."""
    print(f"\n🔎 recall({query!r}) → {len(matches)} matches")
    for m in matches:
        reasons = ", ".join(m.match_reasons) or "-"
        print(f"  {m.score:.2f}  {m.record.content}   ({reasons})")

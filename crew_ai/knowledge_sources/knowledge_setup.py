"""
Embedder and knowledge storage shared by the scripts in this example.

Knowledge needs two things besides the LLM:

* An **embedder**, the model that turns text into vectors. CrewAI uses
  OpenAI's `text-embedding-3-small` unless told otherwise, which would make
  every script need an OpenAI key. Here it is chosen with the EMBEDDER
  variable in .env, like MODEL chooses the LLM:

      ollama/nomic-embed-text           local, free (default)
      openai/text-embedding-3-small     needs OPENAI_API_KEY
      gemini/gemini-embedding-001       needs GEMINI_API_KEY

* A **vector store** where the embedded chunks are saved (ChromaDB). CrewAI
  keeps it in your user data folder and reuses it between runs, so this module
  gives every script and embedder its own store. Otherwise chunks from other
  scripts would be mixed into the answers, and switching embedder would fail
  with "Embedding dimension mismatch".

IMPORTANT: import this module BEFORE anything from crewai. CrewAI reads the
storage location (CREWAI_STORAGE_DIR) once, when it is imported.
"""

import os
import re
import shutil
import sys
from pathlib import Path

import appdirs
from dotenv import load_dotenv

HERE = Path(__file__).parent
KNOWLEDGE_DIR = HERE / "knowledge"  # where the example files live

load_dotenv(HERE / ".env")

DEFAULT_EMBEDDER = "ollama/nomic-embed-text"
EMBEDDER = os.getenv("EMBEDDER") or DEFAULT_EMBEDDER

# One store per example, script and embedder, e.g.
# "agentic-systems-knowledge-sources-01-string-knowledge-ollama-nomic-embed-text"
_script = Path(sys.argv[0]).stem or "interactive"
_name = re.sub(r"[^a-z0-9]+", "-", f"agentic-systems-{HERE.name}-{_script}-{EMBEDDER}".lower()).strip("-")
_OWN_STORAGE = "CREWAI_STORAGE_DIR" not in os.environ  # never touch a location you chose yourself
os.environ.setdefault("CREWAI_STORAGE_DIR", _name)

# EMBEDDER prefix -> (CrewAI provider name, API key variable)
PROVIDERS = {
    "ollama": ("ollama", None),
    "openai": ("openai", "OPENAI_API_KEY"),
    "gemini": ("google-generativeai", "GEMINI_API_KEY"),
}


def build_embedder(name: str | None = None) -> dict:
    """Return the embedder spec to pass as `embedder=` to a Crew or an Agent."""
    from llm import check_ollama, is_set  # imported here so crewai loads after the storage is set

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


def storage_path() -> Path:
    """Folder of this script's vector store (same rule CrewAI uses)."""
    return Path(appdirs.user_data_dir(os.environ["CREWAI_STORAGE_DIR"], "CrewAI"))


def reset_knowledge() -> None:
    """Delete this script's vector store, so the sources are embedded again from scratch.

    Needed after editing a source: chunks are stored by content, so the old
    version of an edited file would otherwise stay in the store.
    """
    path = storage_path()
    if not _OWN_STORAGE:
        print(f"⚠️  CREWAI_STORAGE_DIR was set by you; not deleting {path}.")
    elif path.exists():
        shutil.rmtree(path)
        print(f"🧹 Knowledge store deleted: {path}")

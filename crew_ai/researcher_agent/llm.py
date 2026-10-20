"""
LLM selection shared by the scripts in this example.

The model is chosen with the MODEL variable (in .env or via --model):

* ``ollama/<model>``      -> local model served by Ollama, no API key needed
* ``gpt-4o-mini``         -> OpenAI (needs OPENAI_API_KEY)
* ``anthropic/<model>``   -> Anthropic (needs ANTHROPIC_API_KEY)
* ``gemini/<model>``      -> Google Gemini (needs GEMINI_API_KEY)
* ``groq/<model>``        -> Groq (needs GROQ_API_KEY)

`build_llm()` creates a new LLM (and checks Ollama or the API key first);
`get_llm()` builds it once and reuses it, which is handy in flows where several
steps need the model.

This file is identical in every example of the repository: when you change it,
copy it to all of them.
"""

import json
import os
import urllib.error
import urllib.request
from functools import lru_cache

from crewai import LLM

PLACEHOLDER = "REPLACE_ME"
DEFAULT_MODEL = "ollama/llama3.1:8b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"

PROVIDER_KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}


def is_set(var: str) -> bool:
    value = os.getenv(var, "").strip()
    return bool(value) and value != PLACEHOLDER


def provider_of(model: str) -> str:
    """'anthropic/claude-x' -> 'anthropic'; a bare name such as 'gpt-4o-mini' is OpenAI."""
    return model.split("/", 1)[0].lower() if "/" in model else "openai"


def check_ollama(model: str, base_url: str) -> None:
    """Fail early with a clear message if Ollama is not running or the model is not pulled."""
    name = model.split("/", 1)[1]
    if ":" not in name:
        name += ":latest"

    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=5) as response:
            available = {m["name"] for m in json.load(response).get("models", [])}
    except (urllib.error.URLError, OSError):
        raise SystemExit(
            f"Could not reach Ollama at {base_url}. Start it with `ollama serve` "
            "(or open the Ollama app) and try again."
        )

    if name not in available:
        raise SystemExit(
            f"The model '{name}' is not available in Ollama. Download it with:\n\n"
            f"    ollama pull {name}\n"
        )


def build_llm(model: str | None = None, temperature: float = 0.3) -> LLM:
    model = model or os.getenv("MODEL") or DEFAULT_MODEL
    provider = provider_of(model)

    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL).rstrip("/")
        check_ollama(model, base_url)
        print(f"🦙 Using local model {model} (Ollama at {base_url})\n")
        return LLM(model=model, base_url=base_url, temperature=temperature)

    key_var = PROVIDER_KEYS.get(provider)
    if key_var and not is_set(key_var):
        raise SystemExit(
            f"MODEL is '{model}' but {key_var} is not set. Add your key to .env "
            f"(replacing '{PLACEHOLDER}') or switch to a local model, e.g. MODEL=ollama/llama3.1:8b."
        )

    print(f"☁️  Using hosted model {model}\n")
    return LLM(model=model, temperature=temperature)


@lru_cache(maxsize=None)
def get_llm() -> LLM:
    """Build the LLM once (from MODEL in the environment) and reuse it afterwards."""
    return build_llm()

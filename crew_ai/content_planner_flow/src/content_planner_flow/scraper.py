"""
Scrape a web page to Markdown with Firecrawl.

This is a deterministic step of the flow, so it is plain Python rather than an
agent tool. It calls the Firecrawl REST API directly (no SDK needed). An API key
is optional: Firecrawl works without one at low rate limits, and
FIRECRAWL_API_KEY raises them.
"""

import os
import re
import uuid
from pathlib import Path

import requests

FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v2/scrape"


def _slugify(text: str, max_length: int = 80) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_length].rstrip("-") or str(uuid.uuid4())


def scrape_to_markdown(url: str, out_dir: Path) -> Path:
    """Scrape `url`, save its Markdown (images included) to `out_dir` and return the file path."""
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    if api_key and api_key != "REPLACE_ME":
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.post(
            FIRECRAWL_SCRAPE_URL,
            json={"url": url, "formats": ["markdown"]},
            headers=headers,
            timeout=90,
        )
        data = response.json()
    except (requests.RequestException, ValueError) as error:
        raise SystemExit(f"Could not reach Firecrawl to scrape {url}: {error}")

    if response.status_code != 200 or not data.get("success"):
        raise SystemExit(f"Firecrawl could not scrape {url}: {data.get('error', response.status_code)}")

    page = data["data"]
    title = (page.get("metadata") or {}).get("title") or url

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{_slugify(title)}.md"
    path.write_text(page["markdown"], encoding="utf-8")
    return path

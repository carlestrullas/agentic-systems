#!/usr/bin/env python
"""
PoemFlow: a flow that orchestrates a crew.

    generate_sentence_count ──▶ generate_poem ──▶ save_poem
      plain Python (random)      PoemCrew (LLM)     plain Python (file)

Deterministic steps are ordinary Python; the creative step is delegated to a
crew. All steps share a structured, Pydantic-validated state.

The functions at the bottom are the project's entry points (see
[project.scripts] in pyproject.toml):

    crewai run                         # same as: kickoff
    kickoff --topic "Monday mornings" --model gpt-4o-mini
    plot                               # interactive HTML diagram of the flow
    run_with_trigger '{"topic": "the sea"}'
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path

from crewai.flow.flow import Flow, listen, start
from dotenv import load_dotenv
from pydantic import BaseModel

from poem_flow.crews.poem_crew.poem_crew import PoemCrew
from poem_flow.llm import get_llm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_FILE = PROJECT_ROOT / "output" / "poem.txt"

load_dotenv(PROJECT_ROOT / ".env")


class PoemState(BaseModel):
    topic: str = "learning something new"
    sentence_count: int = 1
    poem: str = ""


class PoemFlow(Flow[PoemState]):
    @start()
    def generate_sentence_count(self) -> None:
        # A deterministic step: no LLM involved.
        self.state.sentence_count = random.randint(1, 5)
        print(f"📏 The poem about {self.state.topic!r} will have {self.state.sentence_count} sentence(s).\n")

    @listen(generate_sentence_count)
    def generate_poem(self) -> None:
        # An AI step: delegate the creative work to a crew.
        result = (
            PoemCrew(llm=get_llm())
            .crew()
            .kickoff(inputs={"topic": self.state.topic, "sentence_count": self.state.sentence_count})
        )
        self.state.poem = result.raw.strip()

    @listen(generate_poem)
    def save_poem(self) -> str:
        OUTPUT_FILE.parent.mkdir(exist_ok=True)
        OUTPUT_FILE.write_text(self.state.poem + "\n", encoding="utf-8")
        print(f"\n✅ Poem saved to {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")
        return self.state.poem


def _run(topic: str | None = None) -> str:
    # inputs fill the matching fields of PoemState before the first step runs.
    poem = PoemFlow().kickoff(inputs={"topic": topic} if topic else None)
    print("\n" + "=" * 60)
    print(poem)
    print("=" * 60)
    return poem


def kickoff() -> None:
    """Run the flow. Used by `crewai run` and by the `kickoff` script."""
    parser = argparse.ArgumentParser(description="Run a flow that uses a crew to write a poem.")
    parser.add_argument("--topic", help="What the poem is about")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args, _ = parser.parse_known_args()
    if args.model:
        os.environ["MODEL"] = args.model
    _run(args.topic)


def plot() -> None:
    """Save (and open) an interactive HTML diagram of the flow."""
    PoemFlow().plot("poem_flow.html")


def run_with_trigger() -> str:
    """Run the flow from a JSON payload, e.g. run_with_trigger '{"topic": "the sea"}'."""
    if len(sys.argv) < 2:
        raise SystemExit("No trigger payload provided. Pass a JSON object as argument.")
    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise SystemExit("Invalid JSON payload provided as argument.")
    return _run(payload.get("topic"))


if __name__ == "__main__":
    kickoff()

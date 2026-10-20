"""
PoemFlow: a flow that orchestrates a crew.

    generate_sentence_count ──▶ generate_poem ──▶ save_poem
      plain Python (random)      PoemCrew (LLM)     plain Python (file)

This is the main pattern of Flows: deterministic steps written in ordinary
Python and AI steps run by crews, connected by @start/@listen and sharing a
structured, Pydantic-validated state.

Run it from the `flows/` folder as a module:

    python -m poem_flow.main
    python -m poem_flow.main --topic "Monday mornings" --model gpt-4o-mini
"""

import argparse
import os
import random
from pathlib import Path

from crewai.flow.flow import Flow, listen, start
from dotenv import load_dotenv
from pydantic import BaseModel

from llm import get_llm
from poem_flow.crews.poem_crew.poem_crew import PoemCrew

FLOWS_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = FLOWS_DIR / "output" / "poem.txt"


class PoemState(BaseModel):
    topic: str = "learning something new"
    sentence_count: int = 1
    poem: str = ""


class PoemFlow(Flow[PoemState]):
    @start()
    def generate_sentence_count(self) -> None:
        # A deterministic step: no LLM involved.
        self.state.sentence_count = random.randint(1, 5)
        print(f"📏 The poem will have {self.state.sentence_count} sentence(s).\n")

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
        return self.state.poem


def main() -> None:
    load_dotenv(FLOWS_DIR / ".env")

    parser = argparse.ArgumentParser(description="Run a flow that uses a crew to write a poem.")
    parser.add_argument("--topic", default=PoemState().topic, help="What the poem is about")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    parser.add_argument("--plot", action="store_true", help="Save (and open) an interactive HTML diagram of the flow")
    args = parser.parse_args()
    if args.model:
        os.environ["MODEL"] = args.model

    flow = PoemFlow()
    if args.plot:
        flow.plot("poem_flow.html")

    # inputs fill the matching fields of PoemState before the first step runs.
    poem = flow.kickoff(inputs={"topic": args.topic})

    print("\n" + "=" * 60)
    print(poem)
    print("=" * 60)
    print(f"\n✅ Poem saved to {OUTPUT_FILE.relative_to(FLOWS_DIR)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
BookFlow: a multi-crew flow that writes a whole book about a topic.

    generate_outline ──▶ generate_chapters ──────────────▶ save_book
      OutlineCrew          ChapterWriterCrew × N              Markdown
      (1 run)              (N runs in parallel)               (Python)

1. OutlineCrew researches the topic and returns an `Outline` (chapter titles).
2. One ChapterWriterCrew per chapter runs concurrently; each gets the full
   outline so it knows what the other chapters cover.
3. The chapters are joined, in order, into `output/book.md`.

Entry points (see [project.scripts] in pyproject.toml):

    crewai run                         # same as: kickoff
    kickoff --topic "Quantum computing" --max-chapters 4 --model gpt-4o-mini
    plot
    run_with_trigger '{"topic": "Quantum computing", "max_chapters": 4}'
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from crewai.flow.flow import Flow, listen, start
from dotenv import load_dotenv
from pydantic import BaseModel

from book_writing_flow.crews.chapter_writer_crew.chapter_writer_crew import ChapterWriterCrew
from book_writing_flow.crews.outline_crew.outline_crew import OutlineCrew
from book_writing_flow.llm import get_llm
from book_writing_flow.models import Chapter
from book_writing_flow.tools import search_enabled

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_FILE = PROJECT_ROOT / "output" / "book.md"

load_dotenv(PROJECT_ROOT / ".env")


class BookState(BaseModel):
    topic: str = "Astronomy in the 2020s"
    max_chapters: int = 6
    titles: list[str] = []
    chapters: list[Chapter] = []


class BookFlow(Flow[BookState]):
    @start()
    def generate_outline(self) -> None:
        if not search_enabled():
            print("⚠️  SERPER_API_KEY not set: the researchers will NOT search the web.\n")

        print(f"📚 Generating the outline of a book about {self.state.topic!r}...")
        result = (
            OutlineCrew(llm=get_llm())
            .crew()
            .kickoff(inputs={"topic": self.state.topic, "max_chapters": self.state.max_chapters})
        )
        if result.pydantic is None:
            raise SystemExit(f"The outline crew did not return a valid outline:\n{result.raw}")

        # Use the titles themselves (not total_chapters) so the two can never disagree.
        self.state.titles = result.pydantic.titles[: self.state.max_chapters]
        print("\nOutline:\n" + "\n".join(f"  {i}. {t}" for i, t in enumerate(self.state.titles, 1)))

    @listen(generate_outline)
    async def generate_chapters(self) -> None:
        print(f"\n✍️  Writing {len(self.state.titles)} chapters in parallel...\n")
        outline = "\n".join(f"{i}. {t}" for i, t in enumerate(self.state.titles, 1))

        async def write_chapter(number: int, title: str) -> Chapter:
            crew = ChapterWriterCrew(llm=get_llm()).crew()
            # crew.kickoff() is blocking, so it runs in a worker thread; this is what
            # lets the chapters really be written at the same time.
            result = await asyncio.to_thread(
                crew.kickoff,
                inputs={"title": title, "topic": self.state.topic, "chapters": outline},
            )
            print(f"✅ Chapter {number} written: {title}")
            chapter = result.pydantic
            return chapter if isinstance(chapter, Chapter) else Chapter(title=title, content=result.raw)

        # gather() keeps the chapters in outline order, whatever order they finish in.
        self.state.chapters = list(
            await asyncio.gather(*(write_chapter(i, t) for i, t in enumerate(self.state.titles, 1)))
        )

    @listen(generate_chapters)
    def save_book(self) -> str:
        contents = "\n".join(f"{i}. {c.title}" for i, c in enumerate(self.state.chapters, 1))
        parts = [f"# {self.state.topic}", "## Contents", contents]
        for i, chapter in enumerate(self.state.chapters, 1):
            parts += [f"## {i}. {chapter.title}", chapter.content.strip()]

        OUTPUT_FILE.parent.mkdir(exist_ok=True)
        OUTPUT_FILE.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
        print(f"\n✅ Book saved to {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")
        return str(OUTPUT_FILE)


def _run(topic: str | None = None, max_chapters: int | None = None) -> str:
    inputs: dict = {}
    if topic:
        inputs["topic"] = topic
    if max_chapters:
        inputs["max_chapters"] = max_chapters
    return BookFlow().kickoff(inputs=inputs or None)


def kickoff() -> None:
    """Run the flow. Used by `crewai run` and by the `kickoff` script."""
    parser = argparse.ArgumentParser(description="Write a book about a topic with a multi-crew flow.")
    parser.add_argument("--topic", help="What the book is about")
    parser.add_argument("--max-chapters", type=int, help="Upper limit for the number of chapters (default 6)")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args, _ = parser.parse_known_args()
    if args.model:
        os.environ["MODEL"] = args.model
    if args.max_chapters is not None and args.max_chapters < 3:
        raise SystemExit("--max-chapters must be at least 3.")
    _run(args.topic, args.max_chapters)


def plot() -> None:
    """Save (and open) an interactive HTML diagram of the flow."""
    BookFlow().plot("book_writing_flow.html")


def run_with_trigger() -> str:
    """Run the flow from a JSON payload with "topic" and, optionally, "max_chapters"."""
    if len(sys.argv) < 2:
        raise SystemExit("No trigger payload provided. Pass a JSON object as argument.")
    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise SystemExit("Invalid JSON payload provided as argument.")
    return _run(payload.get("topic"), payload.get("max_chapters"))


if __name__ == "__main__":
    kickoff()

"""
Technical writer agent built with CrewAI.

A single agent with no tools writes a publication-ready Markdown article on a
topic and saves it to `output/article.md`.

Usage:
    python writer.py --topic "Retrieval-augmented generation"
    python writer.py --topic "Vector databases" --model gpt-4o-mini
"""

import argparse
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv

from llm import build_llm

HERE = Path(__file__).parent
OUTPUT_FILE = HERE / "output" / "article.md"


def build_crew(llm) -> Crew:
    writer = Agent(
        role="Senior Technical Writer",
        goal="Write clear, accurate and engaging technical articles about {topic}",
        backstory=(
            "You are an experienced technical writer who has spent years explaining "
            "machine learning and software engineering to practitioners. You turn "
            "complex ideas into well-structured articles with concrete examples, "
            "and you never pad the text or overstate what a technique can do."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )

    writing_task = Task(
        description=(
            "Write an article about {topic} for data scientists and ML engineers.\n\n"
            "1. Explain what it is and the problem it solves.\n"
            "2. Describe how it works, step by step.\n"
            "3. Give at least one concrete example or use case.\n"
            "4. Discuss limitations, trade-offs and when not to use it."
        ),
        expected_output=(
            "A Markdown article of 600–900 words with a title (#), a short introduction, "
            "3–5 sections with ## headings, and a conclusion with the key takeaways."
        ),
        agent=writer,
        output_file=str(OUTPUT_FILE),
        markdown=True,
    )

    return Crew(agents=[writer], tasks=[writing_task], process=Process.sequential, verbose=True)


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Run the CrewAI technical writer agent.")
    parser.add_argument("--topic", default="AI agents", help="Topic of the article")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    llm = build_llm(args.model, temperature=0.5)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    result = build_crew(llm).kickoff(inputs={"topic": args.topic})

    print("\n" + "=" * 60)
    print(result.raw)
    print("=" * 60)
    print(f"\n✅ Article saved to {OUTPUT_FILE.relative_to(HERE)}")
    print("   Summarise it with: python summarizer.py")


if __name__ == "__main__":
    main()

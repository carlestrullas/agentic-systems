"""
File summarizer agent built with CrewAI.

A single agent uses `FileReadTool` to read a document from disk and writes a
structured summary to `output/summary.md`. By default it summarises the article
produced by `writer.py`, but it works with any text or Markdown file.

Usage:
    python summarizer.py
    python summarizer.py --file path/to/any_document.md
"""

import argparse
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai_tools import FileReadTool
from dotenv import load_dotenv

from llm import build_llm

HERE = Path(__file__).parent
DEFAULT_INPUT = HERE / "output" / "article.md"
OUTPUT_FILE = HERE / "output" / "summary.md"


def build_crew(llm, file_path: Path) -> Crew:
    # Binding the tool to one file means the agent can only read that document.
    file_reader = FileReadTool(file_path=str(file_path))

    analyst = Agent(
        role="Senior Document Analyst",
        goal="Read documents carefully and extract their key ideas in a concise, faithful summary",
        backstory=(
            "You are an analyst who reads long technical documents and briefs busy "
            "colleagues. You only report what the document actually says, keep the "
            "author's terminology, and flag anything that is unclear or unsupported."
        ),
        tools=[file_reader],
        llm=llm,
        allow_delegation=False,
        max_iter=5,
        verbose=True,
    )

    summary_task = Task(
        description=(
            "Use the file reading tool to read the document at '{file_path}'. "
            "Then summarise it: identify its main argument, the key points that "
            "support it, and any practical takeaways."
        ),
        expected_output=(
            "A Markdown summary with:\n"
            "## TL;DR (2 sentences)\n"
            "## Key points (4–6 bullet points)\n"
            "## Takeaways (2–3 bullet points)"
        ),
        agent=analyst,
        output_file=str(OUTPUT_FILE),
        markdown=True,
    )

    return Crew(agents=[analyst], tasks=[summary_task], process=Process.sequential, verbose=True)


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Run the CrewAI file summarizer agent.")
    parser.add_argument("--file", type=Path, default=DEFAULT_INPUT, help="Document to summarise")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    file_path = args.file.resolve()
    if not file_path.is_file():
        raise SystemExit(
            f"File not found: {file_path}\n"
            "Generate an article first with `python writer.py --topic \"...\"` or pass --file."
        )

    llm = build_llm(args.model, temperature=0.2)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    result = build_crew(llm, file_path).kickoff(inputs={"file_path": str(file_path)})

    print("\n" + "=" * 60)
    print(result.raw)
    print("=" * 60)
    print(f"\n✅ Summary saved to {OUTPUT_FILE.relative_to(HERE)}")


if __name__ == "__main__":
    main()

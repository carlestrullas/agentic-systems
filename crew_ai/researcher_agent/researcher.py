"""
Researcher agent built with CrewAI.

A single agent receives a topic, searches the web for recent and reliable
information, and writes a structured Markdown report to `output/report.md`.

The LLM is chosen with the MODEL variable in .env (or --model): a local model
served by Ollama (e.g. ollama/llama3.1:8b) or a hosted one with an API key.

Usage:
    python researcher.py --topic "Small language models"
    python researcher.py --topic "Small language models" --model gpt-4o-mini
"""

import argparse
from datetime import date
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv

from llm import build_llm, is_set

HERE = Path(__file__).parent
OUTPUT_FILE = HERE / "output" / "report.md"


def build_tools() -> list:
    """Web search is optional: without a Serper key the agent relies on the model's own knowledge."""
    if not is_set("SERPER_API_KEY"):
        print("⚠️  SERPER_API_KEY not set: running without web search.\n")
        return []

    from crewai_tools import SerperDevTool

    return [SerperDevTool(n_results=8)]


def build_crew(topic: str, llm) -> Crew:
    researcher = Agent(
        role="Senior Research Analyst",
        goal=f"Find, verify and synthesise the most relevant and up-to-date information about {topic}",
        backstory=(
            "You are a meticulous analyst with years of experience turning scattered "
            "sources into clear, reliable briefings. You prefer primary sources, "
            "cross-check important claims, and always say where a fact comes from. "
            "When the evidence is weak or contradictory, you say so explicitly."
        ),
        tools=build_tools(),
        llm=llm,
        allow_delegation=False,
        max_iter=10,
        verbose=True,
    )

    research_task = Task(
        description=(
            f"Research the topic: '{topic}'. Today's date is {date.today():%B %d, %Y}.\n\n"
            "1. Identify what the topic is and why it matters right now.\n"
            "2. Find the most important recent developments, key players and open debates.\n"
            "3. Cross-check the most important claims across more than one source.\n"
            "4. Note any limitations, risks or points of disagreement."
        ),
        expected_output=(
            "A Markdown report with these sections:\n"
            "## Summary (3–4 sentences)\n"
            "## Key findings (5–8 bullet points, each with its source)\n"
            "## Main players\n"
            "## Open questions and risks\n"
            "## Sources (list of links)"
        ),
        agent=researcher,
        output_file=str(OUTPUT_FILE),
        markdown=True,
    )

    return Crew(
        agents=[researcher],
        tasks=[research_task],
        process=Process.sequential,
        verbose=True,
    )


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Run the CrewAI researcher agent.")
    parser.add_argument("--topic", default="AI agents in production", help="Topic to research")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    llm = build_llm(args.model, temperature=0.2)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    result = build_crew(args.topic, llm).kickoff()

    print("\n" + "=" * 60)
    print(result.raw)
    print("=" * 60)
    print(f"\n✅ Report saved to {OUTPUT_FILE.relative_to(HERE)}")


if __name__ == "__main__":
    main()

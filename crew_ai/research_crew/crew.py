"""
Multi-agent research crew built with CrewAI.

Three specialised agents work sequentially on a topic:

    Research Specialist ──▶ Content Summarizer ──▶ Fact-Checking Specialist
    (web search)            (structure)             (web search, verify)

Agents and tasks are defined in YAML files under `config/`, so prompts can be
tuned without touching the Python code.

Usage:
    python crew.py --topic "Small language models"
    python crew.py --topic "Agentic RAG" --model anthropic/claude-sonnet-4-5
"""

import argparse
from datetime import date
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv

from llm import build_llm, is_set

HERE = Path(__file__).parent
CONFIG_DIR = HERE / "config"
OUTPUT_DIR = HERE / "output"


def load_config(name: str) -> dict:
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_search_tools() -> list:
    """Web search through Serper. Without a key the agents work from the model's own knowledge."""
    if not is_set("SERPER_API_KEY"):
        print(
            "⚠️  SERPER_API_KEY not set: running WITHOUT web search. The researcher and the "
            "fact-checker will rely on the model's own (possibly outdated) knowledge.\n"
        )
        return []

    from crewai_tools import SerperDevTool

    return [SerperDevTool(n_results=8)]


def build_crew(llm) -> Crew:
    agents_cfg = load_config("agents.yaml")
    tasks_cfg = load_config("tasks.yaml")
    search_tools = build_search_tools()

    def make_agent(key: str, tools: list) -> Agent:
        cfg = agents_cfg[key]
        return Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            tools=tools,
            llm=llm,
            allow_delegation=False,
            max_iter=10,
            verbose=True,
        )

    # Only the agents that need to search get the search tool.
    agents = {
        "researcher": make_agent("researcher", search_tools),
        "summarizer": make_agent("summarizer", []),
        "fact_checker": make_agent("fact_checker", search_tools),
    }

    def make_task(key: str, output_file: str, context: list | None = None) -> Task:
        cfg = tasks_cfg[key]
        return Task(
            description=cfg["description"],
            expected_output=cfg["expected_output"],
            agent=agents[cfg["agent"]],
            context=context,
            output_file=str(OUTPUT_DIR / output_file),
            markdown=True,
        )

    research = make_task("research_task", "1_research_notes.md")
    summary = make_task("summary_task", "2_summary.md", context=[research])
    fact_check = make_task("fact_check_task", "3_final_report.md", context=[research, summary])

    return Crew(
        agents=list(agents.values()),
        tasks=[research, summary, fact_check],
        process=Process.sequential,
        verbose=True,
    )


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Run the CrewAI multi-agent research crew.")
    parser.add_argument("--topic", default="AI agents in production", help="Topic to research")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    llm = build_llm(args.model, temperature=0.2)
    OUTPUT_DIR.mkdir(exist_ok=True)

    result = build_crew(llm).kickoff(
        inputs={"topic": args.topic, "today": f"{date.today():%B %d, %Y}"}
    )

    print("\n" + "=" * 60)
    print(result.raw)
    print("=" * 60)
    print(f"\n✅ Outputs saved to {OUTPUT_DIR.relative_to(HERE)}/")
    print("   1_research_notes.md  →  2_summary.md  →  3_final_report.md")


if __name__ == "__main__":
    main()

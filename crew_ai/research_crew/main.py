"""
Run the multi-agent research crew defined in `research_crew.py`.

Usage:
    python main.py --topic "Small language models"
    python main.py --topic "Agentic RAG" --model anthropic/claude-sonnet-4-5
"""

import argparse
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from llm import build_llm
from research_crew import OUTPUT_DIR, ResearchCrew

HERE = Path(__file__).parent


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Run the CrewAI multi-agent research crew.")
    parser.add_argument("--topic", default="AI agents in production", help="Topic to research")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    parser.add_argument("--no-search", action="store_true", help="Run without web search")
    args = parser.parse_args()

    llm = build_llm(args.model, temperature=0.2)
    OUTPUT_DIR.mkdir(exist_ok=True)

    research_crew = ResearchCrew(llm=llm, use_search=not args.no_search)
    result = research_crew.crew().kickoff(
        inputs={"topic": args.topic, "today": f"{date.today():%B %d, %Y}"}
    )

    print("\n" + "=" * 60)
    print(result.raw)
    print("=" * 60)
    print(f"\n✅ Outputs saved to {OUTPUT_DIR.relative_to(HERE)}/")
    print("   1_research_notes.md  →  2_summary.md  →  3_final_report.md")


if __name__ == "__main__":
    main()

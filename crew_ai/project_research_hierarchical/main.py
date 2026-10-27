"""
Run the hierarchical project research crew defined in `project_research_crew.py`.

Usage:
    python main.py --project "An AI assistant that answers phone calls for small restaurants"
    python main.py --project "A multi-agent customer support platform" --model gpt-4o-mini
    python main.py --no-search
"""

import argparse
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from llm import build_llm
from project_research_crew import OUTPUT_DIR, ProjectResearchCrew

HERE = Path(__file__).parent


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Research a project idea with a manager agent and three analysts.")
    parser.add_argument("--project", default="A multi-agent system that automates customer support for online shops")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    parser.add_argument("--no-search", action="store_true", help="Run without web search")
    args = parser.parse_args()

    llm = build_llm(args.model, temperature=0.2)
    OUTPUT_DIR.mkdir(exist_ok=True)

    research_crew = ProjectResearchCrew(llm=llm, use_search=not args.no_search)
    result = research_crew.crew().kickoff(
        inputs={"project": args.project, "today": f"{date.today():%B %d, %Y}"}
    )

    print("\n" + "=" * 60)
    print(result.raw)
    print("=" * 60)
    print(f"\n✅ Outputs saved to {OUTPUT_DIR.relative_to(HERE)}/")
    print("   1_market_demand.md · 2_risk_analysis.md · 3_roi.md  →  4_final_report.md")


if __name__ == "__main__":
    main()

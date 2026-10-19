"""
Answer a money question in natural language with live exchange rates.

Usage:
    python main.py --query "How much is 100 dollars in euros today?"
    python main.py --query "Convert 2500 yen to pounds" --model gpt-4o-mini
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from currency_crew import CurrencyCrew
from llm import build_llm
from models import ConversionRequest

HERE = Path(__file__).parent


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Run the CrewAI currency conversion crew.")
    parser.add_argument(
        "--query", default="How much is 100 dollars in euros today?", help="Question to answer"
    )
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    llm = build_llm(args.model, temperature=0)
    result = CurrencyCrew(llm=llm).crew().kickoff(inputs={"query": args.query})

    request = result.tasks_output[0].pydantic
    print("\n" + "=" * 60)
    if isinstance(request, ConversionRequest):
        print(f"Parsed request: {request.model_dump()}")
        print("-" * 60)
    print(result.raw)
    print("=" * 60)


if __name__ == "__main__":
    main()

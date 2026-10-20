"""
01 · Basic flow: two LLM steps chained with @start and @listen.

    generate_genre ──▶ recommend_movie
      (@start)          (@listen(generate_genre))

* The method decorated with @start() is the entry point of the flow.
* A method decorated with @listen(other) runs when `other` finishes and
  receives its return value as argument.
* `self.state` keeps intermediate values; by default it is a dict that already
  contains a unique `id` for the run.

Usage:
    python 01_basic_flow.py
    python 01_basic_flow.py --model gpt-4o-mini --plot
"""

import argparse
import os
from pathlib import Path
from pprint import pprint

from crewai.flow.flow import Flow, listen, start
from dotenv import load_dotenv

from llm import get_llm

HERE = Path(__file__).parent


class MovieRecommendationFlow(Flow):
    @start()
    def generate_genre(self) -> str:
        genre = get_llm().call(
            "Give me one random movie genre. Answer with the name of the genre only."
        ).strip()
        self.state["genre"] = genre  # intermediate value, kept in the flow state
        print(f"🎬 Genre: {genre}\n")
        return genre

    @listen(generate_genre)
    def recommend_movie(self, genre: str) -> str:
        recommendation = get_llm().call(
            f"Recommend one highly rated movie in the {genre} genre. Give the title, "
            "the year and one sentence on why it is worth watching."
        ).strip()
        self.state["recommendation"] = recommendation
        return recommendation


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    parser.add_argument("--plot", action="store_true", help="Save (and open) an interactive HTML diagram of the flow")
    args = parser.parse_args()
    if args.model:
        os.environ["MODEL"] = args.model

    flow = MovieRecommendationFlow()
    if args.plot:
        flow.plot("01_basic_flow.html")

    result = flow.kickoff()  # the return value of the last step

    print("Final result:\n")
    print(result)
    print("\nFlow state:")
    pprint(flow.state)


if __name__ == "__main__":
    main()

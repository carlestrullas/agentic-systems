"""
Extract entity-relation-entity triplets from text with a structured-output crew.

Usage:
    python main.py
    python main.py --text "Ada Lovelace worked with Charles Babbage on the Analytical Engine."
    python main.py --file notes.txt --model gpt-4o-mini
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from extractor_crew import ExtractorCrew
from llm import build_llm
from models import KnowledgeGraph

HERE = Path(__file__).parent
OUTPUT_FILE = HERE / "output" / "triplets.json"

SAMPLE_TEXT = (
    "Marie Curie was born in Warsaw in 1867 and later moved to Paris, where she studied "
    "at the University of Paris. She married Pierre Curie in 1895. Together they discovered "
    "polonium and radium. Marie Curie won the Nobel Prize in Physics in 1903 and the Nobel "
    "Prize in Chemistry in 1911."
)


def print_table(graph: KnowledgeGraph) -> None:
    rows = [(t.subject, t.relation, t.object) for t in graph.triplets]
    headers = ("subject", "relation", "object")
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]

    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("-" * len(line))
    for row in rows:
        print("  ".join(v.ljust(w) for v, w in zip(row, widths)))


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Extract knowledge-graph triplets from text.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text", help="Text to analyse (defaults to a short sample)")
    source.add_argument("--file", type=Path, help="Read the text from a file")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    text = args.file.read_text(encoding="utf-8") if args.file else (args.text or SAMPLE_TEXT)

    llm = build_llm(args.model, temperature=0)
    result = ExtractorCrew(llm=llm).crew().kickoff(inputs={"text": text})

    graph = result.pydantic
    if not isinstance(graph, KnowledgeGraph):
        raise SystemExit(f"The model did not return valid structured output:\n{result.raw}")

    print("\n" + "=" * 60)
    print_table(graph)
    print("=" * 60)

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(graph.model_dump_json(indent=2), encoding="utf-8")
    print(f"\n✅ {len(graph.triplets)} triplets saved to {OUTPUT_FILE.relative_to(HERE)}")


if __name__ == "__main__":
    main()

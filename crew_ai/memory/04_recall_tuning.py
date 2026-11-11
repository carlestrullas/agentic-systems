"""
04 · Look inside recall: similarity, importance, recency and the composite score.

    query ──▶ embedding ──▶ vector search (LanceDB) ──▶ candidates
                                                           │
           score = semantic_weight   × similarity     (0–1)
                 + recency_weight    × 0.5^(age / recency_half_life_days)
                 + importance_weight × importance     (0–1)  ──▶ top `limit` ──▶ prompt

Memory is RAG over facts, but the ranking is not only similarity. Each match
gets a composite score that also rewards recent and important facts, with
weights you choose when creating the Memory (defaults 0.5 / 0.3 / 0.2).

No agent here: the facts are saved directly with `memory.remember()`, giving
the scope, categories and importance ourselves. When all three are given the
memory LLM does not need to analyse the fact, which makes this script fast
and repeatable. Normally the LLM is still asked when a new fact is almost
identical to a stored one (similarity above `consolidation_threshold`, 0.85),
to decide whether to merge them; this script turns that off so that both
diet facts below are kept. Then the same query is run with the weights you
pass:

* depth="shallow": one vector search with the query, no LLM. Use it when
  latency matters.
* depth="deep" (what agents use): the LLM first splits the query into
  targeted searches and picks the scopes to search, and may explore further
  when the first results look weak. Queries shorter than
  `query_analysis_threshold` (200 characters) skip that LLM step, so with a
  short --query both depths give the same ranking. Task descriptions are
  often longer, which is when deep recall pays off.

Two facts below say opposite things about the user's diet: the old one has
low importance, the correction high importance. Set --importance-weight 0
and watch which one wins.

Usage:
    python 04_recall_tuning.py
    python 04_recall_tuning.py --importance-weight 0
    python 04_recall_tuning.py --query "Where does the user work?" --limit 2
    python 04_recall_tuning.py --depth deep --query "I want to surprise the user with dinner on a
        weekday evening after their team meeting, at a restaurant close to where they work, so tell
        me what they eat and where they work"       # over 200 characters: the LLM splits it
"""

import argparse

from llm import build_llm
from memory_setup import build_memory, reset_store, show_matches, show_records

# (content, scope, categories, importance)
FACTS = [
    ("The user is vegetarian.", "/user/food", ["diet"], 0.2),
    ("Correction: the user eats fish now, but still no meat.", "/user/food", ["diet"], 0.9),
    ("The user's favourite cuisine is Japanese.", "/user/food", ["preferences"], 0.5),
    ("The user works as a data scientist in Barcelona.", "/user/work", ["job"], 0.6),
    ("The user's team has its weekly meeting on Mondays at 10:00.", "/user/work", ["schedule"], 0.3),
    ("The user runs three times a week, early in the morning.", "/user/sport", ["habits"], 0.4),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="See how memory ranks what it recalls.")
    parser.add_argument("--query", default="What can I cook for the user tonight?")
    parser.add_argument("--limit", type=int, default=3, help="How many memories to return")
    parser.add_argument("--depth", choices=["shallow", "deep"], default="shallow")
    parser.add_argument("--semantic-weight", type=float, default=0.5)
    parser.add_argument("--recency-weight", type=float, default=0.3)
    parser.add_argument("--importance-weight", type=float, default=0.2)
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    reset_store()
    llm = build_llm(args.model, temperature=0)  # used by --depth deep and to merge near-duplicates
    memory = build_memory(
        llm,
        semantic_weight=args.semantic_weight,
        recency_weight=args.recency_weight,
        importance_weight=args.importance_weight,
        consolidation_threshold=1.0,  # never merge: keep both diet facts for the demo
    )

    for content, scope, categories, importance in FACTS:
        memory.remember(content, scope=scope, categories=categories, importance=importance)
    show_records(memory.list_records())

    print(
        f"\n⚖️  weights: semantic={args.semantic_weight} recency={args.recency_weight} "
        f"importance={args.importance_weight} · depth={args.depth}"
    )
    show_matches(memory.recall(args.query, limit=args.limit, depth=args.depth), args.query)

    # Recall can be narrowed down before ranking, too.
    show_matches(memory.recall(args.query, scope="/user/work", limit=args.limit, depth="shallow"),
                 f"{args.query}  [scope=/user/work]")
    show_matches(memory.recall(args.query, categories=["diet"], limit=args.limit, depth="shallow"),
                 f"{args.query}  [categories=diet]")


if __name__ == "__main__":
    main()

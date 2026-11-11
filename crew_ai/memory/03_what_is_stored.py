"""
03 · What is stored: facts about entities, organised in scopes and categories.

    meeting notes ──▶ memory LLM ──▶ "Acme Corp's revenue is $5M"      scope /companies/acme
                                     "Beta Corp's revenue is $10M"     scope /companies/beta
                                     "Alice leads the Acme account"    scope /people/alice
                                     ...                               + categories, importance

When a crew saves to memory, the text is not stored as one blob. The memory
LLM splits it into short, self-contained facts and, for each one, picks:

* a **scope**, a path like a folder (/companies/beta), so facts about
  different entities stay apart. This covers what older CrewAI versions
  called "entity memory": a fact sheet per person, company or product.
* **categories** (tags such as "finance" or "contact") and an **importance**
  from 0 to 1, both used later to filter and rank.

A recall searches every scope at once and merges the best matches into one
list, so the agent gets the relevant facts whether they came from this
session, an earlier one or another entity's file. That merged view is what
was called "contextual memory".

The script saves the notes, prints the scope tree and every record, and then
asks a question that needs exactly one entity's facts.

Usage:
    python 03_what_is_stored.py
    python 03_what_is_stored.py --question "Who should I call about the Beta Corp renewal?"
"""

import argparse

from crewai import Agent, Crew, Process, Task

from llm import build_llm
from memory_setup import build_memory, reset_store, show_matches, show_records

NOTES = """
Account review, 4 November:
- Acme Corp: annual revenue of $5M, renewal due in January. Alice Martín leads the
  account and prefers to be contacted by email.
- Beta Corp: annual revenue of $10M, unhappy with response times last quarter.
  Bob Chen is their CTO and the person to call before any renewal discussion.
- Bob mentioned that Beta Corp is evaluating a competitor, so treat it as at risk.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="See how memory stores facts about entities.")
    parser.add_argument("--question", default="What is Beta Corp's revenue, and is the account at risk?")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    reset_store()
    llm = build_llm(args.model, temperature=0)
    memory = build_memory(llm)

    analyst = Agent(
        role="Account Analyst",
        goal="Keep track of customer accounts and answer questions about them precisely.",
        backstory=(
            "You manage the notes of a B2B sales team. You never mix up two customers, "
            "and you quote figures exactly as they were recorded."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )
    task = Task(
        description="{request}",
        expected_output="A short, precise answer or confirmation.",
        agent=analyst,
    )
    crew = Crew(agents=[analyst], tasks=[task], process=Process.sequential, memory=memory, verbose=True)

    # Session part 1: the notes come in and are saved as facts.
    crew.kickoff(inputs={"request": f"Read and acknowledge these meeting notes:\n{NOTES}"})

    print("\n🌳 Scopes chosen by the memory LLM")
    print(memory.tree())
    show_records(memory.list_records())

    # What the agent will get before answering: one search over every scope.
    show_matches(memory.recall(args.question, limit=5), args.question)

    # Part 2: a question that needs one entity's facts, answered from memory.
    result = crew.kickoff(inputs={"request": args.question})
    print("\n" + "=" * 60)
    print(f"Q: {args.question}\n\n{result.raw}")
    print("=" * 60)


if __name__ == "__main__":
    main()

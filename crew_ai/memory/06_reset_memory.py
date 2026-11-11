"""
06 · Reset and forget: wipe the memory, or delete only part of it.

    tell ──▶ ask (remembers) ──▶ forget one user ──▶ ask (that user is forgotten)
                             ──▶ crew.reset_memories("memory") ──▶ ask (everything is forgotten)

Memory keeps growing and persists between runs, so sometimes you need to
remove things: to start a test from scratch, to drop facts that are outdated
or wrong, or because a user asked you to delete their data. There are three
levels:

* `memory.forget(scope=..., categories=..., older_than=..., record_ids=...)`
  deletes only the records that match, and returns how many it deleted.
* `memory.reset(scope)` empties a branch of the scope tree; without a scope,
  everything.
* `crew.reset_memories("memory")` empties the crew's whole memory. The other
  options are "knowledge", "agent_knowledge", "kickoff_outputs" and "all".
  In a CrewAI project the CLI does the same: `crewai reset-memories --memory`.

Deleted records are gone for good, so think twice before doing this with
real users' data you have no copy of.

Usage:
    python 06_reset_memory.py
    python 06_reset_memory.py --question "What do you know about Bob?"
"""

import argparse

from crewai import Agent, Crew, Process, Task

from llm import build_llm
from memory_setup import build_memory, reset_store

FACTS = {
    "alice": "Alice's favourite colour is #46778F and she lives in Girona.",
    "bob": "Bob's favourite colour is orange and he lives in Tarragona.",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Forget part of the memory, then reset all of it.")
    parser.add_argument("--question", default="What are the favourite colours of Alice and Bob?")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    reset_store()
    llm = build_llm(args.model, temperature=0)
    memory = build_memory(llm)

    # Facts saved directly with a known scope per person, so we can delete one of them later.
    for person, fact in FACTS.items():
        memory.remember(fact, scope=f"/people/{person}")

    assistant = Agent(
        role="Personal Assistant",
        goal="Answer questions about the people the user knows, using only what you remember.",
        backstory="You answer from memory. If you do not remember something, you say so clearly.",
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )
    task = Task(
        description="Answer this question: {question}",
        expected_output="A short answer of one or two sentences.",
        agent=assistant,
    )
    # From now on the crew can recall but not save. Otherwise the agent's first answer
    # ("Bob's favourite colour is orange") would be stored in a scope of its own and
    # survive forget(scope="/people/bob"). forget() and reset() still work.
    memory.read_only = True

    crew = Crew(agents=[assistant], tasks=[task], process=Process.sequential, memory=memory, verbose=True)

    def ask(label: str) -> str:
        records = len(memory.list_records())
        answer = crew.kickoff(inputs={"question": args.question}).raw
        return f"{label} ({records} records)\n    {answer}"

    answers = [ask("1️⃣  Everything remembered")]

    deleted = memory.forget(scope="/people/bob")
    answers.append(ask(f"2️⃣  After memory.forget(scope='/people/bob'), {deleted} deleted"))

    crew.reset_memories(command_type="memory")
    answers.append(ask("3️⃣  After crew.reset_memories('memory')"))

    print("\n" + "=" * 60)
    print(f"Q: {args.question}\n")
    print("\n\n".join(answers))
    print("=" * 60)


if __name__ == "__main__":
    main()

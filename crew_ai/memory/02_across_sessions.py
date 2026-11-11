"""
02 · Memory across sessions: a new run, a new crew, the same memory.

    run 1 (--session tell)                     run 2 (--session ask), a new process
    ┌──────────────────────────┐               ┌──────────────────────────────────┐
    │ Crew 1 ──▶ facts saved ──┼──▶ output/ ──▶│ Crew 2 (new agent) ──▶ recalls   │
    └──────────────────────────┘    memory/    └──────────────────────────────────┘

In 01 both kickoffs happened in the same run. Real conversations are spread
over days: the program stops, starts again, and builds new Agent and Crew
objects. What connects the sessions is the **storage**, not the Python
objects. Memory is kept in a LanceDB folder on disk, so any crew that opens
the same folder sees everything saved before. That is what used to be called
"long-term memory": the same Memory serves the current session and all the
previous ones.

Usage:
    python 02_across_sessions.py --session tell
    python 02_across_sessions.py --session ask
    python 02_across_sessions.py --session ask --question "Which city should I train in this weekend?"
    python 02_across_sessions.py --reset          # forget everything and start again
"""

import argparse

from crewai import Agent, Crew, Process, Task

from llm import build_llm
from memory_setup import build_memory, reset_store, show_records, storage_path

FACTS = (
    "Some things about me: I live in Lisbon, I am training for a half marathon in March, "
    "and I can only run early in the morning because I work from 9 to 6."
)


def build_crew(llm, memory, role: str, goal: str) -> Crew:
    agent = Agent(
        role=role,
        goal=goal,
        backstory=(
            "You help one user over many conversations. You use what you already know about "
            "them and never ask for something they have told you before."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )
    task = Task(
        description="Handle this message from the user: {user_message}",
        expected_output="A helpful reply of at most five sentences.",
        agent=agent,
    )
    return Crew(agents=[agent], tasks=[task], process=Process.sequential, memory=memory, verbose=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Share memory between two separate runs.")
    parser.add_argument("--session", choices=["tell", "ask"], default="tell")
    parser.add_argument("--facts", default=FACTS, help="What the user says in the first session")
    parser.add_argument("--question", default="Plan my running for next week.")
    parser.add_argument("--reset", action="store_true", help="Delete the memory and exit")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    if args.reset:
        reset_store()
        return

    llm = build_llm(args.model, temperature=0)
    memory = build_memory(llm)  # same folder in every run: that is the whole trick

    if args.session == "tell":
        crew = build_crew(llm, memory, "Personal Assistant", "Get to know the user.")
        result = crew.kickoff(inputs={"user_message": args.facts})
        print("\n" + "=" * 60)
        print(f"Assistant: {result.raw}")
        show_records(memory.list_records(), "Saved for later sessions")
        print("\nNow run it again in a new session:  python 02_across_sessions.py --session ask")
        return

    # A brand-new crew, with a different agent: only the storage folder is shared.
    print(f"📂 Opening memory from {storage_path().name}")
    show_records(memory.list_records(), "Already in memory from earlier sessions")
    crew = build_crew(llm, memory, "Running Coach", "Plan training that fits the user's life.")
    result = crew.kickoff(inputs={"user_message": args.question})
    print("\n" + "=" * 60)
    print(f"User: {args.question}\n\nCoach: {result.raw}")
    print("=" * 60)


if __name__ == "__main__":
    main()

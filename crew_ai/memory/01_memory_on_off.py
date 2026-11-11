"""
01 · Memory on and off: does the assistant remember what you just told it?

    kickoff 1: "My favourite colour is #46778F"  ──▶ answer ──▶ facts saved to memory
                                                                        │ recall
    kickoff 2: "What is my favourite colour?"   ──▶ prompt + relevant memories ──▶ answer

Without memory, every `crew.kickoff()` starts from a blank slate: the second
run has no idea what the first one was told. With `Crew(memory=...)`:

* After each task, the memory LLM extracts short facts from the task and its
  result ("The user's favourite colour is #46778F") and stores them with an
  embedding.
* Before each task, the task description is used as a query, and the most
  relevant memories (top 5) are added to the agent's prompt.
* The agents also get two tools, "Search memory" and "Save to memory", to
  look things up or save facts themselves.

`Crew(memory=True)` does the same with the defaults (the agents' LLM, the
OpenAI embedder and storage in your user data folder). Here a `Memory` object is passed
instead, to use the local embedder and keep the storage in output/memory/.

The memory is emptied at the start of every run, so the demo starts clean.

Usage:
    python 01_memory_on_off.py
    python 01_memory_on_off.py --no-memory       # same two runs, no memory: the colour is forgotten
    python 01_memory_on_off.py --fact "I am allergic to peanuts" --question "Suggest a snack for me"
"""

import argparse

from crewai import Agent, Crew, Process, Task

from llm import build_llm
from memory_setup import build_memory, reset_store, show_records


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare a personal assistant with and without memory.")
    parser.add_argument("--fact", default="My favourite colour is #46778F.")
    parser.add_argument("--question", default="What is my favourite colour?")
    parser.add_argument("--no-memory", action="store_true", help="Run both kickoffs without memory, to compare")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    llm = build_llm(args.model, temperature=0)

    memory = None
    if not args.no_memory:
        reset_store()
        memory = build_memory(llm)

    assistant = Agent(
        role="Personal Assistant",
        goal="Help the user with their requests, using everything you know about them.",
        backstory=(
            "You are a friendly personal assistant. You pay attention to the details users "
            "share about themselves and use them in later answers. If you do not know "
            "something about the user, you say so instead of guessing."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )

    task = Task(
        description="Handle this message from the user: {user_message}",
        expected_output="A short, friendly reply of one or two sentences.",
        agent=assistant,
    )

    crew = Crew(
        agents=[assistant],
        tasks=[task],
        process=Process.sequential,
        memory=memory or False,  # the only line that changes
        verbose=True,
    )

    first = crew.kickoff(inputs={"user_message": args.fact})
    second = crew.kickoff(inputs={"user_message": args.question})

    print("\n" + "=" * 60)
    print(f"1️⃣  User: {args.fact}\n    Assistant: {first.raw}\n")
    print(f"2️⃣  User: {args.question}\n    Assistant: {second.raw}")
    print("=" * 60)

    if memory is None:
        print("(no memory: the second kickoff never saw the first one)")
    else:
        show_records(memory.list_records())


if __name__ == "__main__":
    main()

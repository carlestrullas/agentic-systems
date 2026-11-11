"""
05 · User memory: one assistant, many users, and no memory leaking between them.

                         ┌── /users/alice ── "Alice has a dog called Luna" ...
    Memory (one store) ──┤
                         └── /users/bob ──── "Bob has a cat called Miso" ...

    crew for Alice: Crew(memory=memory.scope("/users/alice"))  → sees and saves only Alice's facts

An assistant that serves several people must remember each one separately:
Alice's preferences should shape Alice's answers and never appear in Bob's.
`memory.scope(path)` returns a view of the memory restricted to one branch
of the scope tree. Everything the crew saves goes under that path, and every
recall searches only there. In production the path would use a stable user
ID from your login system (/users/8f3a…), not a name. Scopes match by
prefix, so IDs must never be the start of another ID: /users/al would also
see /users/alice.

(Older CrewAI versions did this with an external service, Mem0, and a
user_id. Scopes do the same with the built-in memory.)

The demo runs four kickoffs: Alice and Bob each introduce themselves, then
each asks the same question. Use --user and --message to talk to the
assistant as any user yourself; that mode keeps the memory between runs.

Usage:
    python 05_user_memory.py
    python 05_user_memory.py --user carles --message "I'm vegetarian and I live in Manresa."
    python 05_user_memory.py --user carles --message "Suggest a restaurant for tonight."
"""

import argparse

from crewai import Agent, Crew, Process, Task

from llm import build_llm
from memory_setup import build_memory, reset_store, show_records

INTRODUCTIONS = {
    "alice": "Hi, I'm Alice. I have a dog called Luna and I love hiking in the mountains.",
    "bob": "Hi, I'm Bob. I have a cat called Miso, and my favourite place is a quiet beach.",
}
QUESTION = "Plan a weekend trip for me and my pet."


def build_crew(llm, user_memory) -> Crew:
    assistant = Agent(
        role="Personal Travel Assistant",
        goal="Plan trips that fit what you know about the current user.",
        backstory=(
            "You help many users, one at a time. You only know what the current user has told "
            "you, and if you are missing something important you say so."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )
    task = Task(
        description="Handle this message from the user: {user_message}",
        expected_output="A friendly reply; for a trip, a short plan of at most five lines.",
        agent=assistant,
    )
    return Crew(agents=[assistant], tasks=[task], process=Process.sequential, memory=user_memory, verbose=True)


def talk(llm, memory, user: str, message: str) -> str:
    user_memory = memory.scope(f"/users/{user}")  # this crew sees only this user's branch
    return build_crew(llm, user_memory).kickoff(inputs={"user_message": message}).raw


def main() -> None:
    parser = argparse.ArgumentParser(description="Keep a separate memory for each user.")
    parser.add_argument("--user", help="Talk as this user (keeps the memory between runs)")
    parser.add_argument("--message", help="What the user says (needs --user)")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    if bool(args.user) != bool(args.message):
        parser.error("--user and --message go together")

    llm = build_llm(args.model, temperature=0)

    if args.user:
        memory = build_memory(llm, name="05_user_memory_chat")
        print(f"\n{args.user}: {args.message}\n\nAssistant: {talk(llm, memory, args.user.lower(), args.message)}")
        show_records(memory.list_records(scope=f"/users/{args.user.lower()}"), f"What I know about {args.user}")
        return

    reset_store()
    memory = build_memory(llm)
    replies = {}
    for user, intro in INTRODUCTIONS.items():
        talk(llm, memory, user, intro)
    for user in INTRODUCTIONS:
        replies[user] = talk(llm, memory, user, QUESTION)

    print("\n🌳 One store, one branch per user")
    print(memory.tree())
    print("\n" + "=" * 60)
    for user, reply in replies.items():
        print(f"{user.title()}: {QUESTION}\nAssistant: {reply}\n")
    print("=" * 60)


if __name__ == "__main__":
    main()

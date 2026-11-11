"""
07 · Shared crew memory: one agent learns something, another one uses it.

    Support Agent ──▶ handles the call ──▶ facts saved under /crew/support-team/agent/support-agent
                                                                       │ recall
    Follow-up Writer (no task context) ──▶ prompt + relevant memories ◀┘ ──▶ follow-up email

Memory is not only for remembering users across conversations. Inside a crew
it lets agents collaborate: whatever one agent learns is saved to the crew's
memory, and the next agent finds it when it recalls for its own task.

To prove that the facts travel through memory, the writer's task has
`context=[]`. Normally a sequential crew passes each task's output to the
next one; with an empty context the writer receives nothing from the support
task, so everything it knows comes from memory. Run with --no-memory to see
the writer without it.

The Memory gets `root_scope="/crew/support-team"`, which is what
`Crew(memory=True)` does with the crew's name. Each agent then saves under
its own branch, .../agent/<role>, while recall searches the whole crew
branch, so you can see in the scope tree who learned what.

Usage:
    python 07_shared_crew_memory.py
    python 07_shared_crew_memory.py --no-memory     # the writer gets no facts at all
"""

import argparse

from crewai import Agent, Crew, Process, Task

from llm import build_llm
from memory_setup import build_memory, reset_store, show_records

CALL = """
Customer: Marta Puig, account 4471, Pro plan.
Problem: the nightly sales export to Google Sheets has failed since Monday with "quota exceeded".
Already tried: reconnecting the Google account, which did not help.
She needs it fixed before the board meeting on Friday and prefers an email to a phone call.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Let one agent use what another agent learned.")
    parser.add_argument("--call", default=CALL, help="Notes from the support call")
    parser.add_argument("--no-memory", action="store_true", help="Run the crew without memory, to compare")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    llm = build_llm(args.model, temperature=0)

    memory = None
    if not args.no_memory:
        reset_store()
        memory = build_memory(llm, root_scope="/crew/support-team")

    support_agent = Agent(
        role="Support Agent",
        goal="Understand the customer's problem and decide the next step.",
        backstory="You handle support calls for a reporting tool and write down the key facts of every case.",
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )
    writer = Agent(
        role="Follow-up Writer",
        goal="Write clear follow-up emails after support calls.",
        backstory=(
            "You write the emails that go to customers after a support call. You use only "
            "facts you actually know about the case, and you never invent details."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )

    handle_call = Task(
        description="Handle this support call and summarise the case and the next step:\n{call}",
        expected_output="The key facts of the case and the proposed next step, in a few bullet points.",
        agent=support_agent,
    )
    follow_up = Task(
        description="Write the follow-up email for the support call that was just handled.",
        expected_output="An email of at most 120 words, addressed to the customer by name.",
        agent=writer,
        context=[],  # no output from handle_call: the writer depends on memory alone
    )

    crew = Crew(
        agents=[support_agent, writer],
        tasks=[handle_call, follow_up],
        process=Process.sequential,
        memory=memory or False,
        verbose=True,
    )
    result = crew.kickoff(inputs={"call": args.call})

    print("\n" + "=" * 60)
    print(f"✉️  Follow-up email{' (WITHOUT memory)' if memory is None else ''}:\n\n{result.raw}")
    print("=" * 60)

    if memory is not None:
        print("\n🌳 Who saved what")
        print(memory.tree())
        show_records(memory.list_records())


if __name__ == "__main__":
    main()

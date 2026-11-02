"""
03 · Agent knowledge vs. crew knowledge: who can see what.

                      crew knowledge: company_info.json (shared)
                    ┌───────────────────────────┴──────────────────────────┐
    HR Assistant  + hr_policy.txt                 Product Analyst + feedback.csv, meeting_notes.pdf
      (agent knowledge)                             (agent knowledge)

* `Crew(knowledge_sources=...)` → every agent can use it ("crew" collection).
* `Agent(knowledge_sources=...)` → only that agent (a collection named after
  its role).
* An agent searches its own knowledge AND the crew's, so the Product Analyst
  can combine team sizes (crew) with user feedback (its own), while the HR
  Assistant never sees the feedback.
* `embedder` set on the crew is used by every agent that does not set its own.

The third task asks the HR Assistant about feedback on purpose: it should say
it has no information instead of making it up.

Usage:
    python 03_agent_vs_crew_knowledge.py
"""

import argparse

from knowledge_setup import KNOWLEDGE_DIR, build_embedder, reset_knowledge  # before crewai: it sets the storage

from crewai import Agent, Crew, Process, Task
from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

from llm import build_llm

GROUNDING = (
    " Answer only from the information you were given about the company. If it does not "
    "contain the answer, say clearly that you do not have that information."
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare agent-level and crew-level knowledge.")
    parser.add_argument("--reset", action="store_true", help="Re-embed the knowledge from scratch")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    if args.reset:
        reset_knowledge()

    llm = build_llm(args.model, temperature=0)

    hr_assistant = Agent(
        role="HR Assistant",
        goal="Answer employee questions about people, teams and HR policies.",
        backstory="You work in People Ops and know the HR policy by heart." + GROUNDING,
        knowledge_sources=[TextFileKnowledgeSource(file_paths=[KNOWLEDGE_DIR / "hr_policy.txt"])],
        llm=llm,
        verbose=True,
    )
    product_analyst = Agent(
        role="Product Analyst",
        goal="Connect user feedback and product decisions with the teams that own them.",
        backstory="You read every piece of user feedback and every product meeting note." + GROUNDING,
        knowledge_sources=[
            CSVKnowledgeSource(file_paths=[KNOWLEDGE_DIR / "feedback.csv"]),
            PDFKnowledgeSource(file_paths=[KNOWLEDGE_DIR / "meeting_notes.pdf"]),
        ],
        llm=llm,
        verbose=True,
    )

    tasks = [
        Task(  # crew knowledge (team sizes) + its own (HR policy)
            description="How many people work in the Support team, and how many remote days per week can they work?",
            expected_output="Two short sentences.",
            agent=hr_assistant,
        ),
        Task(  # crew knowledge (Mobile team) + its own (feedback and meeting notes)
            description=(
                "Is mobile performance a problem for users? Say how many feedback comments mention it, "
                "what was decided about it in the last product sync, and how big the Mobile team is."
            ),
            expected_output="A short paragraph.",
            agent=product_analyst,
        ),
        Task(  # not in the HR Assistant's knowledge: it should say so
            description="What do users complain about most in their feedback?",
            expected_output="One or two sentences.",
            agent=hr_assistant,
            context=[],  # do not pass the previous answers: test the knowledge alone
        ),
    ]

    crew = Crew(
        agents=[hr_assistant, product_analyst],
        tasks=tasks,
        process=Process.sequential,
        knowledge_sources=[JSONKnowledgeSource(file_paths=[KNOWLEDGE_DIR / "company_info.json"])],  # shared
        embedder=build_embedder(),  # used by both agents too
        verbose=True,
    )
    crew.kickoff()

    print("\n" + "=" * 60)
    for task in tasks:
        print(f"[{task.output.agent}] {task.description}\n→ {task.output.raw}\n")
    print("=" * 60)


if __name__ == "__main__":
    main()

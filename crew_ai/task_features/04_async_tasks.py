"""
04 · Asynchronous tasks: run independent tasks at the same time.

    breakthroughs_task (async) ──┐
                                 ├──▶ report_task  (context = both)
    regulation_task    (async) ──┘

* `async_execution=True` starts a task without waiting for it to finish, so the
  next task can start right away. Use it for tasks that do not depend on each
  other (two independent research lines, several scrapes…).
* A later task waits for the async tasks listed in its `context` before it
  starts; here the report writer needs both results.
* Two rules CrewAI enforces: a crew may end with at most one async task, and an
  async task cannot use as context another async task from the same parallel
  block (they would be running at the same time).

Compare the elapsed time and the order of the logs with and without --sync.

Usage:
    python 04_async_tasks.py
    python 04_async_tasks.py --sync      # same crew, one task after another
"""

import argparse
import time
from pathlib import Path

from crewai import Agent, Crew, Task
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from llm import build_llm

HERE = Path(__file__).parent


class BreakthroughFindings(BaseModel):
    key_findings: list[str] = Field(..., description="Four to six recent AI breakthroughs, one sentence each.")


class RegulationFindings(BaseModel):
    policies: list[str] = Field(
        ..., description="Four to six key AI regulations or policies, each naming its region (EU, US, China…)."
    )


class FinalReport(BaseModel):
    executive_summary: str = Field(..., description="One paragraph connecting technology and regulation.")
    key_trends: list[str] = Field(..., description="Three to five trends that combine both perspectives.")


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Run two research tasks in parallel.")
    parser.add_argument("--sync", action="store_true", help="Run the research tasks sequentially to compare")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    llm = build_llm(args.model)
    run_async = not args.sync

    researcher = Agent(
        role="AI Researcher",
        goal="Find and summarize the latest AI breakthroughs.",
        backstory="An expert researcher who tracks technological advances in AI.",
        llm=llm,
        verbose=True,
    )
    policy_analyst = Agent(
        role="AI Policy Analyst",
        goal="Summarize the main AI regulations around the world.",
        backstory="A policy expert specialising in AI law and governance.",
        llm=llm,
        verbose=True,
    )
    writer = Agent(
        role="AI Report Writer",
        goal="Write a report that connects AI breakthroughs with AI regulation.",
        backstory="A technical writer who explains how technology and policy shape each other.",
        llm=llm,
        verbose=True,
    )

    breakthroughs_task = Task(
        description="Research the latest AI advancements and summarize the key breakthroughs.",
        expected_output="A list of recent AI breakthroughs.",
        agent=researcher,
        output_pydantic=BreakthroughFindings,
        async_execution=run_async,  # does not wait for this task to finish
    )
    regulation_task = Task(
        description="Analyze the main AI regulations worldwide and summarize the key policies.",
        expected_output="A list of key AI policies by region.",
        agent=policy_analyst,
        output_pydantic=RegulationFindings,
        async_execution=run_async,
    )
    report_task = Task(
        description="Write a report that combines the AI breakthroughs and the AI regulations.",
        expected_output="An executive summary and the key trends.",
        agent=writer,
        output_pydantic=FinalReport,
        context=[breakthroughs_task, regulation_task],  # waits for both
    )

    crew = Crew(
        agents=[researcher, policy_analyst, writer],
        tasks=[breakthroughs_task, regulation_task, report_task],
        verbose=True,
    )

    start = time.perf_counter()
    result = crew.kickoff()
    elapsed = time.perf_counter() - start

    report: FinalReport = result.pydantic
    print("\n" + "=" * 60)
    print(report.executive_summary + "\n")
    for trend in report.key_trends:
        print(f"- {trend}")
    print("=" * 60)
    print(f"\n⏱️  {'Async' if run_async else 'Sync'} run took {elapsed:.1f} s")


if __name__ == "__main__":
    main()

"""
01 · Guardrails: validate a task's output with a Python function.

    summarizer ──▶ output ──▶ validate_summary_length ──✔──▶ final result
                     ▲                  │
                     └─── error msg ◀───✘  (up to guardrail_max_retries times)

* A guardrail receives the task's `TaskOutput` and returns a tuple:
  `(True, value)` to accept (the value replaces the output) or
  `(False, "error message")` to reject it.
* On rejection the error message is sent back to the agent, which tries again.
  The error is an instruction for the model, so make it say what to fix.
* After `guardrail_max_retries` failed attempts (3 by default) the task raises
  an exception instead of passing a bad output on.

Usage:
    python 01_guardrails.py
    python 01_guardrails.py --ask-words 250     # ask for more than the limit and watch the retries
    python 01_guardrails.py --model gpt-4o-mini
"""

import argparse
from pathlib import Path
from typing import Any

from crewai import Agent, Crew, Task, TaskOutput
from dotenv import load_dotenv

from llm import build_llm

HERE = Path(__file__).parent
MAX_WORDS = 150


def validate_summary_length(output: TaskOutput) -> tuple[bool, Any]:
    """Accept summaries of 1 to MAX_WORDS words."""
    words = len(output.raw.split())
    print(f"\n🛡️  Guardrail: the summary has {words} words (limit {MAX_WORDS}).")

    if words == 0:
        return False, "The summary is empty. Write a summary of the paper."
    if words > MAX_WORDS:
        return False, (
            f"The summary has {words} words but the limit is {MAX_WORDS}. Rewrite it in at "
            f"most {MAX_WORDS} words, keeping only the problem, the method and the main result."
        )

    print("🛡️  Guardrail: accepted.\n")
    return True, output


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Validate a summary's length with a guardrail.")
    parser.add_argument("--paper", default="ImageNet Classification with Deep Convolutional Neural Networks (AlexNet)")
    parser.add_argument(
        "--ask-words",
        type=int,
        default=120,
        help=f"Length requested in the prompt; above {MAX_WORDS} the guardrail rejects the output",
    )
    parser.add_argument("--retries", type=int, default=3, help="guardrail_max_retries for the task")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    llm = build_llm(args.model)

    summarizer = Agent(
        role="Research Paper Summarizer",
        goal="Summarize research papers accurately and concisely.",
        backstory="You read machine learning papers and explain their contribution in plain words.",
        llm=llm,
        verbose=True,
    )

    summary_task = Task(
        description=f"Summarize the research paper '{args.paper}' in about {args.ask_words} words.",
        expected_output=f"A single-paragraph summary of about {args.ask_words} words.",
        agent=summarizer,
        guardrail=validate_summary_length,
        guardrail_max_retries=args.retries,
    )

    crew = Crew(agents=[summarizer], tasks=[summary_task], verbose=True)

    try:
        result = crew.kickoff()
    except Exception as error:  # raised once the retries are exhausted
        print(f"\n❌ The guardrail rejected every attempt:\n   {error}")
        return

    print("\n" + "=" * 60)
    print(result.raw)
    print("=" * 60)
    print(f"Retries needed: {summary_task.retry_count}")


if __name__ == "__main__":
    main()

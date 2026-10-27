"""
02 · Guardrails on structured output: validate the content, not just the shape.

    analyst ──▶ ResearchReport ──▶ check_report (code) ──▶ "findings are specific" (LLM) ──▶ result
                (output_pydantic)        guardrail 1               guardrail 2

* `output_pydantic=ResearchReport` already guarantees the *shape*: CrewAI
  parses the answer into the model and fails if a required field is missing.
  A guardrail that only re-checks the JSON keys would add nothing.
* Guardrails are useful for the *content* rules a schema cannot express:
  how many findings, how long the summary is, whether they are specific.
* `guardrails=[...]` runs several guardrails in order. Each one can be a
  Python function (deterministic and free) or a string, which CrewAI turns into
  an LLM-based guardrail that uses the agent's model to judge the output.

Usage:
    python 02_structured_guardrails.py
    python 02_structured_guardrails.py --paper "Attention Is All You Need"
    python 02_structured_guardrails.py --no-llm-guardrail    # only the Python guardrail
"""

import argparse
from pathlib import Path
from typing import Any

from crewai import Agent, Crew, Task, TaskOutput
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from llm import build_llm

HERE = Path(__file__).parent

MIN_FINDINGS, MAX_FINDINGS = 3, 5
MAX_SUMMARY_WORDS = 80


class ResearchReport(BaseModel):
    """A structured report about one research paper."""

    title: str = Field(..., description="The paper's title.")
    summary: str = Field(..., description=f"What the paper does and why it matters, in at most {MAX_SUMMARY_WORDS} words.")
    key_findings: list[str] = Field(
        ..., description=f"Between {MIN_FINDINGS} and {MAX_FINDINGS} concrete findings or contributions."
    )


def check_report(output: TaskOutput) -> tuple[bool, Any]:
    """Rules the schema cannot express: number of findings and summary length."""
    report = output.pydantic
    if not isinstance(report, ResearchReport):
        return False, "Return the report following the ResearchReport schema."

    findings = [f for f in report.key_findings if f.strip()]
    summary_words = len(report.summary.split())
    print(f"\n🛡️  Guardrail 1: {len(findings)} findings, summary of {summary_words} words.")

    if not MIN_FINDINGS <= len(findings) <= MAX_FINDINGS:
        return False, (
            f"key_findings has {len(findings)} items; it must have between {MIN_FINDINGS} and "
            f"{MAX_FINDINGS} non-empty findings."
        )
    if summary_words > MAX_SUMMARY_WORDS:
        return False, f"The summary has {summary_words} words; shorten it to at most {MAX_SUMMARY_WORDS}."

    return True, output


SPECIFIC_FINDINGS = (
    "Every key finding must be a specific claim about this paper (a method, a number, a "
    "comparison or a concrete result), not a generic statement that could describe any paper."
)


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Guardrails on top of structured output.")
    parser.add_argument("--paper", default="Deep Residual Learning for Image Recognition (ResNet)")
    parser.add_argument("--no-llm-guardrail", action="store_true", help="Skip the LLM-based guardrail")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    llm = build_llm(args.model, temperature=0.2)

    analyst = Agent(
        role="Research Analyst",
        goal="Produce precise, structured reports about research papers.",
        backstory="You are an expert in technical writing who never pads a report with generic claims.",
        llm=llm,
        verbose=True,
    )

    guardrails: list = [check_report]
    if not args.no_llm_guardrail:
        guardrails.append(SPECIFIC_FINDINGS)  # a string becomes an LLM-based guardrail

    report_task = Task(
        description=f"Write a structured report about the research paper '{args.paper}'.",
        expected_output="A report with the paper's title, a short summary and its key findings.",
        agent=analyst,
        output_pydantic=ResearchReport,
        guardrails=guardrails,  # run in order; each must pass
        guardrail_max_retries=3,
    )

    crew = Crew(agents=[analyst], tasks=[report_task], verbose=True)

    try:
        result = crew.kickoff()
    except Exception as error:
        print(f"\n❌ The report did not pass the guardrails:\n   {error}")
        return

    report: ResearchReport = result.pydantic
    print("\n" + "=" * 60)
    print(f"# {report.title}\n\n{report.summary}\n")
    for finding in report.key_findings:
        print(f"- {finding}")
    print("=" * 60)


if __name__ == "__main__":
    main()

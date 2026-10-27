"""
03 · Task outputs and context: reuse earlier results instead of regenerating them.

    research_task ──▶ analysis_task ──▶ blog_task
         │      (default: previous task)    ▲
         └──────────── context ─────────────┘   blog_task reads both outputs

* Every task stores its result in `task.output`, a `TaskOutput` with:
  `raw` (text), `pydantic` / `json_dict` (structured output, if any),
  `agent` (who ran it), `description` and `summary` (first words of it).
* In a sequential crew a task receives the output of the task right before it
  by default. `context=[...]` lists exactly which outputs a task receives,
  which is how the blog task gets both the research and the analysis.
* After `kickoff()`, each task's output can be inspected individually, which is
  very handy for debugging long pipelines.

Usage:
    python 03_task_outputs.py
    python 03_task_outputs.py --topic "Small language models" --model gpt-4o-mini
"""

import argparse
from pathlib import Path

from crewai import Agent, Crew, Task
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from llm import build_llm

HERE = Path(__file__).parent


class ResearchFindings(BaseModel):
    title: str = Field(..., description="A short title for the research.")
    key_findings: list[str] = Field(..., description="Five to seven recent developments, one sentence each.")


class AnalysisSummary(BaseModel):
    insights: list[str] = Field(..., description="Three to five insights drawn from the findings.")
    key_takeaway: str = Field(..., description="The single most important conclusion, in one or two sentences.")


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Chain tasks with context and inspect their outputs.")
    parser.add_argument("--topic", default="AI agents")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    llm = build_llm(args.model)

    researcher = Agent(
        role="AI Researcher",
        goal=f"Find and summarize the latest advancements in {args.topic}.",
        backstory="You follow the field closely and separate real progress from hype.",
        llm=llm,
    )
    analyst = Agent(
        role="AI Analyst",
        goal="Extract the insights that matter from research findings.",
        backstory="You are a data analyst who turns lists of facts into clear conclusions.",
        llm=llm,
    )
    writer = Agent(
        role="Tech Writer",
        goal=f"Write a well-structured blog post about {args.topic}.",
        backstory="You turn complex research into readable articles without losing accuracy.",
        llm=llm,
    )

    research_task = Task(
        description=f"Find and summarize the latest advancements in {args.topic}.",
        expected_output="A title and a list of recent developments.",
        agent=researcher,
        output_pydantic=ResearchFindings,
    )
    analysis_task = Task(
        description="Analyze the research findings and extract the key insights.",
        expected_output="A list of insights and the key takeaway.",
        agent=analyst,
        output_pydantic=AnalysisSummary,
        # context=[research_task] is implied: by default a task sees the previous one.
    )
    blog_task = Task(
        description=(
            f"Write a blog post about {args.topic} of about 400 words. Use the research findings "
            "for the facts and the analysis for the angle and the conclusion."
        ),
        expected_output="A blog post in Markdown with a title, an introduction, 2–3 sections and a conclusion.",
        agent=writer,
        context=[research_task, analysis_task],  # both earlier outputs, explicitly
        markdown=True,
    )

    crew = Crew(agents=[researcher, analyst, writer], tasks=[research_task, analysis_task, blog_task], verbose=True)
    result = crew.kickoff()

    print("\n" + "=" * 60)
    print(result.raw)
    print("=" * 60)

    # ── Inspect the output of each task ───────────────────────────────────────
    print("\nOutputs of each task (task.output):\n")
    for task in crew.tasks:
        out = task.output
        print(f"• {out.agent}  [{out.output_format.value}]")
        print(f"    summary : {out.summary}")
        print(f"    raw     : {out.raw[:100].replace(chr(10), ' ')}…")

    analysis: AnalysisSummary = analysis_task.output.pydantic
    print(f"\nStructured access: analysis_task.output.pydantic.key_takeaway\n    {analysis.key_takeaway}")


if __name__ == "__main__":
    main()

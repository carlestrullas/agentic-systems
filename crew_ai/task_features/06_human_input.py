"""
06 · Human in the loop: a person reviews each answer before the crew moves on.

    research_task ──▶ 👤 review ──▶ blog_task ──▶ 👤 review ──▶ final post
          ▲              │               ▲             │
          └── feedback ──┘               └─ feedback ──┘

* `human_input=True` makes the agent stop after its final answer and ask for
  feedback in the terminal.
* Type feedback and press Enter → the agent revises its answer with it and asks
  again. Press Enter on an empty line → the answer is approved and the crew
  continues. (Any text, even "looks good", counts as feedback.)
* Useful wherever a mistake would be expensive: reports that will be
  published, decisions with money or health involved, content sent to clients.

Usage:
    python 06_human_input.py
    python 06_human_input.py --topic "AI in healthcare" --model gpt-4o-mini
"""

import argparse
from datetime import date
from pathlib import Path

from crewai import Agent, Crew, Task
from dotenv import load_dotenv

from llm import build_llm

HERE = Path(__file__).parent
OUTPUT_FILE = HERE / "output" / "reviewed_blog_post.md"


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Review the agents' answers before the crew continues.")
    parser.add_argument("--topic", default="AI trends")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    llm = build_llm(args.model)
    year = date.today().year
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    researcher = Agent(
        role="Senior AI Researcher",
        goal=f"Identify and summarize the most important developments in {args.topic}.",
        backstory="An expert who tracks emerging AI trends and their real-world applications.",
        llm=llm,
        verbose=True,
    )
    content_strategist = Agent(
        role="Tech Content Strategist",
        goal="Turn research insights into an engaging, accurate blog post.",
        backstory="An experienced tech writer who makes AI accessible to a broad audience.",
        llm=llm,
        verbose=True,
    )

    research_task = Task(
        description=(
            f"Analyze the key developments in {args.topic} in {year}: innovations, "
            "breakthroughs and market shifts."
        ),
        expected_output="A structured research summary in Markdown with 5–7 key points.",
        agent=researcher,
        human_input=True,  # 👤 review the research before writing
    )
    blog_task = Task(
        description=(
            "Using the reviewed research, write an engaging blog post that highlights the most "
            "significant developments. Keep it informative and accessible."
        ),
        expected_output="A blog post in Markdown with a title and about 400 words.",
        agent=content_strategist,
        human_input=True,  # 👤 approve the post before it is saved
        markdown=True,
        output_file=str(OUTPUT_FILE),
    )

    print("👤 You will be asked to review each answer.")
    print("   Type feedback to request changes, or press Enter on an empty line to approve.\n")

    crew = Crew(agents=[researcher, content_strategist], tasks=[research_task, blog_task], verbose=True)
    result = crew.kickoff()

    print("\n" + "=" * 60)
    print(result.raw)
    print("=" * 60)
    print(f"\n✅ Approved post saved to {OUTPUT_FILE.relative_to(HERE)}")


if __name__ == "__main__":
    main()

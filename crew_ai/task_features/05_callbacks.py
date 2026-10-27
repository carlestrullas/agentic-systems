"""
05 · Callbacks: run your own code as soon as a task finishes.

    news_task ──▶ TaskOutput ──▶ save_news_digest(output)   (Task callback)
                           └──▶ log_task(output)            (Crew task_callback, every task)

* `Task(callback=fn)` calls `fn(task_output)` right after that task completes,
  before the next task starts: store the result, send a notification, trigger
  another script…
* `Crew(task_callback=fn)` does the same for every task of the crew, which is
  convenient for logging or monitoring a whole pipeline in one place.
* Callbacks are plain Python: they do not call the LLM and cannot change the
  output (use a guardrail for that, see 01 and 02).

Usage:
    python 05_callbacks.py
    python 05_callbacks.py --topic "open-weight LLMs" --model gpt-4o-mini
"""

import argparse
from datetime import datetime
from pathlib import Path

from crewai import Agent, Crew, Task, TaskOutput
from dotenv import load_dotenv

from llm import build_llm

HERE = Path(__file__).parent
OUTPUT_DIR = HERE / "output"
DIGEST_FILE = OUTPUT_DIR / "news_digest.md"
LOG_FILE = OUTPUT_DIR / "tasks.log"


def save_news_digest(output: TaskOutput) -> None:
    """Task callback: save the digest and notify that it is ready."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    DIGEST_FILE.write_text(output.raw, encoding="utf-8")
    print(f"\n🔔 News digest ready → {DIGEST_FILE.relative_to(HERE)}  ({len(output.raw.split())} words)")


def log_task(output: TaskOutput) -> None:
    """Crew-level callback: append one line per finished task to a log file."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} | {output.agent} | {output.summary}\n"
    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(line)
    print(f"📝 Logged → {LOG_FILE.relative_to(HERE)}")


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Run code automatically when a task finishes.")
    parser.add_argument("--topic", default="AI")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    llm = build_llm(args.model)

    news_researcher = Agent(
        role="AI News Researcher",
        goal=f"Summarize the most important recent news about {args.topic}.",
        backstory="A journalist who follows the field closely and only reports what matters.",
        llm=llm,
    )

    news_task = Task(
        description=f"Summarize the most important recent news and breakthroughs about {args.topic}.",
        expected_output="A Markdown digest with 5 headlines, each followed by a two-sentence summary.",
        agent=news_researcher,
        markdown=True,
        callback=save_news_digest,  # runs as soon as this task finishes
    )

    crew = Crew(agents=[news_researcher], tasks=[news_task], task_callback=log_task)
    crew.kickoff()


if __name__ == "__main__":
    main()

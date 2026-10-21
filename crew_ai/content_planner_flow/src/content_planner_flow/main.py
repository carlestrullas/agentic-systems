#!/usr/bin/env python
"""
ContentPlanningFlow: turn a blog post into a ready-to-publish social media plan.

    get_draft ──▶ select_platform ──"twitter"───▶ plan_twitter_thread ──┐
    (Firecrawl     (@router)       └─"linkedin"──▶ plan_linkedin_post ───┴─ or_ ──▶ save_plan
     or a file)                                    (PlanningCrew)                   (JSON)

Deterministic steps (scraping, routing, saving) are plain Python; the AI work
(analysing the post and writing in the author's style) is done by a crew whose
output is a validated Pydantic model.

Entry points (see [project.scripts] in pyproject.toml):

    crewai run                                     # same as: kickoff
    kickoff --url https://example.com/my-post --platform linkedin
    kickoff --draft path/to/post.md
    plot
    run_with_trigger '{"url": "https://example.com/my-post", "platform": "twitter"}'
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Literal

from crewai.flow.flow import Flow, listen, or_, router, start
from dotenv import load_dotenv
from pydantic import BaseModel

from content_planner_flow.crews.planning_crew.planning_crew import PlanningCrew
from content_planner_flow.llm import get_llm
from content_planner_flow.models import TWEET_MAX_CHARS, LinkedInPost, Thread
from content_planner_flow.scraper import scrape_to_markdown

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUT_DIR = PROJECT_ROOT / "output"
DRAFTS_DIR = OUTPUT_DIR / "drafts"

load_dotenv(PROJECT_ROOT / ".env")


class ContentPlanningState(BaseModel):
    source_url: str = ""  # if set, the post is scraped from this URL
    draft_path: str = str(ASSETS_DIR / "sample_draft.md")  # otherwise, this file is used
    platform: Literal["twitter", "linkedin"] = "twitter"
    path_to_example_threads: str = str(ASSETS_DIR / "example_threads.txt")
    path_to_example_linkedin: str = str(ASSETS_DIR / "example_linkedin.txt")


class ContentPlanningFlow(Flow[ContentPlanningState]):
    # ── 1. Get the draft: no agents needed, just Python ──────────────────────

    @start()
    def get_draft(self) -> None:
        if self.state.source_url:
            print(f"🌐 Scraping {self.state.source_url} with Firecrawl...")
            self.state.draft_path = str(scrape_to_markdown(self.state.source_url, DRAFTS_DIR))
        print(f"📄 Draft: {self.state.draft_path}\n")

    # ── 2. Route to the selected platform ─────────────────────────────────────

    @router(get_draft)
    def select_platform(self) -> str:
        return self.state.platform

    # ── 3. Plan the content with the crew ─────────────────────────────────────

    def _run_crew(self) -> BaseModel:
        result = (
            PlanningCrew(llm=get_llm(), platform=self.state.platform)
            .crew()
            .kickoff(
                inputs={
                    "draft_path": self.state.draft_path,
                    "path_to_example_threads": self.state.path_to_example_threads,
                    "path_to_example_linkedin": self.state.path_to_example_linkedin,
                }
            )
        )
        if result.pydantic is None:
            raise SystemExit(f"The model did not return valid structured output:\n{result.raw}")
        return result.pydantic

    @listen("twitter")
    def plan_twitter_thread(self) -> Thread:
        thread: Thread = self._run_crew()
        print(f"\n🧵 Thread: {thread.topic}\n")
        for i, tweet in enumerate(thread.tweets, 1):
            warning = f"  ⚠️ {len(tweet.content)} chars" if len(tweet.content) > TWEET_MAX_CHARS else ""
            print(f"Tweet {i}{' (hook)' if tweet.is_hook else ''}:{warning}\n{tweet.content}")
            if tweet.media_urls:
                print(f"Media: {', '.join(tweet.media_urls)}")
            print("-" * 60)
        return thread

    @listen("linkedin")
    def plan_linkedin_post(self) -> LinkedInPost:
        post: LinkedInPost = self._run_crew()
        print(f"\n💼 LinkedIn post:\n\n{post.content}")
        if post.media_url:
            print(f"\nMedia: {post.media_url}")
        return post

    # ── 4. Save the plan, whichever branch produced it ────────────────────────

    @listen(or_(plan_twitter_thread, plan_linkedin_post))
    def save_plan(self, plan: BaseModel) -> str:
        OUTPUT_DIR.mkdir(exist_ok=True)
        path = OUTPUT_DIR / f"{Path(self.state.draft_path).stem}_{self.state.platform}.json"
        path.write_text(json.dumps(plan.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n✅ Plan saved to {path.relative_to(PROJECT_ROOT)}")
        return str(path)


def _run(source_url: str | None = None, draft: str | None = None, platform: str | None = None) -> str:
    inputs: dict[str, str] = {}
    if source_url:
        inputs["source_url"] = source_url
    if draft:
        inputs["draft_path"] = str(Path(draft).resolve())
    if platform:
        inputs["platform"] = platform
    return ContentPlanningFlow().kickoff(inputs=inputs or None)


def kickoff() -> None:
    """Run the flow. Used by `crewai run` and by the `kickoff` script."""
    parser = argparse.ArgumentParser(description="Turn a blog post into a Twitter thread or a LinkedIn post.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--url", help="Blog post URL to scrape with Firecrawl")
    source.add_argument("--draft", help="Local Markdown file to use instead (default: assets/sample_draft.md)")
    parser.add_argument("--platform", choices=["twitter", "linkedin"], default="twitter")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args, _ = parser.parse_known_args()
    if args.model:
        os.environ["MODEL"] = args.model
    if args.draft and not Path(args.draft).is_file():
        raise SystemExit(f"Draft not found: {args.draft}")
    _run(args.url, args.draft, args.platform)


def plot() -> None:
    """Save (and open) an interactive HTML diagram of the flow."""
    ContentPlanningFlow().plot("content_planner_flow.html")


def run_with_trigger() -> str:
    """Run the flow from a JSON payload with "url" (or "draft") and "platform"."""
    if len(sys.argv) < 2:
        raise SystemExit("No trigger payload provided. Pass a JSON object as argument.")
    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise SystemExit("Invalid JSON payload provided as argument.")
    return _run(payload.get("url"), payload.get("draft"), payload.get("platform"))


if __name__ == "__main__":
    kickoff()

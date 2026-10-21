"""
PlanningCrew: turns a blog post into a social media content plan.

One crew definition serves both platforms. The YAML defines three agents (a
draft analyzer shared by both platforms, plus one planner per platform); the
`platform` argument picks which planner joins the analyzer in the crew:

    twitter:  draft_analyzer ──▶ twitter_thread_planner  ──▶ Thread
    linkedin: draft_analyzer ──▶ linkedin_post_planner   ──▶ LinkedInPost

All agents get `FileReadTool`, the only tool they need: the analyzer reads the
draft and the planners read the examples of the author's style.
"""

from typing import Literal

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool

from content_planner_flow.models import LinkedInPost, Thread

Platform = Literal["twitter", "linkedin"]


@CrewBase
class PlanningCrew:
    """Draft analyzer + a platform-specific planner with structured output."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm: LLM, platform: Platform, verbose: bool = True) -> None:
        self.llm = llm
        self.platform = platform
        self.verbose = verbose

    def _agent(self, name: str) -> Agent:
        return Agent(
            config=self.agents_config[name],
            tools=[FileReadTool()],
            llm=self.llm,
            allow_delegation=False,
            max_iter=8,
            verbose=self.verbose,
        )

    # ── Agents ────────────────────────────────────────────────────────────────

    @agent
    def draft_analyzer(self) -> Agent:
        return self._agent("draft_analyzer")

    @agent
    def twitter_thread_planner(self) -> Agent:
        return self._agent("twitter_thread_planner")

    @agent
    def linkedin_post_planner(self) -> Agent:
        return self._agent("linkedin_post_planner")

    # ── Tasks ─────────────────────────────────────────────────────────────────

    @task
    def analyze_draft(self) -> Task:
        return Task(config=self.tasks_config["analyze_draft"])

    @task
    def create_twitter_thread_plan(self) -> Task:
        return Task(config=self.tasks_config["create_twitter_thread_plan"], output_pydantic=Thread)

    @task
    def create_linkedin_post_plan(self) -> Task:
        return Task(config=self.tasks_config["create_linkedin_post_plan"], output_pydantic=LinkedInPost)

    # ── Crew ──────────────────────────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        if self.platform == "twitter":
            planner, plan_task = self.twitter_thread_planner(), self.create_twitter_thread_plan()
        else:
            planner, plan_task = self.linkedin_post_planner(), self.create_linkedin_post_plan()

        # Only the analyzer and the selected planner take part in this run.
        return Crew(
            agents=[self.draft_analyzer(), planner],
            tasks=[self.analyze_draft(), plan_task],
            process=Process.sequential,
            verbose=self.verbose,
        )

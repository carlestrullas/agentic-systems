"""
ProjectResearchCrew: a hierarchical crew in which a manager agent delegates.

With `Process.hierarchical` the tasks are not run by a fixed agent. CrewAI
gives every task to the `manager_agent`, which has two delegation tools
("delegate work to coworker" and "ask question to coworker") and decides which
specialist should do each one, reviews the answer and can send it back.

* The specialists are registered with `@agent`, so they end up in `self.agents`.
* The manager is built by a plain method (no `@agent`) and passed as
  `manager_agent`: CrewAI rejects a crew whose manager is also in `agents`.
* The manager has no tools of its own; it works only through delegation.
"""

from pathlib import Path

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from llm import is_set

OUTPUT_DIR = Path(__file__).parent / "output"


@CrewBase
class ProjectResearchCrew:
    """Manager → market, risk and ROI analysts → final report."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm: LLM, use_search: bool = True, verbose: bool = True) -> None:
        self.llm = llm
        self.verbose = verbose
        self.search_tools = self._build_search_tools() if use_search else []

    @staticmethod
    def _build_search_tools() -> list:
        """Web search through Serper. Without a key the analysts use the model's own knowledge."""
        if not is_set("SERPER_API_KEY"):
            print(
                "⚠️  SERPER_API_KEY not set: running WITHOUT web search. The analysts will rely "
                "on the model's own (possibly outdated) knowledge.\n"
            )
            return []

        from crewai_tools import SerperDevTool

        return [SerperDevTool(n_results=6)]

    def _specialist(self, name: str) -> Agent:
        return Agent(
            config=self.agents_config[name],
            tools=self.search_tools,
            llm=self.llm,
            allow_delegation=False,  # specialists execute; only the manager delegates
            max_iter=10,
            verbose=self.verbose,
        )

    # ── Manager (not an @agent: it is passed as manager_agent) ────────────────

    def manager(self) -> Agent:
        return Agent(
            config=self.agents_config["manager"],
            llm=self.llm,
            allow_delegation=True,
            verbose=self.verbose,
        )

    # ── Specialists ───────────────────────────────────────────────────────────

    @agent
    def market_analyst(self) -> Agent:
        return self._specialist("market_analyst")

    @agent
    def risk_analyst(self) -> Agent:
        return self._specialist("risk_analyst")

    @agent
    def roi_analyst(self) -> Agent:
        return self._specialist("roi_analyst")

    # ── Tasks (no fixed agent: the manager assigns them) ──────────────────────

    @task
    def market_demand_task(self) -> Task:
        return Task(config=self.tasks_config["market_demand_task"], output_file=str(OUTPUT_DIR / "1_market_demand.md"))

    @task
    def risk_analysis_task(self) -> Task:
        return Task(config=self.tasks_config["risk_analysis_task"], output_file=str(OUTPUT_DIR / "2_risk_analysis.md"))

    @task
    def roi_task(self) -> Task:
        return Task(config=self.tasks_config["roi_task"], output_file=str(OUTPUT_DIR / "3_roi.md"))

    @task
    def final_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_report_task"],
            output_file=str(OUTPUT_DIR / "4_final_report.md"),
            markdown=True,
        )

    # ── Crew ──────────────────────────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # the specialists only
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.manager(),
            verbose=self.verbose,
        )

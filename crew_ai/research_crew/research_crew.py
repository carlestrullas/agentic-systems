"""
ResearchCrew: a modular, class-based CrewAI crew.

The `@CrewBase` decorator turns the class into a crew definition:

* `agents_config` / `tasks_config` point to YAML files (relative to this file)
  that CrewAI loads automatically into dictionaries.
* Each method decorated with `@agent` or `@task` builds one Agent or Task from
  its YAML entry via `config=...`. Anything passed explicitly (llm, tools,
  output_file...) takes precedence over the YAML.
* The `@crew` method assembles the crew; `self.agents` and `self.tasks` are
  filled in automatically, in the order the methods are defined.

Because it is a class, it can be instantiated several times with different
LLMs or options:

    ResearchCrew(llm=build_llm("ollama/llama3.1:8b")).crew().kickoff(inputs={...})
"""

from pathlib import Path

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from llm import is_set

OUTPUT_DIR = Path(__file__).parent / "output"


@CrewBase
class ResearchCrew:
    """Researcher → summarizer → fact-checker, with prompts defined in YAML."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm: LLM, use_search: bool = True, verbose: bool = True) -> None:
        self.llm = llm
        self.verbose = verbose
        self.search_tools = self._build_search_tools() if use_search else []

    @staticmethod
    def _build_search_tools() -> list:
        """Web search through Serper. Without a key the agents use the model's own knowledge."""
        if not is_set("SERPER_API_KEY"):
            print(
                "⚠️  SERPER_API_KEY not set: running WITHOUT web search. The researcher and the "
                "fact-checker will rely on the model's own (possibly outdated) knowledge.\n"
            )
            return []

        from crewai_tools import SerperDevTool

        return [SerperDevTool(n_results=8)]

    def _agent(self, name: str, tools: list) -> Agent:
        return Agent(
            config=self.agents_config[name],
            tools=tools,
            llm=self.llm,
            allow_delegation=False,
            max_iter=10,
            verbose=self.verbose,
        )

    # ── Agents ────────────────────────────────────────────────────────────────
    # Only the agents that need to search get the search tool.

    @agent
    def researcher(self) -> Agent:
        return self._agent("researcher", self.search_tools)

    @agent
    def summarizer(self) -> Agent:
        return self._agent("summarizer", [])

    @agent
    def fact_checker(self) -> Agent:
        return self._agent("fact_checker", self.search_tools)

    # ── Tasks ─────────────────────────────────────────────────────────────────
    # The agent and the context of each task come from tasks.yaml.

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],
            output_file=str(OUTPUT_DIR / "1_research_notes.md"),
            markdown=True,
        )

    @task
    def summary_task(self) -> Task:
        return Task(
            config=self.tasks_config["summary_task"],
            output_file=str(OUTPUT_DIR / "2_summary.md"),
            markdown=True,
        )

    @task
    def fact_check_task(self) -> Task:
        return Task(
            config=self.tasks_config["fact_check_task"],
            output_file=str(OUTPUT_DIR / "3_final_report.md"),
            markdown=True,
        )

    # ── Crew ──────────────────────────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=self.verbose,
        )

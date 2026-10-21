"""
OutlineCrew: researches the topic and designs the outline of the book.

    researcher (web search) ──▶ outline_writer ──▶ Outline(total_chapters, titles)
"""

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from book_writing_flow.models import Outline
from book_writing_flow.tools import search_tools


@CrewBase
class OutlineCrew:
    """Research the topic, then turn the insights into a chapter outline."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm: LLM, verbose: bool = True) -> None:
        self.llm = llm
        self.verbose = verbose

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            tools=search_tools(),
            llm=self.llm,
            allow_delegation=False,
            max_iter=8,
            verbose=self.verbose,
        )

    @agent
    def outline_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["outline_writer"],
            llm=self.llm,
            allow_delegation=False,
            verbose=self.verbose,
        )

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config["research_task"])

    @task
    def write_outline(self) -> Task:
        return Task(config=self.tasks_config["write_outline"], output_pydantic=Outline)

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=self.verbose,
        )

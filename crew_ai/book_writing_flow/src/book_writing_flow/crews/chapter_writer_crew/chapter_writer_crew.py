"""
ChapterWriterCrew: researches and writes one chapter of the book.

    chapter_researcher (web search) ──▶ chapter_writer ──▶ Chapter(title, content)

The flow creates one instance of this crew per chapter and runs them in
parallel, so the crew only ever deals with a single chapter.
"""

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from book_writing_flow.models import Chapter
from book_writing_flow.tools import search_tools


@CrewBase
class ChapterWriterCrew:
    """Research a chapter, then write it."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm: LLM, verbose: bool = True) -> None:
        self.llm = llm
        self.verbose = verbose

    @agent
    def chapter_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["chapter_researcher"],
            tools=search_tools(),
            llm=self.llm,
            allow_delegation=False,
            max_iter=8,
            verbose=self.verbose,
        )

    @agent
    def chapter_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["chapter_writer"],
            llm=self.llm,
            allow_delegation=False,
            verbose=self.verbose,
        )

    @task
    def research_chapter(self) -> Task:
        return Task(config=self.tasks_config["research_chapter"])

    @task
    def write_chapter(self) -> Task:
        return Task(config=self.tasks_config["write_chapter"], output_pydantic=Chapter)

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=self.verbose,
        )

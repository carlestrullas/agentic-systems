"""
ExtractorCrew: a class-based crew whose output is a validated Pydantic object.

The key line is `output_pydantic=KnowledgeGraph` in the task: instead of free
text (which may come wrapped in ```json fences or with small format drifts), the
crew returns a `KnowledgeGraph` instance available as `result.pydantic`.
"""

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from models import KnowledgeGraph


@CrewBase
class ExtractorCrew:
    """Turns unstructured text into subject-relation-object triplets."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm: LLM, verbose: bool = True) -> None:
        self.llm = llm
        self.verbose = verbose

    @agent
    def extractor(self) -> Agent:
        return Agent(
            config=self.agents_config["extractor"],
            llm=self.llm,
            allow_delegation=False,
            verbose=self.verbose,
        )

    @task
    def extraction_task(self) -> Task:
        return Task(
            config=self.tasks_config["extraction_task"],
            output_pydantic=KnowledgeGraph,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=self.verbose,
        )

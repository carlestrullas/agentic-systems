"""
QualityCrew: a class-based crew whose agent looks at an image.

Nothing in the agent or the task is image-specific: the image is attached at
kickoff with `input_files`, and CrewAI sends it to the model in the format its
provider expects (base64 or URL). What matters is that the LLM can see, i.e.
that it is a vision model.
"""

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from models import QualityReport


@CrewBase
class QualityCrew:
    """Inspects one product image and returns a QualityReport."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm: LLM, verbose: bool = True) -> None:
        self.llm = llm
        self.verbose = verbose

    @agent
    def inspector(self) -> Agent:
        return Agent(
            config=self.agents_config["inspector"],
            llm=self.llm,
            allow_delegation=False,
            verbose=self.verbose,
        )

    @task
    def inspection_task(self) -> Task:
        return Task(
            config=self.tasks_config["inspection_task"],
            output_pydantic=QualityReport,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=self.verbose,
        )

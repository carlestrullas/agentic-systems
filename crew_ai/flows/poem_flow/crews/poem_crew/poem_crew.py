"""
PoemCrew: a single-agent crew used as one step of PoemFlow.

It is a normal `@CrewBase` class; the flow does not need to know how the crew
works inside, only which inputs it expects ({topic}, {sentence_count}) and what
it returns. The LLM is injected from outside, so the same crew runs on Ollama
or on a hosted model.
"""

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class PoemCrew:
    """Writes a short poem about a topic with a given number of sentences."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm: LLM, verbose: bool = True) -> None:
        self.llm = llm
        self.verbose = verbose

    @agent
    def poem_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["poem_writer"],
            llm=self.llm,
            allow_delegation=False,
            verbose=self.verbose,
        )

    @task
    def write_poem(self) -> Task:
        return Task(config=self.tasks_config["write_poem"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=self.verbose,
        )

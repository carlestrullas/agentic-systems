"""
CurrencyCrew: two agents and a custom tool, defined as a class.

    "How much is 100 dollars in euros?"
            │
            ▼
    Query Analyst ──▶ ConversionRequest(amount=100, from_currency="USD", to_currency="EUR")
                              │   (structured output, validated by Pydantic)
                              ▼
    Currency Analyst ──▶ CurrencyConverterTool ──▶ live rate ──▶ final answer
"""

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from models import ConversionRequest
from tools import CurrencyConverterTool


@CrewBase
class CurrencyCrew:
    """Parses a free-text money question and answers it with live exchange rates."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm: LLM, verbose: bool = True) -> None:
        self.llm = llm
        self.verbose = verbose

    @agent
    def query_analyst(self) -> Agent:
        # No tools: its only job is to understand the question.
        return Agent(
            config=self.agents_config["query_analyst"],
            llm=self.llm,
            allow_delegation=False,
            verbose=self.verbose,
        )

    @agent
    def currency_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["currency_analyst"],
            tools=[CurrencyConverterTool()],
            llm=self.llm,
            allow_delegation=False,
            max_iter=5,
            verbose=self.verbose,
        )

    @task
    def parse_query_task(self) -> Task:
        return Task(
            config=self.tasks_config["parse_query_task"],
            output_pydantic=ConversionRequest,
        )

    @task
    def conversion_task(self) -> Task:
        return Task(config=self.tasks_config["conversion_task"], markdown=True)

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=self.verbose,
        )

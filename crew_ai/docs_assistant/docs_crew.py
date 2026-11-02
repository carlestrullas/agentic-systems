"""
DocsCrew: answers questions over a folder of documents.

* The documents are **crew knowledge** (`knowledge_sources` on the Crew), so
  they are embedded once when the crew is created and reused by every
  `kickoff()`: ask as many questions as you like with the same crew.
* The answer is a validated `Answer` object (`output_pydantic`), and a
  guardrail rejects answers whose cited documents do not exist or that claim
  to be grounded without citing anything.
"""

from typing import Any

from crewai import LLM, Agent, Crew, Process, Task, TaskOutput
from crewai.knowledge.knowledge_config import KnowledgeConfig
from crewai.project import CrewBase, agent, crew, task

from models import Answer
from sources import DocumentFolderSource


@CrewBase
class DocsCrew:
    """One documentation assistant with the whole folder as knowledge."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm: LLM, source: DocumentFolderSource, embedder: dict, verbose: bool = False) -> None:
        self.llm = llm
        self.source = source
        self.embedder = embedder
        self.verbose = verbose

    def check_sources(self, output: TaskOutput) -> tuple[bool, Any]:
        """Guardrail: cited documents must exist, and a grounded answer must cite at least one."""
        answer = output.pydantic
        if not isinstance(answer, Answer):
            return False, "Return the answer following the Answer schema."

        unknown = [name for name in answer.documents if name not in self.source.documents]
        if unknown:
            return False, (
                f"These documents do not exist: {unknown}. Cite only files from this list: "
                f"{list(self.source.documents)}."
            )
        if answer.found_in_documents and not answer.documents:
            return False, "found_in_documents is true, so list the documents the answer comes from."
        return True, output

    @agent
    def assistant(self) -> Agent:
        return Agent(
            config=self.agents_config["assistant"],
            llm=self.llm,
            allow_delegation=False,
            # Applies to the crew knowledge too (whose defaults are 3 chunks, score ≥ 0.35).
            # Questions often need several files, so let more chunks through.
            knowledge_config=KnowledgeConfig(results_limit=6, score_threshold=0.5),
            verbose=self.verbose,
        )

    @task
    def answer_task(self) -> Task:
        return Task(
            config=self.tasks_config["answer_task"],
            output_pydantic=Answer,
            guardrail=self.check_sources,
            guardrail_max_retries=2,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            knowledge_sources=[self.source],
            embedder=self.embedder,
            verbose=self.verbose,
        )

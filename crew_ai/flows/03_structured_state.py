"""
03 · Structured state: the flow state as a Pydantic model.

`Flow[TaskState]` tells CrewAI that `self.state` is an instance of `TaskState`.
CrewAI adds the `id` field automatically. Fields are accessed as attributes
(`self.state.status`), editors can autocomplete them, and assigning a field that
is not declared in the model raises an error instead of silently creating it.

No LLM is needed for this example.

Usage:
    python 03_structured_state.py
    python 03_structured_state.py --undeclared-field   # shows the validation error
"""

import argparse

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel


class TaskState(BaseModel):
    task: str = ""
    status: str = ""


class StructuredTaskFlow(Flow[TaskState]):
    @start()
    def generate_task(self) -> None:
        print(f"Flow started. State ID: {self.state.id}\n")
        self.state.task = "Develop a new API endpoint"
        self.state.status = "Pending"
        print(f"Task generated: {self.state.task} (status: {self.state.status})")

    @listen(generate_task)
    def start_task(self) -> None:
        self.state.status = "In Progress"
        print(f"Status updated: {self.state.status}")

    @listen(start_task)
    def complete_task(self) -> None:
        self.state.status = "Completed"
        print(f"Status updated: {self.state.status}")


class UndeclaredFieldFlow(Flow[TaskState]):
    """Tries to store a field that TaskState does not declare."""

    @start()
    def generate_task(self) -> None:
        self.state.task = "Develop a new API endpoint"
        self.state.priority = "High"  # not in TaskState → error


def main() -> None:
    parser = argparse.ArgumentParser(description="Structured (Pydantic) flow state.")
    parser.add_argument(
        "--undeclared-field",
        action="store_true",
        help="Run a flow that assigns a field missing from the state model",
    )
    args = parser.parse_args()

    if args.undeclared_field:
        try:
            UndeclaredFieldFlow().kickoff()
        except (ValueError, AttributeError) as error:
            print(f"❌ The flow failed, as expected:\n   {error}")
        return

    flow = StructuredTaskFlow()
    flow.kickoff()
    print(f"\nFinal state: {flow.state.model_dump()}")


if __name__ == "__main__":
    main()

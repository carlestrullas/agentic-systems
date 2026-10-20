"""
02 · Unstructured state: the flow state as a free-form dictionary.

    generate_task ──▶ start_task ──▶ complete_task
    status: Pending   In Progress    Completed

Every step reads and updates `self.state` like a normal dict. Keys can be added
at any moment, which is flexible and quick for prototypes, but nothing stops a
typo such as `self.state["staus"]` from silently creating a new key.

No LLM is needed for this example.

Usage:
    python 02_unstructured_state.py
"""

from pprint import pprint

from crewai.flow.flow import Flow, listen, start


class TaskManagementFlow(Flow):
    @start()
    def generate_task(self) -> None:
        print(f"Flow started. State ID: {self.state['id']}\n")
        self.state["task"] = "Fix a critical bug in the payment system"
        self.state["status"] = "Pending"
        print(f"Task generated: {self.state['task']} (status: {self.state['status']})")

    @listen(generate_task)
    def start_task(self) -> None:
        self.state["status"] = "In Progress"
        self.state["assignee"] = "on-call engineer"  # a new key, added on the fly
        print(f"Status updated: {self.state['status']} (assigned to {self.state['assignee']})")

    @listen(start_task)
    def complete_task(self) -> None:
        self.state["status"] = "Completed"
        print(f"Status updated: {self.state['status']}")


def main() -> None:
    flow = TaskManagementFlow()
    flow.kickoff()

    print("\nFinal state:")
    pprint(flow.state)


if __name__ == "__main__":
    main()

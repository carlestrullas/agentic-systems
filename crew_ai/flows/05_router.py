"""
05 · Routing with @router(): choose the next step at run time.

    classify_ticket ──▶ route_ticket ──"urgent_support"──▶ assign_to_agent
       (@start)          (@router)   └──"email_support"───▶ send_to_email_queue

* The @router(...) method runs after classify_ticket and returns a string.
* Only the listener whose @listen("<label>") matches that string runs next.

The priority is decided in one of two ways:

* With --ticket "...": an LLM reads the ticket and classifies it (AI-driven
  decision inside a deterministic workflow).
* Without it: the priority is chosen at random, so no LLM is needed.

The ticket text is passed with kickoff(inputs=...), which fills the matching
fields of the structured state.

Usage:
    python 05_router.py
    python 05_router.py --ticket "Our checkout page is down and customers cannot pay!"
    python 05_router.py --ticket "How do I change my invoice address?" --model gpt-4o-mini
"""

import argparse
import os
import random
from pathlib import Path

from crewai.flow.flow import Flow, listen, router, start
from dotenv import load_dotenv
from pydantic import BaseModel

HERE = Path(__file__).parent

CLASSIFICATION_PROMPT = (
    "You triage customer support tickets. Classify the ticket below as 'high' "
    "priority if the customer is blocked, losing money, or reports an outage or "
    "security problem; otherwise classify it as 'low'. Answer with exactly one "
    "word: high or low.\n\nTicket: {ticket}"
)


class TicketState(BaseModel):
    ticket: str = ""
    priority: str = "low"


class TicketRoutingFlow(Flow[TicketState]):
    @start()
    def classify_ticket(self) -> None:
        if self.state.ticket:
            from llm import get_llm  # only needed when an LLM classifies the ticket

            print(f"Classifying ticket with the LLM: {self.state.ticket!r}")
            answer = get_llm().call(CLASSIFICATION_PROMPT.format(ticket=self.state.ticket))
            self.state.priority = "high" if "high" in answer.lower() else "low"
        else:
            print("No ticket text given: choosing a random priority.")
            self.state.priority = random.choice(["high", "low"])

        print(f"Ticket classified as: {self.state.priority}")

    @router(classify_ticket)
    def route_ticket(self) -> str:
        return "urgent_support" if self.state.priority == "high" else "email_support"

    @listen("urgent_support")
    def assign_to_agent(self) -> None:
        print("🚨 Urgent ticket assigned to a live support agent!")

    @listen("email_support")
    def send_to_email_queue(self) -> None:
        print("📧 Non-urgent ticket sent to the email support queue.")


def main() -> None:
    load_dotenv(HERE / ".env")

    parser = argparse.ArgumentParser(description="Route a support ticket with @router().")
    parser.add_argument("--ticket", help="Ticket text to classify with the LLM")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    parser.add_argument("--plot", action="store_true", help="Save (and open) an interactive HTML diagram of the flow")
    args = parser.parse_args()
    if args.model:
        os.environ["MODEL"] = args.model

    flow = TicketRoutingFlow()
    if args.plot:
        flow.plot("05_router.html")

    flow.kickoff(inputs={"ticket": args.ticket} if args.ticket else None)


if __name__ == "__main__":
    main()

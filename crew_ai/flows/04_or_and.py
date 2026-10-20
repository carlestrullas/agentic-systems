"""
04 · Conditional triggers with or_() and and_().

OR — a support request can arrive through two channels; it is logged as soon as
either of them produces one:

    live_chat_request ─┐
                       ├─ or_ ──▶ log_request
    email_ticket_request ┘

AND — a ticket is escalated only when BOTH the user has confirmed the issue and
an agent has reviewed it:

    user_confirms_issue ──▶ agent_reviews_ticket
             │                      │
             └──────── and_ ────────┴──▶ escalate_ticket

No LLM is needed for this example.

Usage:
    python 04_or_and.py            # runs both demos
    python 04_or_and.py --demo or
    python 04_or_and.py --demo and
"""

import argparse

from crewai.flow.flow import Flow, and_, listen, or_, start


class SupportFlow(Flow):
    @start()
    def live_chat_request(self) -> str:
        return "Support request received via live chat"

    @start()
    def email_ticket_request(self) -> str:
        return "Support request received via email ticket"

    @listen(or_(live_chat_request, email_ticket_request))
    def log_request(self, request_source: str) -> None:
        print(f"📝 Logging request: {request_source}")


class TicketEscalationFlow(Flow):
    @start()
    def user_confirms_issue(self) -> None:
        self.state["user_confirmation"] = True
        print("✅ User confirmed they still need assistance.")

    @listen(user_confirms_issue)
    def agent_reviews_ticket(self) -> None:
        self.state["agent_review"] = True
        print("✅ Support agent has reviewed the ticket.")

    @listen(and_(user_confirms_issue, agent_reviews_ticket))
    def escalate_ticket(self) -> None:
        print("🚨 Both conditions met: escalating ticket to Level 2 support!")


def main() -> None:
    parser = argparse.ArgumentParser(description="or_() and and_() triggers in CrewAI flows.")
    parser.add_argument("--demo", choices=["or", "and", "both"], default="both")
    args = parser.parse_args()

    if args.demo in ("or", "both"):
        print("── OR: log the request from whichever channel produces it ──")
        SupportFlow().kickoff()
        print()

    if args.demo in ("and", "both"):
        print("── AND: escalate only when both conditions are met ──")
        TicketEscalationFlow().kickoff()


if __name__ == "__main__":
    main()

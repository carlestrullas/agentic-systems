"""
01 · Knowledge from a string: ground the answers in your own text.

    policy text ──▶ chunks ──▶ embeddings ──▶ vector store
                                                   │  most similar chunks
    question ──▶ Returns Assistant ◀────────────────┘  added to the prompt ──▶ answer

* `StringKnowledgeSource(content=...)` turns a piece of text into knowledge.
* `Crew(knowledge_sources=[...])` makes it available to every agent of the
  crew. Before each task CrewAI rewrites the task into a search query, finds
  the most relevant chunks and adds them to the agent's prompt (RAG), with no
  tool call and no retrieval agent needed.
* `Crew(embedder=...)` chooses the embedding model (see knowledge_setup.py).

Run it with --no-knowledge to see the same question answered from the model's
general knowledge: a plausible but invented policy.

Usage:
    python 01_string_knowledge.py
    python 01_string_knowledge.py --question "Do I need the receipt to return a product?"
    python 01_string_knowledge.py --no-knowledge
"""

import argparse

from knowledge_setup import build_embedder, reset_knowledge, storage_path  # before crewai: it sets the storage

from crewai import Agent, Crew, Process, Task
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource

from llm import build_llm

RETURN_POLICY = """
Lumen Store return policy (updated September 2026):
- Customers can return any product within 30 days of delivery.
- Refunds are issued only if the item is unused and in its original packaging.
  Used items can be exchanged for store credit within 14 days, never refunded.
- A proof of purchase (order number or receipt) is always required.
- Refunds go back to the original payment method within 5 working days.
- Personalised products and gift cards cannot be returned.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Answer questions grounded in a string knowledge source.")
    parser.add_argument("--question", default="Can I get a refund if I used the item once?")
    parser.add_argument("--no-knowledge", action="store_true", help="Answer without the policy, to compare")
    parser.add_argument("--reset", action="store_true", help="Re-embed the knowledge from scratch")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    if args.reset:
        reset_knowledge()

    llm = build_llm(args.model, temperature=0)

    returns_agent = Agent(
        role="Product Returns Assistant",
        goal="Answer customer questions about returns and refunds accurately.",
        backstory=(
            "You work in customer service and specialise in returns and refunds. "
            "You answer according to the store's policy and never promise anything it does not allow."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )

    returns_task = Task(
        description="Answer this customer question about returns: {question}",
        expected_output="A short, friendly and accurate answer in two or three sentences.",
        agent=returns_agent,
    )

    knowledge = {} if args.no_knowledge else {
        "knowledge_sources": [StringKnowledgeSource(content=RETURN_POLICY)],  # shared by every agent
        "embedder": build_embedder(),
    }

    crew = Crew(
        agents=[returns_agent],
        tasks=[returns_task],
        process=Process.sequential,
        verbose=True,
        **knowledge,
    )
    result = crew.kickoff(inputs={"question": args.question})

    print("\n" + "=" * 60)
    print(f"Q: {args.question}\n")
    print(result.raw)
    print("=" * 60)
    print("(answered WITHOUT knowledge)" if args.no_knowledge else f"Vector store: {storage_path()}")


if __name__ == "__main__":
    main()

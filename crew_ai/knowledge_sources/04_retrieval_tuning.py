"""
04 · Look inside retrieval: chunks, the search query and the scores.

    files ──▶ chunks (chunk_size, chunk_overlap) ──▶ vector store
                                                          │
    task ──▶ LLM rewrites it as a search query ──▶ top results_limit chunks
                                                   with score ≥ score_threshold ──▶ prompt

Knowledge is RAG done for you, and these are its knobs:

* `chunk_size` / `chunk_overlap` (on each source, in characters): the default
  is 4000 / 200, so small files become a single chunk. Smaller chunks make
  retrieval more precise but each one carries less context.
* `KnowledgeConfig(results_limit=..., score_threshold=...)` (on the agent):
  how many chunks are added to the prompt, and how similar (0–1) they must be.
* The search query is not the task text: the agent's LLM first rewrites the
  task into a short query. A listener on `KnowledgeRetrievalCompletedEvent`
  prints it, and after the run the same query is sent to the store again to
  show each chunk with its score.

Usage:
    python 04_retrieval_tuning.py
    python 04_retrieval_tuning.py --chunk-size 150 --limit 2
    python 04_retrieval_tuning.py --threshold 0.8      # too strict: nothing gets through
"""

import argparse

from knowledge_setup import KNOWLEDGE_DIR, build_embedder, reset_knowledge  # before crewai: it sets the storage

from crewai import Agent, Crew, Process, Task
from crewai.events import BaseEventListener, KnowledgeRetrievalCompletedEvent
from crewai.knowledge.knowledge_config import KnowledgeConfig
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

from llm import build_llm


class RetrievalLogger(BaseEventListener):
    """Prints the search query CrewAI used each time an agent retrieves knowledge."""

    def setup_listeners(self, crewai_event_bus) -> None:
        @crewai_event_bus.on(KnowledgeRetrievalCompletedEvent)
        def on_retrieval(source, event: KnowledgeRetrievalCompletedEvent) -> None:
            print(f"\n🔎 [{event.agent_role}] search query: {event.query!r}")
            print(f"   {len(event.retrieved_knowledge)} characters of knowledge added to the prompt\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect and tune knowledge retrieval.")
    parser.add_argument("--question", default="How long before my holidays do I have to request two weeks off?")
    parser.add_argument("--chunk-size", type=int, default=300, help="Characters per chunk (CrewAI default: 4000)")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="Characters shared by consecutive chunks")
    parser.add_argument("--limit", type=int, default=3, help="results_limit: chunks added to the prompt")
    parser.add_argument("--threshold", type=float, default=0.6, help="score_threshold: minimum similarity (0-1)")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    # Chunking changes what is stored, so start from an empty store on every run.
    reset_knowledge()
    RetrievalLogger()  # registering the listener is enough

    chunking = {"chunk_size": args.chunk_size, "chunk_overlap": args.chunk_overlap}
    sources = [
        TextFileKnowledgeSource(file_paths=[KNOWLEDGE_DIR / "hr_policy.txt"], **chunking),
        PDFKnowledgeSource(file_paths=[KNOWLEDGE_DIR / "meeting_notes.pdf"], **chunking),
    ]
    print(f"✂️  {sum(len(s._chunk_text(t)) for s in sources for t in s.content.values())} chunks "
          f"of ≤{args.chunk_size} characters from 2 files")

    assistant = Agent(
        role="Internal Assistant",
        goal="Answer employee questions from the internal documents.",
        backstory="You answer from the documents you were given and say so when they do not cover a question.",
        knowledge_sources=sources,
        knowledge_config=KnowledgeConfig(results_limit=args.limit, score_threshold=args.threshold),
        embedder=build_embedder(),
        llm=build_llm(args.model, temperature=0),
        verbose=False,  # keep the output focused on retrieval
    )
    task = Task(
        description=f"Answer this question: {args.question}",
        expected_output="A short answer.",
        agent=assistant,
    )

    result = Crew(agents=[assistant], tasks=[task], process=Process.sequential).kickoff()

    # ── Re-run the same search to show the chunks and their scores ────────────
    query = assistant.knowledge_search_query or args.question
    hits = assistant.knowledge.query([query], results_limit=args.limit, score_threshold=0.0)

    print("=" * 60)
    print(f"Top {args.limit} chunks for {query!r} (✔ = above the threshold {args.threshold}):\n")
    for hit in hits:
        mark = "✔" if hit["score"] >= args.threshold else "✘"
        print(f"{mark} {hit['score']:.2f}  {hit['content'][:110].replace(chr(10), ' ')}…")
    print("\n" + "=" * 60)
    print(result.raw)


if __name__ == "__main__":
    main()

"""
Ask questions about a folder of documents (txt, md, pdf, csv, json, xlsx).

Usage:
    python main.py                                   # interactive, over the sample documents
    python main.py --question "Who owns the mobile performance fix and when is it due?"
    python main.py --folder ~/Documents/handbook --model gpt-4o-mini
"""

import argparse
from pathlib import Path

from knowledge_setup import KNOWLEDGE_DIR, build_embedder, reset_knowledge  # before crewai: it sets the storage

from docs_crew import DocsCrew
from llm import build_llm
from models import Answer
from sources import DocumentFolderSource


def print_answer(answer: Answer) -> None:
    print(f"\n💬 {answer.answer}")
    if answer.found_in_documents:
        print(f"📄 Sources: {', '.join(answer.documents)}")
    else:
        print("🤷 Not found in the documents.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Answer questions about a folder of documents.")
    parser.add_argument("--question", help="Ask one question and exit (default: interactive mode)")
    parser.add_argument("--folder", type=Path, default=KNOWLEDGE_DIR, help="Folder with the documents")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    parser.add_argument("--verbose", action="store_true", help="Show the agent's reasoning")
    args = parser.parse_args()

    llm = build_llm(args.model, temperature=0)
    embedder = build_embedder()

    # The folder may have changed since the last run (or be a different one), so
    # start from an empty store: the documents are embedded again in any case.
    reset_knowledge()

    source = DocumentFolderSource(folder=args.folder.expanduser(), chunk_size=800, chunk_overlap=100)
    if not source.documents:
        raise SystemExit(f"No supported documents found in {args.folder}.")
    print(f"📚 {len(source.documents)} documents: {', '.join(source.documents)}")
    for skipped in source.skipped:
        print(f"   skipped: {skipped}")

    print("⏳ Embedding the documents…")
    crew = DocsCrew(llm=llm, source=source, embedder=embedder, verbose=args.verbose).crew()
    documents = ", ".join(source.documents)

    def ask(question: str) -> None:
        try:
            result = crew.kickoff(inputs={"question": question, "documents": documents})
        except Exception as error:  # e.g. the guardrail rejected every attempt
            print(f"\n❌ Could not answer: {error}")
            return
        if isinstance(result.pydantic, Answer):
            print_answer(result.pydantic)
        else:
            print(f"\n{result.raw}")

    if args.question:
        ask(args.question)
        return

    print("\nAsk a question about the documents (empty line to quit).")
    while question := input("\n❓ ").strip():
        ask(question)


if __name__ == "__main__":
    main()

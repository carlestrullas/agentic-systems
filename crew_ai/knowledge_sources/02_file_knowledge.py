"""
02 · Knowledge from files: text, PDF, CSV and JSON.

    knowledge/hr_policy.txt      ──▶ TextFileKnowledgeSource ──▶ HR Policy Assistant
    knowledge/meeting_notes.pdf  ──▶ PDFKnowledgeSource      ──▶ Meeting Notes Summarizer
    knowledge/feedback.csv       ──▶ CSVKnowledgeSource      ──▶ User Feedback Analyst
    knowledge/company_info.json  ──▶ JSONKnowledgeSource     ──▶ Company Info Specialist

* Each file type has its own source class; all of them read the file, turn it
  into text, split it into chunks and embed it.
* Here the knowledge is given to the AGENT (`Agent(knowledge_sources=...)`),
  so only that agent can use it. Crew-level knowledge (01) is shared by all.
* File paths: a plain string such as "hr_policy.txt" is looked up in a folder
  called `knowledge/` under the directory you run the script from. A `Path`
  object is used as is, which is why these scripts pass `KNOWLEDGE_DIR / ...`
  and work from any directory.

Usage:
    python 02_file_knowledge.py --source text
    python 02_file_knowledge.py --source pdf
    python 02_file_knowledge.py --source csv --question "Which plan complains the most?"
    python 02_file_knowledge.py --source json
"""

import argparse

from knowledge_setup import KNOWLEDGE_DIR, build_embedder, reset_knowledge  # before crewai: it sets the storage

from crewai import Agent, Crew, Process, Task
from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

from llm import build_llm

# One agent per file type: source class, file, persona and a default question.
EXAMPLES = {
    "text": {
        "source": TextFileKnowledgeSource,
        "file": "hr_policy.txt",
        "role": "HR Policy Assistant",
        "goal": "Answer employee questions about HR policies accurately.",
        "backstory": "You are the People Ops assistant. You quote the exact numbers in the policy.",
        "question": "When can a new employee start using paid leave, and how many days do they get?",
    },
    "pdf": {
        "source": PDFKnowledgeSource,
        "file": "meeting_notes.pdf",
        "role": "Meeting Notes Summarizer",
        "goal": "Summarize meetings so the team knows what was decided and who does what.",
        "backstory": "You keep the team up to date and never lose an owner or a deadline.",
        "question": "What are the action items from the last product sync, with owners and deadlines?",
    },
    "csv": {
        "source": CSVKnowledgeSource,
        "file": "feedback.csv",
        "role": "User Feedback Analyst",
        "goal": "Turn raw user feedback into clear, actionable themes.",
        "backstory": "You group similar comments and back every theme with how often it appears.",
        "question": "What are the three most common complaints in the feedback, and how many comments mention each?",
    },
    "json": {
        "source": JSONKnowledgeSource,
        "file": "company_info.json",
        "role": "Company Info Specialist",
        "goal": "Answer questions about the company's structure and teams.",
        "backstory": "You are the internal assistant for questions about who is who in the company.",
        "question": "Which teams belong to Engineering, how many people are in each, and who leads the department?",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Give an agent knowledge from a file.")
    parser.add_argument("--source", choices=EXAMPLES, default="text", help="Which file type to try")
    parser.add_argument("--question", help="Your own question (each source has a default one)")
    parser.add_argument("--reset", action="store_true", help="Re-embed the knowledge from scratch")
    parser.add_argument("--model", help="Override the MODEL variable from .env")
    args = parser.parse_args()

    if args.reset:
        reset_knowledge()

    example = EXAMPLES[args.source]
    question = args.question or example["question"]
    source = example["source"](file_paths=[KNOWLEDGE_DIR / example["file"]])

    agent = Agent(
        role=example["role"],
        goal=example["goal"],
        backstory=example["backstory"],
        knowledge_sources=[source],  # only this agent can use it
        embedder=build_embedder(),
        llm=build_llm(args.model, temperature=0),
        allow_delegation=False,
        verbose=True,
    )

    task = Task(
        description=f"Answer this question using the {example['file']} document: {question}",
        expected_output="A clear, concise answer; use a bullet list when listing several items.",
        agent=agent,
    )

    result = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True).kickoff()

    print("\n" + "=" * 60)
    print(f"[{example['file']}] {question}\n")
    print(result.raw)
    print("=" * 60)


if __name__ == "__main__":
    main()

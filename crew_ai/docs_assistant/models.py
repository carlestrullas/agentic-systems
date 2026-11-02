"""
Pydantic schema for the assistant's answer.

`found_in_documents` and `documents` make the answer checkable: code can tell
an answer grounded in the files from an "I don't know", and show the user
which files to open. The guardrail in docs_crew.py enforces that they are
consistent.
"""

from pydantic import BaseModel, Field


class Answer(BaseModel):
    """An answer to a question about the documents."""

    answer: str = Field(
        ...,
        description=(
            "The answer, using only information from the documents. If they do not contain it, "
            "say so plainly and do not guess."
        ),
    )
    found_in_documents: bool = Field(
        ..., description="True if the documents contain the information needed to answer."
    )
    documents: list[str] = Field(
        default_factory=list,
        description=(
            "File names (as written after 'Document:') the answer is based on. "
            "Empty when found_in_documents is false."
        ),
    )

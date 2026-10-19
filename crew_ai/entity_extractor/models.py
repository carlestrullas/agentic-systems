"""
Pydantic schema for the structured output of the extractor.

Passing this model to a Task with `output_pydantic=KnowledgeGraph` makes CrewAI
validate (and, if needed, repair) the agent's answer against the schema, so the
result can be used directly in code with no extra parsing.

Tip: always give every field a `description`. The model sees these descriptions
and uses them as instructions for what to put in each field.
"""

from pydantic import BaseModel, Field


class Triplet(BaseModel):
    """A single fact expressed as entity → relation → entity."""

    subject: str = Field(..., description="The entity the fact is about, e.g. 'Marie Curie'.")
    relation: str = Field(
        ...,
        description="A short verb phrase in snake_case linking subject and object, e.g. 'born_in'.",
    )
    object: str = Field(..., description="The entity or value related to the subject, e.g. 'Warsaw'.")


class KnowledgeGraph(BaseModel):
    """All the facts extracted from a piece of text."""

    triplets: list[Triplet] = Field(
        ...,
        description="Every subject-relation-object fact stated explicitly in the text.",
    )

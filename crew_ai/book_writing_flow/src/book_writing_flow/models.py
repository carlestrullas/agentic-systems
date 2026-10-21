"""Structured outputs shared by the crews and the flow state."""

from pydantic import BaseModel, Field


class Outline(BaseModel):
    """Outline of the book, produced by the outline crew."""

    total_chapters: int = Field(..., ge=1, description="Number of chapters in the book.")
    titles: list[str] = Field(
        ..., description="Title of every chapter, in reading order (one per chapter)."
    )


class Chapter(BaseModel):
    """One chapter, produced by a chapter writer crew."""

    title: str = Field(..., description="Title of the chapter.")
    content: str = Field(
        ..., description="Full text of the chapter in Markdown, without repeating the title."
    )

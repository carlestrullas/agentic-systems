"""
Pydantic schema for the inspection report.

The task uses `output_pydantic=QualityReport`, so the agent's answer about the
image comes back as a validated object that code can act on (for example,
reject the batch when `verdict == "reject"`).
"""

from typing import Literal

from pydantic import BaseModel, Field


class Defect(BaseModel):
    """One visible problem in the product or its packaging."""

    kind: Literal["scratch", "dent", "crack", "stain", "misalignment", "color", "packaging", "missing_part", "other"] = Field(
        ..., description="The category of the defect."
    )
    description: str = Field(..., description="What exactly is visible, in one sentence.")
    location: str = Field(..., description="Where in the image the defect is, e.g. 'top-left corner of the box'.")
    severity: Literal["low", "medium", "high"] = Field(
        ..., description="low: cosmetic; medium: affects appearance or protection; high: affects function or safety."
    )


class QualityReport(BaseModel):
    """The structured result of inspecting one product image."""

    product: str = Field(..., description="What the image shows, in a few words.")
    defects: list[Defect] = Field(
        ..., description="Every visible defect. An empty list if none is visible; never invent defects."
    )
    quality_score: int = Field(..., ge=1, le=10, description="Overall quality from 1 (unacceptable) to 10 (flawless).")
    verdict: Literal["pass", "review", "reject"] = Field(
        ..., description="pass: ship as is; review: a person should check it; reject: do not ship."
    )
    recommendations: list[str] = Field(
        ..., description="One to three concrete actions to fix the problems or prevent them."
    )

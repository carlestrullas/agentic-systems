"""
Custom tools for the agents of this flow.

`crewai create flow` adds this file so the project has a place for its own
tools. This one counts the sentences of a text, which the poem writer could use
to check that its poem has the requested length. It is not attached by default:
to try it, pass `tools=[SentenceCounterTool()]` to the agent in
`crews/poem_crew/poem_crew.py` (use a model with good tool calling).

See `currency_converter/` in this repository for a full custom-tool example.
"""

import re
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class SentenceCounterInput(BaseModel):
    """Input schema for SentenceCounterTool."""

    text: str = Field(..., description="The text whose sentences should be counted.")


class SentenceCounterTool(BaseTool):
    name: str = "Sentence Counter"
    description: str = (
        "Counts how many sentences a text has. Use it to check that a text has the "
        "required number of sentences before giving the final answer."
    )
    args_schema: Type[BaseModel] = SentenceCounterInput

    def _run(self, text: str) -> str:
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
        return f"The text has {len(sentences)} sentence(s)."

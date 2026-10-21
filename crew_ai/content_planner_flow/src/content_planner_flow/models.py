"""
Structured outputs of the planning crew.

Each planner task returns one of these models (`output_pydantic=...`), so the
flow gets a validated object it can print, check and save as JSON. As always
with structured output, every field has a description: the model reads them as
instructions.
"""

from pydantic import BaseModel, Field

TWEET_MAX_CHARS = 280


class Tweet(BaseModel):
    """One tweet of a thread."""

    content: str = Field(
        ..., description=f"Text of the tweet, at most {TWEET_MAX_CHARS} characters."
    )
    is_hook: bool = Field(
        False, description="True only for the first tweet, the hook that opens the thread."
    )
    media_urls: list[str] = Field(
        default_factory=list,
        description="URLs of images from the draft that illustrate this tweet (may be empty).",
    )


class Thread(BaseModel):
    """A Twitter/X thread planned from a blog post."""

    topic: str = Field(..., description="Main topic of the thread, usually the blog post title.")
    tweets: list[Tweet] = Field(..., description="The tweets of the thread, in order.")


class LinkedInPost(BaseModel):
    """A LinkedIn post planned from a blog post."""

    content: str = Field(
        ...,
        description="Full text of the post, with line breaks, 3-5 hashtags and the blog link at the end.",
    )
    media_url: str = Field(
        "", description="URL of the one image from the draft to attach to the post (may be empty)."
    )

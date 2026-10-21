"""Tools shared by the crews of this flow."""

import os


def search_tools() -> list:
    """Web search through Serper, or no tools if SERPER_API_KEY is not set.

    A new list (and tool instance) is returned on every call, so crews running in
    parallel never share a tool object.
    """
    key = os.getenv("SERPER_API_KEY", "").strip()
    if not key or key == "REPLACE_ME":
        return []

    from crewai_tools import SerperDevTool

    return [SerperDevTool(n_results=5)]


def search_enabled() -> bool:
    return bool(search_tools())

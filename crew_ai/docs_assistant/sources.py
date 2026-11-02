"""
DocumentFolderSource: every supported file of a folder as one knowledge source.

It reuses CrewAI's built-in loaders to turn each file into text, and adds one
thing they do not do: every chunk starts with the name of the file it comes
from. The agent can then tell the user *which* document an answer is based on.

    knowledge/
    ├── hr_policy.txt      ──▶ "[Document: hr_policy.txt]\n<chunk>"
    ├── meeting_notes.pdf  ──▶ "[Document: meeting_notes.pdf]\n<chunk>"
    └── …
"""

import asyncio
from pathlib import Path

from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource
from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource
from crewai.knowledge.source.excel_knowledge_source import ExcelKnowledgeSource
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from pydantic import Field

LOADERS = {
    ".txt": TextFileKnowledgeSource,
    ".md": TextFileKnowledgeSource,
    ".pdf": PDFKnowledgeSource,
    ".csv": CSVKnowledgeSource,
    ".json": JSONKnowledgeSource,
    ".xlsx": ExcelKnowledgeSource,  # needs pandas
}


def read_text(path: Path) -> str:
    """Extract the text of one file with the matching CrewAI loader."""
    loader = LOADERS[path.suffix.lower()](file_paths=[path])  # loading happens on creation
    parts = []
    for value in loader.content.values():
        if isinstance(value, dict):  # Excel: one text per sheet
            parts.extend(f"Sheet {sheet}:\n{text}" for sheet, text in value.items())
        else:
            parts.append(value)
    return "\n".join(parts)


class DocumentFolderSource(BaseKnowledgeSource):
    """All the supported documents in a folder, with the file name on every chunk."""

    folder: Path = Field(description="Folder with the documents")
    documents: dict[str, str] = Field(default_factory=dict, description="File name → extracted text")
    skipped: list[str] = Field(default_factory=list, description="Files that could not be loaded")

    def model_post_init(self, _context) -> None:
        self.validate_content()  # load when created, so the caller can list the documents

    def validate_content(self) -> dict[str, str]:
        if not self.folder.is_dir():
            raise ValueError(f"Not a folder: {self.folder}")

        for path in sorted(self.folder.iterdir()):
            if path.name.startswith(".") or not path.is_file():
                continue
            if path.suffix.lower() not in LOADERS:
                self.skipped.append(f"{path.name} (unsupported type)")
                continue
            try:
                text = read_text(path).strip()
            except Exception as error:  # a broken file should not stop the others
                self.skipped.append(f"{path.name} ({error})")
                continue
            if text:
                self.documents[path.name] = text
            else:
                self.skipped.append(f"{path.name} (no text found)")
        return self.documents

    def _labelled_chunks(self) -> list[str]:
        return [
            f"[Document: {name}]\n{chunk}"
            for name, text in self.documents.items()
            for chunk in self._chunk_text(text)
        ]

    def add(self) -> None:
        self.chunks.extend(self._labelled_chunks())
        self._save_documents()

    async def aadd(self) -> None:
        self.chunks.extend(await asyncio.to_thread(self._labelled_chunks))
        await self._asave_documents()

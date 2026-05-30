"""Text extraction module. Must not import DB or Qdrant modules."""

from dataclasses import dataclass
import re

import fitz

PDF_OPEN_ERROR = "PDF could not be opened — file may be corrupted or encrypted."
TEXT_UTF8_ERROR = "Text document could not be decoded as UTF-8."


class ExtractionError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class ExtractedDocument:
    pages: list[tuple[int, str]]
    page_count: int


def normalize_page_text(text: str) -> str:
    text = text.replace("\xad", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


async def extract_document(
    *, filename: str, content_type: str, data: bytes
) -> ExtractedDocument:
    suffix = filename.lower().rsplit(".", 1)[-1]
    if content_type == "application/pdf" or suffix == "pdf":
        return _extract_pdf(data)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExtractionError(TEXT_UTF8_ERROR) from exc
    return ExtractedDocument(pages=[(1, normalize_page_text(text))], page_count=1)


def _extract_pdf(data: bytes) -> ExtractedDocument:
    try:
        with fitz.open(stream=data, filetype="pdf") as pdf:
            pages = [
                (i + 1, normalize_page_text(page.get_text("text")))
                for i, page in enumerate(pdf)
            ]
            return ExtractedDocument(pages=pages, page_count=len(pages))
    except Exception as exc:
        raise ExtractionError(PDF_OPEN_ERROR) from exc

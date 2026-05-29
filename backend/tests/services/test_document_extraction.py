import pytest

from app.services.document_extraction import (
    PDF_OPEN_ERROR,
    TEXT_UTF8_ERROR,
    ExtractedDocument,
    ExtractionError,
    extract_document,
    normalize_page_text,
)


def test_normalize_page_text():
    assert normalize_page_text("a\xad\n\n\n b\t  c ") == "a\n\n b c"


@pytest.mark.asyncio
async def test_extract_text_utf8_as_page_one():
    doc = await extract_document(
        filename="note.txt", content_type="text/plain", data="hello".encode()
    )
    assert doc == ExtractedDocument(pages=[(1, "hello")], page_count=1)


@pytest.mark.asyncio
async def test_extract_markdown_utf8_failure():
    with pytest.raises(ExtractionError, match=TEXT_UTF8_ERROR):
        await extract_document(filename="bad.md", content_type="text/markdown", data=b"\xff")


@pytest.mark.asyncio
async def test_extract_pdf_open_failure_message():
    with pytest.raises(ExtractionError, match=PDF_OPEN_ERROR):
        await extract_document(
            filename="bad.pdf", content_type="application/pdf", data=b"not a pdf"
        )

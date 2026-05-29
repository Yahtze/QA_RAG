from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from app.core.config import Settings

ALLOWED = {"application/pdf", "text/plain", "text/markdown", "application/octet-stream"}


class UploadTooLargeError(Exception): ...


class DisallowedContentTypeError(Exception): ...


class InvalidPdfError(Exception): ...


@dataclass(frozen=True)
class StoredFile:
    storage_path: str
    content_type: str
    size_bytes: int


class LocalStorageService:
    # Stored originals retained when ingestion fails.
    # Delete only on document delete or explicit cleanup.
    def __init__(self, settings: Settings):
        self.settings = settings

    async def store_upload(
        self,
        *,
        user_id: UUID,
        document_id: UUID,
        filename: str,
        content_type: str,
        upload: BinaryIO | AsyncIterator[bytes],
    ) -> StoredFile:
        ctype = content_type.split(";")[0].strip().lower()
        ext = Path(filename).suffix.lower() if filename else ""
        if ctype not in ALLOWED:
            raise DisallowedContentTypeError
        if ctype == "application/octet-stream" and ext not in {".md", ".txt"}:
            raise DisallowedContentTypeError
        if not ext:
            ext = (
                ".pdf"
                if ctype == "application/pdf"
                else ".md"
                if ctype == "text/markdown"
                else ".txt"
            )
        rel = Path("uploads") / str(user_id) / f"{document_id}{ext}"
        full = self.settings.storage_root_path / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        first = b""
        try:
            with full.open("wb") as fh:
                if hasattr(upload, "read"):
                    while True:
                        chunk = upload.read(8192)
                        if not chunk:
                            break
                        if isinstance(chunk, str):
                            chunk = chunk.encode()
                        if not first:
                            first = chunk[:4]
                        size += len(chunk)
                        if size > self.settings.MAX_UPLOAD_BYTES:
                            raise UploadTooLargeError
                        fh.write(chunk)
                else:
                    async for chunk in upload:
                        if not first:
                            first = chunk[:4]
                        size += len(chunk)
                        if size > self.settings.MAX_UPLOAD_BYTES:
                            raise UploadTooLargeError
                        fh.write(chunk)
            if ctype == "application/pdf" and not first.startswith(b"%PDF"):
                raise InvalidPdfError
        except Exception:
            full.unlink(missing_ok=True)
            raise
        return StoredFile(storage_path=str(rel), content_type=ctype, size_bytes=size)

    async def read_bytes(self, storage_path: str) -> bytes:
        return (self.settings.storage_root_path / storage_path).read_bytes()

    async def delete(self, storage_path: str) -> None:
        (self.settings.storage_root_path / storage_path).unlink(missing_ok=True)

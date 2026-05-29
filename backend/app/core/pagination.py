import base64
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import and_, or_

T = TypeVar("T")


@dataclass(frozen=True)
class Cursor:
    created_at: datetime
    id: UUID


class PageInfo(BaseModel):
    next_cursor: str | None
    has_more: bool


class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    page_info: PageInfo


def normalize_limit(limit: int | None, default: int = 20, maximum: int = 100) -> int:
    if limit is None:
        return default
    return max(1, min(limit, maximum))


def encode_cursor(cursor: Cursor) -> str:
    raw = json.dumps({"created_at": cursor.created_at.isoformat(), "id": str(cursor.id)})
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(raw: str | None) -> Cursor | None:
    if raw is None:
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(raw.encode()).decode())
        return Cursor(created_at=datetime.fromisoformat(data["created_at"]), id=UUID(data["id"]))
    except Exception as exc:
        raise ValueError("invalid cursor") from exc


def build_cursor_predicate(model_created_at, model_id, cursor: Cursor | None):
    if cursor is None:
        return None
    return or_(
        model_created_at > cursor.created_at,
        and_(model_created_at == cursor.created_at, model_id > cursor.id),
    )


def page_from_items(
    items: list[T], limit: int, cursor_factory: Callable[[T], Cursor]
) -> CursorPage[T]:
    has_more = len(items) > limit
    page_items = items[:limit]
    next_cursor = encode_cursor(cursor_factory(page_items[-1])) if has_more and page_items else None
    return CursorPage(
        items=page_items, page_info=PageInfo(next_cursor=next_cursor, has_more=has_more)
    )

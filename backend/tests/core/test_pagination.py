from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.core.pagination import Cursor, CursorPage, decode_cursor, encode_cursor, normalize_limit


def test_cursor_round_trip():
    c = Cursor(
        created_at=datetime(2026, 5, 28, 12, 0, tzinfo=UTC),
        id=UUID("00000000-0000-0000-0000-000000000001"),
    )
    assert decode_cursor(encode_cursor(c)) == c


def test_decode_bad_cursor_raises_value_error():
    with pytest.raises(ValueError):
        decode_cursor("bad")


def test_normalize_limit_bounds():
    assert normalize_limit(None) == 20
    assert normalize_limit(0) == 1
    assert normalize_limit(999) == 100


def test_cursor_page_next_cursor():
    page = CursorPage(items=["a"], page_info={"next_cursor": "abc", "has_more": True})
    assert page.page_info.next_cursor == "abc"

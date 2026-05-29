from app.db.base import Base
from app.models import Document, Message, User


def test_all_tables_registered():
    assert {"users", "documents", "conversations", "messages", "citations"}.issubset(
        Base.metadata.tables
    )


def test_named_checks_exist():
    doc_names = {c.name for c in Document.__table__.constraints}
    msg_names = {c.name for c in Message.__table__.constraints}
    assert "ck_documents_status" in doc_names
    assert "ck_messages_role" in msg_names


def test_user_email_unique():
    assert any(c.name == "email" and c.unique for c in User.__table__.columns)

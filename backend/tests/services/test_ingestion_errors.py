import pytest

from app.services.ingestion_errors import (
    DeterministicIngestionError,
    IngestionError,
    RetryableIngestionError,
)


def test_exception_hierarchy():
    assert issubclass(RetryableIngestionError, IngestionError)
    assert issubclass(DeterministicIngestionError, IngestionError)


def test_retryable_error_carries_phase_and_cause():
    cause = RuntimeError("boom")
    err = RetryableIngestionError("embedding", cause)
    assert err.phase == "embedding"
    assert err.cause is cause
    assert "boom" in str(err)


def test_deterministic_error_carries_message_and_phase():
    err = DeterministicIngestionError("bad file", "extraction")
    assert err.message == "bad file"
    assert err.phase == "extraction"
    assert str(err) == "bad file"

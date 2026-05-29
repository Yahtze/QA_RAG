from uuid import UUID

from app.services.ingestion_reconciliation import (
    RecoveryAction,
    RecoveryClassification,
    RecoveryPlan,
)


def test_recovery_plan_ready_not_marked():
    plan = RecoveryPlan(
        document_id=UUID("11111111-1111-1111-1111-111111111111"),
        classification=RecoveryClassification.READY_NOT_MARKED,
        action=RecoveryAction.MARK_READY,
        reason="qdrant synced but document not ready",
    )
    assert plan.action == RecoveryAction.MARK_READY

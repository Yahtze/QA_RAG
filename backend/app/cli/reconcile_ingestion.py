import argparse
import asyncio

from app.db.session import SessionLocal
from app.services.ingestion_reconciliation import IngestionReconciliationService


async def _run(*, apply_changes: bool) -> None:
    async with SessionLocal() as session:
        service = IngestionReconciliationService(session=session)
        stale_docs = await service.list_stale_processing()
        if not stale_docs:
            print("no stale processing documents found")
            return

        for stale in stale_docs:
            plan = await service.plan_recovery(stale.document_id)
            print(
                "document="
                f"{plan.document_id} "
                f"classification={plan.classification} "
                f"action={plan.action} "
                f"reason={plan.reason}"
            )
            if apply_changes:
                result = await service.apply_recovery(plan)
                print(f"applied={result.applied}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile ingestion")
    parser.add_argument("--no-dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(_run(apply_changes=args.no_dry_run))


if __name__ == "__main__":
    main()

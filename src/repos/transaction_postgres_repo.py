from datetime import UTC, datetime

from sqlalchemy import Engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.interfaces.transaction_repo import TransactionRepoInterface
from src.models.budget import Transaction
from src.models.orm import SyncState, TransactionRecord


class TransactionPostgresRepo(TransactionRepoInterface):
    def __init__(self, db: Engine):
        self.db = db

    def upsert_transactions(self, transactions: list[Transaction]) -> int:
        if not transactions:
            return 0

        with Session(self.db) as session:
            values = [
                {
                    "id": t.id,
                    "account_id": t.account_id,
                    "account_name": t.account_name,
                    "date": t.date,
                    "amount": t.amount,
                    "memo": t.memo,
                    "approved": t.approved,
                    "payee_id": t.payee_id,
                    "payee_name": t.payee_name,
                    "category_id": t.category_id,
                    "category_name": t.category_name,
                    "deleted": t.deleted,
                }
                for t in transactions
            ]

            stmt = insert(TransactionRecord).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "account_id": stmt.excluded.account_id,
                    "account_name": stmt.excluded.account_name,
                    "date": stmt.excluded.date,
                    "amount": stmt.excluded.amount,
                    "memo": stmt.excluded.memo,
                    "approved": stmt.excluded.approved,
                    "payee_id": stmt.excluded.payee_id,
                    "payee_name": stmt.excluded.payee_name,
                    "category_id": stmt.excluded.category_id,
                    "category_name": stmt.excluded.category_name,
                    "deleted": stmt.excluded.deleted,
                    "updated_at": datetime.now(UTC),
                },
            )

            result = session.execute(stmt)
            session.commit()
            return result.rowcount

    def get_last_knowledge_of_server(self, budget_id: str) -> int | None:
        with Session(self.db) as session:
            result = session.execute(
                select(SyncState.last_knowledge_of_server).where(
                    SyncState.budget_id == budget_id
                )
            )
            row = result.scalar_one_or_none()
            return row

    def update_sync_state(self, budget_id: str, server_knowledge: int) -> None:
        with Session(self.db) as session:
            stmt = insert(SyncState).values(
                budget_id=budget_id,
                last_knowledge_of_server=server_knowledge,
                last_synced_at=datetime.now(UTC),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["budget_id"],
                set_={
                    "last_knowledge_of_server": server_knowledge,
                    "last_synced_at": datetime.now(UTC),
                },
            )
            session.execute(stmt)
            session.commit()

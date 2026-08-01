from datetime import UTC, datetime, timedelta
from datetime import date as date_type

from sqlalchemy import Engine, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.interfaces.transaction_repo import TransactionRepoInterface
from src.models.budget import Transaction
from src.models.orm import SyncState, TransactionRecord


def _to_domain(record: TransactionRecord) -> Transaction:
    return Transaction(
        id=record.id,
        payee_id=record.payee_id,
        payee_name=record.payee_name,
        date=record.date,
        amount=record.amount,
        memo=record.memo,
        category_id=record.category_id,
        category_name=record.category_name,
        approved=record.approved,
        account_id=record.account_id,
        account_name=record.account_name,
        deleted=record.deleted,
    )


def _date_window(date: str, window_days: int) -> tuple[str, str] | None:
    """ISO bounds either side of ``date``, or None if it isn't a valid date."""
    try:
        centre = date_type.fromisoformat(date)
    except ValueError:
        return None
    delta = timedelta(days=window_days)
    return (centre - delta).isoformat(), (centre + delta).isoformat()


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

    def find_candidate_transactions(
        self,
        amount_milliunits: int,
        date: str | None = None,
        window_days: int = 7,
        payee_hint: str | None = None,
    ) -> list[Transaction]:
        with Session(self.db) as session:
            stmt = select(TransactionRecord).where(
                func.abs(TransactionRecord.amount) == abs(amount_milliunits),
                TransactionRecord.deleted.is_(False),
            )

            if date:
                window = _date_window(date, window_days)
                if window:
                    start, end = window
                    stmt = stmt.where(TransactionRecord.date.between(start, end))

            if payee_hint:
                stmt = stmt.where(
                    TransactionRecord.payee_name.ilike(f"%{payee_hint}%")
                )

            records = session.execute(stmt).scalars().all()
            return [_to_domain(record) for record in records]

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        with Session(self.db) as session:
            record = session.get(TransactionRecord, transaction_id)
            return _to_domain(record) if record else None

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

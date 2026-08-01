from datetime import date
from decimal import Decimal

import pytest

from src.interfaces.transaction_repo import TransactionRepoInterface
from src.models.budget import Transaction
from src.models.invoice import MatchReason
from src.models.order import ExtractedOrder, Product
from src.services.order_matching_service import OrderMatchingService


def _transaction(
    transaction_id: str,
    amount: int = -21500,
    txn_date: str = "2026-03-15",
    payee_name: str | None = "VINAL BAKERY",
) -> Transaction:
    return Transaction(
        id=transaction_id,
        payee_id=None,
        payee_name=payee_name,
        date=txn_date,
        amount=amount,
        memo=None,
        category_id=None,
        category_name=None,
        approved=False,
    )


def _extracted(
    total: str = "21.50",
    order_date: date | None = date(2026, 3, 15),
    vendor_name: str | None = None,
) -> ExtractedOrder:
    return ExtractedOrder(
        overall_cost=Decimal("20.00"),
        total_tax=Decimal("1.50"),
        total_amount=Decimal(total),
        order_date=order_date,
        vendor_name=vendor_name,
        products=[Product(name="Coffee", price=Decimal("10.00"), quantity=2)],
    )


class FakeTransactionRepo(TransactionRepoInterface):
    def __init__(self, candidates: list[Transaction]):
        self.candidates = candidates
        self.calls: list[dict] = []

    def find_candidate_transactions(
        self, amount_milliunits, date=None, window_days=7, payee_hint=None
    ):
        self.calls.append(
            {
                "amount_milliunits": amount_milliunits,
                "date": date,
                "window_days": window_days,
                "payee_hint": payee_hint,
            }
        )
        return list(self.candidates)

    def get_transaction(self, transaction_id):
        for candidate in self.candidates:
            if candidate.id == transaction_id:
                return candidate
        return None

    def upsert_transactions(self, transactions):
        raise NotImplementedError

    def get_last_knowledge_of_server(self, budget_id):
        raise NotImplementedError

    def update_sync_state(self, budget_id, server_knowledge):
        raise NotImplementedError


def test_single_candidate_matches():
    repo = FakeTransactionRepo([_transaction("txn-1")])
    result = OrderMatchingService(repo).match(_extracted())

    assert result.reason == MatchReason.MATCHED
    assert result.is_matched
    assert result.transaction.id == "txn-1"


def test_no_candidates_reports_no_candidates():
    result = OrderMatchingService(FakeTransactionRepo([])).match(_extracted())

    assert result.reason == MatchReason.NO_CANDIDATES
    assert not result.is_matched
    assert result.transaction is None


def test_ambiguous_candidates_are_parked_not_guessed():
    repo = FakeTransactionRepo(
        [
            _transaction("txn-1", payee_name="AMZN Mktp US*AAA"),
            _transaction("txn-2", payee_name="AMZN Mktp US*BBB"),
        ]
    )
    result = OrderMatchingService(repo).match(_extracted())

    assert result.reason == MatchReason.AMBIGUOUS
    assert result.transaction is None
    assert result.candidate_count == 2


def test_vendor_name_disambiguates_when_only_one_payee_matches():
    repo = FakeTransactionRepo(
        [
            _transaction("txn-1", payee_name="VINAL BAKERY"),
            _transaction("txn-2", payee_name="SHAKE SHACK"),
        ]
    )
    result = OrderMatchingService(repo).match(_extracted(vendor_name="Vinal Bakery"))

    assert result.reason == MatchReason.MATCHED
    assert result.transaction.id == "txn-1"
    assert result.candidate_count == 2


def test_invoice_date_disambiguates_when_only_one_falls_on_it():
    repo = FakeTransactionRepo(
        [
            _transaction("txn-1", txn_date="2026-03-15"),
            _transaction("txn-2", txn_date="2026-03-12"),
        ]
    )
    result = OrderMatchingService(repo).match(
        _extracted(order_date=date(2026, 3, 15))
    )

    assert result.reason == MatchReason.MATCHED
    assert result.transaction.id == "txn-1"


def test_amount_is_queried_as_positive_milliunits():
    repo = FakeTransactionRepo([_transaction("txn-1")])
    OrderMatchingService(repo).match(_extracted(total="21.50"))

    assert repo.calls[0]["amount_milliunits"] == 21500


def test_payee_hint_is_never_required_for_the_initial_query():
    # Bank descriptors rarely resemble the vendor name, so filtering the first
    # query on it would turn ordinary matches into misses.
    repo = FakeTransactionRepo([_transaction("txn-1")])
    OrderMatchingService(repo).match(_extracted(vendor_name="Vinal Bakery"))

    assert repo.calls[0]["payee_hint"] is None


@pytest.mark.parametrize("window", [3, 14])
def test_configured_window_is_passed_through(window):
    repo = FakeTransactionRepo([_transaction("txn-1")])
    OrderMatchingService(repo, window_days=window).match(_extracted())

    assert repo.calls[0]["window_days"] == window


def test_missing_order_date_still_queries_without_a_window():
    repo = FakeTransactionRepo([_transaction("txn-1")])
    result = OrderMatchingService(repo).match(_extracted(order_date=None))

    assert repo.calls[0]["date"] is None
    assert result.reason == MatchReason.MATCHED

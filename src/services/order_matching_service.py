from decimal import Decimal

from loguru import logger

from src.interfaces.transaction_repo import TransactionRepoInterface
from src.models.budget import Transaction
from src.models.invoice import MatchReason, TransactionMatch
from src.models.order import ExtractedOrder

MILLIUNITS = 1000
DEFAULT_WINDOW_DAYS = 7


def _to_milliunits(value: Decimal) -> int:
    return int((value * MILLIUNITS).to_integral_value())


class OrderMatchingService:
    """Resolves an extracted order to the YNAB transaction that paid for it.

    Matching runs unattended in a worker, so it only ever commits to a single
    surviving candidate. Both "the charge has not posted yet" and "two
    identical charges on the same day" are normal and are reported back as
    unmatched for a later retry.
    """

    def __init__(
        self,
        transaction_repo: TransactionRepoInterface,
        window_days: int = DEFAULT_WINDOW_DAYS,
    ):
        self.transaction_repo = transaction_repo
        self.window_days = window_days

    def match(self, extracted: ExtractedOrder) -> TransactionMatch:
        amount = _to_milliunits(extracted.total_amount)
        invoice_date = (
            extracted.order_date.isoformat() if extracted.order_date else None
        )

        # Bank descriptors rarely resemble the vendor name on the invoice
        # ("AMZN Mktp US*RT4G91YT3"), so the hint only ever narrows an
        # otherwise ambiguous result -- it is never required for a match.
        candidates = self._find(amount, invoice_date, payee_hint=None)

        if not candidates:
            return TransactionMatch(
                reason=MatchReason.NO_CANDIDATES, candidate_count=0
            )

        if len(candidates) == 1:
            return TransactionMatch(
                transaction=candidates[0],
                reason=MatchReason.MATCHED,
                candidate_count=1,
            )

        narrowed = self._narrow(candidates, extracted, invoice_date)
        if len(narrowed) == 1:
            return TransactionMatch(
                transaction=narrowed[0],
                reason=MatchReason.MATCHED,
                candidate_count=len(candidates),
            )

        logger.info(
            f"{len(candidates)} transactions match {extracted.total_amount}; "
            "parking as ambiguous rather than guessing"
        )
        return TransactionMatch(
            reason=MatchReason.AMBIGUOUS, candidate_count=len(candidates)
        )

    def _find(
        self, amount: int, date: str | None, payee_hint: str | None
    ) -> list[Transaction]:
        return self.transaction_repo.find_candidate_transactions(
            amount_milliunits=amount,
            date=date,
            window_days=self.window_days,
            payee_hint=payee_hint,
        )

    def _narrow(
        self,
        candidates: list[Transaction],
        extracted: ExtractedOrder,
        invoice_date: str | None,
    ) -> list[Transaction]:
        """Whittle several equal-amount candidates down, if it can be done safely.

        Only exact signals are used: the payee actually containing the vendor
        name, and the transaction falling on the invoice date itself. Anything
        looser would be a guess.
        """
        if extracted.vendor_name:
            hint = extracted.vendor_name.lower()
            by_payee = [
                candidate
                for candidate in candidates
                if candidate.payee_name and hint in candidate.payee_name.lower()
            ]
            if len(by_payee) == 1:
                return by_payee
            if by_payee:
                candidates = by_payee

        if invoice_date:
            same_day = [
                candidate
                for candidate in candidates
                if candidate.date == invoice_date
            ]
            if len(same_day) == 1:
                return same_day

        return candidates

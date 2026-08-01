from loguru import logger
from pydantic import ValidationError
from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior

from src.interfaces.pii_redactor import PIIRedactor
from src.models.order import ExtractedOrder

INVOICE_EXTRACTION_SYSTEM_PROMPT = """\
You extract structured order data from vendor invoices and receipts.

Rules:
- Report only what the document states. Never invent an item, price or total.
- `products` is one entry per distinct line item, with its unit price and
  quantity. Do not multiply the unit price by the quantity.
- `overall_cost` is the pre-tax subtotal, `total_tax` is all tax components
  summed, `tip` is the gratuity if present, and `total_amount` is the final
  amount charged.
- Prices may appear with the cents run together with the dollars (for example
  `$1599` meaning `$15.99`). Use the stated subtotal and total to resolve the
  decimal placement.
- Some text is replaced with `<REDACTED_...>` placeholders. Treat those as
  unavailable, never as a value or an item name.
- If the document is not an invoice or receipt, or has no line items, say so
  rather than guessing.
"""


class InvoiceExtractorAgent:
    """Turns invoice markdown into an :class:`ExtractedOrder`.

    Redaction happens here, immediately before the model call, so no caller can
    route unredacted document text to an external provider.
    """

    def __init__(self, llm_client: Agent, pii_redactor: PIIRedactor):
        self.llm_client = llm_client
        self.pii_redactor = pii_redactor

    def extract(self, markdown: str) -> ExtractedOrder | None:
        """Extract an order from invoice markdown.

        Returns ``None`` when the document yields no usable order. Provider and
        network failures are allowed to propagate so the caller can retry them;
        an unusable document is not retried.
        """
        if not markdown.strip():
            return None

        redacted = self.pii_redactor.redact_pii(markdown)

        try:
            result = self.llm_client.run_sync(
                f"Extract the order from this invoice:\n\n{redacted}",
                output_type=ExtractedOrder,
            )
        except (UnexpectedModelBehavior, ValidationError) as exc:
            logger.warning(f"Invoice extraction produced no usable order: {exc}")
            return None

        extracted = result.output
        if extracted is None or not extracted.products:
            logger.warning("Invoice extraction returned no line items")
            return None
        return extracted

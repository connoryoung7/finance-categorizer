from decimal import Decimal

from pydantic import ValidationError
from pydantic_ai.exceptions import UnexpectedModelBehavior
import pytest

from src.agents.invoice_extractor_agent import InvoiceExtractorAgent
from src.interfaces.pii_redactor import PIIRedactor
from src.models.order import ExtractedOrder, Product


class RecordingRedactor(PIIRedactor):
    """Redacts a known token so tests can prove redaction ran first."""

    def __init__(self):
        self.calls: list[str] = []

    def redact_pii(self, text: str) -> str:
        self.calls.append(text)
        return text.replace("4532015112830366", "<REDACTED_CREDIT_CARD>")


class StubAgent:
    """Stands in for a pydantic-ai Agent, recording what it was asked."""

    def __init__(self, output=None, raises: Exception | None = None):
        self.output = output
        self.raises = raises
        self.prompts: list[str] = []

    def run_sync(self, user_prompt, **kwargs):
        self.prompts.append(user_prompt)
        if self.raises:
            raise self.raises
        return type("Result", (), {"output": self.output})()


def _extracted() -> ExtractedOrder:
    return ExtractedOrder(
        overall_cost=Decimal("20.00"),
        total_tax=Decimal("1.50"),
        total_amount=Decimal("21.50"),
        products=[Product(name="Coffee", price=Decimal("10.00"), quantity=2)],
    )


def test_extract_returns_the_model_output():
    agent = InvoiceExtractorAgent(StubAgent(output=_extracted()), RecordingRedactor())

    result = agent.extract("Coffee $10.00\nTotal $21.50")

    assert result is not None
    assert result.total_amount == Decimal("21.50")


def test_redaction_runs_before_the_model_sees_anything():
    llm = StubAgent(output=_extracted())
    redactor = RecordingRedactor()
    agent = InvoiceExtractorAgent(llm, redactor)

    agent.extract("Ham Jamboree $11.00\nPaid with 4532015112830366")

    assert redactor.calls, "redactor was never called"
    assert "4532015112830366" not in llm.prompts[0]
    assert "<REDACTED_CREDIT_CARD>" in llm.prompts[0]


def test_product_names_reach_the_model():
    llm = StubAgent(output=_extracted())
    agent = InvoiceExtractorAgent(llm, RecordingRedactor())

    agent.extract("Ham Jamboree $11.00")

    assert "Ham Jamboree" in llm.prompts[0]


def test_empty_markdown_never_calls_the_model():
    llm = StubAgent(output=_extracted())
    agent = InvoiceExtractorAgent(llm, RecordingRedactor())

    assert agent.extract("   \n  ") is None
    assert llm.prompts == []


def test_order_without_line_items_is_treated_as_no_order():
    empty = ExtractedOrder(
        overall_cost=Decimal("0"),
        total_tax=Decimal("0"),
        total_amount=Decimal("0"),
        products=[],
    )
    agent = InvoiceExtractorAgent(StubAgent(output=empty), RecordingRedactor())

    assert agent.extract("Some unrelated document") is None


@pytest.mark.parametrize(
    "error",
    [
        UnexpectedModelBehavior("model went off script"),
        ValidationError.from_exception_data("ExtractedOrder", []),
    ],
)
def test_unusable_model_output_returns_none(error):
    agent = InvoiceExtractorAgent(StubAgent(raises=error), RecordingRedactor())

    assert agent.extract("Not really an invoice") is None


def test_infrastructure_errors_propagate_so_the_caller_can_retry():
    # A provider outage is retryable; a bad document is not. Only the former
    # should escape.
    agent = InvoiceExtractorAgent(
        StubAgent(raises=ConnectionError("provider unreachable")),
        RecordingRedactor(),
    )

    with pytest.raises(ConnectionError):
        agent.extract("Coffee $10.00")

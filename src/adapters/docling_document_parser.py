import io

from docling.datamodel.base_models import DocumentStream
from docling.document_converter import DocumentConverter
from loguru import logger

from src.interfaces.document_parser import DocumentParser


class DoclingDocumentParser(DocumentParser):
    """Parses uploaded documents to markdown using docling.

    Constructing ``DocumentConverter`` loads models and is slow, so instances
    are cached in ``src.dependencies`` and reused by the worker.
    """

    def __init__(self):
        self.converter = DocumentConverter()

    def parse(self, content: bytes, filename: str = "document.pdf") -> str:
        if not content:
            return ""

        source = DocumentStream(name=filename, stream=io.BytesIO(content))
        try:
            result = self.converter.convert(source, raises_on_error=False)
        except Exception as exc:
            # An unreadable upload is an outcome to record, not a crash.
            logger.warning(f"docling could not parse {filename!r}: {exc}")
            return ""

        return result.document.export_to_markdown().strip()

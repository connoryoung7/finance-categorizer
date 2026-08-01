from abc import ABC, abstractmethod


class DocumentParser(ABC):
    """Converts an uploaded document into markdown for downstream extraction."""

    @abstractmethod
    def parse(self, content: bytes, filename: str = "document.pdf") -> str:
        """Convert document bytes to markdown.

        Implementations must return an empty string for unreadable or
        content-free documents rather than raising -- an uploaded PDF may
        legitimately contain nothing useful, and that is a recorded outcome,
        not an error.

        Args:
            content: The raw document bytes.
            filename: Original filename, used only to infer the format.

        Returns:
            The document as markdown, or ``""`` if nothing could be read.
        """
        pass

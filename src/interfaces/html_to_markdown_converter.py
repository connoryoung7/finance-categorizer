from abc import ABC, abstractmethod


class HTMLToMarkdownConverter(ABC):
    @abstractmethod
    def convert(self, html: str) -> str:
        pass

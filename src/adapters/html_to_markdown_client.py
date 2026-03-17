from html_to_markdown import convert_to_markdown

from src.interfaces.html_to_markdown_converter import HTMLToMarkdownConverter


class HTMLToMarkdownClient(HTMLToMarkdownConverter):
    def convert(self, html: str) -> str:
        return convert_to_markdown(html)

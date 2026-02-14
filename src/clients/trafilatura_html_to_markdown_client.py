from trafilatura import extract

from src.interfaces.html_to_markdown_converter import HTMLToMarkdownConverter


class TrafilaturaHTMLToMarkdownClient(HTMLToMarkdownConverter):
    def convert(self, html: str) -> str:
        result = extract(html, output_format="markdown")
        return result or ""

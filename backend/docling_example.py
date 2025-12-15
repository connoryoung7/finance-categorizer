from docling.document_converter import DocumentConverter


def main():
    converter = DocumentConverter()

    document = converter.convert("https://jaspr.co/")

    print(document.document.export_to_markdown())

if __name__ == "__main__":
    main()
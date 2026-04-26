import os

from dotenv import load_dotenv
from nylas import Client
import tiktoken

from src.adapters.html_to_markdown_client import HTMLToMarkdownClient
from src.config import settings

load_dotenv()

nylas_client = Client(settings.nylas_api_key, settings.nylas_api_uri)
grant_id = settings.nylas_grant_id
converter = HTMLToMarkdownClient()
encoding = tiktoken.get_encoding("o200k_base")

messages = nylas_client.messages.list(
    identifier=grant_id,
    query_params={
        "search_query_native": "category:purchases",
        "limit": 100,
    },  # type: ignore
)


for message in messages.data[0:25]:
    print(f"{message.id}, {message.subject}\n")
    from_email = message.from_[0].get("email")
    if message.from_:
        print("From:", message.from_[0].get("name"), "<" + from_email + ">")

    if not message.body:
        continue

    os.makedirs(f"parsed_messages/{from_email}", exist_ok=True)

    markdown = converter.convert(message.body)
    num_tokens = len(encoding.encode(markdown))
    print(f"Tokens: {num_tokens}\n")

    with open(
        f"parsed_messages/{from_email}/{message.id}.md", "w", encoding="utf-8"
    ) as f:
        f.write(markdown)

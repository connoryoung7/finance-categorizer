import os

from dotenv import load_dotenv
from nylas import Client

from config import settings

load_dotenv()

nylas_client = Client(
    settings.nylas_api_key,
    settings.nylas_api_uri
)
grant_id = settings.nylas_grant_id

messages = nylas_client.messages.list(
  identifier=grant_id,
  query_params={
    "search_query_native": "category:purchases",
    "limit": 100,
  } # type: ignore
)


for message in messages.data[0:25]:
    print(f"{message.id}, {message.subject}\n")
    from_email = message.from_[0].get("email")
    if message.from_:
        print("From:",
                message.from_[0].get("name"),
                "<" + from_email + ">")

    if not message.body:
        continue

    os.makedirs(f"parsed_messages/{from_email}", exist_ok=True)

    print("\n""Converted Content:\n")
    with open(
            f"parsed_messages/{from_email}/{message.id}.html", "w",
            encoding="utf-8"
        ) as f:
        # converted = convert_with_metadata(
        #     message.body,
        #     metadata_config=MetadataConfig(extract_links=False, extract_images=False)
        #     )
        # f.write(converted[0])
        # print(converted[1])
        f.write(message.body)

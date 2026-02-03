from typing import List

from toon_format import toon

from src.models.budget import Category
from src.models.order import Order


class OrderCategorizerAgent:
    def __init__(self, llm_client):
        # TODO: this LLM client should just be a PydanticAI Agent.
        self.llm_client = llm_client

    def categorize_order_content(self, order_content: str, categories: List[Category]) -> Order | None:
        """
        Categorize an order based on its content using an LLM.

        :param order_content: The content of the order in Markdown format.
        :param categories: A list of Category objects representing predefined categories.
        :return: An Order object with the assigned category, or None if categorization fails.
        """
        # Placeholder for categorization logic using llm_client
        response = self.llm_client.chat(messages=[
            {
                "role": "system",
                "content": """You are an expert order categorization agent. You will receive order details in Markdown format
                and must categorize them accurately. You will also be provided with predefined categories
                that will be in TOON format."""
            },
            {
            "role": "user",
                "content": f"""
                order content:        
                {order_content}

                '''toon
                categories{toon.encode(categories)}
                '''
                """
            }
        ])

        return response

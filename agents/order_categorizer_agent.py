from backend.models.budget import Category
from backend.models.order import Order

class OrderCategorizerAgent:
    def __init__(self, llm_client):
        # TODO: this LLM client should just be a PydanticAI Agent.
        self.llm_client = llm_client

    def __categorize_order_content(self, order_content: str, categories: List[Category]) -> Order | None:
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
                "content": f"{order_content}"
            }
        ])

        return response 

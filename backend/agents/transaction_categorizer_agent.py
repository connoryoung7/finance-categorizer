from ddgs import DDGS
from mistralai import Mistral

class OrderCategorizerAgent:
    def __init__(self, llm_client: Mistral):
        mistral_client = llm_client
        model = "mistral-medium-latest"
        pass

    def categorize_transaction_by_payee_name(self, payee_name: str):
        self.llm_client.chat.complete(
            model=self.model,
            messages=[
                {
                    "system": "system",
                    "content": """
                    You are a data labeller for a credit card company. You will be given all the possible categories that a transaction can be in the form of JSON.
                    It is your job to take that payee name, and match it to the category that you think that it's suppose to be.
                    If addition to your categorization, you will also provide a confidence level which will denote how likely this categorization
                    is.
                    """
                },
                {
                    "role": "user",
                    "content": ""
                }
            ]
        )

    def search_payee_name_on_internet(payee_name):
        DDGS().text(payee_name, max_results=3)
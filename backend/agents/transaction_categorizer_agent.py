from ddgs import DDGS
from mistralai import Mistral

from dataclasses import dataclass

@dataclass
class CategorizationResult:
    category_id: str
    confidence_level: float

class OrderCategorizerAgent:
    def __init__(self, llm_client: Mistral, categories: List[str]):
        mistral_client = llm_client
        model = "mistral-medium-latest"
        categories = categories
        pass

    def categorize_transaction(self, transaction: Transaction) -> None:
        self.__categorize_transaction_by_payee_name(payee_name=transaction.payee_name)
    def __categorize_transaction_by_payee_name(self, payee_name: str):
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
                    "content": "categorizes: f{JSON.stringify(categories)} payee_name: {payee_name}"
                }
            ],
            temperature=0.0
        )

    def categorize_internet(self, transaction: Transaction):
        self.llm_client.chat.complete(
            model=self.model,
            messages=[
                {
                    "system": "system",
                    "content": """
                    You are a data labeller for a credit card company. You will be given all the possible categories that a transaction can be in the form of JSON.
                    You will also be given the search results for the payee name on the internet. By looking at the different search results, you want to determine
                    what the category of the transaction is. If addition to your categorization, you will also provide a confidence level which will denote how likely this categorization is.
                    """
                },
                {
                    "role": "user",
                    "content": ""
                }
            ],
            temperature=0.0
        )

    def __search_payee_name_on_internet(payee_name):
        results = DDGS().text(payee_name, max_results=3)
        results.get_text()
        
        return results
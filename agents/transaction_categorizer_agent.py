from dataclasses import dataclass
import json
from typing import List

from ddgs import DDGS
from mistralai import Mistral, SystemMessage, UserMessage
from pydantic import BaseModel

from models.budget import Category, ConfidenceLevel, Transaction
from services.transaction_service import TransactionService


class CategorizationResult(BaseModel):
    category_id: str
    confidence_level: float

@dataclass
class SearchResult:
    title: str
    href: str
    body: str

class CategorizeTransactionAgent:
    """
    This is an agent that is responsible for retrieving transaction data and the categories that the transaction could be 
    categorized as and assigning a category for the transaction.
    """
    def __init__(self, llm_client: Mistral, transaction_service: TransactionService, categories: List[Category]):
        self.mistral_client = llm_client
        self.model = "ministral-8b-latest"
        self.transaction_service = transaction_service
        self.categories = categories

    def categorize_transaction(self, transaction: Transaction) -> None:
        if transaction.amount >= 0: 
            print(f"Skipping categorization for transaction {transaction.id} as it is not an expense.")
            return
        if not transaction.payee_name:
            raise ValueError("Transaction must have a payee name to be categorized.")
        
        category_id = self.transaction_service.determine_category_for_payee(payee_id=transaction.payee_id or "")
        if category_id:
            print(f"Categorized transaction {transaction.id} by payee history to category {category_id}")
            self.transaction_service.categorize_transaction(transaction=transaction, category_id=category_id)
        else:
            if not transaction.payee_name:
                raise ValueError("Transaction must have a payee name to be categorized.")
            
            result = self.categorize_from_web_search_internet(transaction=transaction)
            print(f"Categorized transaction {transaction.id} by web search to category {result.category_id} with confidence {result.confidence_level}")

            if (result.confidence_level * 100) >= ConfidenceLevel.HighConfidence.value:
                self.transaction_service.categorize_transaction(transaction=transaction, category_id=result.category_id)
            else:
                print(f"Skipping categorization for transaction {transaction.id} due to low confidence level of {result.confidence_level}")


    def categorize_from_web_search_internet(self, transaction: Transaction) -> CategorizationResult:
        search_results = self.__search_payee_name_on_internet(payee_name=transaction.payee_name or "")
        response = self.mistral_client.chat.parse(
            model=self.model,
            messages=[
                SystemMessage(
                    content="""
                    You are a data labeller for a credit card company. You will be given all the possible categories that a transaction can be in the form of JSON.
                    You will also be given the search results for the payee name on the internet. By looking at the different search results, you want to determine
                    what the category of the transaction is. If addition to your categorization, you will also provide a confidence level which will denote how likely this categorization is.
                    For context, if you can guarantee that the payee name matches the category, you should provide a confidence level of 0.95 or higher.
                    If there is some uncertainty, you should provide a confidence level between 0.90 and 0.95. If you are unsure, you should provide a confidence level below 0.90.
                    """
                ),
                UserMessage(content=f"categorizes: {json.dumps([c.model_dump_json() for c in self.categories])} search_results: {search_results}")
            ],
            response_format=CategorizationResult,
            temperature=0.0
        )

        return CategorizationResult.model_validate(response.choices[0].message.parsed)

    def __search_payee_name_on_internet(self, payee_name: str, max_results: int = 3) -> List[SearchResult]:
        """Makes a web search on the DuckDuckGo search engine"""
        
        with DDGS() as ddgs:
            search_results = ddgs.text(query=payee_name, max_results=max_results)
            results = []
            for r in search_results:
                results.append(SearchResult(r['title'], href=r['href'], body=r['body']))
        
        return results

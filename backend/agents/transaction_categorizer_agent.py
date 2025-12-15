from ddgs import DDGS
from mistralai import Mistral, SystemMessage, UserMessage

from dataclasses import dataclass
import json
from typing import List

from models.budget import Category, Transaction
from services.transaction_service import TransactionService

@dataclass
class CategorizationResult:
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
        self.model = "mistral-medium-latest"
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
            
            # self.__categorize_transaction_by_payee_name(payee_name=transaction.payee_name)
            print(f"Could not categorize transaction {transaction.id} by payee history.")
    
    def __categorize_transaction_by_payee_name(self, payee_name: str):
        response = self.mistral_client.chat.complete(
            model=self.model,
            messages=[
                SystemMessage(
                    content="""
                    You are a data labeller for a credit card company. You will be given all the possible categories that a transaction can be in the form of JSON.
                    It is your job to take that payee name, and match it to the category that you think that it's suppose to be.
                    If addition to your categorization, you will also provide a confidence level which will denote how likely this categorization
                    is.
                    """
                ),
                UserMessage(
                    content=f"categorizes: {json.dumps([c.model_dump_json   () for c in self.categories])} payee_name: {payee_name}"
                )
            ],
            temperature=0
        )

        print(response.choices[0].message.content)

    def categorize_from_web_search_internet(self, transaction: Transaction):
        search_results = self.__search_payee_name_on_internet(payee_name=transaction.payee_name or "")
        self.mistral_client.chat.complete(
            model=self.model,
            messages=[
                SystemMessage(
                    content="""
                    You are a data labeller for a credit card company. You will be given all the possible categories that a transaction can be in the form of JSON.
                    You will also be given the search results for the payee name on the internet. By looking at the different search results, you want to determine
                    what the category of the transaction is. If addition to your categorization, you will also provide a confidence level which will denote how likely this categorization is.
                    """
                ),
                UserMessage(content=f"categorizes: {json.dumps(self.categories)} search_results: {search_results}")
            ],
            temperature=0.0
        )

    def __search_payee_name_on_internet(self, payee_name: str, max_results: int = 3) -> List[SearchResult]:
        """Makes a web search on the DuckDuckGo search engine"""
        
        with DDGS() as ddgs:
            search_results = ddgs.text(query=payee_name, max_results=max_results)
            results = []
            for r in search_results:
                results.append(SearchResult(r['title'], href=r['href'], body=r['body']))
        
        return results

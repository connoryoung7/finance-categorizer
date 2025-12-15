from typing import List

import ynab

from models.budget import Category, CategoryGroup, Transaction

class YNABClient:
    def __init__(self, access_token: str, budget_id: str) -> None:
        self.configuration = ynab.Configuration(
            host="https://api.ynab.com/v1",
            access_token=access_token
        )
        self.budget_id = budget_id

    @staticmethod
    def __filter_special_chars(s: str) -> str:
        """Filters out special characters from a string, leaving only alphanumeric characters and spaces."""
        return ''.join(char for char in s if char.isalnum() or char == " ")

    def get_categories(self) -> List[Category]:
        with ynab.ApiClient(self.configuration) as api_client:
            api_instance = ynab.CategoriesApi(api_client)
            try:
                response = api_instance.get_categories(budget_id=self.budget_id)
                categories: List[Category] = []
                for group in response.data.category_groups:
                    category_group = CategoryGroup(id=group.id, name=group.name)
                    for c in group.categories:
                        categories.append(
                            Category(
                                id=c.id,
                                name=YNABClient.__filter_special_chars(c.name),
                                category_group=category_group,
                            )
                        )
                    
                return categories
            except Exception as e:
                print(e)
                raise e

    def get_uncategorized_transactions(self, limit: int = 20) -> List[Transaction]:
        """
        Docstring for get_uncategorized_transactions
        
        :param self: Description
        :param limit: The maximum number of transactions to retrieve
        :type limit: int 
        :return: A list of uncategorized transactions
        :rtype: List[Transaction]
        """
        with ynab.ApiClient(self.configuration) as api_client:
            api_instance = ynab.TransactionsApi(api_client)
            response = api_instance.get_transactions(budget_id=self.budget_id, type="uncategorized")
            transactions = []
            for t in response.data.transactions:
                transactions.append(
                    Transaction(
                        id=t.id,
                        payee_id=t.payee_id,
                        payee_name=t.payee_name,
                        date=t.var_date.strftime("%Y-%m-%d"), # type: ignore
                        amount=t.amount,
                        memo=t.memo,
                        category_id=t.category_id,
                        category_name=t.category_name,
                        approved=t.approved,
                    )
                )
            
            return transactions


    def get_payees_by_name(self, name: str):
        with ynab.ApiClient(self.configuration) as api_client:
            api_instance = ynab.PayeesApi(api_client)
            try:
                response = api_instance.get_payees(
                    budget_id=self.budget_id,
                )
                return response.data
            except Exception as e:
                print("Exception when calling PayeesAPI->get_payees: %s\n" % e)

    def categorize_transaction(self, transaction: Transaction):
        with ynab.ApiClient(self.configuration) as api_client:
            api_instance = ynab.TransactionsApi(api_client)
            try:
                transaction_id = transaction.id

                response = api_instance.update_transaction(
                    budget_id=self.budget_id,
                    transaction_id=transaction_id,
                    data=ynab.PutTransactionWrapper(transaction=ynab.ExistingTransaction(
                        category_id=transaction.category_id
                    ))
                )
                print(response.data)
                return response.data
            except Exception as e:
                raise e

    def get_transactions_by_payee_id(self, payee_id: str) -> List[Transaction]:
        with ynab.ApiClient(self.configuration) as api_client:
            api_instance = ynab.TransactionsApi(api_client)
            try:
                api_instance = ynab.TransactionsApi(api_client)

                response = api_instance.get_transactions_by_payee(
                    budget_id=self.budget_id,
                    payee_id=payee_id,
                )
                
                transactions: List[Transaction] = []
                
                for t in response.data.transactions:
                    transactions.append(
                        Transaction(
                            id=t.id,
                            payee_id=t.payee_id,
                            payee_name=t.payee_name,
                            date=t.var_date.strftime("%Y-%m-%d"),
                            amount=t.amount,
                            memo=t.memo,
                            category_id=t.category_id,
                            category_name=t.category_name,
                            approved=t.approved,
                        )
                    )
                return transactions
            except Exception as e:
                raise e
from typing import List

import ynab

from models.budget import Category, CategoryGroup, Transaction

class YNABClient:
    def __init__(self, access_token: str):
        self.configuration = ynab.Configuration(
            host="https://api.ynab.com/v1",
            access_token=access_token
        )

    @staticmethod
    def __filter_special_chars(s: str) -> str:
        return ''.join(char for char in s if char.isalnum() or char == " ")

    def get_categories(self, budget_id: str) -> List[Category]:
        with ynab.ApiClient(self.configuration) as api_client:
            api_instance = ynab.CategoriesApi(api_client)
            try:
                response = api_instance.get_categories(budget_id=budget_id)
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

    def get_transactions(self, budget_id: str):
        with ynab.ApiClient(self.configuration) as api_client:
            api_instance = ynab.TransactionsApi(api_client)
            try:
                response = api_instance.get_transactions(budget_id=budget_id)
                return response.data
            except Exception as e:
                print("Exception when calling get_transactions")

    def get_uncategorized_transactions(self, budget_id: str, payee_id: str) -> None:
        with ynab.ApiClient(self.configuration) as api_client:
            # Create an instance of the API class
            api_instance = ynab.TransactionsApi(api_client)
            try:
                response = api_instance.get_transactions_by_payee(
                    budget_id=budget_id,
                    payee_id=payee_id,
                )

                return response.data
            except Exception as e:
                print("Exception when calling TransactionsApi->get_transactions: %s\n" % e)


    def get_payees_by_name(self, budget_id: str, name: str):
        with ynab.ApiClient(self.configuration) as api_client:
            # Create an instance of the API class
            api_instance = ynab.PayeesApi(api_client)
            try:
                response = api_instance.get_payees(
                    budget_id=budget_id,
                )
                # print(response.data)
                return response.data
            except Exception as e:
                print("Exception when calling PayeesAPI->get_payees: %s\n" % e)

    def categorize_transaction(self, budget_id: str, transaction_id: str, transaction_data: dict):
        with ynab.ApiClient(self.configuration) as api_client:
            api_instance = ynab.TransactionsApi(api_client)
            try:
                data = ynab.PutTransactionWrapper.from_dict({"transaction": transaction_data})

                response = api_instance.update_transaction(
                    budget_id=budget_id,
                    transaction_id=transaction_id,
                    data=data
                )
                return response.data
            except Exception as e:
                print(e)

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
                            payee_name=t.payee_name
                        )
                    )
                return transactions
            except Exception as e:
                print(e)
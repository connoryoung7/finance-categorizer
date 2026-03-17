class DomainError(Exception):
    pass

class TransactionDoesNotExist(DomainError):
    def __init__(self, transaction_id: str):
        super().__init__(f"unknown transaction: {transaction_id}")
        self.transaction_id = transaction_id

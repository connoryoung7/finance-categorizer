from sqlalchemy import Engine

from models.budget import PayeeCategorization


class BudgetRepo:
    def __init___(self, db: Engine):
        self.db = db
    
    def get_payee_categorization(self, payee_id: str) -> PayeeCategorization | None:
        """Retrieve budget data from the database."""
        pass

    def create_payee_categorization(self, payee_id: str, category_id: str, status: str) -> None:
        """Create a new budget entry in the database."""
        pass

    def update_payee_categorization(self, payee_id: str, category_id: str, status: str) -> None:
        """Update an existing budget entry in the database."""
        pass
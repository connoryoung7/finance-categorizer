from src.models.email import EmailCategory
from src.models.budget import Email

class EmailCategorizerAgent:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def categorize_email_content(self, email: Email) -> EmailCategory:
        pass

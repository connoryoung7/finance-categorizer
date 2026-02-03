from src.models.email import Email, EmailCategory


class EmailCategorizerAgent:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def categorize_email_content(self, email: Email) -> EmailCategory:
        """
        
        
        :param self: Description
        :param email: The incoming email that was sent to the personan inbox
        :type email: Email
        :return: Description
        :rtype: EmailCategory
        """
        pass

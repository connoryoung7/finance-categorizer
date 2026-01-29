from models.email import Email

class EmailRouter:
    def __init__(self) -> None:
        pass

    def route_email(self, email: Email) -> None:
        if email.from_ == "auto-confirm@amazon.com":
            # Process Amazon purchase confirmation emails
            pass

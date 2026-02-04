import httpx


class NotificationService:
    def __init__(self, base_url: str, access_token: str):
        self.base_url = base_url
        self.access_token = access_token

    def send_notification(self, topic: str, message: str) -> None:
        '''
        Sends a notification to the specified topic with the given
        message in Markdown format.

        :param self: Description
        :param topic: Description
        :type topic: str
        :param message: Description
        :type message: str
        '''
        httpx.post(
            url=self.__format_api_url(topic),
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Markdown": "yes",
            },
            data={"message": message},
        )

    def __format_api_url(self, topic: str) -> str:
        return f"{self.base_url}/{topic}"

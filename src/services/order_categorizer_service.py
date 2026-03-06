class OrderCategorizerService:
    def __init__(self):
        pass

    def categorize_order(self, order):
        """
        Categorize an order based on predefined rules.

        :param order: A dictionary representing the order details.
        :return: The category name if a match is found, otherwise 'Uncategorized'.
        """
        for category, rule in self.category_rules.items():
            if rule(order):
                return category
        return "Uncategorized"

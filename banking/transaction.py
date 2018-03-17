"""Module implementing features of a bank transaction"""

class Transaction:
    """Class representing a bank transaction"""
    def __init__(self, date, description, amount, *, counterparty=None, category=None):
        self.date = date
        self.description = description
        self.amount = amount
        self.counterparty = counterparty
        self.category = category if category else category_from_description(description)

    def __str__(self):
        return ("| {:10} | {:>9} | {:30} | {:20} | {:15} |"
                "".format(self.date[:10],
                          " £{:.2f}".format(self.amount) if self.amount >= 0
                          else "-£{:.2f}".format(-self.amount),
                          self.description[:30],
                          self.counterparty[:20] if self.counterparty else "",
                          self.category[:15] if self.category else ""))

    def to_dict(self):
        """Return a dict representing the transaction"""
        return {
            "date": self.date,
            "amount": self.amount,
            "description": self.description,
            "counterparty": self.counterparty,
            "category": self.category
        }

    @staticmethod
    def from_dict(transaction_dict):
        """Create a Transaction object from a dict definition"""
        return Transaction(transaction_dict["date"],
                           transaction_dict["description"],
                           transaction_dict["amount"],
                           counterparty=transaction_dict["counterparty"],
                           category=transaction_dict["category"])


def category_from_description(description):
    """TODO"""
    description = description

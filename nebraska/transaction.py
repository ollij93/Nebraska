"""Module implementing features of a bank transaction"""

from .category import Category

class Transaction:
    """Class representing a bank transaction"""
    def __init__(self, date, description, amount, balance_after, categories, *,
                 counterparty=None, category_override=None):
        self.date = date
        self.description = description
        self.amount = amount
        self.balance_after = balance_after
        self.counterparty = counterparty
        self._category = Category.from_description(categories,
                                                   description=description,
                                                   counterparty=counterparty)
        self._category_override = category_override

    def __str__(self):
        return ("| {:10} | {:>9} | {:30} | {:20} | {:15} |"
                "".format(self.date[:10],
                          " £{:.2f}".format(self.amount) if self.amount >= 0
                          else "-£{:.2f}".format(-self.amount),
                          self.description[:30],
                          self.counterparty[:20] if self.counterparty else "",
                          self.get_category().get_name()[:15]))

    def __eq__(self, other):
        return (self.__class__ == other.__class__
                and self.date == other.date
                and self.description == other.description
                and self.amount == other.amount
                and self.balance_after == other.balance_after
                and self.counterparty == other.counterparty)

    def get_category(self):
        """Return the category of this transaction"""
        return self._category_override if self._category_override else self._category

    def set_category_override(self, override):
        """Set the category override for this transaction"""
        self._category_override = override

    def to_dict(self):
        """Return a dict representing the transaction"""
        ret = {
            "date": self.date,
            "amount": self.amount,
            "description": self.description,
            "counterparty": self.counterparty,
            "balance_after": self.balance_after
        }
        if self._category_override:
            ret["category_override"] = self._category_override.get_name()
        return ret

    @staticmethod
    def from_dict(categories, transaction_dict):
        """Create a Transaction object from a dict definition"""
        return Transaction(transaction_dict["date"],
                           transaction_dict["description"],
                           transaction_dict["amount"],
                           transaction_dict["balance_after"],
                           categories,
                           counterparty=transaction_dict["counterparty"],
                           category_override=(Category.get_category(transaction_dict["category_override"])
                                              if "category_override" in transaction_dict
                                              else None))

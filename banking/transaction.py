"""Module implementing features of a bank transaction"""

class Transaction:
    """Class representing a bank transaction"""
    def __init__(self, date, description, amount, balance_after, known_descriptions, *, #pylint: disable=R0913
                 counterparty=None, category_override=None):
        self.date = date
        self.description = description
        self.amount = amount
        self.balance_after = balance_after
        self.counterparty = counterparty
        self._category = category_from_description(known_descriptions, description, counterparty)
        self._category_override = category_override

    def __str__(self):
        return ("| {:10} | {:>9} | {:30} | {:20} | {:15} |"
                "".format(self.date[:10],
                          " £{:.2f}".format(self.amount) if self.amount >= 0
                          else "-£{:.2f}".format(-self.amount),
                          self.description[:30],
                          self.counterparty[:20] if self.counterparty else "",
                          self.get_category()[:15]))

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
            ret["category_override"] = self._category_override
        return ret

    @staticmethod
    def from_dict(known_descriptions, transaction_dict):
        """Create a Transaction object from a dict definition"""
        return Transaction(transaction_dict["date"],
                           transaction_dict["description"],
                           transaction_dict["amount"],
                           transaction_dict["balance_after"],
                           known_descriptions,
                           counterparty=transaction_dict["counterparty"],
                           category_override=(transaction_dict["category_override"]
                                              if "category_override" in transaction_dict
                                              else None))


def category_from_description(known_descriptions, description, counterparty=None):
    """
    Get the category of the given transaction
    """
    for key in known_descriptions:
        category = known_descriptions[key]
        descriptions = category["descriptions"] if "descriptions" in category else []
        counterparts = category["counterparts"] if "counterparts" in category else []
        if (counterparty is not None and counterparty in counterparts
                or any([description.startswith(desc)
                        for desc in descriptions])):
            return key

    return "Unknown"

"""Module implementing features of a bank account"""
from .transaction import Transaction

class Account:
    """Class representing a bank account"""
    def __init__(self, name, transactions=None):
        self.name = name
        self._transactions = transactions if transactions else list()

    def add_transaction(self, transaction):
        """Add a transaction to the list of transactions"""
        self._transactions.append(transaction)

    def get_transactions(self):
        """Return the list of transactions for this account"""
        return self._transactions

    def to_dict(self):
        """Return a dict representing the account"""
        return {
            "name": self.name,
            "transactions": [
                transaction.to_dict()
                for transaction in self._transactions
            ]
        }

    @staticmethod
    def from_dict(account_dict):
        """Create an Account object from a dict definition"""
        ret = Account(account_dict["name"])
        for transaction in account_dict["transactions"]:
            ret.add_transaction(Transaction.from_dict(transaction))
        return ret

    def dump(self):
        """Print all the information for this account"""
        print("-" * 100)
        print("| {:96} |".format(self.name.upper()))
        print("-" * 100)
        for transaction in self._transactions:
            print(transaction)

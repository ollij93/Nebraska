"""Module implementing features of a bank account"""

from .transaction import Transaction

class Account:
    """Class representing a bank account"""
    def __init__(self, name, transactions=None):
        self.name = name
        self._transactions = transactions if transactions else list()

    def __str__(self):
        return self.name

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

    def update_from_fresh(self, fresh_account):
        """Update the existing account with a fresh account from the web"""
        for fresh_transaction in fresh_account.get_transactions():
            for transaction in self.get_transactions():
                if transaction == fresh_transaction:
                    # This (fresh) transaction is already in the existing
                    # account so no need to update
                    break
            else:
                # Existing version of this transaction not found so add it to
                # the existing account
                self._transactions.append(fresh_transaction)
        self._transactions = sorted(self._transactions, key=lambda x: x.date)

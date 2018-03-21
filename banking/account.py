"""Module implementing features of a bank account"""
from ._common import BasePrompt
from .transaction import Transaction, TransactionPrompt

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
    def from_dict(known_descriptions, account_dict):
        """Create an Account object from a dict definition"""
        ret = Account(account_dict["name"])
        for transaction in account_dict["transactions"]:
            ret.add_transaction(Transaction.from_dict(known_descriptions, transaction))
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


class AccountPrompt(BasePrompt):
    """Account level cmd prompt for the interactive mode"""
    def __init__(self, paging_on, known_descriptions, accounts, account):
        super().__init__(paging_on, known_descriptions, accounts)
        self.prompt = "({}) ".format(account.name)
        self.account = account

    def do_transactions(self, arg):
        """
        Dump all the transactions for this account.
        Usage:
            transaction <mode> <option(s)>
        """
        args = arg.split()
        kwargs = [arg for arg in args if arg.startswith("-")]
        args = [arg for arg in args if arg not in kwargs]

        def arg_to_mode(arg):
            """Get transaction method to run from mode arg"""
            if arg == "date":
                return self.transactions_date
            return None

        if not args:
            self.account.dump()
        else:
            mode_method = arg_to_mode(args[0])
            if not mode_method:
                print("NOT IMPLEMENTED")
            elif len(args) == 1:
                print(mode_method.__doc__)
            else:
                mode_method(args[1:])

    def transactions_date(self, args):
        """
        Select a transaction by date.
        Usage:
            transaction date <from_date> [<to_date>]
        """
        if len(args) == 1:
            transactions = [t for t in self.account.get_transactions()
                            if t.date == args[0]]
        elif len(args) == 2:
            transactions = [t for t in self.account.get_transactions()
                            if t.date >= args[0] and t.date <= args[1]]
        else:
            print("Error: invalid args")
            print(self.transactions_date.__doc__)
            return

        if not transactions:
            print("No transactions found")
        elif len(transactions) == 1:
            TransactionPrompt(self.paging_on, self.known_descriptions, self.accounts,
                              transactions[0]).cmdloop()
        else:
            transaction = self._option_selection(transactions)
            if transaction is not None:
                TransactionPrompt(self.paging_on, self.known_descriptions, self.accounts,
                                  transaction).cmdloop()

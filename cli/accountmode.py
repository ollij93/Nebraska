"""
Account CLI mode
"""
from .common import BasePrompt
from .transactionmode import TransactionPrompt


class AccountPrompt(BasePrompt):
    """Account level cmd prompt for the interactive mode"""

    def __init__(self, paging_on, session, account):
        super().__init__(paging_on, session)
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

        options = None
        if not args:
            options = self.account.get_transactions()
        else:
            mode_method = arg_to_mode(args[0])
            if not mode_method:
                print("NOT IMPLEMENTED")
            elif len(args) == 1:
                print(mode_method.__doc__)
            else:
                options = mode_method(args[1:])

        transaction = None
        if options is not None:
            if len(options) == 1:
                transaction = options[0]
            else:
                transaction = self._option_selection(options)

        if transaction is not None:
            TransactionPrompt(self.paging_on, self.session, transaction).cmdloop()

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
                            if args[0] <= t.date <= args[1]]
        else:
            print("Error: Invalid args")
            print(self.transactions_date.__doc__)
            return

        return transactions

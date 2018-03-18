"""
interactive.py - handles the interactive mode of the bank processor
"""

__all__ = (
    "run"
)

import cmd
import io
import json
import os
import pydoc
import sys

NEBRASKA_DIR = os.path.join(os.path.expanduser("~"), ".nebraska")
if not os.path.exists(NEBRASKA_DIR):
    os.makedirs(NEBRASKA_DIR)

KNOWN_DESCS_FILE = os.path.join(NEBRASKA_DIR, "known_descriptions.json")
CONFIG_FILE = os.path.join(NEBRASKA_DIR, "config.json")
CACHE_FILE = os.path.join(NEBRASKA_DIR, "cache.json")

class BaseCmd(cmd.Cmd):
    """Base class for commands available on all prompts"""
    def __init__(self, paging_on):
        super().__init__()
        self.paging_on = paging_on
        self.out = None
        if paging_on:
            self.turn_paging_on()
        else:
            self.turn_paging_off()

    def precmd(self, line):
        self.start_pager()
        return line

    def postcmd(self, stop, line):
        self.flush_pager()
        return stop

    def turn_paging_on(self):
        """Turn on paging"""
        self.paging_on = True

    def turn_paging_off(self):
        """Turn off paging"""
        self.paging_on = False
        sys.stdout = sys.__stdout__

    def start_pager(self):
        """Start paging"""
        if self.paging_on:
            self.out = io.StringIO()
            sys.stdout = self.out

    def flush_pager(self):
        """Flush the pager"""
        sys.stdout = sys.__stdout__
        if self.paging_on and self.out is not None:
            pydoc.pager(self.out.getvalue())
        self.out = None

    def do_paging_off(self, _):
        """Turn paging off"""
        self.turn_paging_off()

    def do_paging_on(self, _):
        """Turn paging on"""
        self.turn_paging_on()

    def do_EOF(self, _): # pylint: disable=C0103
        """Handle EOF (AKA ctrl-d)."""
        print("")
        return self.do_exit(None)

    def do_exit(self, _): # pylint: disable=R0201
        """Exit this submode."""
        return True

    def _option_selection(self, options):
        """Have the user select one of the given options"""
        for index, option in enumerate(options):
            print("({:>3}) {}".format(index, option))
        self.flush_pager()

        option = None
        while True:
            try:
                choice = input("Choose (range 0:{}): ".format(len(options) - 1))
            except EOFError:
                print("")
                break
            # Exit option selection on empty input
            if not choice:
                break
            try:
                index = int(choice)
                option = options[index]
            except (ValueError, IndexError):
                pass
            else:
                break
        return option


class TopPrompt(BaseCmd):
    """Top level cmd prompt for the interactive mode"""
    intro = "Nebraska bank processing"
    prompt = "($$$) "

    def __init__(self, paging_on, known_descriptions, accounts):
        super().__init__(paging_on)
        self.known_descriptions = known_descriptions
        self.accounts = accounts

    def do_accounts(self, name):
        """Move to a given accounts mode"""
        if not name:
            for account in self.accounts:
                print(account.name)
        elif len(name.split()) > 1:
            print("Invalid arguments")
        else:
            for account in self.accounts:
                if account.name == name:
                    AccountPrompt(self.paging_on, account).cmdloop()
                    break
            else:
                print("Account not found")

    def do_dump(self, _):
        """Dump all the accounts and transactions"""
        for account in self.accounts:
            account.dump()

    def do_unknowns(self, _):
        """Print the unknown descriptions and counterparts"""
        unknowns = {"counterparty": set(), "description": set()}
        for transac in [t for acc in self.accounts
                        for t in acc.get_transactions()
                        if t.get_category() == "Unknown"]:
            if transac.counterparty:
                unknowns["counterparty"].add(transac.counterparty)
            else:
                unknowns["description"].add(transac.description)

        for key in [k for k in unknowns if unknowns[k]]:
            unknowns[key] = sorted(unknowns[key])
            print("Unknown {}s:".format(key))
            for unknown in unknowns[key]:
                print("  {}".format(unknown))

    def do_net(self, _):
        """Print the total income and expendature and the net amount"""
        # Calculate total income and expendature
        income = 0
        expendature = 0
        for transac in [t for acc in self.accounts for t in acc.get_transactions()]:
            if transac.amount > 0:
                income += transac.amount
            else:
                expendature += transac.amount
        print(u"Total income: \xA3{:0.2f}".format(income))
        print(u"Total expend:-\xA3{:0.2f}".format(abs(expendature)))
        print(u"Net change:{}\xA3{:0.2f}".format(" -" if income < expendature else " ",
                                                 income + expendature))

    def do_breakdown(self, _):
        """Print the slim spending breakdown"""
        print("Spending breakdown:")
        income, spending = get_values_slim(self.accounts)

        # Handle diffs
        # Deleting from income so need to collect all keys before deleting
        keys = [k for k in income
                if (k in self.known_descriptions
                    and "diff" in self.known_descriptions[k]
                    and self.known_descriptions[k]["diff"])]
        for key in keys:
            if income[key] > abs(spending[key]):
                income[key] += spending[key]
                del spending[key]
            elif income[key] < abs(spending[key]):
                spending[key] += income[key]
                del income[key]
            else:
                del income[key]
                del spending[key]

        for values, name in [(income, "income"), (spending, "spending")]:
            print("  {}:".format(name))
            total = sum(values.values())
            for key in sorted(values.keys()):
                print(u"    ({:6.2f}%) {}: \xA3{:.2f}"
                      u"".format(100 * values[key] / total, key, values[key])
                      .replace(u"\xA3-", u"-\xA3"))

    def do_save(self, _):
        """Save the current state of the accounts to the users cache"""
        with open(CACHE_FILE, "w") as outfile:
            json.dump({"accounts": [account.to_dict() for account in self.accounts]},
                      outfile,
                      indent=4,
                      sort_keys=True)
            print("cache created")


class AccountPrompt(BaseCmd):
    """Account level cmd prompt for the interactive mode"""
    def __init__(self, paging_on, account):
        super().__init__(paging_on)
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
            TransactionPrompt(self.paging_on, transactions[0]).cmdloop()
        else:
            transaction = self._option_selection(transactions)
            if transaction is not None:
                TransactionPrompt(self.paging_on, transaction).cmdloop()


class TransactionPrompt(BaseCmd):
    """Transaction level cmd prompt for the interactive mode"""
    prompt = "(Transaction) "
    def __init__(self, paging_on, transaction):
        super().__init__(paging_on)
        self.transaction = transaction

    def do_show(self, _):
        """Show the current transactions data"""
        print(self.transaction)

    def do_override_category(self, arg):
        """Override the category for this transaction"""
        if not arg:
            print("No category given")
        elif len(arg.split()) > 1:
            print("Too many arguments. Only one category should be specified.")
        else:
            self.transaction.set_category_override(arg)


def get_values_slim(accounts):
    """Get the set of income and spending values by category"""
    income = {}
    spending = {}
    for transac in [t for acc in accounts for t in acc.get_transactions()]:
        cat = transac.get_category()
        values = spending if transac.amount < 0 else income

        if cat not in values:
            values[cat] = 0
        values[cat] += transac.amount

    for cat in [k for values in [income, spending]
                for k in values
                if values[k] == 0]:
        del values[cat]

    for cat in [k for k in income
                if k in spending and spending[k] == -income[k]]:
        # Spending and income perfectly balance so ignore
        del income[cat]
        del spending[cat]
    return income, spending


def run(known_descriptions, accounts):
    """Launch the interactive prompt"""
    TopPrompt(False, known_descriptions, accounts).cmdloop()

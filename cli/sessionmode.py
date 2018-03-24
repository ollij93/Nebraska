"""
Handles the CLI mode of the bank processor
"""

from cli.accountmode import AccountPrompt
from cli.categorymode import CategoryPrompt
from cli.common import BasePrompt
from nebraska.category import UNKNOWN

__all__ = (
    "run"
)

class SessionPrompt(BasePrompt):
    """Top level cmd prompt for the interactive mode"""
    intro = "Nebraska bank processing"
    prompt = "($$$) "

    def do_accounts(self, name):
        """Move to a given accounts mode"""
        if len(name.split()) > 1:
            print("INVALID ARGUMENTS")

        if not name:
            account = self._option_selection(self.session.accounts)
        else:
            for acc in self.session.accounts:
                if acc.name == name:
                    account = acc
                    break
            else:
                print("Account not found")
                return

        if account:
            AccountPrompt(self.paging_on, self.session, account).cmdloop()

    def do_categories(self, name):
        """Move to a given category mode"""
        if len(name.split()) > 1:
            print("INVALID ARGUMENTS")

        if not name:
            category = self._option_selection(self.session.categories)
        else:
            for cat in self.session.categories:
                if cat.name == name:
                    category = cat
                    break
            else:
                print("Category not found")
                return

        if category:
            CategoryPrompt(self.paging_on, self.session, category).cmdloop()

    def do_show(self, _):
        """Dump all the accounts and transactions"""
        for account in self.session.accounts:
            account.dump()

    def do_unknowns(self, _):
        """Print the unknown descriptions and counterparts"""
        unknowns = {"counterparty": set(), "description": set()}
        for transac in [t for acc in self.session.accounts
                        for t in acc.get_transactions()
                        if t.get_category() is UNKNOWN]:
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
        for transac in [t for acc in self.session.accounts for t in acc.get_transactions()]:
            if transac.amount > 0:
                income += transac.amount
            else:
                expendature += transac.amount
        print(u"Total income: \xA3{:0.2f}".format(income))
        print(u"Total expend:-\xA3{:0.2f}".format(abs(expendature)))
        print(u"Net change:{}\xA3{:0.2f}".format(" -" if income < expendature else " ",
                                                 income + expendature))

    def do_breakdown(self, args):
        """Print the slim spending breakdown"""
        args = args.split()
        if not args:
            from_date = None
            to_date = None
        elif args[0] == "date" and len(args) == 3:
            from_date = args[1]
            to_date = args[2]
        else:
            print("Invalid args")
            return
        income, spending = get_values_slim(self.session.accounts, from_date, to_date)

        # Handle diffs
        # Deleting from income so need to collect all keys before deleting
        keys = [k for k in income
                if (k in self.session.categories
                    and k in spending
                    and "diff" in self.session.categories[k]
                    and self.session.categories[k]["diff"])]
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

        print("Spending breakdown:")
        for values, name in [(income, "income"), (spending, "spending")]:
            print("  {}:".format(name))
            total = sum(values.values())
            for key in sorted(values.keys()):
                print(u"    ({:6.2f}%) {}: \xA3{:.2f}"
                      u"".format(100 * values[key] / total, key, values[key])
                      .replace(u"\xA3-", u"-\xA3"))



def get_values_slim(accounts, from_date=None, to_date=None):
    """Get the set of income and spending values by category"""
    income = {}
    spending = {}
    for transac in [t for acc in accounts for t in acc.get_transactions()
                    if ((not to_date or not from_date)
                            or (t.date <= to_date and t.date >= from_date))]:
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

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
                if cat.get_name() == name:
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
        from_date = None
        to_date = None
        if args:
            if args[0] == "date" and len(args) == 3:
                from_date = args[1]
                to_date = args[2]
            elif args:
                print("Invalid args")
                return
        income, spending = get_values_slim(self.session.accounts, from_date, to_date)

        # Handle diffs
        for key in [c for c in income if (c in spending and c.diff)]:
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
        for pairs, name in [(income, "income"), (spending, "spending")]:
            print("  {}:".format(name))
            total = sum([pair[1] for pair in pairs])
            for pair in sorted(pairs, key=lambda p: p[0].get_name()):
                print(u"    ({:6.2f}%) {}: \xA3{:.2f}"
                      u"".format(100 * pair[1] / total, pair[0].get_name(), pair[1])
                      .replace(u"\xA3-", u"-\xA3"))


def get_values_slim(accounts, from_date=None, to_date=None):
    """Get the set of income and spending values by category"""
    income = list()
    spending = list()

    for transac in [t for acc in accounts for t in acc.get_transactions()
                    if ((not to_date or not from_date)
                        or (to_date >= t.date >= from_date))]:
        category = transac.get_category()
        values = spending if transac.amount < 0 else income

        for index, entry in enumerate(values):
            if entry[0] is category:
                values[index] = (entry[0], entry[1] + transac.amount)
                break
        else:
            values.append((category, transac.amount))

    # Use the list comprehension to be able to remove from income and spending within the loop
    for income_index, (category, value) in enumerate([i for i in income]):
        for spending_index, pair in enumerate([s for s in spending]):
            if category is pair[0] and value == -pair[1]:
                del income[income_index]
                del spending[spending_index]

    return income, spending

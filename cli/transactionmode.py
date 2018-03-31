"""
Transaction CLI mode
"""
from .common import BasePrompt
from nebraska.category import Category

class TransactionPrompt(BasePrompt):
    """Transaction level cmd prompt for the interactive mode"""
    prompt = "(Transaction) "
    def __init__(self, paging_on, session, transaction):
        super().__init__(paging_on, session)
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
            self.transaction.set_category_override(Category.get_category(arg))

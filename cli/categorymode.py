"""
Category CLI mode
"""
from .common import BasePrompt

class CategoryPrompt(BasePrompt):
    """Category level cmd prompt for the CLI mode"""
    def __init__(self, paging_on, session, category):
        super().__init__(paging_on, session)
        self.prompt = "({}) ".format(category)
        self.category = category

    def do_show(self, _):
        """Show the category information"""
        print(self.category)
        print("Descriptions:")
        for desc in self.category.descriptions:
            print("- {}".format(desc))
        print("Counterparts:")
        for counterpart in self.category.counterparts:
            print("- {}".format(counterpart))

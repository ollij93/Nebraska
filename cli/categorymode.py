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
        print("diff: {}".format(self.category.diff))

        if self.category.descriptions:
            print("Descriptions:")
        for desc in self.category.descriptions:
            print("- {}".format(desc))

        if self.category.counterparts:
            print("Counterparts:")
        for counterpart in self.category.counterparts:
            print("- {}".format(counterpart))

    def do_add_description(self, description):
        """Add a description to the active category"""
        self.category.add_description(description)

    def do_add_counterpart(self, counterpart):
        """Add a counterpart to the active category"""
        self.category.add_counterpart(counterpart)

    def do_create_child(self, args):
        """Create a new child category with the given name"""
        args = args.split()
        if args and len(args) == 1:
            name = args[0]
            self.category.create_child(name)
        else:
            print("Invalid args")

    def do_child_category(self, name):
        """Move to a given child category mode"""
        if len(name.split()) > 1:
            print("INVALID ARGUMENTS")

        if not name:
            category = self._option_selection(self.category.get_children())
        else:
            for cat in self.session.categories:
                if cat.get_name() == self.category.get_name() + "--" + name:
                    category = cat
                    break
            else:
                print("Category not found")
                return

        if category:
            CategoryPrompt(self.paging_on, self.session, category).cmdloop()

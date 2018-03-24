"""Module implementing features of a bank transaction"""

class Category:
    """Class representing a transaction category"""
    _categories = []

    def __init__(self, name, *, parent=None):
        Category._categories.append(self)
        self.name = name
        self.descriptions = []
        self.counterparts = []

        self.children = []
        self.parent = parent
        if parent:
            parent.children.append(self)

    def __str__(self):
        if self.parent:
            return self.parent.__str__() + " -- " + self.name
        else:
            return self.name

    @staticmethod
    def from_dict(name, category_dict, *, parent=None):
        """Create a new category object from the dict"""
        ret = Category(name, parent=parent)
        if "descriptions" in category_dict:
            ret.descriptions = category_dict["descriptions"]
        if "counterparts" in category_dict:
            ret.counterparts = category_dict["counterparts"]
        if "children" in category_dict:
            for childname in category_dict["children"]:
                Category.from_dict(childname, category_dict["children"][childname], parent=ret)
        return ret

    @staticmethod
    def from_description(categories, *, description=None, counterparty=None):
        """Get the category from the given descriptions and/or counterparty"""
        for category in categories:
            if (counterparty is not None and counterparty in category.counterparts
                    or any([description.startswith(desc)
                            for desc in category.descriptions])):
                return category

        return UNKNOWN

    @staticmethod
    def get_category(name):
        """Get an existing category from the list"""
        for category in Category._categories:
            if category.name == name:
                return category

        print("Failed to find category {}".format(name))

# GLOBAL
UNKNOWN = Category("Unknown")

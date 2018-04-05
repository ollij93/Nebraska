"""Module implementing features of a bank transaction"""


class Category:
    """Class representing a transaction category"""
    _categories = []

    def __init__(self, name, *, parent=None, diff=False):
        Category._categories.append(self)
        self._name = name
        self.descriptions = []
        self.counterparts = []
        self.diff = diff

        self.children = []
        self.parent = parent
        if parent:
            parent.children.append(self)

    def __str__(self):
        return "Category({})".format(self.get_name())

    def get_name(self):
        """Get the full name of this category (including parent name)"""
        if self.parent:
            return "{}--{}".format(self.parent.get_name(), self._name)
        else:
            return self._name

    def get_children(self):
        """Get the list of child categories for this category"""
        return self.children

    def create_child(self, name):
        """Create a new child category with the given name"""
        Category(name, parent=self)

    def add_description(self, desc_string):
        """Add a description string to this category"""
        self.descriptions.append(desc_string)

    def add_counterpart(self, counterpart):
        """Add a counterpart to this category"""
        self.counterparts.append(counterpart)

    def to_dict(self):
        """Create a dict representing this category object"""
        ret = dict()
        if self.descriptions:
            ret["descriptions"] = self.descriptions
        if self.counterparts:
            ret["counterparts"] = self.counterparts
        if self.children:
            ret["children"] = dict()
            for child in self.children:
                ret["children"][child.get_name()] = child.to_dict()
        if self.diff:
            ret["diff"] = True
        return ret

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
        if "diff" in category_dict and category_dict["diff"]:
            ret.diff = True
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
            if category.get_name() == name:
                return category

        print("Failed to find category {}".format(name))


# GLOBAL
UNKNOWN = Category("Unknown")

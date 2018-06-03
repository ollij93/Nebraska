"""
Defines a nebraska Session
"""

import datetime
import json
import os
from .common import (
    NEBRASKA_DIR,
    CACHE_FILE,
    CATEGORIES_FILE,
    CONFIG_FILE
)
from .account import Account
from .category import Category

# Create the NEBRASKA_DIR is required
if not os.path.exists(NEBRASKA_DIR):
    os.makedirs(NEBRASKA_DIR)


class Session:
    """A nebraska user session"""

    def __init__(self):
        self.accounts = []
        self.config = {}
        self.categories = []

    def load(self, *, download=False):
        """Load the system data from the users nebraska dir"""
        raw_categories = {}
        if not os.path.exists(CATEGORIES_FILE):
            with open(CATEGORIES_FILE, "w") as jfile:
                json.dump(raw_categories, jfile, indent=4)
        else:
            with open(CATEGORIES_FILE, "r") as jfile:
                raw_categories = json.load(jfile)
                for name in raw_categories:
                    self.categories.append(Category.from_dict(name, raw_categories[name]))

        self.config = {"keys": {}, "ids": {}}
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as config_file:
                json.dump(self.config, config_file, indent=4)
        else:
            with open(CONFIG_FILE, "r") as config_file:
                self.config = json.load(config_file)

        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as infile:
                self.accounts = json.load(infile)['accounts']
                for index, account in enumerate(self.accounts):
                    self.accounts[index] = Account.from_dict(account)

        if download:
            self.update()

    def save(self):
        """Save the system data to the users nebraska dir"""
        with open(CACHE_FILE, "w") as outfile:
            json.dump({"accounts": [account.to_dict() for account in self.accounts]},
                      outfile,
                      indent=4,
                      sort_keys=True)
            print("cache created")

        with open(CATEGORIES_FILE, "w") as outfile:
            output = dict()
            for category in self.categories:
                output[category.get_name()] = category.to_dict()
            json.dump(output, outfile, indent=4, sort_keys=True)
            print("categories saved")

    def update(self):
        """Update the session by downloading the latest accounts from the web"""
        fresh_accounts = download_all_transactions(self.config)
        for fresh_acc in fresh_accounts:
            for account in self.accounts:
                if account.name == fresh_acc.name:
                    account.update_from_fresh(fresh_acc)
                    break
            else:
                self.accounts.append(fresh_acc)

    def create_category(self, name):
        """Create a new category with the given name"""
        self.categories.append(Category(name))


###########################################################
# DOWNLOAD TRANSACTIONS
###########################################################
DOWNLOAD_METHODS = []


def download_method(method):
    """Descriptor for banknodes to register their download method"""
    DOWNLOAD_METHODS.append(method)
    return method


from .banknodes import *  # pylint: disable=wrong-import-position


def download_all_transactions(config):
    """Load all the nodes and run their download methods"""
    accounts = []
    for method in DOWNLOAD_METHODS:
        accounts.extend(method(config,
                               datetime.date(2018, 1, 1),
                               datetime.date.today()))
    return accounts

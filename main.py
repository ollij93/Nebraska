#!/usr/bin/python3
"""
Main script for running the bank processor
"""
import argparse
import datetime
import importlib
import json
import os

import banknodes

from banking import interactive
from banking.account import Account

NEBRASKA_DIR = os.path.join(os.path.expanduser("~"), ".nebraska")
if not os.path.exists(NEBRASKA_DIR):
    os.makedirs(NEBRASKA_DIR)

CACHE_FILE = os.path.join(NEBRASKA_DIR, "cache.json")
KNOWN_DESCS_FILE = os.path.join(NEBRASKA_DIR, "known_descriptions.json")
CONFIG_FILE = os.path.join(NEBRASKA_DIR, "config.json")

###########################################################
# UNKNOWN DESCRIPTIONS
###########################################################
def get_default_category(known_descriptions, transac):
    """
    Get the category of the given transaction
    """
    counterpart = transac.counterparty
    description = transac.description
    for key in known_descriptions:
        category = known_descriptions[key]
        descriptions = category["descriptions"] if "descriptions" in category else []
        counterparts = category["counterparts"] if "counterparts" in category else []
        if (counterpart is not None and counterpart in counterparts
                or any([description.startswith(desc)
                        for desc in descriptions])):
            return key

    return "Unknown"


###########################################################
# PROCESS
###########################################################
def process_transaction_categorys(known_descriptions, transactions):
    """Add the category to each transaction in the list"""
    for transac in transactions:
        transac.category = get_default_category(known_descriptions, transac)


###########################################################
# PARSE ARGS
###########################################################
def parseargs():
    """Parse the cli arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cache', action='store_true',
                        help="Use the saved transactions file instead of "
                             "downloading from the web.")
    return parser.parse_args()


###########################################################
# INIT
###########################################################
def init():
    """Initialize by loading the config"""

    known_descriptions = {}
    if not os.path.exists(KNOWN_DESCS_FILE):
        with open(KNOWN_DESCS_FILE, "w") as jfile:
            json.dump(jfile, known_descriptions, indent=4)
    else:
        with open(KNOWN_DESCS_FILE, "r") as jfile:
            known_descriptions = json.load(jfile)

    config = {"keys": {}, "ids": {}}
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as config_file:
            json.dump(config_file, config, indent=4)
    else:
        with open(CONFIG_FILE, "r") as config_file:
            config = json.load(config_file)

    return known_descriptions, config


###########################################################
# DOWNLOAD TRANSACTIONS
###########################################################
def download_all_transactions(known_descriptions, config):
    """Load all the nodes and run their download methods"""
    accounts = []
    for module_name in banknodes.__all__:
        node = importlib.import_module("banknodes." + module_name)
        if hasattr(node, "download"):
            download_method = getattr(node, "download")
            account = download_method(config,
                                      datetime.date(2018, 1, 1),
                                      datetime.date.today())

            process_transaction_categorys(known_descriptions,
                                          account.get_transactions())
            accounts.append(account)
    return accounts


###########################################################
# MAIN
###########################################################
def main(known_descriptions, config, args):
    """Run the main method"""
    if args.cache:
        with open(CACHE_FILE, "r") as infile:
            accounts = json.load(infile)['accounts']
            for index, account in enumerate(accounts):
                accounts[index] = Account.from_dict(account)
    else:
        accounts = download_all_transactions(known_descriptions, config)
        with open(CACHE_FILE, "w") as outfile:
            json.dump({"accounts": [account.to_dict() for account in accounts]}, outfile)
            print("cache created")

    interactive.run(known_descriptions, accounts)

###########################################################
# Start of script
###########################################################
if __name__ == '__main__':
    ARGS = parseargs()
    DESCS, CONFIG = init()
    main(DESCS, CONFIG, ARGS)

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
    if not os.path.exists(interactive.KNOWN_DESCS_FILE):
        with open(interactive.KNOWN_DESCS_FILE, "w") as jfile:
            json.dump(jfile, known_descriptions, indent=4)
    else:
        with open(interactive.KNOWN_DESCS_FILE, "r") as jfile:
            known_descriptions = json.load(jfile)

    config = {"keys": {}, "ids": {}}
    if not os.path.exists(interactive.CONFIG_FILE):
        with open(interactive.CONFIG_FILE, "w") as config_file:
            json.dump(config_file, config, indent=4)
    else:
        with open(interactive.CONFIG_FILE, "r") as config_file:
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
                                      known_descriptions,
                                      datetime.date(2018, 1, 1),
                                      datetime.date.today())
            accounts.append(account)
    return accounts


###########################################################
# MAIN
###########################################################
def main(known_descriptions, config, args):
    """Run the main method"""
    accounts = []
    if os.path.exists(interactive.CACHE_FILE):
        with open(interactive.CACHE_FILE, "r") as infile:
            accounts = json.load(infile)['accounts']
            for index, account in enumerate(accounts):
                accounts[index] = Account.from_dict(known_descriptions, account)

    if not args.cache:
        fresh_accounts = download_all_transactions(known_descriptions, config)
        for fresh_acc in fresh_accounts:
            for account in accounts:
                if account.name == fresh_acc.name:
                    account.update_from_fresh(fresh_acc)
                    break
            else:
                accounts.append(fresh_acc)

    interactive.run(known_descriptions, accounts)

###########################################################
# Start of script
###########################################################
if __name__ == '__main__':
    ARGS = parseargs()
    DESCS, CONFIG = init()
    main(DESCS, CONFIG, ARGS)

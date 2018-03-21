#!/usr/bin/python3
"""
Main script for running the bank processor
"""
import argparse
import datetime
import importlib

import banknodes

from banking import run

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
def main(args):
    """Run the main method"""
    known_descriptions, config, accounts = run.init()

    if not args.cache:
        fresh_accounts = download_all_transactions(known_descriptions, config)
        for fresh_acc in fresh_accounts:
            for account in accounts:
                if account.name == fresh_acc.name:
                    account.update_from_fresh(fresh_acc)
                    break
            else:
                accounts.append(fresh_acc)

    run.run(known_descriptions, accounts)

###########################################################
# Start of script
###########################################################
if __name__ == '__main__':
    ARGS = parseargs()
    main(ARGS)

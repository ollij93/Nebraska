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

###########################################################
# INCOME and EXPENDATURE
###########################################################
def print_income_expendature(transactions):
    """
    Print the total income and expendature and the net amount
    """
    # Calculate total income and expendature
    income = 0
    expendature = 0
    for bank in transactions:
        for transac in transactions[bank]:
            if transac['amount'] > 0:
                income += transac['amount']
            else:
                expendature += transac['amount']
    print(u"Total income: \xA3{:0.2f}".format(income))
    print(u"Total expend:-\xA3{:0.2f}".format(abs(expendature)))
    print(u"Net change:{}\xA3{:0.2f}".format(" -" if income < expendature else " ",
                                             income + expendature))


###########################################################
# SPENDING BREAKDOWN (SLIM)
###########################################################
def print_spending_breakdown_slim(known_descriptions, transactions):
    """
    Print the slim spending breakdown
    """
    print("Spending breakdown:")
    income, spending = get_values_slim(known_descriptions, transactions)

    # Handle diffs
    # Deleting from income so need to collect all keys before deleting
    keys = [k for k in income]
    for key in keys:
        if (key in known_descriptions
                and "diff" in known_descriptions[key]
                and known_descriptions[key]["diff"]):
            if income[key] > abs(spending[key]):
                income[key] += spending[key]
                del spending[key]
            elif income[key] < abs(spending[key]):
                spending[key] += income[key]
                del income[key]
            else:
                del income[key]
                del spending[key]

    for values, name in [(income, "income"), (spending, "spending")]:
        print("  {}:".format(name))
        total = sum(values.values())
        for key in sorted(values.keys()):
            print(u"    ({:6.2f}%) {}: \xA3{:.2f}"
                  u"".format(100 * values[key] / total, key, values[key])
                  .replace(u"\xA3-", u"-\xA3"))


###########################################################
# UNKNOWN DESCRIPTIONS
###########################################################
def print_unknown_descriptions(known_descriptions, transactions):
    """
    Print the unknown descriptions and counterparts
    """
    unknowns = {"counterparty": set(), "description": set()}
    for bank in transactions:
        for transac in transactions[bank]:
            if get_catagory(known_descriptions, transac) == "Unknown":
                if "counterparty" in transac:
                    unknowns["counterparty"].add(transac["counterparty"])
                else:
                    unknowns["description"].add(transac["description"])

    for key in unknowns:
        unknowns[key] = sorted(unknowns[key])
        if unknowns[key]:
            print("Unknown {}s:".format(key))
            for unknown in unknowns[key]:
                print("  {}".format(unknown))


def get_catagory(known_descriptions, transac):
    """
    Get the category of the given transaction
    """
    counterpart = transac['counterparty'] if "counterparty" in transac else None
    description = transac['description']
    for key in known_descriptions:
        catagory = known_descriptions[key]
        descriptions = catagory["descriptions"] if "descriptions" in catagory else []
        counterparts = catagory["counterparts"] if "counterparts" in catagory else []
        if (counterpart is not None and counterpart in counterparts
                or any([description.startswith(desc)
                        for desc in descriptions])):
            return key

    return "Unknown"


###########################################################
# GET VALUES (SLIM)
###########################################################
def get_values_slim(known_descriptions, transactions):
    """
    Get the set of income and spending values by category
    """
    income = {}
    spending = {}
    for bank in transactions:
        for transac in transactions[bank]:
            cat = get_catagory(known_descriptions, transac)
            if transac['amount'] < 0:
                values = spending
            else:
                values = income

            if cat not in values:
                values[cat] = 0
            values[cat] += transac['amount']
    for values in [income, spending]:
        for cat in [k for k in values]:
            if values[cat] == 0:
                del values[cat]

    for cat in [k for k in income]:
        if cat in spending and spending[cat] == -income[cat]:
            # Spending and income perfectly balance so ignore
            del income[cat]
            del spending[cat]
    return income, spending


###########################################################
# GET TOTAL OUT
###########################################################
def get_total_out(transactions):
    """Get the total outgoing amount"""
    total = 0
    for transac in transactions:
        amount = transac['amount']
        if amount < 0:
            total += amount

    return total


###########################################################
# PROCESS
###########################################################
def process_transactions(known_descriptions, transactions,
                         net=False, breakdown=None,
                         unknowns=False):
    """Process all the transactions in the given modes"""
    if net:
        print_income_expendature(transactions)
    if breakdown:
        print_spending_breakdown_slim(known_descriptions, transactions)
    if unknowns:
        print_unknown_descriptions(known_descriptions, transactions)


###########################################################
# PARSE ARGS
###########################################################
def parseargs():
    """Parse the cli arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cache',
                        help="Use a saved transactions file instead of "
                             "downloading from the web.")
    parser.add_argument('-n', '--net', action='store_true',
                        help="Display the net change in value for the period.")
    parser.add_argument('-b', '--breakdown', action='store_true',
                        help="Display the spending breakdown.")
    parser.add_argument('-u', '--unknowns', action='store_true',
                        help="Display the unknown descriptions.")
    return parser.parse_args()


###########################################################
# INIT
###########################################################
def init():
    """Initialize by loading the config"""
    nebraska_dir = os.path.join(os.path.expanduser("~"), ".nebraska")
    if not os.path.exists(nebraska_dir):
        os.makedirs(nebraska_dir)

    known_descriptions = {}
    json_filename = os.path.join(nebraska_dir, "known_descriptions.json")
    if not os.path.exists(json_filename):
        with open(json_filename, "w") as jfile:
            json.dump(jfile, known_descriptions, indent=4)
    else:
        with open(json_filename, "r") as jfile:
            known_descriptions = json.load(jfile)

    config = {"keys": {}, "ids": {}}
    config_filename = os.path.join(nebraska_dir, "config.json")
    if not os.path.exists(config_filename):
        with open(config_filename, "w") as config_file:
            json.dump(config_file, config, indent=4)
    else:
        with open(config_filename, "r") as config_file:
            config = json.load(config_file)

    return known_descriptions, config


###########################################################
# DOWNLOAD TRANSACTIONS
###########################################################
def download_all_transactions(config):
    """Load all the nodes and run their download methods"""
    transactions = {}
    for module_name in banknodes.__all__:
        node = importlib.import_module("banknodes." + module_name)
        if hasattr(node, "download"):
            download_method = getattr(node, "download")
            transactions[module_name] = download_method(config,
                                                        datetime.date(2018, 1, 1),
                                                        datetime.date.today())
    return transactions


###########################################################
# MAIN
###########################################################
def main(known_descriptions, config, args):
    """Run the main method"""
    if args.cache:
        with open(args.cache, "r") as infile:
            transactions = json.load(infile)['transactions']
    else:

        transactions = download_all_transactions(config)
        with open("cache.json", "w") as outfile:
            json.dump({"transactions": transactions},
                      outfile,
                      indent=4,
                      sort-keys=True)
            print("cache.json created")

    process_transactions(known_descriptions,
                         transactions,
                         net=args.net,
                         breakdown=args.breakdown,
                         unknowns=args.unknowns)

###########################################################
# Start of script
###########################################################
if __name__ == '__main__':
    ARGS = parseargs()
    DESCS, CONFIG = init()
    main(DESCS, CONFIG, ARGS)

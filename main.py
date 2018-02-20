#!/usr/bin/python
import argparse
import datetime
import importlib
import json

import banknodes

###########
# GLOBALS #
###########
_known_descriptions = {}

###########################################################
# INCOME and EXPENDATURE
###########################################################
def print_income_expendature(transactions):
    # Calculate total income and expendature
    income = 0
    expendature = 0
    for bank in transactions:
        for transac in transactions[bank]:
            if transac['amount'] > 0:
                income += transac['amount']
            else:
                expendature += transac['amount']
    print(u"Total income: \xA3{}".format(income)).encode("utf-8")
    print(u"Total expend:-\xA3{}".format(abs(expendature))).encode("utf-8")
    print(u"Net change:{}\xA3{}".format(" -" if income < expendature else " ",
                                        income + expendature)).encode("utf-8")


###########################################################
# SPENDING BREAKDOWN (FULL)
###########################################################
def print_spending_breakdown(transactions):
    return 

    """
    THE NEW LAYOUT FOR KNOWN_DESCS BREAKS THIS!!!
    """
    print("Spending breakdown:")
    values = {}
    for key in _known_descriptions:
        print("--{}".format(key))
        for subkey in _known_descriptions[key]:
            values[subkey] = 0
            for transac in transactions:
                if transac['description'].startswith(subkey):
                    values[subkey] += transac['amount']
            print (u"  {}-{}: \xA3{}"
                   u"".format(key, subkey, values[subkey])
                  ).replace(u"\xA3-", u"-\xA3").encode("utf-8")
    
    values['Unknown'] = 0
    for transac in transactions:
        known = 0
        for key in _known_descriptions:
            for subkey in _known_descriptions[key]:
                if transac['description'].startswith(subkey):
                    known = 1
        if known is not 1:
            values['Unknown'] += transac['amount']

    print (u"--Unknown: \xA3{}".format(values['Unknown'])
          ).replace(u"\xA3-", u"-\xA3").encode("utf-8")


###########################################################
# SPENDING BREAKDOWN (SLIM)
###########################################################
def print_spending_breakdown_slim(transactions):
    print("Spending breakdown:")
    income, spending = get_values_slim(transactions)        

    # Handle diffs
    for key in [k for k in income.keys()]:
        if (key in spending
                and "diff" in _known_descriptions[key]
                and _known_descriptions[key]["diff"]):
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
            print (u"    ({:6.2f}%) {}: \xA3{:.2f}"
                   u"".format(100 * values[key] / total, key, values[key])
                   ).replace(u"\xA3-", u"-\xA3").encode("utf-8")


###########################################################
# UNKNOWN DESCRIPTIONS
###########################################################
def print_unknown_descriptions(transactions):
    unknowns = {"counterparty": set(), "description": set()}
    for bank in transactions:
        for transac in transactions[bank]:
            if get_catagory(transac) == "Unknown":
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


def get_catagory(transac):
    counterpart = transac['counterparty'] if "counterparty" in transac else None
    description = transac['description']
    for key in _known_descriptions:
        catagory = _known_descriptions[key]
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
def get_values_slim(transactions):
    income = {}
    spending = {}
    for bank in transactions:
        for transac in transactions[bank]:
            cat = get_catagory(transac)
            if transac['amount'] < 0:
                values = spending
            else:
                values = income

            if cat not in values:
                values[cat] = 0
            values[cat] += transac['amount']
    for values in [income, spending]:
        for cat in [k for k in values.keys()]:
            if values[cat] == 0:
                del values[cat]

    for cat in [k for k in income.keys()]:
        if cat in spending and spending[cat] == -income[cat]:
            # Spending and income perfectly balance so ignore
            del income[cat]
            del spending[cat]
    return income, spending


###########################################################
# GET TOTAL OUT
###########################################################
def get_total_out(transactions):
    total = 0
    for transac in transactions:
        amount = transac['amount']
        if amount < 0:
            total += amount

    return total


###########################################################
# PROCESS
###########################################################
def process_transactions(transactions, net=False, breakdown=None,
        unknowns=False, chart=False):
    if net:
        print_income_expendature(transactions)
    if breakdown:
        print_spending_breakdown_slim(transactions)
    if unknowns:
        print_unknown_descriptions(transactions)
    if chart:
        lloyd_graphic.show_spending_pie_chart(transactions)


###########################################################
# PARSE ARGS
###########################################################
def parseargs():
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
    global _known_descriptions
    with open("known_descriptions.json", "r") as jfile:
        _known_descriptions = json.load(jfile)


###########################################################
# DOWNLOAD TRANSACTIONS
###########################################################
def download_all_transactions():
    transactions = {}
    for module_name in banknodes.__all__:
        node = importlib.import_module("banknodes." + module_name)
        transactions[module_name] = node.download(datetime.date(2018, 01, 01),
                                                  datetime.date(2018, 02, 20))
    return transactions


###########################################################
# MAIN
###########################################################
def main(args):
    if args.cache:
        with open(args.cache, "r") as infile:
            transactions = json.load(infile)['transactions']
    else:
        transactions = download_all_transactions()
        with open("cache.json", "w") as outfile:
            json.dump({"transactions": transactions}, outfile)
            print("cache.json created")

    process_transactions(transactions,
                         net=args.net,
                         breakdown=args.breakdown,
                         unknowns=args.unknowns)
                         #chart=args.chart)

###########################################################
# Start of script
###########################################################
if __name__ == '__main__':
    args = parseargs()
    init()
    main(args)

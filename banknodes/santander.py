"""
Download transaction history from Santander via tellers
"""

import datetime
import time

import requests

def download(config, from_date, to_date):
    """Main flow of the santander account processing"""
    if "keys" not in config or "teller" not in config["keys"]:
        raise Exception("Teller API key not in config. See README for help with this error.")

    # Get the current accounts information from teller
    success = False
    while not success:
        try:
            headers = {'Authorization': 'Bearer ' + config["keys"]["teller"]}
            res = requests.get('https://api.teller.io/accounts', headers=headers)
            res = requests.get(res.json()[0]["links"]["transactions"], headers=headers)
            success = True
        except requests.exceptions.ConnectionError:
            print("Retrying in 1")
            time.sleep(1)

    transactions = res.json()
    ret = []
    for transac in transactions:
        transac['amount'] = float(transac['amount'])

        date = transac["date"].split("-")
        date = datetime.date(int(date[0]), int(date[1]), int(date[2]))
        if date >= from_date and date <= to_date:
            ret.append(transac)
    return ret

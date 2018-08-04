"""
Download transaction history from Santander website
"""

import csv
import datetime
import getpass
import os
import re
import time

from robobrowser import RoboBrowser

from ..account import Account
from ..session import download_method
from ..transaction import Transaction

from .common import prompt, split_range

__all__ = (
    "download"
)


def download_internal(user_id, from_date, to_date):
    """Download the csv files for the transaction between the given dates"""
    # Create the browser and open the lloyds login page
    browser = RoboBrowser(parser='html5lib')
    browser.open('https://retail.santander.co.uk/LOGSUK_NS_ENS/BtoChannelDriver.ssobto?dse_operationName=LOGON&dse_processorState=initial&redirect=S')

    while browser.find("h1").get_text() == "Log on to Online Banking":
        print(browser.find("h1").get_text())
        form = browser.get_form(id='formCustomerID_1')
        form['infoLDAP_E.customerID'] = str(user_id)
        browser.submit_form(form)

    while (browser.find("h1").get_text() == "Log on"
           and browser.find("h2").get_text() == "We are unfamiliar with the computer you are using"):
        print(browser.find("h2").get_text())
        form = browser.get_form(id="formCustomerID")
        form['cbQuestionChallenge.responseUser'] = prompt(
            browser.find("span", class_="data").get_text().strip() + "?: ")
        browser.submit_form(form, submit=[x[1] for x in form.submit_fields.items(multi=True) if x[0] == "buttons.1"][0])

    # We're logged in, now enter memorable information
    while browser.find("h1").get_text() == "Recognise this image and phrase / word?":
        print(browser.find_all("h1")[1].get_text())
        form = browser.get_form(id='formAuthenticationAbbey')

        inputs = browser.find_all("input", id=re.compile("signPosition"))
        for input in inputs:
            form[input.get_attribute_list("name")[0]] = prompt(
                "Password character {}:".format(input.get_attribute_list("id")[0][len("signPosition"):]))

        inputs = browser.find_all("input", id=re.compile("passwordPosition"))
        for input in inputs:
            form[input.get_attribute_list("name")[0]] = prompt(
                "Security Number character {}:".format(input.get_attribute_list("id")[0][len("passwordPosition"):]))

        browser.submit_form(form, submit=[x[1] for x in form.submit_fields.items(multi=True) if x[0] == "buttons.1"][0])

    # hopefully now we're logged in...
    print(browser.find("h1").get_text() + ": "
          + ", ".join([s.find("a").get_text()
                       for s in browser.find_all("span", class_="name")]))

    account_names = [s.find("a").get_text() for s in browser.find_all("span", class_="name")]

    for account_name in account_names:
        print(account_name)
        account_link = [a for a in browser.find_all("a") if a.get_text() == account_name][0]

        browser.follow_link(account_link)
        try:
            yield account_name, download_account_internal(browser, from_date, to_date)
        except:
            pass
        browser.back()
        #print("back to: " + browser.find("h1").get_text())


def download_account_internal(browser, from_date, to_date):
    """Return the list of csv files downloaded for this account"""
    print(browser.find("h1").get_text())
    export_link = browser.find("a", class_="download")
    browser.follow_link(export_link)

    ret = []
    for (f_date, t_date) in split_range(from_date, to_date):
        ret.append(download_range(browser, f_date, t_date))

    browser.back()
    #print("back to: " + browser.find("h1").get_text())
    return ret


def download_range(browser, from_date, to_date):
    """
    Download an individual csv file from a browser on the accounts Export page
    """
    print(browser.find("h1").get_text())
    print('Exporting {0} to {1}'.format(from_date, to_date))

    form = browser.get_form('downloadTransaction')
    form["downloadStatementsForm.typeFile"] = "Text file (TXT)"
    browser.submit_form(form, submit=[x[1] for x in form.submit_fields.items(multi=True) if x[0] == "downloadStatementsForm.events.2"][0])

    form = browser.get_form('downloadTransaction')
    form["downloadStatementsForm.typeFile"] = "Text file (TXT)"
    form['downloadStatementsForm.fromDate.day'] = from_date.day
    form['downloadStatementsForm.fromDate.month'] = from_date.month
    form['downloadStatementsForm.fromDate.year'] = from_date.year
    form['downloadStatementsForm.toDate.day'] = to_date.day
    form['downloadStatementsForm.toDate.month'] = to_date.month
    form['downloadStatementsForm.toDate.year'] = to_date.year
    browser.submit_form(form, submit=[x[1] for x in form.submit_fields.items(multi=True) if x[0] == "downloadStatementsForm.events.0"][0])

    if browser.response.headers["Content-Type"] != 'text/plain':
        print("No transactions could be downloaded for this range.")
        return None

    disposition = browser.response.headers['Content-Disposition']
    prefix = 'attachment; filename='
    if not disposition.startswith(prefix):
        raise Exception('Missing "Content-Disposition: attachment" header')

    suggested_prefix, ext = os.path.splitext(disposition[len(prefix):])
    filename = '{0}_{1:%Y-%m-%d}_{2:%Y-%m-%d}{3}'.format(
        suggested_prefix, from_date, to_date, ext).strip('"')

    with open(filename, 'w') as save_file:
        for line in browser.response.text:
            save_file.write(line)

    print('Saved transactions to "{0}"'.format(filename))

    time.sleep(1)
    browser.back()
    #print("back to: " + browser.find("h1").get_text())
    time.sleep(2)
    browser.back()
    #print("back to: " + browser.find("h1").get_text())
    return filename


@download_method
def download(config, from_date, to_date):
    """Main flow of the santander account processing"""
    if "ids" not in config or "santander" not in config["ids"]:
        print("Santander ID not in config, skipping. See README for help.")
        return []

    accounts = []
    for acc_name, filenames in download_internal(user_id=config["ids"]["santander"],
                                                 from_date=from_date,
                                                 to_date=to_date):
        accounts.append(Account("santander-" + acc_name))
        account = accounts[-1]
        for filename in filenames:
            if filename is None:
                continue

            with open(filename, 'r') as fileopen:
                transaction_dict = {}
                for linenum, line in enumerate(fileopen.readlines()):
                    offset = 4
                    if linenum < offset:
                        # Skip the opening lines
                        continue

                    # Correct for the offset
                    linenum = linenum - offset
                    if linenum % 5 == 0:
                        date_raw = line.split()[1].split("/")
                        transaction_dict = {
                            "date": "{}-{}-{}".format(date_raw[2], date_raw[1], date_raw[0])
                        }
                    if linenum % 5 == 1:
                        transaction_dict["desc"] = " ".join(line.split()[1:])
                    if linenum % 5 == 2:
                        transaction_dict["amount"] = float(line.split()[1])
                    if linenum % 5 == 3:
                        transaction_dict["balance"] = float(line.split()[1])
                        account.add_transaction(Transaction(
                            transaction_dict["date"],
                            transaction_dict["desc"],
                            transaction_dict["amount"],
                            transaction_dict["balance"]))
            os.remove(filename)
    return accounts


if __name__ == "__main__":
    print(download({"ids": { "santander": "TEST ID HERE!!!" } },
                             datetime.date(2018, 1, 1),
                             datetime.date.today()))

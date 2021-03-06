"""
Download transaction history from Lloyds Bank website
"""

import csv
import datetime
import getpass
import os

from robobrowser import RoboBrowser

from ..account import Account
from ..session import download_method
from ..transaction import Transaction

__all__ = (
    "download"
)


def prompt(prompt_message, password=False):
    """Prompt the user for some input"""
    if password:
        val = getpass.getpass(prompt_message)
    else:
        val = input(prompt_message)
    return val


def download_internal(user_id, from_date, to_date):
    """Download the csv files for the transaction between the given dates"""
    # Create the browser and open the lloyds login page
    browser = RoboBrowser(parser='html5lib')
    browser.open('https://online.lloydsbank.co.uk/personal/logon/login.jsp?WT.ac=hpIBlogon')

    while 'Enter Memorable Information' not in browser.parsed.title.text:
        print(browser.parsed.title.text)
        form = browser.get_form(id='frmLogin')
        form['frmLogin:strCustomerLogin_userID'] = str(user_id)
        form['frmLogin:strCustomerLogin_pwd'] = prompt('Enter password: ', True)
        browser.submit_form(form)

    # We're logged in, now enter memorable information
    print(browser.parsed.title.text)
    form = browser.get_form(id='frmentermemorableinformation1')
    field = 'frmentermemorableinformation1:strEnterMemorableInformation_memInfo{0}'

    for i in range(1, 4):
        label = browser.find("label", {"for": field.format(i)})
        form[field.format(i)] = '&nbsp;' + prompt(label.text.strip())
    browser.submit_form(form)

    # hopefully now we're logged in...
    print(browser.parsed.title.text)
    links = []
    for link in browser.get_links("View statement"):
        if link.text == "View statement":
            links.append(link)

    # loop through all accounts
    for index, link in enumerate(links):
        acc_name = link['data-wt-ac'].split(" resource")[0]
        print(acc_name)
        print(browser.parsed.title)
        browser.follow_link(link)
        yield acc_name, download_account_internal(browser, from_date, to_date)
        browser.back()


def download_account_internal(browser, from_date, to_date):
    """Return the list of csv files downloaded for this account"""
    print(browser.parsed.title.text)
    export_link = browser.get_link('Export', id='lnkExportStatementSSR')
    browser.follow_link(export_link)

    ret = []
    for (f_date, t_date) in split_range(from_date, to_date):
        ret.append(download_range(browser, f_date, t_date))

    browser.back()
    return ret


def split_range(from_date, to_date):
    """Split the given date range into three month segments"""
    three_months = datetime.timedelta(days=(28 * 3))
    one_day = datetime.timedelta(days=1)

    assert from_date <= to_date

    while to_date - from_date > three_months:
        yield (from_date, from_date + three_months)
        from_date += (three_months + one_day)

    yield (from_date, to_date)


def download_range(browser, from_date, to_date):
    """
    Download an individual csv file from a browser on the accounts Export page
    """
    print(browser.parsed.title.text)
    print('Exporting {0} to {1}'.format(from_date, to_date))

    form = browser.get_form('export-statement-form')
    form["exportDateRange"] = "between"
    form["searchDateTo"] = to_date.strftime("%d/%m/%Y")
    form["searchDateFrom"] = from_date.strftime("%d/%m/%Y")
    form["export-format"] = "Internet banking text/spreadsheet (.CSV)"
    browser.submit_form(form)

    if browser.response.headers["Content-Type"] != 'application/csv':
        print("No transactions could be downloaded for this range.")
        return None

    disposition = browser.response.headers['Content-Disposition']
    prefix = 'attachment; filename='
    if not disposition.startswith(prefix):
        raise Exception('Missing "Content-Disposition: attachment" header')

    suggested_prefix, ext = os.path.splitext(disposition[len(prefix):])
    filename = '{0}_{1:%Y-%m-%d}_{2:%Y-%m-%d}{3}'.format(
        suggested_prefix, from_date, to_date, ext)

    with open(filename, 'a') as csv_file:
        for line in browser.response.text:
            csv_file.write(line)

    print('Saved transactions to "{0}"'.format(filename))

    browser.back()
    return filename


@download_method
def download(config, from_date, to_date):
    """Main flow of the lloyds account processing"""
    if "ids" not in config or "lloyds" not in config["ids"]:
        print("Lloyds ID not in config, skipping. See README for help.")
        return []

    accounts = []
    for acc_name, filenames in download_internal(user_id=config["ids"]["lloyds"],
                                                 from_date=from_date,
                                                 to_date=to_date):
        accounts.append(Account("lloyds-" + acc_name))
        account = accounts[-1]
        for filename in filenames:
            if filename is None:
                continue

            with open(filename, 'r') as fileopen:
                csvreader = csv.reader(fileopen)
                firstrow = True
                for row in csvreader:
                    if firstrow:
                        firstrow = False
                        continue
                    date_raw = row[0].split("/")
                    date = "{}-{}-{}".format(date_raw[2], date_raw[1], date_raw[0])
                    desc = row[4]
                    if row[5] != "":
                        amount = -float(row[5])
                    else:
                        amount = float(row[6])
                    balance_after = float(row[7])
                    account.add_transaction(Transaction(date, desc, amount, balance_after))
            os.remove(filename)
    return accounts

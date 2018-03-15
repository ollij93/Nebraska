"""
Download transaction history from Lloyds Bank website
"""

__all__ = (
    "download"
)

import csv
import datetime
import getpass
import os

from robobrowser import RoboBrowser

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
        label = browser.find("label", {"for": field.format(i)}) # pylint: disable=E1102
        form[field.format(i)] = '&nbsp;' + prompt(label.text.strip())
    browser.submit_form(form)

    # hopefully now we're logged in...
    print(browser.parsed.title.text)
    links = []
    for link in browser.get_links("View statement"):
        if link.text == "View statement":
            links.append(link)

    # allow user to choose one
    print('Accounts:')
    for index, link in enumerate(links):
        print('{}:'.format(index), link['data-wt-ac'].split(" resource")[0])

    acc_num = prompt('Please select an account:')
    browser.follow_link(links[int(acc_num)])

    print(browser.parsed.title.text)
    export_link = browser.get_link('Export', id='lnkExportStatementSSR')
    browser.follow_link(export_link)

    for (f_date, t_date) in split_range(from_date, to_date):
        yield download_range(browser, f_date, t_date)

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
    print(browser.response.text)

    if browser.response.headers["Content-Type"] != 'application/csv':
        raise Exception('Did not get a CSV back (maybe there are more than 150 transactions?)')

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

def download(config, from_date, to_date):
    """Main flow of the lloyds account processing"""
    if "ids" not in config or "lloyds" not in config["ids"]:
        raise Exception("Lloyds ID not in config. See README for help with this error.")

    transactions = []
    for filename in download_internal(user_id=config["ids"]["lloyds"],
                                      from_date=from_date,
                                      to_date=to_date):
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
                transactions.append({
                    "date": date,
                    "description": desc,
                    "amount": amount,
                })
        os.remove(filename)
    return transactions

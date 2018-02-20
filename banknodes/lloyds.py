"""
Download transaction history from Lloyds Bank website
"""

__all__ = (
    "download"
)

import argparse
import csv
import datetime
import getpass
import json
import mechanize
import os.path

def prompt(prompt, password=False):
    if password:
        return getpass.getpass(prompt)
    else:
        print prompt,
        return raw_input()

def extract(data, before, after):
    start = data.index(before) + len(before)
    end   = data.index(after, start)
    return data[start:end]

def download_internal(user_id, from_date, to_date):
    # a new browser and open the login page
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'LBG Statement Downloader http://github.com/bitplane/tsb-downloader')]

    br.open('https://online.lloydsbank.co.uk/personal/logon/login.jsp?WT.ac=hpIBlogon')
    title = br.title()
    while 'Enter Memorable Information' not in title:
        print br.title()
        br.select_form(name='frmLogin')
        br['frmLogin:strCustomerLogin_userID'] = str(user_id)
        br['frmLogin:strCustomerLogin_pwd']    = prompt('Enter password: ', True)
        response = br.submit() # attempt log-in
        title    = br.title()

    # We're logged in, now enter memorable information
    print br.title()
    br.select_form('frmentermemorableinformation1')
    data   = response.read()
    field  = 'frmentermemorableinformation1:strEnterMemorableInformation_memInfo{0}'
    before = '<label for="{0}">'
    after  = '</label>'

    for i in range(1, 4):
        br[field.format(i)] = ['&nbsp;' + prompt(extract(data, before.format(field.format(i)), after))]
    response = br.submit()

    # hopefully now we're logged in...
    title = br.title()

    # dismiss any nagging messages
    if 'Mandatory Messages' in title:
        for link in br.links():
            if 'lkcont_to_your_acc' in link.url:
                br.follow_link(link)
                break

    title = br.title() #'Personal Account Overview' in title

    links = []
    for link in br.links():
        attrs = {attr[0]:attr[1] for attr in link.attrs}
        if 'id' in attrs and 'lnkAccFuncs_viewStatement' in attrs['id']:
            links.append(link)

    # allow user to choose one
    print 'Accounts:'
    for i in range(len(links)):
        attrs = {attr[0]:attr[1] for attr in links[i].attrs}
        print '{0}:'.format(i), attrs['data-wt-ac'].split(" resource")[0]

    n = prompt('Please select an account:')
    link = links[int(n)]
    response = br.follow_link(link)

    print br.title()
    export_link = br.find_link(text='Export')
    br.follow_link(export_link)

    for (f, t) in split_range(from_date, to_date):
        yield download_range(br, f, t)

def split_range(from_date, to_date):
    THREE_MONTHS = datetime.timedelta(days=(28 * 3))
    ONE_DAY = datetime.timedelta(days=1)

    assert from_date <= to_date

    while to_date - from_date > THREE_MONTHS:
        yield (from_date, from_date + THREE_MONTHS)
        from_date += (THREE_MONTHS + ONE_DAY)

    yield (from_date, to_date)

def download_range(br, from_date, to_date):
    print br.title()
    print 'Exporting {0} to {1}'.format(from_date, to_date)

    br.select_form('export-statement-form')

    for control in br.form.controls:
        if control.type == "radio" and control.name == "exportDateRange":
                control.value = ["between"]
        if control.type == "text":
            if control.name == "searchDateTo":
                control.value = to_date.strftime("%d/%m/%Y")
            elif control.name == "searchDateFrom":
                control.value = from_date.strftime("%d/%m/%Y")
        if control.type == "select" and control.name == "export-format":
            for item in control.items:
                if u"(.CSV)" in item.name:
                    control.value = [item.name]

    response = br.submit()
    info = response.info()

    if info.gettype() != 'application/csv':
        raise Exception('Did not get a CSV back (maybe there are more than 150 transactions?)')

    disposition = info.getheader('Content-Disposition')
    PREFIX='attachment; filename='
    if disposition.startswith(PREFIX):
        suggested_prefix, ext = os.path.splitext(disposition[len(PREFIX):])
        filename = '{0}_{1:%Y-%m-%d}_{2:%Y-%m-%d}{3}'.format(
            suggested_prefix, from_date, to_date, ext)

        with open(filename, 'a') as f:
            for line in response:
                f.write(line)

        print 'Saved transactions to "{0}"'.format(filename)
    else:
        raise Exception('Missing "Content-Disposition: attachment" header')

    br.back()
    return (filename)

def download(from_date, to_date):
    transactions = []
    for filename in download_internal(user_id="USERIDHERE",
                                      from_date=from_date,
                                      to_date=to_date):
        with open(filename, 'rb') as fileopen:
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
                balance = float(row[7])
                transactions.append({
                        "date": date,
                        "description": desc,
                        "amount": amount,
                    })
        os.remove(filename)
    return transactions


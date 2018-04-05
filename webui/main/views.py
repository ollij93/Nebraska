from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

import json
import os
import sys
sys.path.insert(0, '../../nebraska')

from nebraska.session import Session

# Create your views here.
def index(requests):
    session = Session()
    session.load()

    transactions = sorted(session.accounts[0].get_transactions(),
                          key=lambda t: t.date)

    js_dates = '['
    js_balnc = '['

    num_transactions = len(transactions)

    for i, tran in enumerate(transactions):
        js_dates += '"' + tran.date + '", '

        js_balnc += str(tran.balance_after) + ', '

    js_dates = js_dates[:-2] + ']'
    js_balnc = js_balnc[:-2] + ']'

    parameters = {}
    parameters['js_dates'] = js_dates
    parameters['js_balnc'] = js_balnc

    return render(requests, 'main/index.html', parameters)

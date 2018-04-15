import datetime

import itertools
from django.shortcuts import render
from django.http import JsonResponse

from nebraska.session import Session


# Create your views here.
def json(requests):
    session = Session()
    session.load()

    all_transactions = sorted(itertools.chain.from_iterable([a.get_transactions() for a in session.accounts]),
                              key=lambda x: x.date)

    from_date = all_transactions[0].date.split("-")
    to_date = all_transactions[-1].date.split("-")

    from_date = datetime.date(int(from_date[0]), int(from_date[1]), int(from_date[2]))
    to_date = datetime.date(int(to_date[0]), int(to_date[1]), int(to_date[2]))

    delta = to_date - from_date

    # Get the set of date strings in the required range
    dates = []
    for i in range(delta.days + 1):
        dates.append(str(from_date + datetime.timedelta(days=i)))

    # Reverse the dates so the balance can be tracked backwards
    dates.reverse()

    balances = {}
    for account in session.accounts:
        if not account.get_transactions():
            continue
        balances[account.name] = [0] * len(dates)
        for idx, date in enumerate(dates):
            previous_transactions = account.get_transactions(to_date=date)
            if previous_transactions:
                balances[account.name][idx] = previous_transactions[-1].balance_after
            else:
                future_transactions = account.get_transactions(from_date=date)
                balances[account.name][idx] = future_transactions[0].balance_after - future_transactions[0].amount

    balances["total"] = [sum([balances[account][idx] for account in balances]) for idx in range(len(dates))]

    # Put all the dates back in order
    dates.reverse()
    for key in balances:
        balances[key].reverse()

    return JsonResponse({"dates": dates, "balances": balances})


def index(requests):
    return render(requests, 'main/index.html')

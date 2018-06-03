import datetime
import getpass


def prompt(prompt_message, password=False):
    """Prompt the user for some input"""
    if password:
        val = getpass.getpass(prompt_message)
    else:
        val = input(prompt_message)
    return val


def split_range(from_date, to_date):
    """Split the given date range into three month segments"""
    three_months = datetime.timedelta(days=(28 * 3))
    one_day = datetime.timedelta(days=1)

    assert from_date <= to_date

    while to_date - from_date > three_months:
        yield (from_date, from_date + three_months)
        from_date += (three_months + one_day)

    yield (from_date, to_date)

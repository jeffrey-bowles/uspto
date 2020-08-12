"""
All the functions in this file are used to generate constants used by
views.py and pto_cron.py. Each of the below functions load date or
pickled data that does not change once the application has started.
A cron job updates this information once every night in a separate
process, after the USPTO has uploaded the latest daily patent data.
Once the cron job has finished, the processed data is saved and the
application is restarted.
"""

import pickle
from datetime import date
from dateutil.relativedelta import relativedelta

from pto.constants import ORDERED_PATS
from pto.models import Patent


def yearsago(years, months=0, from_date=None):
    """Calculate exact date x number of years ago."""
    if from_date is None:
        from_date = date.today()
    return from_date - relativedelta(years=years, months=months)


def get_date_arrays():
    """Get necessary dates to make instaniating easy for pto_cron.py"""
    four_year_start = yearsago(4)
    four_year_late = yearsago(3, 6)
    four_year_end = yearsago(3)
    eight_year_start = yearsago(8)
    eight_year_late = yearsago(7, 6)
    eight_year_end = yearsago(7)
    twelve_year_start = yearsago(12)
    twelve_year_late = yearsago(11, 6)
    twelve_year_end = yearsago(11)

    date_arrays = [
        [four_year_start, four_year_late, four_year_end],
        [eight_year_start, eight_year_late, eight_year_end],
        [twelve_year_start, twelve_year_late, twelve_year_end]
    ]
    return date_arrays


def get_ordered_data():
    """Return all necessary data for app/enhanced pagination speeds."""
    ordered_dict, ordered_qs = {}, {}
    for ordered_file in ORDERED_PATS:
        ordered_dict[ordered_file] = pickle.load(
            open(ordered_file+'_ordered_ids.p', 'rb')
        )
        ordered_qs[ordered_file] = Patent.objects.in_bulk(
            ordered_dict[ordered_file]['patent_number']
        )
    return ordered_dict, ordered_qs


def get_fee_codes():
    """Load generated mainenance fee codes defined by the USPTO"""
    fee_codes = pickle.load(open('fee_event_codes.p', 'rb'))
    return fee_codes


def get_paid_patents():
    """Get patents that have already been paid for each patent set"""
    paid_patents = pickle.load(open('paid_patents.p', 'rb'))
    return paid_patents

"""Constants used to load and process data for the this app"""

FIRST_WORD = {
    'four': '1',
    'eight': '2',
    'twelve': '3'
}

FIRST_NUM = {
    1: 'four',
    2: 'eight',
    3: 'twelve'
}

ANAMES = [
    'assignee_first_name',
    'assignee_last_name',
    'assignee_organization',
    'assignee_lastknown_city',
    'assignee_lastknown_state',
    'assignee_lastknown_country',
    'assignee_lastknown_location_id'
]

SORT_IDS = [
    'patent_number',
    'issue_date',
    'application_number',
    'application_date',
    'pat_assignee_name',
    'correspondent_name'
]

# Dictionary converting Vue routes to patent set names
PAT_PARAM_CONVERSION = {
    '1': 'four_year',
    '2': 'four_year_late',
    '3': 'eight_year',
    '4': 'eight_year_late',
    '5': 'twelve_year',
    '6': 'twelve_year_late'
}

ORDERED_PATS = [
    'four_year',
    'four_year_late',
    'eight_year',
    'eight_year_late',
    'twelve_year',
    'twelve_year_late'
]

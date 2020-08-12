"""
This view functions in this files are responsible for generating the paginated
USPTO assignment and maintenance fee table data. The main table containing
assignment data uses Vue routing with the Quasar plugin, while the individual
fee events are loaded using the django framework.
"""

from __future__ import unicode_literals

from django.shortcuts import render
from django.http import JsonResponse

from pto.serializers import PatentSerializer
from pto.extras import get_ordered_data, get_fee_codes, get_paid_patents
from pto.constants import PAT_PARAM_CONVERSION
from pto.models import FeeEvents


# Load ordered dictionaries/sorted lists built from patent sets
ORDERED_DICT, ORDERED_QS = get_ordered_data()

# Mainenance fee codes defined by the USPTO
FEE_CODES = get_fee_codes()

# Patents that have already been paid for each patent set
PAID_PATENTS = get_paid_patents()


def update_patents(request):
    """(Re)load sorted, filtered paginated patent data using Vue.js and
    Quasar framework and routes. Returns serialized queryset and total
    patent document counts.
    """
    params = request.GET.copy()
    patent_set = str(params['patent_set'])
    set_id = PAT_PARAM_CONVERSION[patent_set]
    start_row = int(params['start_row'])
    count = int(params['count'])
    end_row = start_row+count
    sort_by = params['sort_by']
    descending = params['descending']
    unpaid = params['unpaid']
    filt = request.GET.get('filter', default=None)
    if descending == 'true':
        sort_by = '-'+sort_by
    pats_to_remove = set()
    if unpaid == 'true':
        pats_to_remove = PAID_PATENTS[set_id]
    pats_to_load = []
    if filt:
        [pats_to_load.append(ORDERED_QS[set_id][pat])
         for pat in ORDERED_DICT[set_id][sort_by]
         if filt in str(ORDERED_QS[set_id][pat].patent_number)
         and pat not in pats_to_remove]
        pats_count = len(pats_to_load)
        pats_to_load = pats_to_load[start_row:end_row]
    else:
        [pats_to_load.append(ORDERED_QS[set_id][pat])
         for pat in [x for x in ORDERED_DICT[set_id][sort_by]
                     if x not in pats_to_remove][start_row:end_row]]
        if unpaid == 'true':
            pats_count = ORDERED_DICT[set_id]['count'] - len(pats_to_remove)
        else:
            pats_count = ORDERED_DICT[set_id]['count']
    queryset = [PatentSerializer(p).data for p in pats_to_load]
    queryset_and_counts = {'patents': queryset, 'count': pats_count}
    return JsonResponse(queryset_and_counts)


def update_fee_events(request):
    """Load Mainenance Fee Event records for each selected patent using
    django framework and templates.
    """
    patent = int(request.GET['patent'])
    fee_events = FeeEvents.objects.filter(patent_id=patent)
    event_results = [[event.maintenance_date, event.maintenance_code,
                      FEE_CODES[event.maintenance_code]] for event in fee_events]
    context = {'event_results': event_results}
    return render(request, 'pto/events.html', context)

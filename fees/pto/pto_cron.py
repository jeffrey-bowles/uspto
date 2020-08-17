"""
This module automates the daily/weekly retrieval of USPTO Maintenance
Fee and Assignment data from their bulk data website -
(https://bulkdata.uspto.gov/), as well as their PatentView API -
https://www.patentsview.org/api/patents. This data is processed
and then the server is reloaded each night with the updated.
"""

import re
import csv
import json
import shlex
import pickle
import zipfile
import subprocess
from glob import glob
from math import ceil
from time import strftime
from xml.etree import ElementTree as ET
from datetime import date, timedelta
import requests

from pto.extras import yearsago, get_date_arrays
from pto.constants import FIRST_WORD, FIRST_NUM, ANAMES, SORT_IDS
from pto.models import Patent, FeeEvents


DATE_ARRAYS = get_date_arrays()


def reload_server():
    """Reload the server after update of datatsets."""
    subprocess.call('./reload-dev.sh')


def process_docs(docs):
    """Create ordered lists of patent numbers for each table option."""
    ordered_docs = {}
    ordered_docs['count'] = docs.count()
    for sort_id in SORT_IDS:
        if 'name' in sort_id:
            docs_sorted = docs.extra(select={
                'has_foo': 'LENGTH(pto_patent.'+sort_id+') > 0'
            })
            docs_sorted_asc = docs_sorted.extra(order_by=[
                '-has_foo', sort_id
            ])
            ordered_docs[sort_id] = [p.pk for p in docs_sorted_asc]
            docs_sorted_reversed = docs_sorted.extra(order_by=[
                '-has_foo', '-'+sort_id
            ])
            ordered_docs['-'+sort_id] = [p.pk for p in docs_sorted_reversed]
        else:
            docs_sorted = docs.order_by(sort_id)
            idlst = [p.pk for p in docs_sorted]
            ordered_docs[sort_id] = idlst
            reverse_list = idlst[::-1]
            ordered_docs['-'+sort_id] = reverse_list
    return ordered_docs


def process_paid_patents(category, patent_list):
    """Create updated lists of patents that the maintenance fee for
    the specific time frame has already been paid for.
    """
    first_category_word = category.split('_')[0]

    # fee code format is MX55Y, where X is the size of the entity, and
    # Y is the maintenance year code
    code_num = FIRST_WORD[first_category_word]
    payment_codes = []
    for i in range(1, 4):
        payment_codes.append('M'+str(i)+'55'+code_num)
    filtered_fees = FeeEvents.objects.filter(
        patent_id__in=patent_list,
        maintenance_code__in=payment_codes
    )
    paid_fees = set([g.patent_id for g in filtered_fees])
    return paid_fees


def patent_api_check(start_date, end_date):
    """update rows for time frames with latest PatentsView API
    information
    """
    api_results = []
    api_count = 1
    total_pat_num = 100000
    while ceil(total_pat_num/10000) >= api_count:
        start = start_date.strftime('%Y-%m-%d')
        end = end_date.strftime('%Y-%m-%d')
        url = ('https://www.patentsview.org/api/patents/query?q={"_and":[{"_gt'
               'e":{"patent_date":"' + start + '"}},{"_lte":{"patent_date":"' +
               end + '"}}]}&f=["patent_number","patent_date","assignee_first_'
               'name","assignee_last_name","assignee_organization","assignee_'
               'lastknown_city","assignee_last,known_state","assignee_lastknow'
               'n_country","assignee_lastknown_latitude","assignee_lastknown_'
               'longitude","assignee_lastknown_location_id","assignee_type"]&'
               'o={"include_subentity_total_counts":"true","matched_subentiti'
               'es_only":"true","per_page":"10000","page":"' +str(api_count) +
               '"}'
              )
        api_request = requests.get(url)
        api_content = api_request.content
        api_json = json.loads(api_content)
        api_results += api_json['patents']
        if api_count == 1:
            total_pat_num = int(api_json['total_patent_count'])
        api_count += 1
    return api_results


def parse_api_result(patent):
    """Get assignee fields from USPTO API results"""
    fields = patent['assignees'][0]
    name = ''
    if (fields[ANAMES[0]] is None or fields[ANAMES[1]] is None):
        name = fields[ANAMES[2]]
    else:
        name = fields[ANAMES[0]] + ' '  + fields[ANAMES[1]]
    address = '*API GENERATED\n'
    for i in range(3, 6):
        if fields[ANAMES[i]] != None:
            address += fields[ANAMES[i]] + ' '
    address += '\n'
    if fields[ANAMES[6]] != None:
        address += fields[ANAMES[6]]
    return name, address


def initial_assignment_data():
    """Build assignment dataset from USPTO csv files if not yet been created"""

    # create necessary directories that we will save USPTO assignment data to
    subprocess.call(shlex.split('mkdir -p ../../ad/csv'))
    subprocess.call(shlex.split('mkdir -p ../../ad/adzips'))

    # download the latest, most comprehensive USPTO assignment dataset
    cfile = ('https://bulkdata.uspto.gov/data/patent/assignment/economics/'
             '2019/csv.zip'
            )
    assignment_csv_data = requests.get(cfile)

    # write zip file to disk
    zfile = '../../ad/adzips/csv.zip'
    with open(zfile, 'wb') as csv_zip:
        csv_zip.write(assignment_csv_data.content)

    # open zip file to get assignment data
    csv_prefix = '../../ad/csv'
    with zipfile.ZipFile(zfile, 'r') as extract_csv:
        extract_csv.extractall(path=csv_prefix)

    # Assignment data is broken up in separate csv files. For this reason,
    # a complete dataset must be build from the associated data spread out
    # in three csv files. A copy of the schema can be found here:
    # uspto/fees/pat_assign_dataset_schema.pdf
    mapped_dict = {}
    mapped_list = ['assignee', 'assignment', 'documentid']

    for mapfile in mapped_list:
        csvfile = '../../ad/csv/' + mapfile + '.csv'
        rows = []
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            rows.append(row)
        mapped_dict[mapfile] = rows

    mapped_data = {}
    for row in mapped_dict['assignment']:
        rfid = ''
        for i, col in enumerate(row):
            if i == 0:
                rfid = col
                mapped_data[rfid] = {}
            if i == 2:
                mapped_data[rfid]['correspondent_name'] = col
            if 2 < i < 7:
                if 'correspondent_address' not in mapped_data[rfid]:
                    mapped_data[rfid]['correspondent_address'] = col
                else:
                    mapped_data[rfid]['correspondent_address'] += '\n' + col
            if i == 7:
                mapped_data[rfid]['reel_num'] = col
            if i == 8:
                mapped_data[rfid]['frame_num'] = col

    for row in mapped_dict['documentid']:
        rfid = ''
        for i, col in enumerate(row):
            if i == 0:
                rfid = col
            if rfid in mapped_data:
                if i == 3:
                    mapped_data[rfid]['application_number'] = col
                if i == 4:
                    mapped_data[rfid]['application_date'] = col
                if i == 9:
                    mapped_data[rfid]['patent_number'] = col
                if i == 10:
                    mapped_data[rfid]['issue_date'] = col

    for row in mapped_dict['assignee']:
        rfid = ''
        for i, col in enumerate(row):
            if i == 0:
                rfid = col
            if rfid in mapped_data:
                if i == 1:
                    mapped_data[rfid]['assignee_name'] = col
                if i > 1:
                    if 'assignee_address' not in mapped_data[rfid]:
                        mapped_data[rfid]['assignee_address'] = col
                    else:
                        mapped_data[rfid]['assignee_address'] += '\n'+col

    # Saved pickled data just in case we need it for future reference,
    # also to test for it's existence when running function to determine
    # whether it needs to be run before rest of update functions
    pickle.dump(mapped_data, open('mapped_data.p', 'wb'), protocol=2)

    # Update all patent database rows with complete current assignment data
    for pat in mapped_data.values():
        try:
            saved_pat = Patent.objects.get(patent_number=pat['patent_number'])
            saved_pat.reel_num = pat['reel_num']
            saved_pat.frame_num = pat['frame_num']
            saved_pat.correspondent_name = pat['correspondent_name']
            saved_pat.correspondent_address = pat['correspondent_address']
            saved_pat.pat_assignee_name = pat['assignee_name']
            saved_pat.pat_assignee_address = pat['assignee_address']
            saved_pat.save()
        except Exception as e:
            print(e)

    reload_server()


def generate_final_data():
    """This function generates the bulk of the data used by the app."""
    paid_patents = {}
    for cnt, i in enumerate(DATE_ARRAYS):
        for j in range(2):
            beginning = i[j]
            end = i[j+1]
            extra_text = ''
            if j == 0:
                extra_text = '_late'
            key_name = FIRST_NUM[cnt+1] + '_year' + extra_text
            pats = Patent.objects.filter(issue_date__range=(beginning, end))
            ordered_ids = process_docs(pats)
            pickle.dump(ordered_ids,
                        open(key_name+'_ordered_ids.p', 'wb'), protocol=2)
            pat_list = ordered_ids['patent_number']
            paid_patents[key_name] = process_paid_patents(key_name, pat_list)

            # on average, the main USPTO assignment data is ~25% incomplete
            # With USPTO API, 40-50% of the missing data can be added
            while beginning < end:
                old_beginning = beginning
                beginning += timedelta(7)

                # just try, not worth risking rest of the code breaking if
                # there is an error retrieving some of the api results
                try:
                    api_updates = patent_api_check(old_beginning, beginning)
                    api_updates = [
                        y for y in api_updates
                        if y['assignees'][0]['assignee_last_name'] != None
                        or y['assignees'][0]['assignee_organization'] != None
                    ]

                    # filter patent set so we only check empty db entries
                    empties = pats.filter(pat_assignee_name='')
                    for pdata in api_updates:
                        try:
                            existing = empties.get(
                                patent_number=pdata['patent_number']
                            )
                            name, address = parse_api_result(pdata)
                            existing.pat_assignee_name = name
                            existing.pat_assignee_address = address
                            existing.save()
                        except:
                            pass
                except:
                    pass
    pickle.dump(paid_patents, open('paid_patents.p', 'wb'), protocol=2)


def process_assignment_xml(zip_file):
    """download and process USPTO assignment zip and xml files"""
    rfile = ('https://bulkdata.uspto.gov/data/patent/assignment/'
             + zip_file
            )
    assignment_zip = requests.get(rfile)

    # write zip file to disk
    zfile = '../../ad/adzips/' + zip_file
    with open(zfile, 'wb') as assignment_file:
        assignment_file.write(assignment_zip.content)

    # open zip file to get assignment data
    xml_prefix = '../../ad/'
    with zipfile.ZipFile(zfile, 'r') as xml_file:
        xml_file.extractall(path=xml_prefix)

    assn_data = xml_prefix + zip_file.replace('zip', 'xml')
    assn_tree = ET.parse(assn_data)
    assn_root = assn_tree.getroot()
    all_assignments = assn_root.findall('./patent-assignments/')
    for assignment in all_assignments:
        records = assignment.getchildren()
        reel_num, frame_num, correspondent_name, correspondent_address, \
        pat_assignee_name, pat_assignee_address = '', '', '', '', '', ''
        correspondent_addys, pat_addys, all_doc_nums = [], [], []
        for record in records:
            if record.tag == 'assignment-record':
                assignee_data = record.getchildren()
                for assignee_field in assignee_data:
                    if assignee_field.tag == 'reel-no':
                        reel_num = assignee_field.text
                    if assignee_field.tag == 'frame-no':
                        frame_num = assignee_field.text
                    if assignee_field.tag == 'correspondent':
                        correspondent_fields = assignee_field.getchildren()
                        for cfield in correspondent_fields:
                            if cfield.tag == 'name':
                                correspondent_name = cfield.text
                            else:
                                correspondent_addys.append(cfield.text)
            if record.tag == 'patent-assignees':
                pat_assignees = record.findall('./patent-assignee')
                for pat_assignee in pat_assignees:
                    pat_assignee_fields = pat_assignee.getchildren()
                    for pat_address in pat_assignee_fields:
                        if pat_address.tag == 'name':
                            pat_assignee_name = pat_address.text
                        else:
                            pat_addys.append(pat_address.text)
            if record.tag == 'patent-properties':
                doc_records = record.findall('./patent-property')
                for pat_assignee in doc_records:
                    doc_nums = []
                    doc_record_list = pat_assignee.findall('.//document-id')
                    for doc_record in doc_record_list:
                        doc_rec = doc_record.find('./doc-number')
                        doc_num = doc_rec.text
                        if len(doc_num) < 10:
                            doc_nums.append(doc_num)
                    all_doc_nums.append(doc_nums)
        correspondent_addys = [addy for addy in correspondent_addys if addy]
        correspondent_address = '\n'.join(correspondent_addys)
        pat_addys = [addy for addy in pat_addys if addy]
        pat_assignee_address = '\n'.join(pat_addys)
        all_data = [reel_num, frame_num, correspondent_name,
                    correspondent_address, pat_assignee_name,
                    pat_assignee_address]
        for pat_app_nums in all_doc_nums:
            parent_patent = ''
            if len(pat_app_nums) == 1:
                try:
                    parent_patent = Patent.objects.get(
                        application_number=pat_app_nums[0]
                    )
                except:
                    try:
                        parent_patent = Patent.objects.get(
                            patent_number=pat_app_nums[0]
                        )
                    except:
                        pass
            if len(pat_app_nums) == 2:
                try:
                    parent_patent = Patent.objects.get(
                        application_number=pat_app_nums[0],
                        patent_number=pat_app_nums[1]
                    )
                except:
                    try:
                        parent_patent = Patent.objects.get(
                            application_number=pat_app_nums[-1],
                            patent_number=pat_app_nums[0]
                        )
                    except:
                        pass
            if parent_patent:

                # Every now and then an empty record gets included, but
                # it is always missing the correspondent_name
                if correspondent_name != '' and \
                parent_patent.correspondent_name == '':
                    parent_patent.reel_num = all_data[0],
                    parent_patent.frame_num = all_data[1],
                    parent_patent.correspondent_name = all_data[2],
                    parent_patent.correspondent_address = all_data[3],
                    parent_patent.pat_assignee_name = all_data[4],
                    parent_patent.pat_assignee_address = all_data[5]
                    parent_patent.save()


def initial_pto_assignment_data():
    """Build upon assignment dataset created from initial_assignment_data() by
    dowloading and processing USPTO assignment zip and xml files
    """
    all_zip_links = ['ad19800101-20191231-'+str(i).zfill(2)+'.zip'
                     for i in range(1, 18)]
    daily_xmls = date(2020, 1, 1)
    today = date.today()
    while daily_xmls < today:
        zip_to_add = 'ad'+daily_xmls.strftime('%Y%m%d')+'.zip'
        all_zip_links.append(zip_to_add)
        daily_xmls = daily_xmls + timedelta(1)
    pickle.dump(all_zip_links, open('all_zip_links.p', 'wb'), protocol=2)


    if not glob('finished_zips.p'):
        rem_zips = '../../ad/adzips/*.zip'
        finished_zips = [zippy.split('/')[-1] for zippy in glob(rem_zips)]
    else:
        finished_zips = pickle.load(open('finished_zips.p', 'rb'))

    remaining_zips = [zfile for zfile in all_zip_links
                      if zfile not in finished_zips]

    for remaining_zip in remaining_zips:
        process_assignment_xml(remaining_zip)

        # keep updating processed data in case process is interrupted
        finished_zips.append(remaining_zip)
        pickle.dump(today, open('finished_zips.p', 'wb'), protocol=2)

    pickle.dump(today, open('last_assignment_update.p', 'wb'), protocol=2)
    reload_server()


def update_pto_assignment_data():
    """NEED TO SET UP SEPARATE CRON JOB FOR ASSIGNMENT DATA
    (EVERY DAY AT 12:00AM)
    """

    # Trying to keep database minimal size to load fastest, only the last
    # twelve years of data are required, so we will back up old data, and
    # remove old rows.
    today = date.today()
    old_date_obj = yearsago(12)
    old_date = str(old_date_obj)
    filepath = ('removed-%s.sql' % today)
    sql_string = 'mysqldump -h 127.0.0.1 -u root -P 3306 fees pto_patent \
    --where="issue_date<\'%s\'" --result-file=../../%s' % (old_date, filepath)
    subprocess.call(shlex.split(sql_string))

    # Remove all DB records older than 12 years
    old_pats = Patent.objects.filter(issue_date__lt=old_date_obj)
    for pat in old_pats:
        pat.delete()

    # Since cron job running at midnight, we want yesterday to get latest
    # data since USPTO updates around 10pm every day
    yesterday = today - timedelta(1)
    yester_str = yesterday.strftime('%Y%m%d')
    yester_strf = 'ad' + yester_str + '.zip'
    process_assignment_xml(yester_strf)

    # Make sure to save a record of last date updated so the program
    # processes any missing days
    pickle.dump(today, open('last_assignment_update.p', 'wb'), protocol=2)
    reload_server()


def update_pto_data():
    """CRON JOB FOR maintenance fee DATA (EVERY Wednesday AT 12:00AM)
    USPTO Maintenance Fee Data contains all patents, so we can build
    patent database first and associate assignment data later.
    """

    # Get latest maintenance fee data from USPTO (updated every Tuesday)
    mainfile = ('https://bulkdata.uspto.gov/data/patent/'
                'maintenancefee/MaintFeeEvents.zip'
               )
    main_req = requests.get(mainfile)

    # write zip file to disk
    zfile = '../../maintenance_fee_data/maintfees.zip'
    with open(zfile, 'wb') as main_zip:
        main_zip.write(main_req.content)

    # open zip file to get maintenance fee data
    mzip = zipfile.ZipFile(open(zfile, 'rb'))

    # There are multiple files in the zip, so we need the biggest one, which
    # contains the maintenance fee data, and the smallest one, which contains
    # the fee code descriptions
    sorted_files = sorted([(x.file_size, x.filename) for x in mzip.infolist()])
    mfile = sorted_files[-1][-1]
    efile = sorted_files[0][-1]

    # each line contains a maintenance fee entry, so split into list of entries
    with mzip.open(mfile) as main_lines:
        lines = main_lines.readlines()

    lines = set([line.decode() for line in lines])

    # Need to load the previous entries to compare to latest entries
    # because text comparison is much faster than DB filtering for # of entries
    mpickle = '../../maintenance_fee_data/maintfees_old.p'
    if glob(mpickle):
        old_lines = pickle.load(open(mpickle, 'rb'))
        new_lines = lines.difference(old_lines)

        # split each entry into the separate fields, also remove example lines
        split_lines = [line.split() for line in new_lines]
        split_lines = [line for line in split_lines
                       if not line[1].startswith('59')]

        for line in split_lines:
            patent_number = line[0].lstrip('0')
            application_number = line[1]
            entity_status = line[2]
            application_date = date(int(line[3][:4]),
                                    int(line[3][4:6]),
                                    int(line[3][6:])
                                   )
            issue_date = date(int(line[4][:4]),
                              int(line[4][4:6]), int(line[4][6:]))

            # if there is no entity date, set as the patent date
            try:
                maintenance_date = date(int(line[5][:4]),
                                        int(line[5][4:6]), int(line[5][6:]))
            except:
                maintenance_date = date(int(line[4][:4]),
                                        int(line[4][4:6]), int(line[4][6:]))

            # Deal with lines without maintenance code
            try:
                maintenance_code = line[6]
            except:
                maintenance_code = 'N/A'

            # Cant use get_or_create here because patent_number is a unique
            # field, but sometimes the application fields change in the
            # updated USPTO data
            patent = Patent.objects.filter(patent_number=patent_number)
            if patent:
                patent = patent.first()
            else:
                patent = Patent.objects.create(
                    patent_number=patent_number,
                    application_number=application_number,
                    application_date=application_date,
                    issue_date=issue_date,
                )

            # need to add/update the entity_status for each entry
            patent.entity_status = entity_status
            patent.save()

            fee_event, fee_created = FeeEvents.objects.get_or_create(
                patent=patent,
                maintenance_date=maintenance_date,
                maintenance_code=maintenance_code,
            )

    # if the file doesn't exist, then the database hasn't been built out yet
    else:

        # split each entry into the separate fields, also remove example lines
        split_lines = [line.split() for line in lines]
        split_lines = [line for line in split_lines
                       if not line[1].startswith('59')]

        # Create new maintenance event entries, but have to check each because
        # there is no easy way to separate the new entries
        pat_dict = {}
        for sline in split_lines:
            ref_id = sline[0].lstrip('0')
            if ref_id in pat_dict:
                pat_dict[ref_id].append(sline[1:])
            else:
                pat_dict[ref_id] = [sline[1:]]
        vcnt = 0
        for k, mdata in pat_dict.items():
            patent_number = k
            for i, pat_data in enumerate(mdata):
                if i == 0:
                    application_number = pat_data[0]
                    entity_status = pat_data[1]
                    application_date = date(int(pat_data[2][:4]),
                                            int(pat_data[2][4:6]),
                                            int(pat_data[2][6:]))
                    issue_date = date(int(pat_data[3][:4]),
                                      int(pat_data[3][4:6]),
                                      int(pat_data[3][6:]))

                    patent = Patent.objects.create(
                        patent_number=patent_number,
                        application_number=application_number,
                        entity_status=entity_status,
                        application_date=application_date,
                        issue_date=issue_date,
                    )

                # if there is no Fee Event Entry Date, set as the patent date
                try:
                    maintenance_date = date(int(pat_data[4][:4]),
                                            int(pat_data[4][4:6]),
                                            int(pat_data[4][6:]))
                except:
                    maintenance_date = date(int(pat_data[3][:4]),
                                            int(pat_data[3][4:6]),
                                            int(pat_data[3][6:]))
                # Deal with entries without maintenance code
                try:
                    maintenance_code = pat_data[5]
                except:
                    maintenance_code = 'N/A'

                fee_created = FeeEvents.objects.create(
                    patent=patent,
                    maintenance_date=maintenance_date,
                    maintenance_code=maintenance_code,
                )
            vcnt += 1

    # Need to save latest data in order to compare to new data the next week
    pickle.dump(lines, open(mpickle, 'wb'), protocol=2)

    # Create a pickled dictionary with event codes as keys and
    # their respective descriptions as their values
    with mzip.open(efile) as fee_file:
        fee_lines = fee_file.readlines()

    fee_codes = {}
    for line in fee_lines:
        line = line.decode()
        split_line = re.match(r'(.*?)\s+(.*?)\n', line)
        fee_codes[split_line.group(1)] = split_line.group(2)

    pickle.dump(fee_codes, open('fee_event_codes.p', 'wb'), protocol=2)

    # When all the above code has executed, we can generate the
    # remaining data and reload the server
    generate_final_data()
    reload_server()

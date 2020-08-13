"""
This is the initial database setup and population file to generate all
the necessary and up-to-date tables for this project using publicly
available USPTO .zip, .xml, .csv, and .txt files and API data
"""

from pto.pto_cron import (update_pto_data, initial_assignment_data,
    initial_pto_assignment_data)

update_pto_data()
initial_assignment_data()
initial_pto_assignment_data()

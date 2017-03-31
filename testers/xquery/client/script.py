#!/usr/bin/env python3

import sys
import os
import markus_xquery_config as cfg
from markus_xquery_tester import MarkusXQueryTester
from markusapi import Markus


if __name__ == '__main__':

    # Modify uppercase variables with your settings

    # The dataset files to be used for testing each student xquery submission, and the points assigned: student xquery
    # file names are the keys, dicts of dataset file names and points are the values.
    TEST_POINTS = {'all_data1.xml': 1, 'all_data2.xml': 2}
    TEST_SPECS = {'correct.xq': TEST_POINTS}
    tester = MarkusXQueryTester(path_to_solution=cfg.PATH_TO_SOLUTION, specs=TEST_SPECS, schemas=cfg.SCHEMAS)
    tester.run()
    # use markus apis if needed
    root_url = sys.argv[1]
    api_key = sys.argv[2]
    assignment_id = sys.argv[3]
    group_id = sys.argv[4]
    repo_name = sys.argv[5]
    # file_name = 'feedback_xquery.txt'
    # if os.path.isfile(file_name):
    #     api = Markus(api_key, root_url)
    #     with open(file_name) as open_file:
    #         api.upload_feedback_file(assignment_id, group_id, file_name, open_file.read())

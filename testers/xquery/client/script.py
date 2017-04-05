#!/usr/bin/env python3

import sys

from os.path import isfile

from markus_tester import MarkusTestSpecs
from markus_xquery_tester import MarkusXQueryTester
from markusapi import Markus


if __name__ == '__main__':

    # Markus identifiers
    root_url = sys.argv[1]
    api_key = sys.argv[2]
    assignment_id = sys.argv[3]
    group_id = sys.argv[4]
    repo_name = sys.argv[5]

    # Modify uppercase variables with your settings

    TEST_SPECS = MarkusTestSpecs('/path/to/specs')
    # The points assigned to each test case.
    POINTS1 = {'bad_xml': 0, 'bad_dtd': 1, 'bad_content': 2, '': 3}
    POINTS2 = {'bad_xml': 0, 'bad_dtd': 2, 'bad_content': 4, '': 6}
    POINTS3 = {'bad_xml': 0, 'bad_dtd': 3, 'bad_content': 6, '': 9}
    TEST_SPECS.set_points(POINTS1, {'correct.xq':                 ['data1.xml'],
                                    'correct_different_order.xq': ['data1.xml'],
                                    'bad_query.xq':               ['data1.xml'],
                                    'bad_xml.xq':                 ['data1.xml'],
                                    'bad_dtd.xq':                 ['data1.xml'],
                                    'bad_content.xq':             ['data1.xml'],
                                    'missing.xq':                 ['data1.xml']})
    TEST_SPECS.set_points(POINTS2, {'correct.xq':                 ['data2.xml'],
                                    'correct_different_order.xq': ['data2.xml'],
                                    'bad_query.xq':               ['data2.xml'],
                                    'bad_xml.xq':                 ['data2.xml'],
                                    'bad_dtd.xq':                 ['data2.xml'],
                                    'bad_content.xq':             ['data2.xml'],
                                    'missing.xq':                 ['data2.xml']})
    TEST_SPECS.set_points(POINTS3, {'correct_multi_data.xq':      ['data1.xml,data2.xml']})
    # True to strip leading and trailing spaces from xml data
    TEST_SPECS['strip_spaces'] = True
    # The feedback file name
    FEEDBACK_FILE = 'feedback_xquery.txt'

    tester = MarkusXQueryTester(specs=TEST_SPECS, feedback_file=FEEDBACK_FILE)
    tester.run()
    # use markus apis if needed
    # if isfile(FEEDBACK_FILE):
    #     api = Markus(api_key, root_url)
    #     with open(FEEDBACK_FILE) as feedback_open:
    #         api.upload_feedback_file(assignment_id, group_id, FEEDBACK_FILE, feedback_open.read())

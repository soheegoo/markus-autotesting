#!/usr/bin/env python3

import sys

from os.path import isfile

from markus_utils import MarkusUtils
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

    # The points assigned to each test case.
    TEST_SPECS = MarkusUtils.load_specs('/path/to/specs')
    TEST_MATRIX = TEST_SPECS['matrix']
    POINTS1 = {'bad_xml': 0, 'bad_dtd': 1, 'bad_content': 2, '': 3}
    POINTS2 = {'bad_xml': 0, 'bad_dtd': 2, 'bad_content': 4, '': 6}
    POINTS3 = {'bad_xml': 0, 'bad_dtd': 3, 'bad_content': 6, '': 9}
    TEST_MATRIX['correct.xq']['data1.xml']['points'] = POINTS1
    TEST_MATRIX['correct.xq']['data2.xml']['points'] = POINTS2
    TEST_MATRIX['correct_different_order.xq']['data1.xml']['points'] = POINTS1
    TEST_MATRIX['correct_different_order.xq']['data2.xml']['points'] = POINTS2
    TEST_MATRIX['correct_multi_data.xq']['data1.xml-data2.xml']['points'] = POINTS3
    TEST_MATRIX['bad_query.xq']['data1.xml']['points'] = POINTS1
    TEST_MATRIX['bad_query.xq']['data2.xml']['points'] = POINTS2
    TEST_MATRIX['bad_xml.xq']['data1.xml']['points'] = POINTS1
    TEST_MATRIX['bad_xml.xq']['data2.xml']['points'] = POINTS2
    TEST_MATRIX['bad_dtd.xq']['data1.xml']['points'] = POINTS1
    TEST_MATRIX['bad_dtd.xq']['data2.xml']['points'] = POINTS2
    TEST_MATRIX['bad_content.xq']['data1.xml']['points'] = POINTS1
    TEST_MATRIX['bad_content.xq']['data2.xml']['points'] = POINTS2
    TEST_MATRIX['missing.xq']['data1.xml']['points'] = POINTS1
    TEST_MATRIX['missing.xq']['data2.xml']['points'] = POINTS2
    # The feedback file name
    FEEDBACK_FILE = 'feedback_xquery.txt'

    tester = MarkusXQueryTester(specs=TEST_SPECS, feedback_file=FEEDBACK_FILE)
    tester.run()
    # use markus apis if needed
    # if isfile(FEEDBACK_FILE):
    #     api = Markus(api_key, root_url)
    #     with open(FEEDBACK_FILE) as feedback_open:
    #         api.upload_feedback_file(assignment_id, group_id, FEEDBACK_FILE, feedback_open.read())

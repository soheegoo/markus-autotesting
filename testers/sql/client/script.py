#!/usr/bin/env python3

import sys

from os.path import isfile

from markus_sql_tester import MarkusSQLTester
from markus_tester import MarkusTestSpecs
from markusapi import Markus


if __name__ == '__main__':

    # Markus identifiers
    root_url = sys.argv[1]
    api_key = sys.argv[2]
    assignment_id = sys.argv[3]
    group_id = sys.argv[4]
    repo_name = sys.argv[5]

    # Modify uppercase variables with your settings

    # The dataset files to be used for testing each student sql submission, and the points assigned: student sql file
    # names are the keys, dicts of dataset file names and points are the values.
    # (Students are required to create a solution table in their submission, named as the sql file without the file
    # extension; e.g. an 'example.sql' file must have a 'CREATE TABLE example [...];' in it)
    # The ORDER_BY clauses used to check the order of student sql submissions; if a sql file name is missing here, it is
    # checked without taking any ordering into account.
    # (Students are required to submit an additional sql file with '_order' suffix for each submission with ordering,
    # which selects from their solution table and does the ordering; e.g. an 'example.sql' file must have an additional
    # 'example_order.sql' file with a 'SELECT * FROM example ORDER BY [...];' in it)
    TEST_SPECS = MarkusTestSpecs('/path/to/specs')
    # The points assigned to each test case.
    POINTS1 = 1
    POINTS2 = 2
    POINTS = {'data1.sql': 1, 'data2.sql': 2}
    TEST_SPECS = {'correct_no_order.sql': POINTS, 'correct_with_order.sql': POINTS,
                  'bad_col_count.sql': POINTS, 'bad_col_name.sql': POINTS,
                  'bad_col_order.sql': POINTS, 'bad_col_type.sql': POINTS,
                  'bad_row_count.sql': POINTS, 'bad_row_order.sql': POINTS,
                  'bad_row_content_no_order.sql': POINTS, 'bad_row_content_with_order.sql': POINTS,
                  'bad_query': POINTS, 'compatible_column_type.sql': POINTS, 'missing.sql': POINTS}
    # The schema name
    TEST_SPECS['schema_name'] = 'ate'
    # The feedback file name
    FEEDBACK_FILE = 'feedback_sql.txt'

    tester = MarkusSQLTester(specs=TEST_SPECS, feedback_file=FEEDBACK_FILE)
    tester.run()
    # use markus apis if needed
    # if isfile(FEEDBACK_FILE):
    #     api = Markus(api_key, root_url)
    #     with open(FEEDBACK_FILE) as feedback_open:
    #         api.upload_feedback_file(assignment_id, group_id, FEEDBACK_FILE, feedback_open.read())

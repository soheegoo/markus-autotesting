#!/usr/bin/env python3

import sys
import os
import markus_sql_config as cfg
from markus_sql_tester import MarkusSQLTester
from markusapi import Markus


if __name__ == '__main__':

    # Modify uppercase variables with your settings

    # The dataset files to be used for testing each student sql submission, and the points assigned: student sql file
    # names are the keys, dicts of dataset file names and points are the values.
    # (Students are required to create a solution table in their submission, named as the sql file without the file
    # extension; e.g. an 'example.sql' file must have a 'CREATE TABLE example [...];' in it)
    TEST_POINTS = {'all_data1.sql': 1, 'all_data2.sql': 2}
    TEST_SPECS = {'correct_no_order.sql': TEST_POINTS, 'correct_with_order.sql': TEST_POINTS,
                  'bad_col_count.sql': TEST_POINTS, 'bad_col_name.sql': TEST_POINTS,
                  'bad_col_order.sql': TEST_POINTS, 'bad_col_type.sql': TEST_POINTS,
                  'bad_row_count.sql': TEST_POINTS, 'bad_row_order.sql': TEST_POINTS,
                  'bad_row_content_no_order.sql': TEST_POINTS, 'bad_row_content_with_order.sql': TEST_POINTS,
                  'compatible_column_type.sql': TEST_POINTS, 'missing.sql': TEST_POINTS}
    # The ORDER_BY clauses used to check the order of student sql submissions; if a sql file name is missing here, it is
    # checked without taking any ordering into account.
    # (Students are required to submit an additional sql file with '_order' suffix for each submission with ordering,
    # which selects from their solution table and does the ordering; e.g. an 'example.sql' file must have an additional
    # 'example_order.sql' file with a 'SELECT * FROM example ORDER BY [...];' in it)
    ORDER_BYS = {'correct_with_order.sql': 'word', 'bad_row_order.sql': 'word',
                 'bad_row_content_with_order.sql': 'word'}
    # The schema name
    SCHEMA_NAME = 'ate'
    tester = MarkusSQLTester(oracle_database=cfg.ORACLE_DATABASE, test_database=cfg.TEST_DATABASE, user_name=cfg.USER,
                             user_password=cfg.PASSWORD, path_to_solution=cfg.PATH_TO_SOLUTION, schema_name=SCHEMA_NAME,
                             specs=TEST_SPECS, order_bys=ORDER_BYS)
    tester.run()
    # use markus apis if needed
    root_url = sys.argv[1]
    api_key = sys.argv[2]
    assignment_id = sys.argv[3]
    group_id = sys.argv[4]
    # file_name = 'feedback.txt'
    # if os.path.isfile(file_name):
    #     api = Markus(api_key, root_url)
    #     with open(file_name) as open_file:
    #         api.upload_feedback_file(assignment_id, group_id, file_name, open_file.read())

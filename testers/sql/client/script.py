#!/usr/bin/env python3

import sys
import markus_sql_config as cfg
from markus_sql_tester import MarkusSQLTester
# from markusapi import Markus


if __name__ == '__main__':

    # Modify uppercase variables with your settings

    # The dataset files to be used for testing each student sql submission, and the points assigned: student sql file
    # names are the keys, dicts of dataset file names and points are the values.
    TEST_POINTS = {'data1.sql': 1, 'data2.sql': 2}
    TEST_SPECS = {'correct.sql': TEST_POINTS, 'badnumcolumns.sql': TEST_POINTS, 'badcolumnnames.sql': TEST_POINTS,
                  'badcolumntypes.sql': TEST_POINTS, 'badnumrows.sql': TEST_POINTS, 'badrowscontent.sql': TEST_POINTS,
                  'badrowsorder.sql': TEST_POINTS, 'compatiblecolumntypes.sql': TEST_POINTS}
    # The schema name
    SCHEMA_NAME = 'ate'
    tester = MarkusSQLTester(oracle_database=cfg.ORACLE_DATABASE, test_database=cfg.TEST_DATABASE, user_name=cfg.USER,
                             user_password=cfg.PASSWORD, path_to_solution=cfg.PATH_TO_SOLUTION, schema_name=SCHEMA_NAME,
                             specs=TEST_SPECS)
    tester.run()
    # use markus apis if needed (uncomment import markusapi)
    root_url = sys.argv[1]
    api_key = sys.argv[2]
    assignment_id = sys.argv[3]
    group_id = sys.argv[4]
    # file_name = 'result.txt'
    # api = Markus(api_key, root_url)
    # with open(file_name) as open_file:
    #     api.upload_feedback_file(assignment_id, group_id, file_name, open_file.read())

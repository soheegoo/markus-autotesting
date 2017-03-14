#!/usr/bin/env python3

import sys
import os

import markus_sql_config as sql_cfg
import markus_jdbc_config as jdbc_cfg
from markus_jdbc_tester import MarkusJDBCTester
from markusapi import Markus


if __name__ == '__main__':

    JAVA_FILES = ['Submission.java']
    # TODO use JAVA_FILES in the specs?
    JAVA_SPECS = {'selectMethod': {'all_data1.sql': 1, 'all_data2.sql': 1},
                  'insertMethod': {'all_data1.sql': 1, 'all_data2.sql': 1}}
    SQL_SPECS = {'insertMethod': {'all_data1.sql': [('Table1', 1), ('Table2', 1)],
                                  'all_data2.sql': [('Table1', 1), ('Table2', 1)]}}
    SCHEMA_NAME = 'ate'
    tester = MarkusJDBCTester(oracle_database=sql_cfg.ORACLE_DATABASE, test_database=sql_cfg.TEST_DATABASE,
                              user_name=sql_cfg.USER, user_password=sql_cfg.PASSWORD,
                              path_to_solution=sql_cfg.PATH_TO_SOLUTION, schema_name=SCHEMA_NAME, java_specs=JAVA_SPECS,
                              java_files=JAVA_FILES, java_jar=jdbc_cfg.PATH_TO_JDBC_JAR, sql_specs=SQL_SPECS)
    tester.run()
    # use markus apis if needed
    root_url = sys.argv[1]
    api_key = sys.argv[2]
    assignment_id = sys.argv[3]
    group_id = sys.argv[4]
    repo_name = sys.argv[5]
    # file_name = 'feedback_jdbc.txt'
    # if os.path.isfile(file_name):
    #     api = Markus(api_key, root_url)
    #     with open(file_name) as open_file:
    #         api.upload_feedback_file(assignment_id, group_id, file_name, open_file.read())

#!/usr/bin/env python3

import sys

import os

from markus_jdbc_tester import MarkusJDBCTester
from markus_tester import MarkusTestSpecs
from markusapi import Markus


if __name__ == '__main__':

    # Markus identifiers
    root_url = sys.argv[1]
    api_key = sys.argv[2]
    assignment_id = sys.argv[3]
    group_id = sys.argv[4]
    repo_name = sys.argv[5]
    SPECS = MarkusTestSpecs()

    # Students are required to create a solution table in their submission, named as the sql file without the file
    # extension; e.g. an 'example.sql' file must have a 'CREATE TABLE example [...];' in it.
    # Students are also required to submit an additional sql file with '_order' suffix for each submission that cares
    # about ordering, which selects from their solution table and does the ordering; e.g. an 'example.sql' file must
    # have an additional 'example_order.sql' file with a 'SELECT * FROM example ORDER BY [...];' in it)

    # The points assigned to each test case; points can be assigned in three ways:
    # 1) to some tests+datasets
    #    SPECS['points'] = {'test1': {'data1': 11, 'data2': 12}, 'test2': {'data1': 21, 'data2': 22}}
    # 2) to all datasets of some tests
    #    SPECS['test_points'] = {'test1': 1, 'test2': 2}
    # 3) to all tests of some datasets
    #    SPECS['data_points'] = {'data1': 1, 'data2': 2}
    # If you don't specify some tests/datasets from the solution, they are assigned a default of 1 point.
    SPECS['data_points'] = {'data1j.sql': 1, 'data2j.sql': 2}

    # The schema name
    SPECS['schema_name'] = 'ate'

    # The feedback file name (defaults to no feedback file if commented out).
    # SPECS['feedback_file'] = 'feedback_jdbc.txt'

    tester = MarkusJDBCTester(specs=SPECS)
    tester.run()
    # Use markus apis if needed
    # if os.path.isfile(SPECS['feedback_file']):
    #     api = Markus(api_key, root_url)
    #     with open(SPECS['feedback_file']) as feedback_open:
    #         api.upload_feedback_file(assignment_id, group_id, SPECS['feedback_file'], feedback_open.read())

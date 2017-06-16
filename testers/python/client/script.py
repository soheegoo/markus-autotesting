#!/usr/bin/env python3

import os
import sys

from markus_pam_tester import MarkusPAMTester
from markus_tester import MarkusTestSpecs
from markusapi import Markus


if __name__ == '__main__':

    # Markus identifiers
    root_url = sys.argv[1]
    api_key = sys.argv[2]
    assignment_id = sys.argv[3]
    group_id = sys.argv[4]
    repo_name = sys.argv[5]
    TEST_SPECS = MarkusTestSpecs('/path/to/specs')

    # Modify uppercase variables with your settings

    # The test files (uploaded as support files) to test the student submission, and the points assigned:
    # test file names are the keys, dicts of test functions (or test classes) and points are the values;
    # if a test function/class is missing, it is assigned a default of 1 point (use TEST_POINTS = {} for all 1s).
    POINTS = {'test_passes': 1, 'test_fails': 2, 'Test2': 1}
    TEST_SPECS.set_test_points('test.py', POINTS)
    # The max time to run a single test on the student submission.
    TEST_SPECS['test_timeout'] = 10
    # The max time to run all tests on the student submission.
    TEST_SPECS['global_timeout'] = 30
    # The feedback file name
    FEEDBACK_FILE = 'feedback_python.txt'
    tester = MarkusPAMTester(specs=TEST_SPECS, feedback_file=FEEDBACK_FILE)
    tester.run()
    # use markus apis if needed
    # if os.path.isfile(FEEDBACK_FILE):
    #     api = Markus(api_key, root_url)
    #     with open(FEEDBACK_FILE) as feedback_open:
    #         api.upload_feedback_file(assignment_id, group_id, FEEDBACK_FILE, feedback_open.read())

#!/usr/bin/env python3

import sys

from os.path import isfile

import markus_pam_config as cfg
from markus_pam_tester import MarkusPAMTester
from markusapi import Markus


if __name__ == '__main__':

    # Modify uppercase variables with your settings

    # The test files (uploaded as support files) to test the student submission, and the points assigned:
    # test file names are the keys, dicts of test functions (or test classes) and points are the values;
    # if a test function/class is missing, it is assigned a default of 1 point (use TEST_POINTS = {} for all 1s).
    TEST_POINTS = {'Test1.test_passes': 1, 'Test1.test_fails': 2, 'Test2': 1}
    TEST_SPECS = {'test.py': TEST_POINTS}
    # The max time to run a single test on the student submission.
    TEST_TIMEOUT = 5
    # The max time to run all tests on the student submission.
    GLOBAL_TIMEOUT = 20
    # The feedback file name
    FEEDBACK_FILE = 'feedback_python.txt'
    tester = MarkusPAMTester(path_to_uam=cfg.PATH_TO_UAM, specs=TEST_SPECS, test_timeout=TEST_TIMEOUT,
                             global_timeout=GLOBAL_TIMEOUT, feedback_file=FEEDBACK_FILE)
    tester.run()
    # use markus apis if needed
    root_url = sys.argv[1]
    api_key = sys.argv[2]
    assignment_id = sys.argv[3]
    group_id = sys.argv[4]
    repo_name = sys.argv[5]
    # if isfile(FEEDBACK_FILE):
    #     api = Markus(api_key, root_url)
    #     with open(FEEDBACK_FILE) as open_file:
    #         api.upload_feedback_file(assignment_id, group_id, FEEDBACK_FILE, open_file.read())

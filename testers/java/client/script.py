#!/usr/bin/env python3

import os
import sys

from markus_jam_tester import MarkusJAMTester
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

    POINTS = {'Test1.testPasses': 1, 'Test1.testFails': 2, 'Test2': 1}
    TEST_SPECS.set_test_points(POINTS, 'Tests.java')
    # The max time to run all tests on the student submission.
    TEST_SPECS['global_timeout'] = 20
    # The feedback file name
    FEEDBACK_FILE = 'feedback_java.txt'

    tester = MarkusJAMTester(specs=TEST_SPECS, feedback_file=FEEDBACK_FILE)
    tester.run()
    # use markus apis if needed
    if os.path.isfile(FEEDBACK_FILE):
        api = Markus(api_key, root_url)
        with open(FEEDBACK_FILE) as feedback_open:
            api.upload_feedback_file(assignment_id, group_id, FEEDBACK_FILE, feedback_open.read())

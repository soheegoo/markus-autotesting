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
    SPECS = MarkusTestSpecs()

    # The test files to run (precompiled on the server), and the points assigned:
    # points can be assigned per test function, or per test class (every test function in the class will be worth those
    # points); if a test function/class is missing, it is assigned a default of 1 point (use POINTS = {} for all 1s).
    POINTS1 = {'testPasses': 1, 'testFails': 2}
    POINTS2 = {'Test2': 1}
    SPECS['test_points'] = {'Test1.java': POINTS1}
    SPECS['test_points'] = {'Test2.java': POINTS2}

    # The max time to run all tests (defaults to 30 seconds if commented out).
    # SPECS['global_timeout'] = 30

    # The feedback file name (defaults to no feedback file if commented out).
    # SPECS['feedback_file'] = 'feedback_java.txt'

    tester = MarkusJAMTester(specs=SPECS)
    tester.run()
    # Use markus apis if needed
    # if os.path.isfile(FEEDBACK_FILE):
    #     api = Markus(api_key, root_url)
    #     with open(FEEDBACK_FILE) as feedback_open:
    #         api.upload_feedback_file(assignment_id, group_id, FEEDBACK_FILE, feedback_open.read())

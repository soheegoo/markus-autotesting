#!/usr/bin/env python3

import os
import sys

from markus_python_tester import MarkusPythonTester
from markus_tester import MarkusTestSpecs
from markusapi import Markus


if __name__ == '__main__':

    """
    MarkUs identifiers.
    """
    root_url = sys.argv[1]
    api_key = sys.argv[2]
    assignment_id = sys.argv[3]
    group_id = sys.argv[4]
    repo_name = sys.argv[5]
    SPECS = MarkusTestSpecs()

    """
    The test files to run (uploaded as support files), and the points assigned:
    points can be assigned per test function, or per test class (every test function in the class will be worth those
    points); if a test function/class is missing, it is assigned a default of 1 point (use POINTS = {} for all 1s).
    """
    POINTS = {}
    SPECS['test_points'] = {'test.py': POINTS, 'test2.py': POINTS}

    """
    The feedback file name; defaults to no feedback file if commented out.
    """
    # SPECS['feedback_file'] = 'feedback_python.txt'

    tester = MarkusPythonTester(specs=SPECS)
    tester.run()

    """
    Use MarkUs apis if needed.
    """
    # if os.path.isfile(SPECS['feedback_file']):
    #     api = Markus(api_key, root_url)
    #     with open(SPECS['feedback_file']) as feedback_open:
    #         api.upload_feedback_file(assignment_id, group_id, SPECS['feedback_file'], feedback_open.read())

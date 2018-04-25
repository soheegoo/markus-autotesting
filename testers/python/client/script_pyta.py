#!/usr/bin/env python3

import os
import sys

from markus_pyta_tester import MarkusPyTATester
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
    The student files to analyze with PyTA, and the points assigned; 1 point will be deducted per message occurrence, up
    to a minimum of 0.
    """
    SPECS['test_points'] = {'submission.py': 10}

    """
    The PyTA configuration; you can comment this out and use a support file named .pylintrc instead.
    In either case, you should not specify 'pyta-output-file' and 'pyta-reporter'.
    """
    SPECS['pyta_config'] = {}

    """
    The feedback file name (defaults to no feedback file if commented out).
    """
    # SPECS['feedback_file'] = 'feedback_pyta.txt'

    tester = MarkusPyTATester(specs=SPECS)
    tester.run()

    """
    Use MarkUs apis if needed.
    """
    # api = Markus(api_key, root_url)
    # api.upload_annotations(assignment_id, group_id, tester.annotations)
    # if os.path.isfile(SPECS['feedback_file']):
    #     with open(SPECS['feedback_file']) as feedback_open:
    #         api.upload_feedback_file(assignment_id, group_id, SPECS['feedback_file'], feedback_open.read())

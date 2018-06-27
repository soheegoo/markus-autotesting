#!/usr/bin/env python3

import os
import sys

from markus_haskell_tester import MarkusHaskellTester
from markus_tester import MarkusTestSpecs
from markusapi import Markus


if __name__ == '__main__':

    ''' Markus identifiers '''
    root_url = sys.argv[1]
    api_key = sys.argv[2]
    assignment_id = sys.argv[3]
    group_id = sys.argv[4]
    repo_name = sys.argv[5]
    SPECS = MarkusTestSpecs()

    '''
    The test files to run (uploaded as support files), and the points assigned:
    points can be assigned per test.  If a test is missing, it is assigned a 
    default of 1 point (use POINTS = {} for all 1s).
    '''
    POINTS = {}
    SPECS['test_points'] = {'Test.hs': POINTS}

    '''
    The max time to run a single test (defaults to 10 seconds if commented out).
    (this timeout may not work in particular cases, e.g. with multi-threading)
    '''
    
    # SPECS['test_timeout'] = 10

    '''
    The number of test cases to run for each quickcheck test 
    (default is 100)
    '''

    # SPECS['test_cases'] = 100

    '''
    The feedback file name (defaults to no feedback file if commented out).
    '''

    # SPECS['feedback_file'] = 'feedback_haskell.txt'

    tester = MarkusHaskellTester(specs=SPECS)
    tester.run()
    
    '''
    Use markus apis if needed
    '''
    # if os.path.isfile(SPECS['feedback_file']):
    #     api = Markus(api_key, root_url)
    #     with open(SPECS['feedback_file']) as feedback_open:
    #         api.upload_feedback_file(assignment_id, group_id, SPECS['feedback_file'], feedback_open.read())

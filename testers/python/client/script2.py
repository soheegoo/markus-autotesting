#!/usr/bin/env python3

from markus_python_tester import MarkusPythonTester
from markus_tester import MarkusTestSpecs

if __name__ == '__main__':

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

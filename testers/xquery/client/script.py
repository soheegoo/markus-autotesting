#!/usr/bin/env python3

from markus_tester import MarkusTestSpecs
from markus_xquery_tester import MarkusXQueryTester

if __name__ == '__main__':

    # Modify uppercase variables with your settings

    TEST_SPECS = MarkusTestSpecs('/path/to/specs')
    # The points assigned to each test case.
    POINTS1 = {'bad_xml': 0, 'bad_dtd': 1, 'bad_content': 2, '': 3}
    POINTS2 = {'bad_xml': 0, 'bad_dtd': 2, 'bad_content': 4, '': 6}
    POINTS3 = {'bad_xml': 0, 'bad_dtd': 3, 'bad_content': 6, '': 9}
    TEST_SPECS.set_data_points('data1.xml', POINTS1)
    TEST_SPECS.set_data_points('data2.xml', POINTS2)
    TEST_SPECS.set_data_points('data1.xml,data2.xml', POINTS3)
    # The feedback file name
    FEEDBACK_FILE = 'feedback_xquery.txt'

    tester = MarkusXQueryTester(specs=TEST_SPECS, feedback_file=FEEDBACK_FILE)
    tester.run()

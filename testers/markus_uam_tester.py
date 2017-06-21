import contextlib

from markus_tester import MarkusTester, MarkusTestSpecs, MarkusTest
from markus_utils import MarkusUtils
from uam_tester import UAMResult, UAMTester


class MarkusUAMTester(MarkusTester):
    """
    A wrapper to run a UAM tester (https://github.com/ProjectAT/uam) within Markus' test framework.
    """

    def __init__(self, specs, feedback_file='feedback_uam.txt', tester_class=UAMTester, test_ext=''):
        super().__init__(specs, feedback_file)
        path_to_tests = specs.get('path_to_tests', '.')
        test_points = {
            test_file: specs.matrix[test_file][MarkusTestSpecs.MATRIX_NODATA_KEY][MarkusTestSpecs.MATRIX_POINTS_KEY]
            for test_file in specs.test_files}
        global_timeout = specs.get('global_timeout', UAMTester.GLOBAL_TIMEOUT_DEFAULT)
        test_timeout = specs.get('test_timeout', UAMTester.TEST_TIMEOUT_DEFAULT)
        self.uam_tester = tester_class(specs['path_to_uam'], path_to_tests, test_points, global_timeout, test_timeout,
                                       result_filename='result.json')
        self.test_ext = test_ext

    def run(self):
        try:
            with contextlib.ExitStack() as stack:
                feedback_open = (stack.enter_context(open(self.feedback_file, 'w'))
                                 if self.feedback_file is not None
                                 else None)
                results = self.uam_tester.run()
                for result in results:
                    points_awarded, points_total = self.uam_tester.get_test_points(result, self.test_ext)
                    test = MarkusUAMTest(result, points_awarded, points_total, feedback_open)
                    xml = test.run()
                    print(xml)
        except Exception as e:
            MarkusUtils.print_test_error(name='All tests', message=str(e))


class MarkusUAMTest(MarkusTest):

    def __init__(self, uam_result, points_awarded, points_total, feedback_open):
        super().__init__(uam_result.test_title, [], {MarkusTestSpecs.MATRIX_POINTS_KEY: points_total}, None,
                         feedback_open)
        self.test_data_name = uam_result.test_title
        self.uam_result = uam_result
        self.points_awarded = points_awarded

    def run(self):
        if self.uam_result.status == UAMResult.Status.PASS:
            return self.passed()
        elif self.uam_result.status == UAMResult.Status.FAIL:
            # TODO add test_solution=self.uam_result.trace? (But test trace could be confusing)
            return self.failed(points_awarded=self.points_awarded, message=self.uam_result.message)
        else:
            return self.error(message=self.uam_result.message)

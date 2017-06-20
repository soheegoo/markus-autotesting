import contextlib

from markus_tester import MarkusTestSpecs
from markus_uam_tester import MarkusUAMTester, MarkusUAMTest
from pam_tester import PAMTester
from markus_utils import MarkusUtils


class MarkusPAMTester(MarkusUAMTester):
    """
    A wrapper to run the Python AutoMarker (pam - https://github.com/ProjectAT/uam) within Markus' test framework.
    """

    def __init__(self, specs, feedback_file='feedback_python.txt'):
        super().__init__(specs, feedback_file, tester_class=PAMTester)
        self.test_timeout = specs['test_timeout']
        test_points = {
            test_file: specs.matrix[test_file][MarkusTestSpecs.MATRIX_NODATA_KEY][MarkusTestSpecs.MATRIX_POINTS_KEY]
            for test_file in specs.test_files}
        self.pam_tester = PAMTester(self.path_to_uam, test_points, self.test_timeout, self.global_timeout,
                                    result_filename='result.json')

    def run(self):
        try:
            with contextlib.ExitStack() as stack:
                feedback_open = (stack.enter_context(open(self.feedback_file, 'w'))
                                 if self.feedback_file is not None
                                 else None)
                results = self.pam_tester.run()
                for result in results:
                    points_awarded, points_total = self.pam_tester.get_test_points(result, file_ext='py')
                    test = MarkusUAMTest(result, points_awarded, points_total, feedback_open)
                    xml = test.run()
                    print(xml)
        except Exception as e:
            MarkusUtils.print_test_error(name='All PYTHON tests', message=str(e))

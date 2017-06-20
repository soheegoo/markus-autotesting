from markus_tester import MarkusTester, MarkusTestSpecs, MarkusTest
from uam_tester import UAMResult, UAMTester


class MarkusUAMTester(MarkusTester):

    def __init__(self, specs, feedback_file='feedback_uam.txt', tester_class=UAMTester):
        super().__init__(specs, feedback_file)
        self.path_to_uam = specs['path_to_uam']
        self.global_timeout = specs['global_timeout']
        test_points = {
            test_file: specs.matrix[test_file][MarkusTestSpecs.MATRIX_NODATA_KEY][MarkusTestSpecs.MATRIX_POINTS_KEY]
            for test_file in specs.test_files}
        self.uam_tester = tester_class(self.path_to_uam, test_points, self.global_timeout,
                                       result_filename='result.json')

    def create_uam_tester(self, path_to_uam, test_points, global_timeout):
        return UAMTester(path_to_uam, test_points, global_timeout, result_filename='result.json')


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

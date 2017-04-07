from contextlib import ExitStack
from json import loads

from os.path import splitext
from xml.sax.saxutils import escape

from markus_utils import MarkusUtils


class MarkusTestSpecs:

    MATRIX_KEY = 'matrix'
    MATRIX_NONTEST_KEY = 'extra'
    MATRIX_POINTS_KEY = 'points'
    DATA_FILES_SEPARATOR = ','

    def __init__(self, path_to_specs):
        self._specs = {}
        with open(path_to_specs, 'r') as specs_open:
            self._specs = loads(specs_open.read())

    def __getitem__(self, item):
        return self._specs[item]

    def __setitem__(self, key, value):
        self._specs[key] = value

    @property
    def matrix(self):
        return self[MarkusTestSpecs.MATRIX_KEY]

    # TODO Create function to assing points to all tests and datasets, all datasets of a test, all tests of a dataset
    def set_points(self, points, test_data):
        for test_file, data_files in test_data.items():
            for data_file in data_files:
                self.matrix[test_file][data_file][MarkusTestSpecs.MATRIX_POINTS_KEY] = points


class MarkusTester:

    def __init__(self, specs, feedback_file=None):
        self.specs = specs
        self.feedback_file = feedback_file

    def create_test(self, test_file, data_files, test_data_config, test_extra, feedback_open):
        # TODO Make it more elegant using a factory pattern, and add all global test configs
        return MarkusTest(test_file, data_files, test_data_config, test_extra, feedback_open)

    def run(self):
        try:
            with ExitStack() as stack:
                feedback_open = (stack.enter_context(open(self.feedback_file, 'w'))
                                 if self.feedback_file is not None
                                 else None)
                for test_file in sorted(self.specs.matrix.keys()):
                    test_extra = self.specs.matrix[test_file].get(MarkusTestSpecs.MATRIX_NONTEST_KEY)
                    for data_files in sorted(self.specs.matrix[test_file].keys()):
                        if data_files == MarkusTestSpecs.MATRIX_NONTEST_KEY:
                            continue
                        test_data_config = self.specs.matrix[test_file][data_files]
                        if MarkusTestSpecs.DATA_FILES_SEPARATOR in data_files:
                            data_files = data_files.split(MarkusTestSpecs.DATA_FILES_SEPARATOR)
                        else:
                            data_files = [data_files]
                        test = self.create_test(test_file, data_files, test_data_config, test_extra, feedback_open)
                        xml = test.run()
                        print(xml)
        except Exception as e:
            MarkusUtils.print_test_error(name='All tests', message=str(e))


class MarkusTest:

    def __init__(self, test_file, data_files, test_data_config, test_extra, feedback_open=None):
        self.test_file = test_file
        self.test_name = splitext(test_file)[0]
        self.data_files = data_files
        self.data_name = MarkusTestSpecs.DATA_FILES_SEPARATOR.join([splitext(data_file)[0] for data_file in data_files])
        self.test_data_name = '{} + {}'.format(self.test_name, self.data_name)
        # TODO Use a default or disable if not set?
        self.points = test_data_config[MarkusTestSpecs.MATRIX_POINTS_KEY]
        if isinstance(self.points, dict):
            self.points_total = max(self.points.values())
        else:
            self.points_total = self.points
        if self.points_total <= 0:
            raise ValueError('The test total points must be > 0')
        self.test_data_config = test_data_config
        self.test_extra = test_extra
        self.feedback_open = feedback_open

    def format_result(self, status, points_awarded, output):
        """
        Creates the test result in the format expected by Markus.
        :param status: One of 'pass', 'fail', 'error'.
        :param points_awarded: The points awarded by the test, must be an integer >= 0 and <= test total points.
        :param output: The test output.
        :return The formatted test result.
        """
        if points_awarded < 0:
            raise ValueError('The test points awarded must be >= 0')
        if points_awarded > self.points_total:
            raise ValueError('The test points awarded must be <= test total points')
        output_escaped = escape(output.replace('\x00', ''), entities={"'": '&apos;'})
        name = '[{}/{}] {}'.format(points_awarded, self.points_total, self.test_data_name)
        return '''
<test>
    <name>{}</name>
    <input></input>
    <expected></expected>
    <actual>{}</actual>
    <marks_earned>{}</marks_earned>
    <status>{}</status>
</test>'''.format(name, output_escaped, points_awarded, status)

    def passed(self, message=''):
        """
        Passes this test with the test total points.
        :param message: An optional message, will be shown as test output.
        :return The formatted passed test.
        """
        return self.format_result(status='pass', points_awarded=self.points_total, output=message)

    def failed(self, points_awarded, message):
        """
        Fails this test with 0 or some points awarded.
        :param message: The failure message, will be shown as test output.
        :param points_awarded: The points awarded by the test, must be an integer >= 0 and < test total points.
        :return The formatted failed test.
        """
        if points_awarded >= self.points_total:
            raise ValueError('The test points awarded must be < test total points')
        return self.format_result(status='fail', points_awarded=points_awarded, output=message)

    def error(self, message):
        """
        Err this test.
        :param message: The error message, will be shown as test output.
        :return The formatted erred test.
        """
        return self.format_result(status='error', points_awarded=0, output=message)

    def add_feedback(self, status, feedback='', oracle_solution=None, test_solution=None):
        """
        Adds the test feedback to the feedback file.
        :param status: One of 'pass', 'fail', 'error'.
        :param feedback: The feedback, can be None.
        :param oracle_solution: The expected solution, can be None.
        :param test_solution: The test solution, can be None.
        """
        if self.feedback_open is None:
            raise ValueError('The test is not supposed to write to a feedback file')
        self.feedback_open.write('========== {}: {} ==========\n\n'.format(self.test_data_name, status.upper()))
        if feedback:
            self.feedback_open.write('## Feedback: {}\n\n'.format(feedback))
        if status != 'pass':
            if oracle_solution:
                self.feedback_open.write('## Expected Solution:\n\n')
                self.feedback_open.write(oracle_solution)
            if test_solution:
                self.feedback_open.write('## Your Solution:\n\n')
                self.feedback_open.write(test_solution)
        self.feedback_open.write('\n')

    def passed_and_feedback(self, message=''):
        result = self.passed(message=message)
        self.add_feedback(status='pass')
        return result

    def failed_and_feedback(self, points_awarded, message, oracle_solution=None, test_solution=None):
        result = self.failed(points_awarded=points_awarded, message=message)
        self.add_feedback(status='fail', feedback=message, oracle_solution=oracle_solution, test_solution=test_solution)
        return result

    def error_and_feedback(self, message, oracle_solution=None, test_solution=None):
        result = self.error(message=message)
        self.add_feedback(status='error', feedback=message, oracle_solution=oracle_solution,
                          test_solution=test_solution)
        return result

    def run(self):
        """
        Runs this test.
        :return The formatted test.
        """
        raise NotImplementedError

from contextlib import ExitStack

from os.path import splitext
from xml.sax.saxutils import escape

from markus_utils import MarkusUtils


class MarkusTester:

    MATRIX_NONTEST_KEY = 'extra'
    MATRIX_POINTS_KEY = 'points'
    DATA_FILES_SEPARATOR = ','

    def __init__(self, specs, feedback_file=None):
        self.specs = specs
        self.matrix = specs['matrix']
        self.feedback_file = feedback_file

    def create_test(self, test_file, data_files, test_data_config, test_extra, feedback_open):
        return MarkusTest(test_file, data_files, test_data_config, test_extra, feedback_open)

    def run(self):
        try:
            with ExitStack() as stack:
                feedback_open = (stack.enter_context(open(self.feedback_file, 'w'))
                                 if self.feedback_file is not None
                                 else None)
                for test_file in sorted(self.matrix.keys()):
                    test_extra = self.matrix[test_file].get(MarkusTester.MATRIX_NONTEST_KEY)
                    for data_files, test_data_config in sorted(self.matrix[test_file].items()):
                        if data_files == MarkusTester.MATRIX_NONTEST_KEY:
                            continue
                        if MarkusTester.DATA_FILES_SEPARATOR in data_files:
                            data_files = data_files.split(MarkusTester.DATA_FILES_SEPARATOR)
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
        self.data_name = MarkusTester.DATA_FILES_SEPARATOR.join([splitext(data_file)[0] for data_file in data_files])
        self.test_data_name = '{} + {}'.format(self.test_name, self.data_name)
        # TODO Use a default or disable if not set? + Create function to assign same points to all
        self.points = test_data_config[MarkusTester.MATRIX_POINTS_KEY]
        if isinstance(self.points, dict):
            self.points_total = max(self.points)
        else:
            self.points_total = self.points
        if self.points_total <= 0:
            raise ValueError('The test total points must be > 0')
        self.test_data_config = test_data_config
        self.test_extra = test_extra
        self.feedback_open = feedback_open

    def format_result(self, status, output, points_awarded):
        """
        Creates the test result in the format expected by Markus.
        :param status: One of 'pass', 'fail', 'error'.
        :param output: The test output.
        :param points_awarded: The points awarded by the test, must be an integer >= 0 and <= test total points.
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
        :return The formatted test passed.
        """
        return self.format_result(status='pass', output=message, points_awarded=self.points_total)

    def failed(self, points_awarded, message):
        """
        Fails this test with 0 or some points awarded.
        :param message: The failure message, will be shown as test output.
        :param points_awarded: The points awarded by the test, must be an integer >= 0 and < test total points.
        :return The formatted test failed.
        """
        if points_awarded >= self.points_total:
            raise ValueError('The test points awarded must be < test total points')
        return self.format_result(status='fail', output=message, points_awarded=points_awarded)

    def error(self, message):
        """
        Err this test.
        :param message: The error message, will be shown as test output.
        :return The formatted test errored.
        """
        return self.format_result(status='error', output=message, points_awarded=0)

    def run(self):
        """
        Runs this test.
        """
        raise NotImplementedError

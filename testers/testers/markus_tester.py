import collections
import contextlib
import enum
import json
import os
import subprocess
import sys

class MarkusTest:

    class Status(enum.Enum):
        PASS = 'pass'
        PARTIAL = 'partial'
        FAIL = 'fail'
        ERROR = 'error'
        ERROR_ALL = 'error_all'

    def __init__(self, tester, test_file, data_files, points, test_extra, feedback_open=None):
        self.tester = tester
        self.test_file = test_file  # TODO Is really a file or a more generic test the base unit here?
        self.data_files = data_files
        self.points = points  # TODO Use a default or disable if not set?
        if isinstance(self.points, collections.abc.Mapping):
            self.points_total = sum(self.points.values())
        else:
            self.points_total = self.points
        if self.points_total <= 0:
            raise ValueError('The test total points must be > 0')
        self.test_extra = test_extra
        self.feedback_open = feedback_open

    @property
    def test_name(self):
        return os.path.splitext(self.test_file)[0]

    @property
    def data_name(self):
        return MarkusTestSpecs.DATA_FILES_SEPARATOR.join([os.path.splitext(data_file)[0]
                                                          for data_file in self.data_files])

    @property
    def test_data_name(self):
        if self.data_name == MarkusTestSpecs.MATRIX_NODATA_KEY:
            return self.test_name
        else:
            return '{} + {}'.format(self.test_name, self.data_name)

    @staticmethod
    def format_result(test_name, status, output, points_earned, points_total, time=None):
        """
        Formats a test result as expected by Markus.
        :param test_name: The test name
        :param status: A member of MarkusTest.Status.
        :param output: The test output.
        :param points_earned: The points earned by the test, must be a float >= 0 (can be greater than the test total
                              points when assigning bonus points).
        :param points_total: The total points the test could earn, must be a float >= 0.
        :param time: The time it took to run the test, can be None
        :return The formatted test result.
        """
        if points_total < 0:
            raise ValueError('The test total points must be >= 0')
        if points_earned < 0:
            raise ValueError('The test points earned must be >= 0')
        if time is not None:
            if not isinstance(time, int) or time < 0:
                raise ValueError('The time must be a positive integer or None')

        result_json = json.dumps({'name': test_name, 
                                  'input': '', 
                                  'expected': '', 
                                  'actual': output, 
                                  'marks_earned': points_earned, 
                                  'marks_total': points_total, 
                                  'status': status.value, 
                                  'time': time})
        return result_json

    def format(self, status, output, points_earned):
        """
        Formats the result of this test as expected by Markus.
        :param status: A member of MarkusTest.Status.
        :param output: The test output.
        :param points_earned: The points earned by the test, must be a float >= 0 (can be greater than the test total
                              points when assigning bonus points).
        :return The formatted test result.
        """
        return MarkusTest.format_result(self.test_data_name, status, output, points_earned, self.points_total)

    def add_feedback(self, status, feedback='', oracle_solution=None, test_solution=None):
        """
        Adds the feedback of this test to the feedback file.
        :param status: A member of MarkusTest.Status.
        :param feedback: The feedback, can be None.
        :param oracle_solution: The expected solution, can be None.
        :param test_solution: The test solution, can be None.
        """
        # TODO Reconcile with format: return both, or print both
        if self.feedback_open is None:
            raise ValueError('No feedback file enabled')
        self.feedback_open.write('========== {}: {} ==========\n\n'.format(self.test_data_name, status.value.upper()))
        if feedback:
            self.feedback_open.write('## Feedback: {}\n\n'.format(feedback))
        if status != self.Status.PASS:
            if oracle_solution:
                self.feedback_open.write('## Expected Solution:\n\n')
                self.feedback_open.write(oracle_solution)
            if test_solution:
                self.feedback_open.write('## Your Solution:\n\n')
                self.feedback_open.write(test_solution)
        self.feedback_open.write('\n')

    def passed_with_bonus(self, points_bonus, message=''):
        """
        Passes this test earning bonus points in addition to the test total points. If a feedback file is enabled, adds
        feedback to it.
        :param points_bonus: The bonus points, must be a float >= 0.
        :param message: An optional message, will be shown as test output.
        :return The formatted passed test.
        """
        if points_bonus < 0:
            raise ValueError('The test bonus points must be >= 0')
        result = self.format(status=self.Status.PASS, output=message, points_earned=self.points_total+points_bonus)
        if self.feedback_open:
            self.add_feedback(status=self.Status.PASS)
        return result

    def passed(self, message=''):
        """
        Passes this test earning the test total points. If a feedback file is enabled, adds feedback to it.
        :param message: An optional message, will be shown as test output.
        :return The formatted passed test.
        """
        result = self.format(status=self.Status.PASS, output=message, points_earned=self.points_total)
        if self.feedback_open:
            self.add_feedback(status=self.Status.PASS)
        return result

    def partially_passed(self, points_earned, message, oracle_solution=None, test_solution=None):
        """
        Partially passes this test with some points earned. If a feedback file is enabled, adds feedback to it.
        :param points_earned: The points earned by the test, must be a float > 0 and < the test total points.
        :param message: The message explaining why the test was not fully passed, will be shown as test output.
        :param oracle_solution: The optional correct solution to be added to the feedback file.
        :param test_solution: The optional student solution to be added to the feedback file.
        :return The formatted partially passed test.
        """
        if points_earned <= 0:
            raise ValueError('The test points earned must be > 0')
        if points_earned >= self.points_total:
            raise ValueError('The test points earned must be < the test total points')
        result = self.format(status=self.Status.PARTIAL, output=message, points_earned=points_earned)
        if self.feedback_open:
            self.add_feedback(status=self.Status.PARTIAL, feedback=message, oracle_solution=oracle_solution,
                              test_solution=test_solution)
        return result

    def failed(self, message, oracle_solution=None, test_solution=None):
        """
        Fails this test with 0 points earned. If a feedback file is enabled, adds feedback to it.
        :param message: The failure message, will be shown as test output.
        :param oracle_solution: The optional correct solution to be added to the feedback file.
        :param test_solution: The optional student solution to be added to the feedback file.
        :return The formatted failed test.
        """
        result = self.format(status=self.Status.FAIL, output=message, points_earned=0)
        if self.feedback_open:
            self.add_feedback(status=self.Status.FAIL, feedback=message, oracle_solution=oracle_solution,
                              test_solution=test_solution)
        return result

    def done(self, points_earned, message='', oracle_solution=None, test_solution=None):
        """
        Passes, partially passes or fails this test depending on the points earned. If the points are <= 0 this test is
        failed with 0 points earned, if the points are >= test total points this test is passed earning the test total
        points (plus the possible bonus), otherwise this test is partially passed. If a feedback file is enabled, adds
        feedback to it.
        :param points_earned: The points earned by the test.
        :param message: The optional message explaining the test outcome, will be shown as test output.
        :param oracle_solution: The optional correct solution to be added to the feedback file.
        :param test_solution: The optional student solution to be added to the feedback file.
        :return The formatted test.
        """
        if points_earned <= 0:
            return self.failed(message, oracle_solution, test_solution)
        elif points_earned == self.points_total:
            return self.passed(message)
        elif points_earned > self.points_total:
            points_bonus = points_earned - self.points_total
            return self.passed_with_bonus(points_bonus, message)
        else:
            return self.partially_passed(points_earned, message, oracle_solution, test_solution)

    def error(self, message):
        """
        Err this test. If a feedback file is enabled, adds feedback to it.
        :param message: The error message, will be shown as test output.
        :return The formatted erred test.
        """
        result = self.format(status=self.Status.ERROR, output=message, points_earned=0)
        if self.feedback_open:
            self.add_feedback(status=self.Status.ERROR, feedback=message)
        return result

    def run(self):
        """
        Runs this test.
        :return The formatted test.
        """
        raise NotImplementedError


class MarkusTester:

    def __init__(self, specs, test_class=MarkusTest):
        self.specs = specs
        self.test_class = test_class

    @staticmethod
    def error_all(message, points_total=0):
        """
        Err all tests of this tester with a single message.
        :param message: The error message.
        :param points_total: The total points the tests could earn, must be a float >= 0.
        :return The formatted erred tests.
        """
        return MarkusTest.format_result(test_name='All tests', status=MarkusTest.Status.ERROR_ALL, output=message,
                                        points_earned=0, points_total=points_total)

    def before_tester_run(self):
        """
        Callback invoked before running this tester.
        Use this for tester initialization steps that can fail, rather than using __init__.
        """
        pass

    def before_test_run(self, test):
        """
        Callback invoked before running a test.
        Use this for test initialization steps that can fail, rather than using test_class.__init__().
        :param test: The test after initialization.
        """
        pass

    def after_successful_test_run(self, test):
        """
        Callback invoked after successfully running a test.
        Use this to access test data in the tester. Don't use this for test cleanup steps, use test_class.run() instead.
        :param test: The test after execution.
        """
        pass

    def after_tester_run(self):
        """
        Callback invoked after running this tester, including in case of exceptions.
        Use this for tester cleanup steps that should always be executed, regardless of errors.
        """
        pass

    def run(self):
        """
        Runs this tester.
        """
        try:
            self.before_tester_run()
            with contextlib.ExitStack() as stack:
                feedback_open = (stack.enter_context(open(self.specs.feedback_file, 'w'))
                                 if self.specs.feedback_file is not None
                                 else None)
                for test_file in sorted(self.specs.tests):
                    test_extra = self.specs.matrix[test_file].get(MarkusTestSpecs.MATRIX_NONTEST_KEY, {})
                    for data_files in sorted(self.specs.matrix[test_file].keys()):
                        if data_files == MarkusTestSpecs.MATRIX_NONTEST_KEY:
                            continue
                        points = self.specs.matrix[test_file][data_files]
                        if MarkusTestSpecs.DATA_FILES_SEPARATOR in data_files:
                            data_files = data_files.split(MarkusTestSpecs.DATA_FILES_SEPARATOR)
                        else:
                            data_files = [data_files]
                        test = self.test_class(self, test_file, data_files, points, test_extra, feedback_open)
                        try:
                            # if a test __init__ fails it should really stop the whole tester, we don't have enough
                            # info to continue safely, e.g. the total points (which skews the student mark)
                            self.before_test_run(test)
                            xml = test.run()
                            self.after_successful_test_run(test)
                        except Exception as e:
                            xml = test.error(message=str(e))
                        finally:
                            print(xml, flush=True)
        except Exception as e:
            print(MarkusTester.error_all(message=str(e)), flush=True)
        finally:
            self.after_tester_run()

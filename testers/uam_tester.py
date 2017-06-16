import enum
import json


class UAMResult:
    """
    A test result from uam.
    """

    class Status(enum.Enum):
        PASS = 1
        FAIL = 2
        ERROR = 3

    def __init__(self, file_name, class_name, test_name, status, description=None, message=None, trace=None):
        self.file_name = file_name
        self.class_name = class_name
        self.test_name = test_name
        self.status = status
        self.description = description
        self.message = message
        self.trace = trace

    @property
    def test_title(self):
        title = self.test_name if not self.class_name else '{}.{}'.format(self.class_name, self.test_name)
        if self.description:
            title += ' ({})'.format(self.description)
        return title


class UAMTester:
    """
    A base wrapper class to run a uam tester (https://github.com/ProjectAT/uam).
    """

    ERROR_MGSG = {
        'no_result': 'UAM framework error: no result file generated',
        'timeout': 'Tests timed out'
    }
    GLOBAL_TIMEOUT_DEFAULT = 30

    def __init__(self, path_to_uam, test_points, result_filename='result.json'):
        """
        Initializes the basic parameters to run a uam tester.
        :param path_to_uam: The path to the uam installation.
        :param test_points: A dict of test files to run and points assigned: the keys are test file names, the values
                            are dicts of test functions (or test classes) to points; if a test function/class is
                            missing, it is assigned a default of 1 point (use an empty dict for all 1s).
        :param result_filename: The file name of the json output.
        """
        self.path_to_uam = path_to_uam
        self.test_points = test_points
        self.result_filename = result_filename

    def collect_results(self):
        """
        Collects results from a uam tester.
        :return: A list of results (possibly empty).
        """
        results = []
        with open(self.result_filename) as result_file:
            result = json.load(result_file)
            for file_class, test_result in result['results'].items():
                file_class_names = file_class.split('.')
                if len(file_class_names) == 1:  # Class (java) or file (python)
                    file_name = file_class_names[0]
                    class_name = file_class_names[0] if file_name.istitle() else None
                else:  # file.Class (python)
                    file_name = file_class_names[0]
                    class_name = file_class_names[1]
                if 'passes' in test_result:
                    for test_id, test_desc in test_result['passes'].items():
                        test_name = test_id.rpartition(':')[2] if ':' in test_id else test_id.rpartition('.')[2]
                        results.append(
                            UAMResult(file_name, class_name, test_name, status=UAMResult.Status.PASS,
                                      description=test_desc))
                if 'failures' in test_result:
                    for test_id, test_stack in test_result['failures'].items():
                        test_name = test_id.rpartition(':')[2] if ':' in test_id else test_id.rpartition('.')[2]
                        results.append(
                            UAMResult(file_name, class_name, test_name, status=UAMResult.Status.FAIL,
                                      description=test_stack['description'], message=test_stack['message'],
                                      trace=test_stack['details']))
                if 'errors' in test_result:
                    for test_id, test_stack in test_result['errors'].items():
                        test_name = test_id.rpartition(':')[2] if ':' in test_id else test_id.rpartition('.')[2]
                        results.append(
                            UAMResult(file_name, class_name, test_name, status=UAMResult.Status.ERROR,
                                      description=test_stack['description'], message=test_stack['message']))
        return results

    def get_test_points(self, result, file_ext):
        """
        Gets the points awarded over the possible total for a uam test result based on the test specifications.
        :param result: A uam test result.
        :return: The tuple (points awarded, total possible points)
        """
        test_file = '{}.{}'.format(result.file_name, file_ext)
        test_points = self.test_points[test_file]
        total = test_points.get(result.test_name, test_points.get(result.class_name, 1))
        awarded = 0
        if result.status == UAMResult.Status.PASS:
            awarded = total
        return awarded, total

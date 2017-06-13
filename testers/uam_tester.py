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

    def __init__(self, class_name, name, status, description='', message='', trace=''):
        self.class_name = class_name
        self.name = name
        self.status = status
        self.description = description
        self.message = message
        self.trace = trace


class UAMTester:
    """
    A base wrapper class to run a uam tester (https://github.com/ProjectAT/uam).
    """

    def __init__(self, path_to_uam, specs, result_filename='result.json'):
        """
        Initializes the basic parameters to run a uam tester.
        :param path_to_uam: The path to the uam installation.
        :param specs: The test specifications, i.e. the test files to run and the points assigned: test file names are
        the keys, dicts of test functions (or test classes) and points are the values; if a test function/class is
        missing, it is assigned a default of 1 point (use an empty dict for all 1s).
        :param result_filename: The file name of the json output.
        """
        self.path_to_uam = path_to_uam
        self.specs = specs
        self.result_filename = result_filename

    def collect_results(self):
        """
        Collects results from a uam tester.
        :return: A list of results (possibly empty).
        """
        results = []
        with open(self.result_filename) as result_file:
            result = json.load(result_file)
            for test_class_name, test_class_result in result['results'].items():
                if 'passes' in test_class_result:
                    for test_name, test_desc in test_class_result['passes'].items():
                        results.append(
                            UAMResult(class_name=test_class_name.partition('.')[2], name=test_name,
                                      status=UAMResult.Status.PASS, description=test_desc))
                if 'failures' in test_class_result:
                    for test_name, test_stack in test_class_result['failures'].items():
                        results.append(
                            UAMResult(class_name=test_class_name.partition('.')[2], name=test_name,
                                      status=UAMResult.Status.FAIL, description=test_stack['description'],
                                      message=test_stack['message'], trace=test_stack['details']))
                if 'errors' in test_class_result:
                    for test_name, test_stack in test_class_result['errors'].items():
                        results.append(
                            UAMResult(class_name=test_class_name.partition('.')[2], name=test_name,
                                      status=UAMResult.Status.ERROR, description=test_stack['description'],
                                      message=test_stack['message']))
        return results

import os
import subprocess

from uam_tester import UAMTester


class JAMTester(UAMTester):
    """
    A base wrapper class to run the Java AutoMarker (jam - https://github.com/ProjectAT/uam/tree/master/jam).
    """

    def __init__(self, path_to_uam, path_to_tests, test_points, global_timeout=UAMTester.GLOBAL_TIMEOUT_DEFAULT,
                 test_timeout=UAMTester.TEST_TIMEOUT_DEFAULT, result_filename='result.json'):
        super().__init__(path_to_uam, path_to_tests, test_points, global_timeout, test_timeout, result_filename)
        self.path_to_jam = os.path.join(self.path_to_uam, 'jam')
        self.path_to_jam_jars = os.path.join(self.path_to_jam, 'lib', '*')

    def generate_results(self):
        java_cmd = ['java', '-cp', '.:{}:{}'.format(self.path_to_jam_jars, self.path_to_tests),
                    'org.junit.runner.JAMCore']
        java_cmd.extend(sorted([os.path.splitext(test_file)[0] for test_file in self.test_points.keys()]))
        java_cmd.append(os.path.join(self.path_to_jam, 'exceptionExplanations.xml'))
        subprocess.run(java_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, check=False,
                       timeout=self.global_timeout)  # apparently, jam returns error if at least a test fails

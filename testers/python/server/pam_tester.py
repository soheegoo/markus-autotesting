import os
import subprocess
import sys

from uam_tester import UAMTester


class PAMTester(UAMTester):
    """
    A base wrapper class to run the Python AutoMarker (pam - https://github.com/ProjectAT/uam).
    """

    TEST_TIMEOUT_DEFAULT = 10

    def __init__(self, path_to_uam, test_points, test_timeout=TEST_TIMEOUT_DEFAULT, global_timeout=UAMTester.GLOBAL_TIMEOUT_DEFAULT,
                 result_filename='result.json'):
        """
        Initializes the various parameters to run pam.
        :param path_to_uam: The path to the uam installation.
        :param test_points: A dict of test files to run and points assigned: the keys are test file names, the values
                            are dicts of test functions (or test classes) to points; if a test function/class is
                            missing, it is assigned a default of 1 point (use an empty dict for all 1s).
        :param test_timeout: The max time to run a single test on the student submission.
        :param global_timeout: The max time to run all tests on the student submission.
        :param result_filename: The file name of pam's json output.
        """
        super().__init__(path_to_uam, test_points, global_timeout, result_filename)
        self.path_to_pam = os.path.join(path_to_uam, 'pam', 'pam.py')
        self.test_timeout = test_timeout

    def generate_results(self):
        """
        Runs pam.
        """
        shell_command = [sys.executable, self.path_to_pam, '-t', str(self.test_timeout), self.result_filename]
        shell_command.extend(sorted(self.test_points.keys()))
        env = os.environ.copy()  # need to add path to uam libs
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = "{}:{}".format(env['PYTHONPATH'], self.path_to_uam)
        else:
            env['PYTHONPATH'] = self.path_to_uam
        subprocess.run(shell_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, shell=False,
                       env=env, timeout=self.global_timeout)

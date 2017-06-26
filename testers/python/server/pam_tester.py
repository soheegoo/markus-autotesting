import os
import shutil
import subprocess
import sys

from uam_tester import UAMTester


class PAMTester(UAMTester):
    """
    A base wrapper class to run the Python AutoMarker (pam - https://github.com/ProjectAT/uam/tree/master/pam).
    """

    def __init__(self, path_to_uam, path_to_tests, test_points, global_timeout=UAMTester.GLOBAL_TIMEOUT_DEFAULT,
                 test_timeout=UAMTester.TEST_TIMEOUT_DEFAULT, result_filename='result.json'):
        super().__init__(path_to_uam, path_to_tests, test_points, global_timeout, test_timeout, result_filename)
        self.path_to_pam = os.path.join(path_to_uam, 'pam', 'pam.py')

    def generate_results(self):
        shell_command = [sys.executable, self.path_to_pam, '-t', str(self.test_timeout), self.result_filename]
        shell_command.extend(sorted(self.test_points.keys()))
        env = os.environ.copy()  # need to add path to uam libs
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = "{}:{}".format(env['PYTHONPATH'], self.path_to_uam)
        else:
            env['PYTHONPATH'] = self.path_to_uam
        if self.path_to_tests != '.':
            for test_file in self.test_points.keys():
                shutil.copy(os.path.join(self.path_to_tests, test_file), '.')
        subprocess.run(shell_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, shell=False,
                       env=env, timeout=self.global_timeout)

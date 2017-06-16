import os
import subprocess
import sys

from uam_tester import UAMTester


class PAMTester(UAMTester):
    """
    A base wrapper class to run the Python AutoMarker (pam - https://github.com/ProjectAT/uam).
    """

    def __init__(self, path_to_uam, test_points, test_timeout=10, global_timeout=30, result_filename='result.json'):
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
        super().__init__(path_to_uam, test_points, result_filename)
        self.path_to_pam = os.path.join(path_to_uam, 'pam', 'pam.py')
        self.test_timeout = test_timeout
        self.global_timeout = global_timeout

    def run(self):
        """
        Runs pam.
        """
        shell_command = [sys.executable, self.path_to_pam, '-t', str(self.test_timeout), self.result_filename]
        shell_command.extend(sorted(self.test_points.keys()))
        try:
            env = os.environ.copy()  # need to add path to uam libs
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = "{systempath}:{uampath}".format(systempath=env['PYTHONPATH'],
                                                                    uampath=self.path_to_uam)
            else:
                env['PYTHONPATH'] = self.path_to_uam
            subprocess.run(shell_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, shell=False,
                           env=env, timeout=self.global_timeout)
            return self.collect_results()
        except subprocess.TimeoutExpired:
            raise Exception('Timeout')
        except subprocess.CalledProcessError as e:
            raise Exception('PAM framework error\nstdout: {stdout}\nstderr: {stderr}'.format(stdout=e.stdout,
                                                                                             stderr=e.stderr))
        except OSError:
            raise Exception('PAM framework error: no result file generated')

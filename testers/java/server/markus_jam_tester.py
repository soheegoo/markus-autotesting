import contextlib
import glob
import os
import subprocess

from markus_uam_tester import MarkusUAMTest, MarkusUAMTester
from markus_utils import MarkusUtils
from uam_tester import UAMTester


class MarkusJAMTester(MarkusUAMTester):

    ERROR_MGSG = {
        'no_submission': 'Java submission files not found',
        'bad_javac': "Java compilation error: '{}'",
        'bad_java': "Java runtime error: '{}'",
    }
    ERROR_MGSG.update(UAMTester.ERROR_MGSG)

    def __init__(self, specs, feedback_file='feedback_java.txt'):
        super().__init__(specs, feedback_file)
        self.path_to_tests = specs['path_to_tests']
        self.path_to_jam = os.path.join(self.path_to_uam, 'jam')
        self.path_to_jam_jars = os.path.join(self.path_to_jam, 'lib', '*')

    def init_java(self, java_files):
        javac_cmd = ['javac']
        javac_cmd.extend(java_files)
        subprocess.run(javac_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, check=True)

    def check_java(self):
        java_cmd = ['java', '-cp', '.:{}:{}'.format(self.path_to_jam_jars, self.path_to_tests),
                    'org.junit.runner.JAMCore']
        java_cmd.extend(sorted([os.path.splitext(test_file)[0] for test_file in self.specs.test_files]))
        java_cmd.append(os.path.join(self.path_to_jam, 'exceptionExplanations.xml'))
        subprocess.run(java_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, check=False,
                       timeout=self.global_timeout)  # apparently, jam returns error if at least a test fails

    def run(self):
        try:
            java_files = glob.glob('*.java')
            if not java_files:
                MarkusUtils.print_test_error(name='All JAVA tests', message=self.ERROR_MGSG['no_submission'])
                return
            try:
                self.init_java(java_files)
            except subprocess.CalledProcessError as e:
                msg = self.ERROR_MGSG['bad_javac'].format(e.stdout)
                MarkusUtils.print_test_error(name='All JAVA tests', message=msg)
                return
            with contextlib.ExitStack() as stack:
                feedback_open = (stack.enter_context(open(self.feedback_file, 'w'))
                                 if self.feedback_file is not None
                                 else None)
                try:
                    self.check_java()
                    results = self.uam_tester.collect_results()
                except subprocess.TimeoutExpired:
                    raise Exception(self.ERROR_MGSG['timeout'])
                except subprocess.CalledProcessError as e:
                    raise Exception(self.ERROR_MGSG['bad_java'].format(e.stdout))
                except OSError:
                    raise Exception(self.ERROR_MGSG['no_result'])
                for result in results:
                    points_awarded, points_total = self.uam_tester.get_test_points(result, file_ext='java')
                    test = MarkusUAMTest(result, points_awarded, points_total, feedback_open)
                    xml = test.run()
                    print(xml)
        except Exception as e:
            MarkusUtils.print_test_error(name='All JAVA tests', message=str(e))

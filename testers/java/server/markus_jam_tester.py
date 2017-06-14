import contextlib
import os
import subprocess

from markus_tester import MarkusTester, MarkusTest
from markus_utils import MarkusUtils
from uam_tester import UAMTester, UAMResult


class MarkusJAMTester(MarkusTester):

    ERROR_MGSG = {
        'bad_javac': "Java compilation error: '{}'",
        'bad_java': "Java runtime error: '{}'",
    }
    ERROR_MGSG.update(UAMTester.ERROR_MGSG)

    def __init__(self, specs, feedback_file='feedback_java.txt'):
        super().__init__(specs=specs, feedback_file=feedback_file)
        self.path_to_uam = specs['path_to_uam']
        self.global_timeout = specs['global_timeout']
        self.path_to_jam = os.path.join(self.path_to_uam, 'jam')
        self.path_to_jam_jars = os.path.join(self.path_to_jam, 'lib', '*')
        self.uam_tester = UAMTester(path_to_uam=self.path_to_uam, specs=specs, result_filename='result.json')

    def init_java(self):
        javac_cmd = ['javac', '*.java']
        subprocess.run(javac_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, check=True)

    def check_java(self):
        java_cmd = ['java', '-cp', self.path_to_jam, '*.java', 'org.junit.runner.JAMCore']
        java_cmd.extend(sorted(self.specs.keys()))  # TODO matrix + change UAMTester.get_test_points() + fix MarkusPAMtester accordingly ? OR NONE OF THIS
        java_cmd.append(os.path.join(self.path_to_jam, 'exceptionExplanations.xml'))
        subprocess.run(java_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, check=True,
                       timeout=self.global_timeout)

    def run(self):
        # TODO Precompiled tests vs added as support files?
        # TODO Think about settings: classpath, points, data files
        # TODO Are student submissions compiled by jam?
        # TODO Support for packages?
        try:
            try:
                self.init_java()
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
                    for result in results:
                        points_awarded, points_total = self.uam_tester.get_test_points(result)
                        test = MarkusJAMTest(result, points_awarded, points_total, feedback_open)
                        xml = test.run()
                        print(xml)
                except subprocess.TimeoutExpired:
                    raise Exception(self.ERROR_MGSG['timeout'])
                except subprocess.CalledProcessError as e:
                    raise Exception(self.ERROR_MGSG['bad_java'].format(e.stdout))
                except OSError:
                    raise Exception(self.ERROR_MGSG['no_result'])
        except Exception as e:
            MarkusUtils.print_test_error(name='All JAM tests', message=str(e))


class MarkusJAMTest(MarkusTest):

    def __init__(self, uam_result, points_awarded, points_total, feedback_open):
        test_name = (uam_result.name
                     if not uam_result.description
                     else '{} ({})'.format(uam_result.name, uam_result.description))
        super().__init__(test_name, [], {'points': points_total}, None, feedback_open)
        self.test_data_name = test_name
        self.uam_result = uam_result
        self.points_awarded = points_awarded

    def run(self):
        if self.uam_result.status == UAMResult.Status.PASS:
            return self.passed()
        elif self.uam_result.status == UAMResult.Status.FAIL:
            # TODO add test_solution=self.pam_result.trace? (But test trace could be confusing)
            return self.failed(points_awarded=self.points_awarded, message=self.uam_result.message)
        else:
            return self.error(message=self.uam_result.message)

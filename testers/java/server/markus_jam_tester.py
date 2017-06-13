import contextlib
import subprocess

from markus_tester import MarkusTester, MarkusTest
from markus_utils import MarkusUtils
from uam_tester import UAMTester


class MarkusJAMTester(MarkusTester):

    def __init__(self, specs, feedback_file='feedback_java.txt'):
        super().__init__(specs=specs, feedback_file=feedback_file)
        self.path_to_uam = specs['path_to_uam']
        self.uam_tester = UAMTester(path_to_uam=self.path_to_uam, specs=specs, result_filename='result.json')

    def create_test(self, test_file, data_files, test_data_config, test_extra, feedback_open):
        return MarkusJAMTest(test_file, data_files, test_data_config, test_extra, feedback_open)

    def init_java(self):
        javac_cmd = ['javac', '-cp', 'TODO', '*.java']
        subprocess.run(javac_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, check=True)

    def run(self):
        # TODO Precompiled tests vs added as support files?
        # TODO Think about settings: classpath, points, data files
        # TODO Compile student submission, execute junit tests/suite, reuse existing json output parser
        try:
            with contextlib.ExitStack() as stack:
                feedback_open = (stack.enter_context(open(self.feedback_file, 'w'))
                                 if self.feedback_file is not None
                                 else None)
                results = self.uam_tester.collect_results()
                for result in results:
                    points_awarded, points_total = self.pam_tester.get_test_points(result)
                    test = MarkusJAMTest(result, points_awarded, points_total, feedback_open)
                    xml = test.run()
                    print(xml)
        except Exception as e:
            MarkusUtils.print_test_error(name='All PAM tests', message=str(e))


class MarkusJAMTest(MarkusTest):

    ERROR_MGSG = {
        'bad_javac': "Java compilation error: '{}'",
        'bad_java': "Java runtime error: 'stdout: {}'; 'stderr: {}'"
    }

    def __init__(self, test_file, data_files, test_data_config, test_extra, feedback_open):
        super().__init__(test_file, data_files, test_data_config, test_extra, feedback_open)

    def run(self):
        pass

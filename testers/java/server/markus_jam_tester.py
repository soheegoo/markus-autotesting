from subprocess import run, PIPE, STDOUT

from markus_tester import MarkusTester, MarkusTest


class MarkusJAMTester(MarkusTester):

    def __init__(self, specs, feedback_file='feedback_java.txt'):
        super().__init__(specs=specs, feedback_file=feedback_file)

    def create_test(self, test_file, data_files, test_data_config, test_extra, feedback_open):
        return MarkusJAMTest(test_file, data_files, test_data_config, test_extra, feedback_open)

    def init_java(self):
        javac_cmd = ['javac', '-cp', 'TODO', '*.java']
        run(javac_cmd, stdout=PIPE, stderr=STDOUT, universal_newlines=True, check=True)


class MarkusJAMTest(MarkusTest):

    ERROR_MGSG = {
        'bad_javac': "Java compilation error: '{}'",
        'bad_java': "Java runtime error: 'stdout: {}'; 'stderr: {}'"
    }

    def __init__(self, test_file, data_files, test_data_config, test_extra, feedback_open):
        super().__init__(test_file, data_files, test_data_config, test_extra, feedback_open)

    def run(self):
        pass

import glob
import subprocess

from jam_tester import JAMTester
from markus_uam_tester import MarkusUAMTester
from markus_utils import MarkusUtils


class MarkusJAMTester(MarkusUAMTester):

    ERROR_MGSG = {
        'no_submission': 'Java submission files not found',
        'bad_javac': "Java compilation error: '{}'"
    }

    def __init__(self, specs, feedback_file='feedback_java.txt'):
        super().__init__(specs, feedback_file, tester_class=JAMTester, test_ext='java')

    def run(self):
        try:
            java_files = glob.glob('*.java')
            if not java_files:
                MarkusUtils.print_test_error(name='All tests', message=self.ERROR_MGSG['no_submission'])
                return
            try:
                javac_cmd = ['javac']
                javac_cmd.extend(java_files)
                subprocess.run(javac_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                               check=True)
            except subprocess.CalledProcessError as e:
                msg = self.ERROR_MGSG['bad_javac'].format(e.stdout)
                MarkusUtils.print_test_error(name='All tests', message=msg)
                return
        except Exception as e:
            MarkusUtils.print_test_error(name='All tests', message=str(e))
        super().run()

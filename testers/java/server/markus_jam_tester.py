import glob
import subprocess

from jam_tester import JAMTester
from markus_tester import MarkusTester
from markus_uam_tester import MarkusUAMTester, MarkusUAMTest


class MarkusJAMTester(MarkusUAMTester):

    ERROR_MGSG = {
        'no_submission': 'Java submission files not found',
        'bad_javac': "Java compilation error: '{}'"
    }

    def __init__(self, specs, test_class=MarkusUAMTest):
        super().__init__(specs, test_class, tester_class=JAMTester, test_ext='java')

    def run(self):
        try:
            java_files = glob.glob('*.java')
            if not java_files:
                print(MarkusTester.error_all(message=self.ERROR_MGSG['no_submission']), flush=True)
                return
            try:
                javac_cmd = ['javac']
                javac_cmd.extend(java_files)
                subprocess.run(javac_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                               check=True)
            except subprocess.CalledProcessError as e:
                msg = self.ERROR_MGSG['bad_javac'].format(e.stdout)
                print(MarkusTester.error_all(message=msg), flush=True)
                return
        except Exception as e:
            print(MarkusTester.error_all(message=str(e)), flush=True)
        super().run()

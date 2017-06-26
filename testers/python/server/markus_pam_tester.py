from markus_uam_tester import MarkusUAMTester
from pam_tester import PAMTester


class MarkusPAMTester(MarkusUAMTester):

    def __init__(self, specs, feedback_file='feedback_python.txt'):
        super().__init__(specs, feedback_file, tester_class=PAMTester, test_ext='py')

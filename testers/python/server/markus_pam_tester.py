from markus_uam_tester import MarkusUAMTester
from pam_tester import PAMTester


class MarkusPAMTester(MarkusUAMTester):

    def __init__(self, specs):
        super().__init__(specs, tester_class=PAMTester, test_ext='py')

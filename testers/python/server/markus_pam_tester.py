from markus_uam_tester import MarkusUAMTester, MarkusUAMTest
from pam_tester import PAMTester


class MarkusPAMTester(MarkusUAMTester):

    def __init__(self, specs, test_class=MarkusUAMTest):
        super().__init__(specs, test_class, tester_class=PAMTester, test_ext='py')

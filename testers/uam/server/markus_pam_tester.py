from pam_tester import PAMTester, PAMResult
from markus_utils import MarkusUtils


class MarkusPAMTester(PAMTester):
    """
    A wrapper to run the Python AutoMarker (pam - https://github.com/ProjectAT/uam) within Markus' test framework.
    """

    def print_results(self, results):
        """
        Prints pam results in Markus' test framework format.
        :param results: A list of results (possibly empty).
        """
        for result in results:
            awarded, total = self.get_test_points(result)
            status = 'pass' if result.status == PAMResult.Status.PASS else 'fail'
            name = result.name if not result.description else '{name} ({desc})'.format(name=result.name,
                                                                                       desc=result.description)
            MarkusUtils.print_test_result(name=name, status=status, output=result.message, points_awarded=awarded,
                                          points_total=total)

    def print_error(self, message):
        """
        Prints an error in Markus' test framework format.
        :param message: The error message.
        """
        MarkusUtils.print_test_error(name='All PAM tests', message=message)

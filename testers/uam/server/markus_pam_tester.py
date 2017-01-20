from pam_wrapper import PAMWrapper, PAMResult
from markus_utils import MarkusUtilsMixin


class MarkusPAMTester(MarkusUtilsMixin, PAMWrapper):
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
            info = '[{awarded} / {total}] {name}'.format(awarded=awarded, total=total, name=name)
            self.print_result(name=info, input='', expected='', actual=result.message, marks=awarded, status=status)

    def print_error(self, message):
        """
        Prints an error in Markus' test framework format.
        :param message: The error message.
        """
        self.print_result(name='All PAM tests', input='', expected='', actual=message, marks=0, status='error')

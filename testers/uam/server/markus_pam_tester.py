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
            test_names = result.name.split('.')
            test_file = '{}.py'.format(test_names[0])
            class_name = test_names[1] if len(test_names) == 3 else None
            test_name = '{}.{}'.format(class_name, test_names[2]) if class_name else test_names[1]
            test_points = self.specs[test_file]
            marks = 0
            if result.status == PAMResult.Status.PASS:
                marks = test_points.get(test_name, test_points.get(class_name, 1))
            status = 'pass' if result.status == PAMResult.Status.PASS else 'fail'
            name = result.name if not result.description else '{name} ({desc})'.format(name=result.name,
                                                                                       desc=result.description)
            self.print_result(name=name, input='', expected='', actual=result.message, marks=marks, status=status)

    def print_error(self, message):
        """
        Prints an error in Markus' test framework format.
        :param message: The error message.
        """
        self.print_result(name='All PAM tests', input='', expected='', actual=message, marks=0, status='error')

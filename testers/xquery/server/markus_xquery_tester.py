from markus_utils import MarkusUtils


class MarkusXQueryTester:

    def __init__(self, path_to_solution, output_filename='feedback_xquery.txt'):
        self.path_to_solution = path_to_solution
        self.output_filename = output_filename

    def run(self):

        try:
            with open(self.output_filename, 'w') as output_open:
                pass
        except Exception as e:
            MarkusUtils.print_test_error(name='All XQUERY tests', message=str(e))

import os

from markus_utils import MarkusUtils


class MarkusXQueryTester:

    ERROR_MSGS = {
        'no_submission': "Submission file '{}' not found"
    }

    def __init__(self, path_to_solution, specs, output_filename='feedback_xquery.txt'):
        self.path_to_solution = path_to_solution
        self.specs = specs
        self.output_filename = output_filename

    def run(self):

        try:
            with open(self.output_filename, 'w') as output_open:
                for xq_file in sorted(self.specs.keys()):
                    test_name = os.path.splitext(xq_file)[0]
                    for data_file, points_total in sorted(self.specs[xq_file].items()):
                        data_name = os.path.splitext(data_file)[0]
                        test_data_name = '{} + {}'.format(test_name, data_name)
                        # check that the submission exists
                        if not os.path.isfile(xq_file):
                            msg = self.ERROR_MSGS['no_submission'].format(xq_file)
                            MarkusUtils.print_test_error(name=test_data_name, message=msg, points_total=points_total)
                            continue
                        # TODO galax-run -doc dataset={data_file} {xq_file}
                        # TODO check if student xml is well-formed
                        # TODO check if student xml is conformant to output schema
                        # TODO compare student and solution xml using dicts and the xmltodict package
                        # TODO what output to instructor/student?
        except Exception as e:
            MarkusUtils.print_test_error(name='All XQUERY tests', message=str(e))

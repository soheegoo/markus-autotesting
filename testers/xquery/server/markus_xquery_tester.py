import glob
import os
import subprocess

import xmltodict

from markus_utils import MarkusUtils


class MarkusXQueryTester:

    SCHEMA_DIR = 'schemas'
    DATASET_DIR = 'datasets'
    ERROR_MSGS = {
        'no_submission': "Submission file '{}' not found",
        'bad_query': "Galax error: 'stdout: {}', 'stderr: {}'",
        'not_well_formed': "",
        'not_valid': "",
        'not_correct': ""
    }

    def __init__(self, path_to_solution, specs, schemas, output_filename='feedback_xquery.txt'):
        self.path_to_solution = path_to_solution
        self.specs = specs
        self.schemas = schemas
        self.output_filename = output_filename

    def check_query(self, data_file, xq_file):
        dataset_file = os.path.join(self.path_to_solution, self.DATASET_DIR, data_file)
        galax_cmd = ['galax-run', '-doc', 'dataset={}'.format(dataset_file), xq_file]
        galax = subprocess.run(galax_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                               check=True)

        return galax.stdout

    def check_well_formed(self, test_xml):
        test_xml = '<?xml version="1.0" encoding="UTF-8"?>' + test_xml
        xmllint_cmd = ['xmllint', '--format', '-']
        xmllint = subprocess.run(xmllint_cmd, input=test_xml, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True, check=True)

        return xmllint.stdout

    def check_dtd(self, xq_file, test_xml):
        schema_file = os.path.join(self.path_to_solution, self.SCHEMA_DIR, self.schemas[xq_file][0])
        root_tag = self.schemas[xq_file][1]
        i = test_xml.find('\n')
        test_xml = test_xml[:i] + '\n<!DOCTYPE {} SYSTEM "{}">'.format(root_tag, schema_file) + test_xml[i:]
        xmllint_cmd = ['xmllint', '--noout', '--valid', '-']
        subprocess.run(xmllint_cmd, input=test_xml, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       universal_newlines=True, check=True)

        return test_xml

    def check_xml(self, test_data_name, test_xml):
        oracle_file = os.path.join(self.path_to_solution, '{}.xml'.format(test_data_name.replace(' ', '')))
        with open(oracle_file, 'r') as solution_open:
            oracle_xml = solution_open.read()
            oracle_dict = xmltodict.parse(oracle_xml, process_namespaces=True)
        test_dict = xmltodict.parse(test_xml, process_namespaces=True)
        if oracle_dict != test_dict:
            return self.ERROR_MSGS['not_correct'], 'fail'

        return '', 'pass'

    def print_file(self, output_open, test_xml):
        output_open.write(test_xml)

    def print_file_error(self):
        pass

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
                        try:
                            test_xml = self.check_query(data_file=data_file, xq_file=xq_file)
                            test_xml = self.check_well_formed(test_xml=test_xml)
                            test_xml = self.check_dtd(xq_file=xq_file, test_xml=test_xml)
                            output, status = self.check_xml(test_data_name=test_data_name, test_xml=test_xml)
                            points_awarded = points_total if status == 'pass' else 0
                            MarkusUtils.print_test_result(name=test_data_name, status=status, output=output,
                                                          points_awarded=points_awarded, points_total=points_total)
                            self.print_file(output_open=output_open, test_xml=test_xml)
                        except subprocess.CalledProcessError as e:
                            msg = self.ERROR_MSGS['bad_query'].format(e.stdout, e.stderr)
                            MarkusUtils.print_test_error(name=test_data_name, message=msg, points_total=points_total)
                        # TODO print test_output at the last successful step (raw, linted, or dtd-ed)
                        # TODO order dicts before comparing parsed xmls
                        # TODO what output to instructor/student on file?
                        # TODO 1 test vs 4 tests?
                        # TODO security of xml solutions, especially since we give away the solution location by dtd?
        except Exception as e:
            MarkusUtils.print_test_error(name='All XQUERY tests', message=str(e))

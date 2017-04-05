import subprocess

from os.path import isfile, join

from xmltodict import parse

from markus_tester import MarkusTester, MarkusTest


class MarkusXQueryTester(MarkusTester):

    SCHEMA_DIR = 'schemas'
    DATASET_DIR = 'datasets'

    def __init__(self, specs, feedback_file='feedback_xquery.txt'):
        super().__init__(specs=specs, feedback_file=feedback_file)
        self.path_to_solution = specs['path_to_solution']

    def create_test(self, test_file, data_files, test_data_config, test_extra, feedback_open):
        return MarkusXQueryTest(test_file, data_files, test_data_config, test_extra, feedback_open,
                                self.path_to_solution)


class MarkusXQueryTest(MarkusTest):

    ERROR_MSGS = {
        'no_submission': "Submission file '{}' not found",
        'bad_query': "The query has a syntax error; galax-run stdout: '{}', stderr: '{}'",
        'bad_xml': "The xml is not well-formed; xmllint stdout: '{}', stderr: '{}'",
        'bad_dtd': "The xml does not conform to the dtd; xmllint stdout: '{}', stderr: '{}'",
        'bad_content': "The xml does not match the solution"
    }

    def __init__(self, test_file, data_files, test_data_config, test_extra, feedback_open, path_to_solution):
        super().__init__(test_file, data_files, test_data_config, test_extra, feedback_open)
        self.path_to_solution = path_to_solution

    def check_query(self):
        dataset_arg = []
        for i, data_file in enumerate(self.data_files):
            dataset_arg.append('-doc')
            dataset_arg.append('dataset{}={}'.format(str(i), join(self.path_to_solution, MarkusXQueryTester.DATASET_DIR,
                                                                  data_file)))
        galax_cmd = ['galax-run', self.test_file]
        galax_cmd[1:1] = dataset_arg
        galax = subprocess.run(galax_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                               check=True)

        return galax.stdout

    def check_well_formed(self, test_xml):
        test_xml = '<?xml version="1.0" encoding="UTF-8"?>' + test_xml
        xmllint_cmd = ['xmllint', '--format', '-']
        xmllint = subprocess.run(xmllint_cmd, input=test_xml, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True, check=True)

        return xmllint.stdout

    def check_dtd(self, test_xml):
        schema_file = join(self.path_to_solution, MarkusXQueryTester.SCHEMA_DIR, self.test_extra['out_schema'])
        root_tag = self.test_extra['out_root_tag']
        i = test_xml.find('\n')
        test_xml = test_xml[:i] + '\n<!DOCTYPE {} SYSTEM "{}">'.format(root_tag, schema_file) + test_xml[i:]
        xmllint_cmd = ['xmllint', '--noout', '--valid', '-']
        subprocess.run(xmllint_cmd, input=test_xml, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       universal_newlines=True, check=True)

        return test_xml

    def check_xml(self, test_xml):
        oracle_file = join(self.path_to_solution, '{}.xml'.format(self.test_data_name.replace(' ', '')))
        with open(oracle_file, 'r') as oracle_open:
            oracle_xml = oracle_open.read()
            oracle_dict = parse(oracle_xml, process_namespaces=True)
        test_dict = parse(test_xml, process_namespaces=True)
        if oracle_dict != test_dict:
            return 'fail'

        return 'pass'

    def print_file(self, feedback_open, test_xml):
        feedback_open.write(test_xml)

    def print_file_error(self):
        pass

    def run(self):
        # check that the submission exists
        if not isfile(self.test_file):
            msg = MarkusXQueryTest.ERROR_MSGS['no_submission'].format(self.test_file)
            return self.error(message=msg)
        #
        try:
            test_xml = self.check_query()
        except subprocess.CalledProcessError as e:
            msg = self.ERROR_MSGS['bad_query'].format(e.stdout, e.stderr)
            return self.error(message=msg)
        #
        try:
            test_xml = self.check_well_formed(test_xml=test_xml)
        except subprocess.CalledProcessError as e:
            msg = self.ERROR_MSGS['bad_xml'].format(e.stdout, e.stderr)
            return self.failed(points_awarded=self.points['bad_xml'], message=msg)
        #
        try:
            test_xml = self.check_dtd(test_xml=test_xml)
        except subprocess.CalledProcessError as e:
            msg = self.ERROR_MSGS['bad_dtd'].format(e.stdout, e.stderr)
            return self.failed(points_awarded=self.points['bad_dtd'], message=msg)
        #
        output, status = self.check_xml(test_xml=test_xml)
        self.print_file(feedback_open=self.feedback_open, test_xml=test_xml)
        return (self.passed()
                if status == 'pass'
                else self.failed(points_awarded=self.points['bad_content'], message=self.ERROR_MSGS['bad_content']))
        # TODO print test_output at the last successful step (raw, linted, or dtd-ed)
        # TODO order dicts before comparing parsed xmls
        # TODO what output to instructor/student on file?
        # TODO security of xml solutions, especially since we give away the solution location by dtd?

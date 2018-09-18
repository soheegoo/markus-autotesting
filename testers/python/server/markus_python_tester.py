import contextlib
import subprocess
import os
import tempfile
import csv
import unittest
import pytest
import io
import xml.etree.ElementTree as eTree

from markus_tester import MarkusTester, MarkusTest, MarkusTestSpecs

class MarkusTextTestResults(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.results = []
        self.successes = []

    def addSuccess(self, test):
        self.results.append({'status': 'success', 
                             'name'  : test.id(), 
                             'errors': ''})
        self.successes.append(test)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.results.append({'status': 'failure', 
                             'name'  : test.id(), 
                             'errors': self.failures[-1][-1]})

    def addError(self, test, err):
        super().addError(test, err)
        self.results.append({'status': 'error', 
                             'name'  : test.id(), 
                             'errors': self.failures[-1][-1]})

class MarkusPythonTest(MarkusTest):

    def __init__(self, tester, feedback_open, test_file, result):
        self._test_name = result['name']
        all_points = tester.specs.matrix[test_file][MarkusTestSpecs.MATRIX_NODATA_KEY]
        points = all_points.get(self._test_name, 1)
        self.status = result['status']
        self.message = result['errors']
        super().__init__(tester, test_file, [MarkusTestSpecs.MATRIX_NODATA_KEY], points, {}, feedback_open)

    @property
    def test_name(self):
        return self._test_name

    def run(self):
        if self.status == "success":
            return self.passed(message=self.message)
        elif self.status == "failure":
            return self.failed(message=self.message)
        else:
            return self.error(message=self.message)

class MarkusPythonTester(MarkusTester):

    def __init__(self, specs, test_class=MarkusPythonTest):
        super().__init__(specs, test_class)


    def _load_unittest_tests(self, test_file):
        """
        """
        # get TestSuites from test files
        test_loader = unittest.defaultTestLoader
        test_file_dir = os.path.dirname(test_file)
        discovered_tests = test_loader.discover(test_file_dir, test_file)
        return unittest.TestSuite(discovered_tests)

    def _parse_junitxml(self, xml_filename):
        tree = eTree.parse(xml_filename)
        root = tree.getroot()
        for testcase in root.iterfind('testcase'):
            result = {}
            classname = testcase.attrib['classname']    
            testname = testcase.attrib['name']
            result['name'] = '{}.{}'.format(classname, testname)
            failure = testcase.find('failure')
            if failure is not None:
                result['status'] = 'failure'
                result['errors'] = failure.text
            else:
                result['status'] = 'success'
                result['errors'] = ''
            yield result

    def _run_unittest_tests(self, test_file):
        test_suite = self._load_unittest_tests(test_file)
        with open(os.devnull, 'w') as nullstream:    
            test_runner = unittest.TextTestRunner(
                verbosity=2, # TODO: don't hardcode this
                stream=nullstream,
                resultclass=MarkusTextTestResults)
            test_result = test_runner.run(test_suite)
        return test_result.results

    def _run_pytest_tests(self, test_file):
        results = []
        this_dir = os.path.dirname(os.path.abspath(__file__))
        with tempfile.NamedTemporaryFile(mode="w+", dir=this_dir) as sf:
            pytest.main([test_file, '--junitxml', sf.name])
            results = list(self._parse_junitxml(sf))
        return results

    def _detect_test_tool_function(self, test_file):
        """
        """
        with open(test_file) as f:
            for line in f:
                if 'import' in line:
                    if 'unittest' in line:
                        return self._run_unittest_tests
                    if 'pytest' in line:
                        return self._run_pytest_tests
        return self._run_unittest_tests


    def run_python_tests(self):
        """
        """
        results = {}
        for test_file in self.specs.tests:
            func = self._detect_test_tool_function(test_file)
            result = func(test_file)
            results[test_file] = result
        return results

    def run(self):
        try:
            try:
                results = self.run_python_tests()
            except subprocess.CalledProcessError as e:
                msg = (e.stdout or '' + e.stderr or '') or str(e)
                print(MarkusTester.error_all(message=msg), flush=True)
                return
            with contextlib.ExitStack() as stack:
                feedback_open = (stack.enter_context(open(self.specs.feedback_file, 'w'))
                                 if self.specs.feedback_file is not None
                                 else None)
                for test_file, result in results.items():
                    for res in result:
                        test = self.test_class(self, feedback_open, test_file, res)
                        print(test.run(), flush=True)
        except Exception as e:
            print(MarkusTester.error_all(message=str(e)), flush=True)
            return

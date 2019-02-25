import contextlib
import enum
import json
import subprocess

from testers.markus_tester import MarkusTester, MarkusTest

class MarkusJavaTest(MarkusTest):

    class JUnitStatus(enum.Enum):
        SUCCESSFUL = 1
        ABORTED = 2
        FAILED = 3

    ERRORS = {
        'bad_javac': 'Java compilation error: "{}"',
        'bad_java': 'Java runtime error: "{}"'
    }

    def __init__(self, tester, result, feedback_open=None):
        self.class_name, _sep, self.method_name = result['name'].partition('.')
        self.description = result.get('description')
        self.status = MarkusJavaTest.JUnitStatus[result['status']]
        self.message = result.get('message', None)
        super().__init__(tester, feedback_open)

    @property
    def test_name(self):
        name = f'{self.class_name}.{self.method_name}'
        if self.description:
            name += f' ({self.description})'
        return name

    def run(self):
        if self.status == MarkusJavaTest.JUnitStatus.SUCCESSFUL:
            return self.passed()
        elif self.status == MarkusJavaTest.JUnitStatus.FAILED:
            return self.failed(message=self.message)
        else:
            return self.error(message=self.message)


class MarkusJavaTester(MarkusTester):

    JAVA_TESTER_CLASS = 'edu.toronto.cs.teach.MarkusJavaTester'

    def __init__(self, specs, test_class=MarkusJavaTest):
        super().__init__(specs, test_class)
        self.java_classpath = f'.:{specs["path_to_tester_jars"]}/*'

    def compile(self):
        javac_command = ['javac', '-cp', self.java_classpath]
        javac_command.extend([group.get('script_file_path', '') for group in self.specs['runnable_group']])
        # student files imported by tests will be compiled on cascade
        subprocess.run(javac_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                       check=True)

    def run_junit(self):
        java_command = ['java', '-cp', self.java_classpath, MarkusJavaTester.JAVA_TESTER_CLASS]
        javac_command.extend([group.get('script_file_path', '') for group in self.specs['runnable_group']])
        java = subprocess.run(java_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                              check=True)
        return java

    def run(self):
        # TODO Create an interface in markus_tester for running all tests at once, when using native test libraries
        try:
            # check that the submission compiles against the tests
            try:
                self.compile()
            except subprocess.CalledProcessError as e:
                msg = MarkusJavaTest.ERRORS['bad_javac'].format(e.stdout)
                print(MarkusTester.error_all(message=msg), flush=True)
                return
            # run the tests with junit
            try:
                results = self.run_junit()
                if results.stderr:
                    print(MarkusTester.error_all(message=results.stderr), flush=True)
                    return
            except subprocess.CalledProcessError as e:
                msg = MarkusJavaTest.ERRORS['bad_java'].format(e.stdout + e.stderr)
                print(MarkusTester.error_all(message=msg), flush=True)
                return
            with contextlib.ExitStack() as stack:
                feedback_open = (stack.enter_context(open(self.specs['feedback_file'], 'w'))
                                 if self.specs.get('feedback_file') is not None
                                 else None)
                for result in json.loads(results.stdout):
                    test = self.test_class(self, result, feedback_open)
                    result_json = test.run()
                    print(result_json, flush=True)
        except Exception as e:
            print(MarkusTester.error_all(message=str(e)), flush=True)

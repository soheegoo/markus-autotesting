import contextlib
import subprocess

from markus_tester import MarkusTester, MarkusTest


class MarkusJavaTest(MarkusTest):

    ERRORS = {
        'bad_javac': 'Java compilation error: "{}"',
        'bad_java': 'Java runtime error: "{}"'
    }

    def __init__(self, tester, test_file, data_files, points, test_extra, feedback_open):
        super().__init__(tester, test_file, data_files, points, test_extra, feedback_open)

    @property
    def test_name(self):
        return self.test_file

    def run(self):
        pass


class MarkusJavaTester(MarkusTester):

    def __init__(self, specs, test_class=MarkusJavaTest):
        super().__init__(specs, test_class)
        self.java_classpath = f'.:{specs["path_to_tester"]}:{specs["path_to_junit5_jar"]}'

    def compile(self):
        javac_command = ['javac', '-cp', self.java_classpath] + [test_file for test_file in self.specs.tests]
        # everything imported by tests will be compiled on cascade
        subprocess.run(javac_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                       check=True)

    def go(self):
        java_command = ['java', '-cp', self.java_classpath, self.__class__.__name__]
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
                print(MarkusTester.error_all(message=msg))
                return
            # run the tests with junit5
            try:
                results = self.go()
            except subprocess.CalledProcessError as e:
                msg = MarkusJavaTest.ERRORS['bad_java'].format(e.stdout + e.stderr)
                print(MarkusTester.error_all(message=msg))
                return
            with contextlib.ExitStack() as stack:
                feedback_open = (stack.enter_context(open(self.specs.feedback_file, 'w'))
                                 if self.specs.feedback_file is not None
                                 else None)
                for result in results:
                    points_total = 0  # TODO Get from specs
                    test = self.test_class(self, result, points_total, feedback_open)  # TODO Adjust constructor
                    xml = test.run()
                    print(xml)
        except Exception as e:
            print(MarkusTester.error_all(message=str(e)))
            return

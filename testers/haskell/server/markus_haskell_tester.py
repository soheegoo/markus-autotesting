import contextlib
import subprocess
import enum
import os
import tempfile
import csv

from markus_tester import MarkusTester, MarkusTest, MarkusTestSpecs


class MarkusHaskellTest(MarkusTest):

    def __init__(self, tester, feedback_open, test_file, result):
        self._test_name = result['name']
        all_points = tester.specs.matrix[test_file][MarkusTestSpecs.MATRIX_NODATA_KEY]
        points = all_points.get(self._test_name, 1)
        self.status = result['status']
        self.message = result['description']
        super().__init__(tester, test_file, [MarkusTestSpecs.MATRIX_NODATA_KEY], points, {}, feedback_open)

    @property
    def test_name(self):
        return self._test_name

    def run(self):
        if self.status == "PASS":
            return self.passed()
        elif self.status == "FAIL":
            return self.failed(message=self.message)
        else:
            return self.error(message=self.message)


class MarkusHaskellTester(MarkusTester):

    # column indexes of relevant data from tasty-stats csv
    # reference: http://hackage.haskell.org/package/tasty-stats
    class TastyStats(enum.Enum):
        NAME = 1
        TIME = 2
        RESULT = 3
        DESCRIPTION = -1

    def __init__(self, specs, test_class=MarkusRacketTest):
        super().__init__(specs, test_class)
    
    def _test_run_flags(self):
        module_flag = f"--modules={os.path.basename(test_file)}"
        stats_flag = "--ingredient=Test.Tasty.Stats.consoleStatsReporter"
        flags = [module_flag, stats_flag]
        if self.specs.test_timeout:
            flags.append(f"--timeout={self.specs.test_timeout}s")
        if self.specs.test_cases:
            flags.append(f"--quickcheck-tests={self.specs.test_cases}")
        return flags

    def _parse_test_results(self, reader):
        test_results = []
        for line in reader:
            result = {'status' : line[TastyStats.RESULT], 
                      'name' : line[TastyStats.NAME], 
                      'description' : line[TastyStats.DESCRIPTION], 
                      'time' : line[TastyStats.TIME]}
            test_results.append(result)
        return test_results

    def run_haskell_tests(self, test_files)
        results = {}
        for test_file in self.specs.tests:

            with tempfile.NamedTemporaryFile() as f:
                cmd = ['tasty-discover', '.', '_', f.name] + self._test_run_flags()
                discover_proc = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, universal_newlines=True)
                if discover_proc.stderr:
                    print(MarkusTester.error_all(message=discover_proc.stderr), flush=True)
                    continue
                with tempfile.NamedTemporaryFile(mode="w+") as sf:
                    cmd = ['runghc', f.name, f"--stats={sf.name}"]
                    test_proc = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, universal_newlines=True, check=True)
                    results[test_file] = {'stderr':test_proc.stderr, 'results':self._parse_test_results(csv.reader(sf))}
        return results

    def run(self):
        try:
            # run the tests with haskell's tasty-discover
            try:
                results = self.run_haskell_tests()
            except subprocess.CalledProcessError as e:
                msg = e.stdout + e.stderr
                print(MarkusTester.error_all(message=msg), flush=True)
                return
            with contextlib.ExitStack() as stack:
                feedback_open = (stack.enter_context(open(self.specs.feedback_file, 'w'))
                                 if self.specs.feedback_file is not None
                                 else None)
                for test_file, result in results.items():
                    if result['stderr']:
                        print(MarkusTester.error_all(message=result.stderr), flush=True)
                    for res in result:
                        test = self.test_class(self, feedback_open, test_file, res)
                        print(test.run(), flush=True)

        except Exception as e:
            print(MarkusTester.error_all(message=str(e)), flush=True)
            return

import subprocess


class MarkusCustomTester:

    def __init__(self, specs):
        self.specs = specs

    def run(self):
        file_paths = self.specs.get('test_data', 'script_files', default=[])
        for file_path in file_paths:
            subprocess.run(f'./{file_path}')

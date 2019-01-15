import subprocess

class MarkusHaskellTester:
    def __init__(self, specs):
        self.specs = specs

    def run(self):
        for group in self.specs.get('runnable_group', []):
            file_path = group.get('script_file_path')
            if file_path:
                subprocess.run(f'./{file_path}')

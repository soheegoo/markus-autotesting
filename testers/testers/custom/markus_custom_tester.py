import subprocess
import os

class MarkusCustomTester:
    def __init__(self, specs):
        self.specs = specs

    def run(self):
        file_path = self.specs.get('script_file_path')
        if file_path:
            subprocess.run(f'./{file_path}')

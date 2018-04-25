import os
import sys

import python_ta
from pylint.config import VALIDATORS
from python_ta.reporters import PositionReporter, PlainReporter

from markus_tester import MarkusTester, MarkusTest


class MarkusPyTAReporter(PositionReporter):

    def print_messages(self, level='all'):
        super().print_messages(level=level)
        PlainReporter.print_messages(self, level)

    def output_blob(self):
        pass


class MarkusPyTATest(MarkusTest):

    ERROR_MSGS = {
        'reported': "{} error(s)"
    }

    def __init__(self, tester, test_file, data_files, points, test_extra, feedback_open=None):
        super().__init__(tester, test_file, data_files, points, test_extra, feedback_open)
        self.annotations = []

    @property
    def test_name(self):
        return f'PyTA {super().test_name}'

    def add_annotations(self, reporter):
        for result in reporter._output['results']:
            if 'filename' not in result:
                continue
            for msg_group in result.get('msg_styles', []) + result.get('msg_errors', []):
                for msg in msg_group['occurrences']:
                    self.annotations.append({
                        'annotation_category_name': None,
                        'filename': result['filename'],
                        'content': msg['text'],
                        'line_start': msg['lineno'],
                        'line_end': msg['end_lineno'],
                        'column_start': msg['col_offset'],
                        'column_end': msg['end_col_offset']
                    })

    def run(self):
        reporter = python_ta.check_all(self.test_file, config=self.tester.pyta_config)
        self.add_annotations(reporter)
        num_messages = len(reporter._error_messages + reporter._style_messages)
        points_earned = max(0, self.points_total - num_messages)  # deduct 1 point per message occurrence (not type)
        message = self.ERROR_MSGS['reported'].format(num_messages) if num_messages > 0 else ''
        return self.done(points_earned, message)


class MarkusPyTATester(MarkusTester):

    def __init__(self, specs, test_class=MarkusPyTATest):
        super().__init__(specs, test_class)
        self.pyta_config = specs.get('pyta_config', {})
        self.pyta_config.update({'pyta-output-file': self.specs.feedback_file,
                                 'pyta-reporter': 'MarkusPyTAReporter'})
        self.devnull = open(os.devnull, 'w')
        self.annotations = []
        VALIDATORS[MarkusPyTAReporter.__name__] = MarkusPyTAReporter

    def before_test_run(self, test):
        sys.stdout = test.feedback_open
        sys.stderr = self.devnull

    def after_test_run(self, test):
        self.annotations.extend(test.annotations)
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stdout__

    def run(self):
        super().run()
        self.devnull.close()

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
        'reported': "{} errors"
    }

    def run(self):
        config = {'pyta-output-file': self.tester.specs.feedback_file,
                  'pyta-reporter': 'MarkusPyTAReporter'}
        sys.stdout = self.feedback_open
        sys.stderr = open(os.devnull, 'w')
        reporter = python_ta.check_all(self.test_file, config=config)
        sys.stderr.close()
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stdout__
        num_messages = len(reporter._error_messages + reporter._style_messages)
        points_earned = max(0, self.points_total - num_messages)  # deduct 1 mark per message occurrence (not type)
        message = self.ERROR_MSGS['reported'].format(num_messages) if num_messages > 0 else ''
        return self.done(points_earned, message)


class MarkusPyTATester(MarkusTester):

    def __init__(self, specs, test_class=MarkusPyTATest):
        super().__init__(specs, test_class)
        self.pyta_config = specs['pyta_config']
        self.pyta_config.update({'pyta-output-file': self.specs.feedback_file,
                                 'pyta-reporter': 'MarkusPyTAReporter'})
        VALIDATORS[MarkusPyTAReporter.__name__] = MarkusPyTAReporter

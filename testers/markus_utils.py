import os
import subprocess
from xml.sax import saxutils


class MarkusUtilsMixin:

    @staticmethod
    def print_test_result(name, status, output, points_awarded, points_total=None):
        """
        Prints one test result in Markus' test framework format.
        :param name: The test name.
        :param status: One of 'pass', 'fail', 'error'.
        :param output: The test output.
        :param points_awarded: The points awarded by the test, must be an integer >= 0 (and <= points_total if present).
        :param points_total: The total points the test can award, must be an integer > 0. Can be None if unknown.
        """
        if points_total is not None and points_total <= 0:
            raise ValueError('The total points must be > 0')
        if points_awarded < 0:
            raise ValueError('The points awarded must be >= 0')
        if points_total is not None and points_awarded > points_total:
            raise ValueError('The points awarded must be <= the total points')

        output_escaped = saxutils.escape(output.replace('\x00', ''), entities={"'": '&apos;'})
        info = name if points_total is None else '[{awarded}/{total}] {name}'.format(awarded=points_awarded,
                                                                                     total=points_total, name=name)
        print('''
<test>
    <name>{info}</name>
    <input></input>
    <expected></expected>
    <actual>{output}</actual>
    <marks_earned>{awarded}</marks_earned>
    <status>{status}</status>
</test>'''.format(info=info, output=output_escaped, awarded=points_awarded, status=status))

    @staticmethod
    def print_test_error(name, message, points_total=None):
        """
        Prints one test error result in Markus' test framework format.
        :param name: The test name.
        :param message: The error message, will be shown as test output.
        :param points_total: The total points the test could have awarded, must be an integer > 0. Can be None if
                             unknown.
        """
        MarkusUtilsMixin.print_test_result(name=name, status='error', output=message, points_awarded=0,
                                           points_total=points_total)

    @staticmethod
    def upload_svn_file(markus_root_url, file_name, group_name, assignment_name, svn_user, svn_password,
                        commit_message):
        markus_server_url, slash, markus_instance = markus_root_url.rpartition('/')
        repo_url = '/'.join([markus_server_url, 'svn', markus_instance, group_name])
        svn_co_command = ['svn', 'co', '--username', svn_user, '--password', svn_password, repo_url]
        subprocess.run(svn_co_command)
        repo_path = os.path.join(group_name, assignment_name, file_name)
        previous_file = os.path.isfile(repo_path)
        cp_command = ['cp', '-f', file_name, repo_path]
        subprocess.run(cp_command)
        if not previous_file:
            svn_add_command = ['svn', 'add', repo_path]
            subprocess.run(svn_add_command)
        svn_ci_command = ['svn', 'ci', '--username', svn_user, '--password', svn_password, '-m', commit_message,
                          repo_path]
        subprocess.run(svn_ci_command)

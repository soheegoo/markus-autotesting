import glob
import os
import json
import shutil
import subprocess


# Helper functions
def upload_svn_file(api, tests_path, group_repo_name, assignment_name, file_name, svn_user, svn_password,
                    commit_message):
    repo_url = f'{api.parsed_url.scheme}://{api.parsed_url.netloc}/svn{api.parsed_url.path}/{group_repo_name}'
    repo_path = os.path.join(tests_path, group_repo_name)
    svn_co_command = ['svn', 'co', '--username', svn_user, '--password', svn_password, repo_url, repo_path]
    subprocess.run(svn_co_command, capture_output=True, check=True)
    file_path = os.path.join(tests_path, file_name)
    repo_file_path = os.path.join(repo_path, assignment_name, file_name)
    previous_file = os.path.isfile(repo_file_path)
    shutil.copy2(file_path, repo_file_path)
    if not previous_file:
        svn_add_command = ['svn', 'add', repo_file_path]
        subprocess.run(svn_add_command, capture_output=True, check=True)
    svn_ci_command = ['svn', 'ci', '--username', svn_user, '--password', svn_password, '-m', commit_message,
                      repo_file_path]
    subprocess.run(svn_ci_command, capture_output=True, check=True)


# Hooks
def before_all(api, tests_path, assignment_id, group_id, group_repo_name):
    # clean up unwanted files
    pattern = os.path.join(tests_path, '**', '*.o')
    for file_path in glob.glob(pattern, recursive=True):
        os.remove(file_path)


def before_each(api, tests_path, assignment_id, group_id, group_repo_name):
    pass


def after_each(api, tests_path, assignment_id, group_id, group_repo_name):
    pass


def after_all(api, tests_path, assignment_id, group_id, group_repo_name):
    # upload feedback file
    feedback_name = 'feedback_pyta.txt'
    feedback_path = os.path.join(tests_path, feedback_name)
    if os.path.isfile(feedback_path):
        with open(feedback_path) as feedback_open:
            api.upload_feedback_file(assignment_id, group_id, feedback_name, feedback_open.read())
            # upload in svn repo
            upload_svn_file(api, tests_path, group_repo_name, 'AX', feedback_name, 'svn_user', 'svn_password',
                            'Feedback file')
    # upload annotations
    annotations_name = 'feedback_pyta.json'
    annotations_path = os.path.join(tests_path, annotations_name)
    if os.path.isfile(annotations_path):
        with open(annotations_path) as annotations_open:
            api.upload_annotations(assignment_id, group_id, json.load(annotations_open))

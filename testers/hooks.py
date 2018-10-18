import os


def before_all():
    pass


def before_each():
    pass


def after_each():
    pass


def after_all(api, working_dir, assignment_id, group_id, repo_name):
    feedback_name = 'feedback_pyta.txt'
    feedback_path = os.path.join(working_dir, feedback_name)
    if os.path.isfile(feedback_path):
        with open(feedback_path) as feedback_open:
            api.upload_feedback_file(assignment_id, group_id, feedback_name, feedback_open.read())

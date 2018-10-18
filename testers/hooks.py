import os
import json


def before_all(api, tests_path, assignment_id, group_id, group_repo_name):
    pass


def before_each(api, tests_path, assignment_id, group_id, group_repo_name):
    pass


def after_each(api, tests_path, assignment_id, group_id, group_repo_name):
    pass


def after_all(api, tests_path, assignment_id, group_id, group_repo_name):
    feedback_name = 'feedback_pyta.txt'
    feedback_path = os.path.join(tests_path, feedback_name)
    if os.path.isfile(feedback_path):
        with open(feedback_path) as feedback_open:
            api.upload_feedback_file(assignment_id, group_id, feedback_name, feedback_open.read())

    annotation_name = 'feedback_pyta.json'
    annotation_path = os.path.join(tests_path, annotation_name)
    if os.path.isfile(annotation_path):
        with open(annotation_path) as annotation_open:
            api.upload_annotations(assignment_id, group_id, json.load(annotation_open))

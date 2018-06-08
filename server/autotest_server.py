#!/usr/bin/env python3

import os
import fcntl
import shutil
import time
import json 
import requests
import subprocess
import signal
import urllib
import redis
import rq
import pwd
from contextlib import contextmanager
from functools import wraps
import config

CURRENT_TEST_SCRIPT_FORMAT = '{}_{}'
TEST_SCRIPT_DIR = os.path.join(config.WORKSPACE_DIR, config.SCRIPTS_DIR_NAME)
TEST_RESULT_DIR = os.path.join(config.WORKSPACE_DIR, config.RESULTS_DIR_NAME)
REDIS_CURRENT_TEST_SCRIPT_HASH = '{}:{}'.format(config.REDIS_PREFIX, config.REDIS_CURRENT_TEST_SCRIPT_HASH)
REDIS_WORKERS_LIST = '{}:{}'.format(config.REDIS_PREFIX, config.REDIS_WORKERS_LIST)
REDIS_POP_HASH = '{}:{}'.format(config.REDIS_PREFIX, config.REDIS_POP_HASH)

### HELPER FUNCTIONS ###

def stringify(*args):
    for a in args:
        yield str(a)

def current_user():
    return pwd.getpwuid(os.getuid()).pw_name

def decode_if_bytes(b):
    return b.decode('utf-8') if isinstance(b, bytes) else b

def clean_dir_name(name):
    """ Return name modified so that it can be used as a unix style directory name """
    return name.replace('/', '_')

def get_test_script_key(markus_address, assignment_id):
    """ 
    Return unique key for each assignment used for 
    storing the location of test scripts in Redis 
    """
    clean_markus_address = clean_dir_name(markus_address)
    return CURRENT_TEST_SCRIPT_FORMAT.format(clean_markus_address, assignment_id)

def test_script_directory(markus_address, assignment_id, set_to=None):
    """
    Return the directory containing the test scripts for a specific assignment.
    Optionally updates the location of the test script directory to the value 
    of the set_to keyword argument (if it is not None)
    """
    key = get_test_script_key(markus_address, assignment_id)
    r = redis_connection()
    if set_to is not None:
        r.hset(REDIS_CURRENT_TEST_SCRIPT_HASH, key, set_to)
    out = r.hget(REDIS_CURRENT_TEST_SCRIPT_HASH, key)
    return decode_if_bytes(out)

def recursive_iglob(root_dir):
    """
    Walk breadth first over a directory tree starting at root_dir and
    yield the path to each directory or file encountered. 
    Yields a tuple containing a string indicating whether the path is to
    a directory ("d") or a file ("f") and the path itself. 
    """
    for root, dirnames, filenames in os.walk(root_dir):
        yield from (('d', os.path.join(root, d)) for d in dirnames)
        yield from (('f', os.path.join(root, f)) for f in filenames)

def redis_connection():
    """
    Return the currently open redis connection object. If there is no 
    connection currently open, one is created using the keyword arguments 
    specified in config.REDIS_CONNECTION_KWARGS
    """
    conn = rq.get_current_connection()
    if conn:
        return conn
    kwargs = config.REDIS_CONNECTION_KWARGS
    rq.use_connection(redis=redis.Redis(**kwargs))
    return rq.get_current_connection()

def copy_tree(src, dst):
    """
    Recursively copy all files and subdirectories in the path 
    indicated by src to the path indicated by dst. If directories
    don't exist, they are created. 
    """
    for fd, file_or_dir in recursive_iglob(src):
        target = os.path.join(dst, os.path.relpath(file_or_dir, src))
        if fd == 'd':
            os.makedirs(target, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(file_or_dir, target)

def ignore_missing_dir_error(_func, _path, excinfo):
    """ Used by shutil.rmtree to ignore a FileNotFoundError """
    err_type, err_inst, traceback = excinfo
    if err_type == FileNotFoundError:
        return 
    raise err_inst

def move_tree(src, dst):
    """
    Recursively move all files and subdirectories in the path 
    indicated by src to the path indicated by dst. If directories
    don't exist, they are created. 
    """
    copy_tree(src, dst)
    shutil.rmtree(src, onerror=ignore_missing_dir_error)

def loads_partial_json(json_string, expected_type=None):
    """
    Return a list of objects loaded from a json string and a boolean
    indicating whether the json_string was malformed.  This will try 
    to load as many valid objects as possible from a (potentially 
    malformed) json string. If the optional expected_type keyword argument
    is not None then only objects of the given type are returned, 
    if any objects of a different type are found, the string will 
    be treated as malfomed.
    """
    i = 0
    decoder = json.JSONDecoder()
    results = []
    malformed = False
    json_string = json_string.strip()
    while i < len(json_string):
        try:
            obj, ind = decoder.raw_decode(json_string[i:])
            if expected_type is None or isinstance(obj, expected_type):
                results.append(obj)
            elif json_string[i:i+ind].strip():
                malformed = True
            i += ind
        except json.JSONDecodeError:
            if json_string[i].strip():
                malformed = True
            i += 1
    return results, malformed

@contextmanager
def fd_open(path, flags=os.O_RDONLY, *args, **kwargs):
    """
    Open the file or directory at path, yield its 
    file descriptor, and close it when finished. 
    flags, *args and **kwargs are passed on to os.open.
    """
    fd = os.open(path, flags, *args, **kwargs)
    yield fd
    os.close(fd)

@contextmanager
def fd_lock(file_descriptor, exclusive=True):
    """
    Lock the object with the given file descriptor and unlock it 
    when finished.  A lock can either be exclusive or shared by
    setting the exclusive keyword argument to True or False.
    """
    fcntl.flock(file_descriptor, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
    yield
    fcntl.flock(file_descriptor, fcntl.LOCK_UN)

@contextmanager
def tester_user():
    """
    Pop the next available user from the array named REDIS_WORKERS_LIST in redis, 
    yield the user information and pop it back in the queue when finished.
    This will block until a user is available if the queue is empty. 
    """
    r = redis_connection()
    _, user_data = r.blpop(REDIS_WORKERS_LIST)
    try:
        yield json.loads(decode_if_bytes(user_data))
    finally:
        r.rpush(REDIS_WORKERS_LIST, user_data)

### MAINTENANCE FUNCTIONS ###

def update_pop_interval_stat(queue_name):
    """
    Update the values contained in the redis hash named REDIS_POP_HASH for 
    the queue named queue_name. This should be called whenever a new job
    is popped from a queue for which we want to keep track of the popping 
    rate. For more details about the data updated see get_pop_interval_stat.
    """
    r = redis_connection()
    now = time.time()
    r.hsetnx(REDIS_POP_HASH, '{}_start'.format(queue_name), now)
    r.hset(REDIS_POP_HASH, '{}_last'.format(queue_name), now)
    r.hincrby(REDIS_POP_HASH, '{}_count'.format(queue_name), 1)

def clear_pop_interval_stat(queue_name):
    """
    Reset the values contained in the redis hash named REDIS_POP_HASH for 
    the queue named queue_name. This should be called whenever a queue becomes 
    empty. For more details about the data updated see get_pop_interval_stat. 
    """
    r = redis_connection()
    r.hdel(REDIS_POP_HASH, '{}_start'.format(queue_name))
    r.hset(REDIS_POP_HASH, '{}_last'.format(queue_name), 0)
    r.hset(REDIS_POP_HASH, '{}_count'.format(queue_name), 0)

def get_pop_interval_stat(queue_name):
    """
    Return the following data about the queue named queue_name:
        - the time the first job was popped from the queue during the 
          current burst of jobs. 
        - the number of jobs popped from the queue during the current 
          burst of jobs.
        - the time the most recent job was popped from the queue during
          current burst of jobs.
    """
    r = redis_connection()
    start = r.hget(REDIS_POP_HASH, '{}_start'.format(queue_name))
    last = r.hget(REDIS_POP_HASH, '{}_count'.format(queue_name))
    count = r.hget(REDIS_POP_HASH, '{}_count'.format(queue_name))
    return start, last, count

def get_avg_pop_interval(queue_name):
    """
    Return the average interval between pops off of the end of the
    queue named queue_name during the current burst of jobs. 
    Return None if there are no jobs in the queue, indicating that 
    there is no current burst.
    """
    start, last, count = get_pop_interval_stat(queue_name)
    try:
        start = float(start)
        last = float(last)
        count = int(count)
    except TypeError:
        return None
    count -= 1
    return (last-start) / count if count else 0

def clean_up():
    """ Reset the pop interval data for each empty queue """
    with rq.Connection(redis_connection()):
        for q in rq.Queue.all():
            if q != rq.queue.FailedQueue():
                if q.is_empty():
                    clear_pop_interval_stat(q.name)


def clean_after(func):
    """ 
    Call the clean_up function after the 
    decorated function func is finished 
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            clean_up()
    return wrapper

### RUN TESTS ###

def copy_test_script_files(markus_address, assignment_id, tests_path):
    """
    Copy test script files for a given assignment to the tests_path
    directory. tests_path may already exist and contain files and 
    subdirectories.
    """
    test_script_dir = test_script_directory(markus_address, assignment_id)
    with fd_open(test_script_dir) as fd:
        with fd_lock(fd, exclusive=False):
            copy_tree(test_script_dir, tests_path)

def setup_files(files_path, tests_path, test_scripts, markus_address, assignment_id):
    """
    Copy test script files and student files to the working directory tests_path. 
    The following permissions are also set:
        - tests_path directory:     rwxrwx--T
        - subdirectories:           rwxr-xr-x
        - test script files:        rwxr-xr-x
        - other files:              rw-r--r--
    """
    if files_path != tests_path:
        move_tree(files_path, tests_path)
        copy_test_script_files(markus_address, assignment_id, tests_path)
        os.chmod(tests_path, 0o1770)
    for fd, file_or_dir in recursive_iglob(tests_path):
        permissions = 0o755 
        if fd == 'f' and os.path.relpath(file_or_dir, tests_path) not in test_scripts:
            permissions -= 0o111
        os.chmod(file_or_dir, permissions)



def test_run_command(markus_address, user_api_key, assignment_id, 
                     group_id, group_repo_name, test_username=None):
    """
    Return a command used to run test scripts as a the test_username
    user, with the correct arguments. Set test_username to None to 
    run as the current user.

    >>> test_script = 'mysscript.py'
    >>> test_run_command('a', 'b', 'c', 'd', 'e', 'f').format(test_script)
    'sudo -u f -- bash -c "./myscript.py a b c d e"'

    >>> test_run_command('a', 'b', 'c', 'd', 'e', None).format(test_script)
    './myscript.py a b c d e'
    """
    cmd = ' '.join(stringify('./{}', markus_address, user_api_key, assignment_id, group_id, group_repo_name))

    if test_username is not None:
        cmd = ' '.join(('sudo', '-u', test_username, '--', 'bash', '-c', 
                        '"{}"'.format(cmd)))

    return cmd

def create_test_script_result(file_name, stdout, stderr, run_time, timeout=None):
    """
    Return the arguments passed to this function in a dictionary. If stderr is 
    falsy, change it to None. Load the json string in stdout as a dictionary.
    """
    test_results, malformed = loads_partial_json(stdout, dict)
    return {'file_name' : file_name,
            'time' : run_time,
            'timeout' : timeout,
            'tests' : test_results, 
            'stderr' : stderr or None,
            'malformed' :  stdout if malformed else None}

def run_test_scripts(cmd, test_scripts, tests_path):
    """
    Run each test script in test_scripts in the tests_path directory using the 
    command cmd. Return the results. 
    """
    results = []
    for file_name, timeout in test_scripts.items():
        out, err = '', '' 
        start = time.time()
        timeout = None
        try:
            args = cmd.format(file_name)
            proc = subprocess.Popen(args, start_new_session=True, cwd=tests_path, shell=True, 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                out, err = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                pgrp = os.getpgid(proc.pid)
                os.killpg(pgrp, signal.SIGKILL)
                out, err = proc.communicate()
                timeout = timeout
        except Exception as e:
            err += '\n\n{}'.format(e.message)
        finally:
            out = decode_if_bytes(out)
            err = decode_if_bytes(err)
            duration = int(round(time.time()-start, 3) * 1000)
            results.append(create_test_script_result(file_name, out, err, duration, timeout))
    return results

def store_results(results, markus_address, assignment_id, group_id, submission_id):
    """
    Write the results of multiple test script runs to an output file as a json string.
    The output file is located at:
        {TEST_RESULT_DIR}/{markus_address}/{assignment_id}/{group_id}/{submission_id}/ouput.json
    """
    clean_markus_address = clean_dir_name(markus_address)
    run_time = "run_{}".format(int(time.time()))
    destination = os.path.join(*stringify(TEST_RESULT_DIR, clean_markus_address, assignment_id, group_id, 's{}'.format(submission_id or ''), run_time))
    os.makedirs(destination, exist_ok=True)
    with open(os.path.join(destination, 'output.json'), 'w') as f:
        json.dump(results, f, indent=4)

def clean_up_tests(tests_path, test_username):
    """
    Run a command that clears the tests_path working directory 
    and kills all processes started by the user test_username
    """    
    cmds = ['chmod -Rf ugo+rwX {}'.format(tests_path)]

    if test_username != current_user():
        cmds.append('killall -KILL -u {}'.format(test_username))        
        sudo_cmd = 'sudo -u {} -- bash -c '.format(test_username)
        cmds = [sudo_cmd + cmd for cmd in cmds]

    cmds.append('rm -rf {}'.format(tests_path))

    for cmd in cmds:
        subprocess.run(cmd, shell=True)


def report(results, markus_address, assignment_id, group_id, 
           server_api_key, run_id, error, time_to_service):
    """ Post the results of running test scripts to the markus api """
    url = '/'.join(stringify('api', 'assignments', assignment_id, 
                                    'groups', group_id, 'test_script_results'))
    url = urllib.parse.urljoin(markus_address, url)
    
    headers = {'Authorization' : 'MarkUsAuth {}'.format(server_api_key),
               'Accept'     : 'application/json'}
    
    data = {'test_scripts'       : results,
            'error'              : error, 
            'time_to_service'    : time_to_service} 

    data = {'test_run_id' : run_id, 'test_output' : json.dumps(data)}

    requests.post(url, headers=headers, data=data)

@clean_after
def run_test(markus_address, user_api_key, server_api_key, test_scripts, files_path, 
             assignment_id, group_id, group_repo_name, submission_id, run_id, enqueue_time):
    """
    Run autotesting tests using the tests in test_scripts on the files in files_path. 

    This function should be used by an rq worker.
    """
    job = rq.get_current_job()
    update_pop_interval_stat(job.origin)
    time_to_service = int(round(time.time() - enqueue_time, 3) * 1000)
    
    results = []
    error = None
    with tester_user() as user_data:
        test_username = user_data.get('username')
        try:
            tests_path = user_data['worker_dir']
            setup_files(files_path, tests_path, test_scripts, markus_address, assignment_id)
            cmd = test_run_command(markus_address, user_api_key, assignment_id, 
                                   group_id, group_repo_name, test_username)
            results = run_test_scripts(cmd, test_scripts, tests_path)
            store_results(results, markus_address, assignment_id, group_id, submission_id)
        except Exception as e:
            error = str(e)
        finally:
            clean_up_tests(tests_path, test_username)
            report(results, markus_address, assignment_id, group_id, 
                   server_api_key, run_id, error, time_to_service)

### UPDATE TEST SCRIPTS ### 

@clean_after
def update_test_scripts(files_path, assignment_id, markus_address):
    """
    Copy new test scripts for a given assignment to from the files_path
    to a new location. Indicate that these new test scripts should be used instead of 
    the old ones. And remove the old ones when it is safe to do so (they are not in the
    process of being copied to a working directory).

    This function should be used by an rq worker.
    """
    test_script_dir_name = "test_scripts_{}".format(int(time.time()))
    clean_markus_address = clean_dir_name(markus_address)
    new_dir = os.path.join(*stringify(TEST_SCRIPT_DIR, clean_markus_address, assignment_id, test_script_dir_name))
    move_tree(files_path, new_dir)
    old_test_script_dir = test_script_directory(markus_address, assignment_id)
    test_script_directory(markus_address, assignment_id, set_to=new_dir)
    if old_test_script_dir is not None:
        with fd_open(old_test_script_dir) as fd:
            with fd_lock(fd, exclusive=True):
                shutil.rmtree(old_test_script_dir, onerror=ignore_missing_dir_error)


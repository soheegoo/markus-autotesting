#!/usr/bin/env python3

#### CHANGE CONFIG PARAMETERS BELOW ####

## PYTHON CONFIGS ##

ADDITIONAL_PIP_PACKAGES = ''

## REDIS CONFIGS ##

# name of redis hash used to store the locations of test script directories
REDIS_CURRENT_TEST_SCRIPT_HASH = 'curr_test_scripts'
# name of redis hash used to store pop interval data for each worker queue 
REDIS_POP_HASH = 'pop_intervals'
# name of redis list used to store testers data (username and workspace directory)
REDIS_TESTERS_LIST = 'testers'
# dictionary containing keyword arguments to pass to rq.use_connection 
# when connecting to a redis database (empty dictionary is default)
REDIS_CONNECTION_KWARGS = {}

## WORKING DIR CONFIGS ##

# the main working directory
WORKING_DIR = '/home/vagrant/Markus/data/dev/autotest/server'
# name of the directory containing test scripts
TEST_SCRIPTS_DIR_NAME = 'scripts'
# name of the directory containing test results
TEST_RESULTS_DIR_NAME = 'results'
# name of the directory containing virtual environments
VENVS_DIR_NAME = 'venvs'
# name of the directory containing specs files
SPECS_DIR_NAME = 'specs'
# name of the directory containing workspaces for the workers
WORKSPACES_DIR_NAME = 'workspaces'
# name of the server user
SERVER_USER = ''
# names of the tester users
TESTER_USERS = ''


### QUEUE CONFIGS ###

# functions used to select which type of queue to use. They must accept any number
# of keyword arguments and should only return a boolean (see autotest_enqueuer._get_queue)
def batch_filter(**kwargs):
    return kwargs.get('batch_id') is not None

def single_filter(**kwargs):
    return kwargs.get('user_type') == 'Admin' and not batch_filter(**kwargs)

def student_filter(**kwargs):
    return kwargs.get('user_type') == 'Student' and not batch_filter(**kwargs)

# list of worker queues. Values of each are a string indicating the queue name,
# and a function used to select whether or not to use this type of queue 
# (see autotest_enqueuer._get_queue)
batch_queue = {'name': 'batch', 'filter': batch_filter}
single_queue = {'name': 'single', 'filter': single_filter}
student_queue = {'name': 'student', 'filter': student_filter}
WORKER_QUEUES = [batch_queue, single_queue, student_queue]

# name of the service queue
SERVICE_QUEUE = 'service'

### WORKER CONFIGS ###

WORKERS = [(4, [SERVICE_QUEUE, student_queue['name'], single_queue['name'], batch_queue['name']]),
           (2, [SERVICE_QUEUE, single_queue['name'], student_queue['name'], batch_queue['name']]),
           (2, [SERVICE_QUEUE, batch_queue['name'], student_queue['name'], single_queue['name']])]

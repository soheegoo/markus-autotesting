#!/usr/bin/env python3

#### CHANGE CONFIG PARAMETERS BELOW ####

## PYTHON CONFIGS ##

ADDITIONAL_PIP_PACKAGES = ''

## REDIS CONFIGS ##
# name of redis hash used to store the locations of test script directories 
CURRENT_TEST_SCRIPT_HASH = 'curr_test_scripts'
# name of redis hash used to store pop interval data for each worker queue 
POP_HASH = 'pop_intervals'
# name of redis list used to store user data (username and working directory)
USER_LIST = 'users'
# dictionary containing keyword arguments to pass to rq.use_connection 
# when connecting to a redis database (empty dictionary is default)
REDIS_CONNECTION_KWARGS = {}
# name of the service queue 
SERVICE_QUEUE = 'service'

## WORKING DIR CONFIGS ##
WORKING_DIR = '/home/vagrant/Markus/data/dev/autotest/server'
# path to root directory containing test scripts
TEST_SCRIPT_DIR_NAME = 'scripts'
# path to root directory containing test results
TEST_RESULT_DIR_NAME = 'results'
# path to root directory containing virtual environments
VENVS_DIR_NAME = 'venvs'
# path to root directory containing specs files
SPECS_DIR_NAME = 'specs'


### QUEUE CONFIGS ###
# functions used to select which type of queue to use. They must accept any number 
# of keyword arguments and should only return a boolean (see automated_test_enqueuer._get_queue) 
def batch_filter(**kwargs):
	return kwargs.get('batch_id') is not None

def single_filter(**kwargs):
	return kwargs.get('user_type') == 'Admin' and not batch_filter(**kwargs)

def student_filter(**kwargs):
	return kwargs.get('user_type') == 'Student' and not batch_filter(**kwargs)

# list of queue types. Values of each are a string indicating the queue name, 
# and a function used to select whether or not to use this type of queue 
# (see automated_test_enqueuer._get_queue)

QUEUES = [('batch', batch_filter),
		  ('single', single_filter),
		  ('student', student_filter)]

### WORKER CONFIGS ###

WORKERS = [(4, [SERVICE_QUEUE, 'batch', 'student', 'single']),
		   (2, [SERVICE_QUEUE, 'student', 'single', 'batch']),
		   (2, [SERVICE_QUEUE, 'single', 'student', 'batch'])]



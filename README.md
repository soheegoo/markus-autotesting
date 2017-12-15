Automated Testing Engine (ATE)
==============================

The Automated Testing Engine (ATE) allows instructors and tas to run tests on students submissions and automatically
create marks for them. It also allows students to run a separate set of tests and self-assess their submission.

ATE consists of a client component integrated into MarkUs, and a standalone server component. Testing jobs are queued
using the gem Resque with a first in first out strategy, and served one at a time or concurrently up to a configurable
limit.

## 1. Installation

The client requirements are already included in a MarkUs installation.

To install the server, run the top level `install.sh server_user test_user working_dir [num_workers]`..TODO

To restart the server, run the `start_resque.sh queue_name [num_workers]`..TODO

To install a tester, run the `install.sh` script in the respective tester dir. We come with a set of ready-to-use
testers (python+java (cite uam), sql, jdbc, xquery)..TODO

To create an environment for a course, run the `create_test_env.sh` script..TODO

If you are a MarkUs developer, you can just `bundle install --deployment`..TODO

## 2. Running ATE

Examples of architectures:

1) MarkUs development

   One Resque worker to serve client and server (this setup can be used in production too, but it is not recommended).

   `TERM_CHILD=1 QUEUES=* bundle exec rake environment resque:work`

2) MarkUs production with dedicated test server

   One Resque client worker and one dedicated Resque server worker, either on the same machine or on separate machines.

   client:  
   `ATE_FILES_QUEUE_NAME=name_in_config_options`  
   `RAILS_ENV=production TERM_CHILD=1 BACKGROUND=yes QUEUES=${ATE_FILES_QUEUE_NAME} bundle exec rake environment
   resque:work`  
   (The other Resque queues that MarkUs uses for background processing can be added to this command, namely
   `JOB_CREATE_INDIVIDUAL_GROUPS_QUEUE_NAME`, `JOB_COLLECT_SUBMISSIONS_QUEUE_NAME`,
   `JOB_UNCOLLECT_SUBMISSIONS_QUEUE_NAME`)

   server:  
   `ATE_TESTS_QUEUE_NAME=name_in_config_options`  
   `TERM_CHILD=1 BACKGROUND=yes QUEUES=${ATE_TESTS_QUEUE_NAME} bundle exec rake resque:work`

3) MarkUs production with shared test server

   N Resque client workers and one shared Resque server worker, either on the same machine or on separate machines.

   The commands are exactly the same as #2, with one caveat: each client runs a client command, where the queue names
   are different.

4) TODO add concurrency example

Check out Resque on GitHub to get an idea of all the possible queue configurations.

## 3. MarkUs ATE Config Options

##### AUTOMATED_TESTING_ENGINE_ON
Enables ATE.

##### ATE_EXPERIMENTAL_STUDENT_TESTS_ON
Allows the instructor to let students run tests periodically.

##### ATE_EXPERIMENTAL_STUDENT_TESTS_BUFFER_TIME
With student tests enabled, a student can't request a new test if they already have a test in execution, to prevent
denial of service. If the test script fails unexpectedly and does not return a result, a student would effectively be
locked out from further testing.  
This is the amount of time after which a student can request a new test anyway.  
(Ignored if `ATE_EXPERIMENTAL_STUDENT_TESTS_ON` is 'false'.)

##### ATE_CLIENT_DIR
The directory on the client where the test files are stored.  
The user running MarkUs must be able to write here.

##### ATE_FILES_QUEUE_NAME
The name of the Resque client queue where the test files wait to be copied to the server.

##### ATE_SERVER_HOST
The server host name.  
(Use 'localhost' for a local development server where files are copied using the file system.)

##### ATE_SERVER_FILES_USERNAME
The server username used to copy the test files over and to run the Resque server workers.  
SSH passwordless login must be set up for the user running MarkUs to connect with this username on the server.  
(Ignored if `ATE_SERVER_HOST` is 'localhost'.)

##### ATE_SERVER_FILES_DIR
The directory on the server where test files are copied.  
Multiple clients can use the same directory, and `ATE_SERVER_FILES_USERNAME` must be able to write here.  
(If `ATE_SERVER_HOST` is 'localhost', the user running MarkUs must be able to write here.)

##### ATE_SERVER_RESULTS_DIR
The directory on the server where test results are logged.  
`ATE_SERVER_FILES_USERNAME` must be able to write here.  
(If `ATE_SERVER_HOST` is 'localhost', the user running MarkUs must be able to write here.)

##### ATE_SERVER_TESTS
An array of hashes with the server workers configurations. Each hash is a concurrent worker on the server running the
tests, and has the following keys:
* **user**: The server username used to run the tests. `ATE_SERVER_FILES_USERNAME` must be able to sudo -u to it.  
(Can be the same as `ATE_SERVER_FILES_USERNAME`, or ignored if `ATE_SERVER_HOST` is 'localhost'.)
TODO INSTALL AND START_RESQUE REQUIRE DIFFERENT USERS FOR TESTS
* **dir**: The directory on the server where tests run.  
`ATE_SERVER_FILES_USERNAME` and `user` must be able to write here.  
(Can be the same as `ATE_SERVER_FILES_DIR`.)
* **queue**: The name of the Resque server queue where tests wait to be executed.

The `user`, `dir` and `queue` settings must be different among concurrent test workers.

## 4. Test scripts output format

The test scripts the instructors upload and run on the server must print the following output on stdout for each test:

```
<test>
    <name>REQUIRED (STRING)</name>
    <input>OPTIONAL (STRING, NOT DISPLAYED YET)</input>
    <expected>OPTIONAL (STRING, NOT DISPLAYED YET)</expected>
    <actual>OPTIONAL (STRING, DISPLAYED AS OUTPUT)</actual>
    <marks_earned>REQUIRED (INTEGER OR FLOAT)</marks_earned>
    <marks_total>OPTIONAL (INTEGER OR FLOAT)</marks_total>
    <status>REQUIRED (ONE OF pass,partial,fail,error,error_all)</status>
</test>
```

This output is sent back to the client and logged under `ATE_SERVER_RESULTS_DIR` in files named 'output.txt'.  
Printing on stderr instead is not sent back but still logged under `ATE_SERVER_RESULTS_DIR` in files named 'errors.txt'.

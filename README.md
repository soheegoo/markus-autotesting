Autotesting with Markus
==============================

Autotesting allows instructors to run tests on students submissions and automatically create marks for them.
It also allows students to run a separate set of tests and self-assess their submissions.

Autotesting consists of a client component integrated into MarkUs, and a standalone server component.
Jobs are enqueued using the gem Resque with a first in first out strategy, and served one at a time or concurrently.

## Install and run

### Client

The autotesting client requirements are already included in a MarkUs installation.

### Server

To install the autotesting server, run the `install.sh` script from the top level directory.
You must pass a directory, which will be used as the working directory.
You may also pass the names of a user to run the server, a user to run the testers, and the number of concurrent
requests accepted (see [Appendix A](#appendix-a:-installation-options) for the details).

The server will be installed and started, and a sample configuration for MarkUs will be generated as `markus_conf.rb`
(see [Appendix B](#appendix-b:-markus-configuration-options) for the details).

To stop and start the server, use the `stop_resque.sh` and `start_resque.sh` scripts under the `server` directory.

If you are a MarkUs developer, install the server with `install.sh /path_to_markus/data/dev/autotest/server`.

### Testers

Instructors can create and submit arbitrary scripts through MarkUs to run tests. The scripts must start with a shebang
line, and output results according to the specifications (see [Appendix C](#appendix-c:-test-scripts-output-format) for
the details).

Alternatively, we come with a set of ready-to-use testers for: python (https://github.com/ProjectAT/uam), java, sql,
jdbc, xquery. To install one of these testers, run the `install.sh` script in the respective tester directory.

If you use one of our testers, you should create a dedicated environment for each course (or even each assignment if you
want to). To do so, run the `create_test_env.sh` script under the `testers` directory, passing (in order) the working
directory of the autotesting server, the tester name (python|java|sql|jdbc|xquery), the python version you are using
(our testers are written in python, the environment needs to know which version you have available), the course name,
and the optional assignment name.

## Appendix A: Installation options

Let **X** be the user running `install.sh`, **S** the user passed with the *--server* option, **T** the user passed with
the *--tester* option.

1) **S** and **T** unspecified:

   **X** is used as **S** and **T**, the tester directory and queue have a default name, the *--workers* option is
   ignored: local file system copy of student files, student code executed as user **X**;

2) **S** specified, **T** unspecified:

   **S** is used as **S** and **T**, the tester directory and queue have a default name, the *--workers* option is
   ignored: authenticated scp copy of student files, student code executed as user **S**;

3) **S** unspecified, **T** specified:

   **X** is used as **S**, **T** is used, the tester directory and queue are named **T**, the *--workers n* option
   adds concurrency by making n **T** users, directories and queues (named **T0**..**Tn-1**): local file system copy of
   student files, student code executed as user(s) **T** (**X** does `sudo -u T`);

4) **S** and **T** specified and equal:

   same as 2;

5) **S** and **T** specified and different:

   **S** and **T** are used, the tester directory and queue are named **T**, the *--workers n* option adds concurrency
   by making n **T** users, directories and queues (named **T0**..**Tn-1**): authenticated scp copy of student files,
   student code executed as user(s) **T** (**S** does `sudo -u T`).

NOTE: **X** can be == **S** and/or **T**, but it is different than leaving **S** and/or **T** unspecified.

## Appendix B: MarkUs configuration options

##### AUTOTEST_ON
Enables autotesting.

##### AUTOTEST_STUDENT_TESTS_ON
Allows the instructor to let students run tests on their own.

##### AUTOTEST_STUDENT_TESTS_BUFFER_TIME
With student tests enabled, a student can't request a new test if they already have a test in execution, to prevent
denial of service. If the test script fails unexpectedly and does not return a result, a student would effectively be
locked out from further testing.
This is the amount of time after which a student can request a new test anyway.

(Ignored if **AUTOTEST_STUDENT_TESTS_ON** is *false*)

##### AUTOTEST_CLIENT_DIR
The directory where the test files for assignments are stored.  
The user running MarkUs must be able to write here.

##### AUTOTEST_RUN_QUEUE
The name of the Resque queue where the test files wait to be copied to the server.

##### AUTOTEST_SERVER_HOST
The server host name.

(Use *localhost* if the server runs on the same machine)

##### AUTOTEST_SERVER_FILES_USERNAME
The server user to copy the test and student files over.
SSH passwordless login must be set up for the user running MarkUs to connect with this user on the server.
Multiple MarkUses can use the same user.

(Can be *nil*, forcing **AUTOTEST_SERVER_HOST** to be *localhost* and local file system copy to be used)

##### AUTOTEST_SERVER_FILES_DIR
The directory on the server where test and student files are copied.
Multiple MarkUses can use the same directory.

##### AUTOTEST_SERVER_RESULTS_DIR
The directory on the server where test results are logged.
Multiple MarkUses can use the same directory.

##### AUTOTEST_SERVER_TESTS
An array of hashes with the server testers configurations. Each hash is a concurrent tester on the server running the
tests, and has the following keys:
* **user**: The server user to run the tests
  (Can be *nil* if there is no dedicated user);
* **dir**: The directory on the server where tests run;
* **queue**: The name of the Resque server queue where tests wait to be executed.

These settings must be different among concurrent testers, or they will interfere with each other.

## Appendix C: Test scripts output format

The test scripts the instructors upload and run on the server must print the following on stdout for each test:

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

Stdout is sent back to MarkUs and logged under **AUTOTEST_SERVER_RESULTS_DIR** in files named `output.txt`.
Stderr is sent back too and logged under **AUTOTEST_SERVER_RESULTS_DIR** in files named `errors.txt`.

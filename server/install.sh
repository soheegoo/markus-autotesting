#!/usr/bin/env bash

# Installs the autotesting server and optionally the available testers.
# Run it as user ATE_SERVER_FILES_USERNAME.

usage() {
	echo
	echo "**USAGE**"
	echo
	echo "$0 [-u TEST_USER] [-q QUEUE] [-t TESTERS]"
	echo
	echo "**OPTIONS**"
	echo
	echo "-q QUEUE, --queue QUEUE: [optional, defaults to \"ate_tests\"] The name of the test server queue."
	echo "-t TESTERS, --testers TESTERS: [optional] A comma-separated list of tester names to install together with the test server."
	echo "-h, --help: [optional] Prints this help."
	echo
	echo "**EXAMPLES**"
	echo
	echo "./install.sh"
	echo "Installs a production-test instance of MarkUs autotester, using the code from the master branch of the official MarkUs autotester repository."
	echo
	echo "./install.sh -g adisandro/some-branch"
	echo "Installs a production-test instance of MarkUs autotester, using the code from the some-branch branch of adisandro's MarkUs autotester repository."
}

# check correct arguments
TESTERS=
TESTUSER=atetest
QUEUENAME=ate_tests
while [ "$1" != "" ]; do
	case "$1" in
		-u | --test-user )
			shift
			TESTUSER="$1"
			;;
		-q | --queue )
			shift
			QUEUENAME="$1"
			;;
		-t | --testers )
			shift
			IFS=',' read -a TESTERS <<< "$1"
			;;
		-h | --help )
			usage
			exit
			;;
		* )
			usage >&2
			exit 1
	esac
	shift
done
SERVNAME=ateserver
FILESDIR=../files
TESTSDIR=../tests
RESULTSDIR=../test_runs
VENVSDIR=../venvs

# kill the previous server, if any
echo "Killing previous Resque workers"
kill -QUIT `pgrep -f resque` || { echo "No previous Resque worker found, no need to kill them"; }
# install dependencies and run the test server
mkdir -p ${FILESDIR}
mkdir -p ${RESULTSDIR}
mkdir -p ${VENVSDIR}
sudo -u ${TESTUSER} -- mkdir -p ${TESTSDIR}
bundle install --deployment
TERM_CHILD=1 BACKGROUND=yes QUEUES=${QUEUENAME} bundle exec rake resque:work
echo "Resque started listening for queue ${QUEUENAME}"
# install testers, if any
cd ..
for i in "${!TESTERS[@]}"; do
	TESTERNAME=${TESTERS[$i]}
	if cd ${TESTERNAME}; then
		./install.sh $(pwd)
		cd ..
	fi
done
# TODO create update_install too?

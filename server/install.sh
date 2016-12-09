#!/usr/bin/env bash

# Installs the autotesting server and optionally the available testers.
# Run it as user ATE_SERVER_FILES_USERNAME.

usage() {
	echo
	echo "**USAGE**"
	echo
	echo "$0 [-q QUEUE] [-t TESTERS]"
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
	echo "Installs the MarkUs autotester, using a queue named \"ate_tests\"."
	echo
	echo "./install.sh -q some_queue -t uam"
	echo "Installs the MarkUs autotester, using a queue named \"some_queue\", and the \"uam\" tester."
}

# check correct arguments
QUEUENAME=ate_tests
TESTERS=()
while [ "$1" != "" ]; do
	case "$1" in
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
FILESDIR=files
TESTSDIR=tests
RESULTSDIR=test_runs
VENVSDIR=venvs
TESTERSDIR=testers

# kill the previous server, if any
echo "Killing previous Resque workers"
kill -QUIT `pgrep -f resque` || { echo "No previous Resque worker found, no need to kill them"; }
# install dependencies and run the test server
bundle install --deployment
TERM_CHILD=1 BACKGROUND=yes QUEUES=${QUEUENAME} bundle exec rake resque:work
echo "Resque started listening for queue ${QUEUENAME}"
# create basic dirs and install testers
cd ..
mkdir -p ${FILESDIR}
mkdir -p ${RESULTSDIR}
mkdir -p ${VENVSDIR}
mkdir -p ${TESTSDIR}
chmod g+rwx,o-rwx ${TESTSDIR}
cd ${TESTERSDIR}
for i in "${!TESTERS[@]}"; do
	TESTERNAME=${TESTERS[$i]}
	if cd ${TESTERNAME}; then
		./install.sh $(pwd)
		cd ..
	fi
done
echo "You should now do: sudo chown TEST_USER:SERVER_USER ${TESTSDIR}"

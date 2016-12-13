#!/usr/bin/env bash

# Deploys the autotesting server and optionally the available testers.
# (run this as a super user, e.g. sudo install.sh)

usage() {
	echo
	echo "**USAGE**"
	echo
	echo "$0 [-q QUEUE] [-s SERVER_USER] [-t TEST_USER] [-d WORKING_DIR] [-T TESTERS]"
	echo
	echo "**OPTIONS**"
	echo
	echo "-q QUEUE, --queue QUEUE: [optional, defaults to \"ate_tests\"] The name of the test server queue."
	echo "-s SERVER_USER, --user-server SERVER_USER: [optional, defaults to \"ateserver\"] The user that runs the test server."
	echo "-t TEST_USER, --user-test TEST_USER: [optional, defaults to \"atetest\"] The user that runs the student code being tested."
	echo "-d WORKING_DIR, --dir WORKING_DIR: [optional, defaults to \"../\"] The name of the test server working directory."
	echo "-T TESTERS, --testers TESTERS: [optional] A comma-separated list of tester names to install together with the test server."
	echo "-h, --help: [optional] Prints this help."
	echo
	echo "**EXAMPLES**"
	echo
	echo "./install.sh"
	echo "Installs the MarkUs autotester, using the queue \"ate_tests\", server user \"ateserver\" and test user \"atetest\"."
	echo
	echo "./install.sh -q some_queue -s server_user -t test_user -d /some/dir -T uam"
	echo "Installs the MarkUs autotester, using the queue \"some_queue\", server user \"server_user\", test user \"test_user\", working directory \"/some/dir\", and the \"uam\" tester."
}

QUEUENAME=ate_tests
USERSERVER=ateserver
USERTEST=atetest
WORKINGDIR=..
TESTERS=()
while [ "$1" != "" ]; do
	case "$1" in
		-q | --queue )
			shift
			QUEUENAME="$1"
			;;
		-s | --server-user )
			shift
			USERSERVER="$1"
			;;
		-t | --test-user )
			shift
			USERTEST="$1"
			;;
		-d | --dir )
			shift
			WORKINGDIR="$1"
			;;
		-T | --testers )
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

SERVERDIR=server
TESTERSDIR=testers
FILESDIR=${WORKINGDIR}/files
TESTSDIR=${WORKINGDIR}/tests
RESULTSDIR=${WORKINGDIR}/test_runs
VENVSDIR=${WORKINGDIR}/venvs

echo "[AUTOTEST] Killing running Resque workers"
kill -QUIT `pgrep -f resque` || { echo "[AUTOTEST] No running Resque worker found, no need to kill them"; }
cd ${SERVERDIR}
echo "[AUTOTEST] Installing dependencies"
bundle install --deployment
sudo -u ${USERSERVER} -- TERM_CHILD=1 BACKGROUND=yes QUEUES=${QUEUENAME} bundle exec rake resque:work
echo "[AUTOTEST] Resque started for autotesting server"
cd ..
sudo -u ${USERSERVER} <<-EOF
	mkdir -p ${FILESDIR}
	mkdir -p ${RESULTSDIR}
	chmod u=rwx,go= ${RESULTSDIR}
	mkdir -p ${VENVSDIR}
	mkdir -p ${TESTSDIR}
	chmod ug=rwx,o= ${TESTSDIR}
EOF
chown ${USERTEST}:${USERSERVER} ${TESTSDIR}
for i in "${!TESTERS[@]}"; do
	TESTERNAME=${TESTERS[$i]}
	if cd ${TESTERSDIR}/${TESTERNAME}; then
		echo "[AUTOTEST] Installing tester ${TESTERNAME}"
		./install.sh $(pwd)
		cd ../../
	fi
done

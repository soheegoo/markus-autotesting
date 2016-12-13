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
SHORT=q:s:t:d:T:h
LONG=queue:,user-server:,user-test:,dir:,testers:,help
PARSED=`getopt -o ${SHORT} -l ${LONG} -n "$0" -- "$@"`
eval set -- "${PARSED}"

QUEUENAME=ate_tests
USERSERVER=ateserver
USERTEST=atetest
WORKINGDIR=..
TESTERS=()
while true; do
	case "$1" in
		-q | --queue )
			QUEUENAME="$2"
			shift 2
			;;
		-s | --server-user )
			USERSERVER="$2"
			shift 2
			;;
		-t | --test-user )
			USERTEST="$2"
			shift 2
			;;
		-d | --dir )
			WORKINGDIR="$2"
			shift 2
			;;
		-T | --testers )
			IFS=',' read -a TESTERS <<< "$2"
			shift 2
			;;
		-h | --help )
			usage
			exit
			;;
		-- )
			shift
			break
			;;
		* )
			usage >&2
			exit 1
	esac
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

#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo usage: $0 xquery_dir
	exit 1
fi

XQDIR=$1
SOLUTIONDIR=${XQDIR}/solution
DATASETDIR=${SOLUTIONDIR}/datasets
QUERYDIR=${SOLUTIONDIR}/queries
SCHEMADIR=${SOLUTIONDIR}/schemas

echo '[XQUERY] Installing system packages'
sudo apt-get install python3 galax libxml2-utils
echo '[XQUERY] Creating solutions'
chmod go-rwx ${QUERYDIR}
SCHEMAS=""
for queryfile in ${QUERYDIR}/*; do
	queryname=$(basename -s .xq ${queryfile})
	# find corresponding output schema and root tag
	schemafile=$(find ${SCHEMADIR} -type f -name all*.dtd)
	if [[ ! "${schemafile}" ]]; then
		schemafile=$(find ${SCHEMADIR} -type f -name ${queryname}*.dtd)
	fi
	schema=$(basename ${schemafile})
	roottag=$(head -n 2 ${schemafile} | tail -n 1 | awk '{print $2;}')
	SCHEMAS="'${queryname}.xq': ('${schema}', '${roottag}'), ${SCHEMAS}"
	for datafile in ${DATASETDIR}/*; do
		dataset=$(basename ${datafile})
		dataname=${dataset%.*} # shortest trailing matching pattern deleted == until the last '.'
		dataext=${dataset##*.} # longest leading matching pattern deleted == from the last '.'
		if [[ ${dataext} == dtd ]]; then # discard dataset dtds
			continue
		fi
		if [[ ${dataname} != ${queryname}* && ${dataname} != all* ]]; then # discard datasets not used for this query
			continue
		fi
		echo "[XQUERY] Creating solution '${queryname}' for data '${dataname}'"
		echo '<?xml version="1.0" encoding="UTF-8"?>' >| /tmp/ate.xml
		echo "<!DOCTYPE ${roottag} SYSTEM \"${schema}\">" >> /tmp/ate.xml
		galax-run -doc dataset=${datafile} ${queryfile} >> /tmp/ate.xml
		xmllint --format /tmp/ate.xml >| ${SOLUTIONDIR}/${queryname}+${dataname}.xml
	done
done
rm /tmp/ate.xml
echo '[XQUERY] Updating python config file'
echo "PATH_TO_SOLUTION = '${SOLUTIONDIR}'" >| server/markus_xquery_config.py
echo "SCHEMAS = {${SCHEMAS}}" >> server/markus_xquery_config.py

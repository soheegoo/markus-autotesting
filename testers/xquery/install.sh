#!/usr/bin/env bash

if [ $# -ne 1 ]; then
	echo usage: $0 xquery_dir
	exit 1
fi

XQDIR=$1
SPECS=${XQDIR}/specs.json
SOLUTIONDIR=${XQDIR}/solution
DATASETDIR=${SOLUTIONDIR}/datasets
QUERYDIR=${SOLUTIONDIR}/queries
SCHEMADIR=${SOLUTIONDIR}/schemas

echo '[XQUERY] Installing system packages'
sudo apt-get install python3 galax libxml2-utils
echo '[XQUERY] Creating solutions'
chmod go-rwx ${QUERYDIR}
jq -r '.matrix | keys[]' ${SPECS} | while read queryfile; do
	queryname=$(basename -s .xq ${queryfile})
	jq -r --arg q ${queryfile} '.matrix | .[$q] | keys | map(select(. != "extra"))[]' ${SPECS} | while read datafile; do
		schema=$(jq -r --arg q ${queryfile} '.matrix | .[$q] | .extra | .out_schema' ${SPECS})
		roottag=$(jq -r --arg q ${queryfile} '.matrix | .[$q] | .extra | .out_root_tag' ${SPECS})
		dataname=""
		galaxarg=""
		if [[ ${datafile} == *,* ]]; then # multiple datasets for the same query, comma-separated
			IFS=',' read -a datafiles <<< ${datafile}
			for i in ${!datafiles[@]}; do
				multidatafile=${datafiles[${i}]}
				datanamei=$(basename -s .xml ${multidatafile})
				galaxargi="-doc dataset${i}=${DATASETDIR}/${multidatafile}"
				if [[ ${i} > 0 ]]; then
					dataname="${dataname},${datanamei}"
					galaxarg="${galaxarg} ${galaxargi}"
				else
					dataname="${datanamei}"
					galaxarg="${galaxargi}"
				fi
			done
		else
			dataname=$(basename -s .xml ${datafile})
			galaxarg="-doc dataset0=${DATASETDIR}/${datafile}"
		fi
		echo "[XQUERY] Creating solution '${queryname}' for data '${dataname}'"
		echo '<?xml version="1.0" encoding="UTF-8"?>' >| /tmp/ate.xml
		echo "<!DOCTYPE ${roottag} SYSTEM \"${SCHEMADIR}/${schema}\">" >> /tmp/ate.xml
		galax-run ${galaxarg} ${QUERYDIR}/${queryfile} >> /tmp/ate.xml
		xmllint --format /tmp/ate.xml >| ${SOLUTIONDIR}/${queryname}+${dataname}.xml
	done
done
rm /tmp/ate.xml
echo '[XQUERY] Updating json specs file'
sed -i -e "s#/path/to/solution#${SOLUTIONDIR}#g" specs.json

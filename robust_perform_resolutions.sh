#!/bin/bash

RRTYPE=mx
NAMESERVER=8.8.8.8

X="$1"

if [ ! -e "$X" ] 
then
        echo "$X does not exist"
        exit 1
fi

echo "[`date`] About to resolve $(cat $X | wc -l | awk '{print $1}') domains ($X) ..."
cat $X | adnshost --asynch --config "nameserver $NAMESERVER" --type "$RRTYPE" --pipe ----addr-ipv4-only > "results/adnshost-$X.txt"

inputs=$(cat $X | wc -l | awk '{print $1}')
resolutions=$(grep -c -E '^\d+ \d+' results/adnshost-$X.txt)

if [ "$inputs" == "$resolutions" ]
then
        echo "[`date`] Completed resolutions on $X"
        mv $X done/
else
        echo "[`date`] Error resolving $X: $inputs != $resolutions"
        mv $X errors/
fi

grep -hE '^\d+ \d+ (temp|remote)fail' results/adnshost-$X.txt | awk '{print $6}' > retries1-$X

if [ -s  "retries1-$X" ] 
then
	echo "[`date`] About to retry $(cat retries1-$X | wc -l | awk '{print $1}') failed domains ($X retries 1) ..."
	cat retries1-$X | adnshost --asynch --config "nameserver $NAMESERVER" --type "$RRTYPE" --pipe ----addr-ipv4-only > "results/adnshost-retries1-$X.txt"
	mv retries1-$X done/

	grep -hE '^\d+ \d+ (temp|remote)fail' results/adnshost-retries1-$X.txt | awk '{print $6}' > retries2-$X
	if [ -s "retries2-$X" ]
	then
		echo "[`date`] About to retry $(cat retries2-$X | wc -l | awk '{print $1}') failed domains ($X retries 2) ..."
		cat retries2-$X | adnshost --asynch --config "nameserver $NAMESERVER" --type "$RRTYPE" --pipe ----addr-ipv4-only > "results/adnshost-retries2-$X.txt"
		mv retries2-$X done/

		grep -hE '^\d+ \d+ (temp|remote)fail' results/adnshost-retries2-$X.txt | awk '{print $6}' > retries3-$X
		if [ -s "retries3-$X" ]
		then
			echo "[`date`] About to retry $(cat retries3-$X | wc -l | awk '{print $1}') failed domains ($X retries 3) ..."
			cat retries3-$X | adnshost --asynch --config "nameserver $NAMESERVER" --type "$RRTYPE" --pipe ----addr-ipv4-only > "results/adnshost-retries3-$X.txt"
			mv retries3-$X done/
		fi
	fi
fi
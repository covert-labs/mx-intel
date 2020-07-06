#!/bin/bash

#
# Simple way to parallelize dig lookups
#  1. splits input file
#  2. uses xargs against splits to launch separate dig processes
#  3. combines the output from dig into the main output file.
#

NUM_PROC=10

START_DIR=`pwd`
RRTYPE="$1"
NAMESERVER="$2"
INPUT=`./get_abs_path.sh "$3"`
OUTPUT=`./get_abs_path.sh "$4"`

NUM_LINES=$(wc -l "$INPUT" | awk '{print $1}')
LINES_PER_PROC=$[$NUM_LINES / $NUM_PROC]

TMP_DIR=`mktemp -d`
cd "$TMP_DIR"

# gsplit check for MacOS since Mac's native "split" doesn't the options below.
SPLIT=$(which gsplit)
if [ -z "$SPLIT" ]
then
	SPLIT=$(which split)
fi

"$SPLIT" -l "$LINES_PER_PROC" -d -a 4 "$INPUT" dig_split_
ls dig_split_* | xargs -I DIG_INPUT -n 1 -P "$NUM_PROC" "$START_DIR/dig_wrapper.sh" "$RRTYPE" "$NAMESERVER" DIG_INPUT output-DIG_INPUT
cat output-* > "$OUTPUT"
cd $START_DIR
rm -rf "$TMP_DIR"

#!/bin/bash

RRTYPE="$1"
NAMESERVER="$2"
INPUT_FILE="$3"
OUTPUT_FILE="$4"

exec dig "$RRTYPE" "@${NAMESERVER}" +noclass +nottlid +noquestion +nostats -f "$INPUT_FILE" > "$OUTPUT_FILE"

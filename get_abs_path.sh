#! /bin/sh
echo "$(cd "$(dirname "$1")"; pwd)/$(basename "$1")"

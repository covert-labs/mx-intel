#!/usr/bin/python

import sys
import json

domains_file = sys.argv[1]
json_records_file = sys.argv[2]

domains = set([domain.strip() for domain in open(domains_file)])

for line in open(json_records_file):
    line = line.strip()
    rec = json.loads(line)
    if rec['domain'].strip('.') in domains:
        print(line)

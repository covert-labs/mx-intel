#!/usr/bin/python

import sys
import json
import sys
import os
import subprocess
import re
import collections


if __name__ == '__main__':
    main_results_file = sys.argv[1]
    output_file = sys.argv[2]

    print(f'Reading from {main_results_file} ...')
    with open(main_results_file, 'r') as main_results:
        all_results = [json.loads(line) for line in main_results]

        results_map = collections.defaultdict(list)
        for rec in all_results:
            rec['domain'] = rec['domain'].strip('.') # some of my original "dig" based records have a trailing dot.
            results_map[rec['domain']].append(rec)
        
        includes = collections.defaultdict(set)
        ips = collections.defaultdict(set)

        for domain, lst in results_map.items():
            for rec in lst:
                for ip in rec.get('ip4', []):
                    ips[domain].add(ip)
                for include in rec.get('include', []):
                    includes[domain].add(include)

                    done = set()
                    done.add(domain)
                    more_include_records = results_map.get(include, [])
                    while len(more_include_records) > 0:
                        for rec in more_include_records:
                            for ip in rec.get('ip4', []):
                                ips[domain].add(ip)
                            more_include_records = []
                            for include_domain in rec.get('include', []):
                                if include_domain not in done:
                                    done.add(include_domain)
                                    more_include_records.extend(results_map.get(include_domain, []))

        print(f'Writing to {output_file} ...')
        with open(output_file, 'w') as outf:
            all_domains  = set(list(includes.keys()) + list(ips.keys()))
            for domain in all_domains:
                rec = {
                    'domain': domain,
                    'includes': list(includes[domain]),
                    'ips': list(ips[domain]),
                }
                print(json.dumps(rec), file = outf)
        

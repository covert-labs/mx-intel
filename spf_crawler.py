#!/usr/bin/python

import sys
import json
import sys
import os
import subprocess
import re
import collections

nameserver = '8.8.8.8'

def perform_dns_queries(input_filename, output_filename, error_filename, rrtype='txt'):
    command = [
        'adnshost', 
        '--qc-query',
        '--asynch',
        '--config', f'nameserver {nameserver}', 
        '--type', rrtype.lower(),
        '--pipe'
    ]

    print(f'About to run adnshost (rrtype={rrtype}) on {input_filename} and write to {output_filename} ...')
    with open(input_filename, 'r') as inputs, open(output_filename, 'w') as outputs, open(error_filename, 'a') as errors:
        cmd = subprocess.Popen(
            command,
            stdin=inputs,
            stdout=outputs,
            stderr=errors
        )
        cmd.wait()

def perform_dns_queries_dig(input_filename, output_filename, error_filename, rrtype='txt'):
    command = [
        './parallel_dig.sh',
        rrtype.upper(),
        nameserver, 
        input_filename,
        output_filename
    ]

    print(f'About to run parallel_dig.sh (rrtype={rrtype}) on {input_filename} and write to {output_filename} ...')
    with open(error_filename, 'a') as errors:
        cmd = subprocess.Popen(
            command,
            stderr=errors
        )
        cmd.wait()

def parse_line(line):
    '''
    Parses the TXT record and extracts SPF details.  Returns None for non-SPF records
    '''
    m = re.search(r'^(?P<domain>\S+?)\.?\s+TXT\s+"(?P<txt>.*)"$', line)
    if m:
        result =  m.groupdict()
        result['domain'] = result['domain'].strip('.')

        # seeing some weird embedded " " in the middle of the some of the records.  Example (from dig for amica.com)
        # "v=spf1 ip4:158.228.129.79 ip4:158.228.200.70 ip4:67.217.81.1 ip4:23.23.239.161 ip4:174.129.15.10 ip4:35.176.132.251 ip4:52.60.115.116 ip4:67.217.81.25 include:spf-000f3401.pphosted.com include:spfa.amica.com include:spfb.amica.com include:mailgun.org incl" "ude:archer.rsa.com include:spf.protection.outlook.com ~all"
        result['txt'] = result['txt'].replace('" "', '') 

        spf_data = collections.defaultdict(list)
        if re.search(r'^v=spf[1-3]', result['txt']):
            prefixes = ['ip4', 'ip6', 'include', 'redirect', 'a']
            for part in result['txt'].split(' '):
                nameval = part.split(':', 2)
                nameval[0] = nameval[0].strip('+?') # remove the modifiers for Pass and Neutral
                if nameval[0] in prefixes and len(nameval) > 1:
                    spf_data[nameval[0]].append(nameval[1])
            result.update(spf_data)
            return result
    return None

def parse_status(line):
    m = re.search(r'^(\d+) (\d+) (?P<status>\S+) (\d+) (?P<substatus>\S+) (?P<domain>\S+) \S+ "(?P<message>.*)"$', line)
    if m:
        return  m.groupdict()
    return None

def parse_results(input_filename):
    results = []
    statuses = []
    with open(input_filename) as inputs:
        for line in inputs:
            line = line.strip()
            rec = parse_line(line)
            if rec:
                results.append(rec)
            else:
                status = parse_status(line)
                if status:
                    statuses.append(status)
                #else:
                    #print('NO MATCH:', line)
    return results, statuses

if __name__ == '__main__':

    max_attempts = 5
    output_dir = 'spf-results'
    inputfile = sys.argv[1]

    run_name = os.path.basename(inputfile).replace('.txt', '')
    outputsfile = f'{output_dir}/{run_name}-outputs.txt'
    errorsfile = f'{output_dir}/{run_name}-errors.txt'
    main_results_file = f'{output_dir}/{run_name}-all.json'
    attempts = 0
    done = set()
    retries = collections.Counter()

    with open(main_results_file, 'w') as main_results:
        while True:
            perform_dns_queries_dig(
                inputfile,
                outputsfile,
                errorsfile
            )
            attempts += 1

            new_domains_a = set()
            new_domains = set()
            results, statuses = parse_results(outputsfile)
            
            for rec in results:
                print(json.dumps(rec), file = main_results)

                done.add(rec['domain'])
                for domain in rec.get('include', []):
                    if domain not in done:
                        new_domains.add(domain)
                        done.add(domain)
                for domain in rec.get('redirect', []):
                    if domain not in done:
                        new_domains.add(domain)
                        done.add(domain)
                for domain in rec.get('a', []):
                    if domain not in done:
                        new_domains_a.add(domain)
                        done.add(domain)
            print(f'found {len(new_domains)} new domains for SPF, and {len(new_domains_a)} for A lookups')

            status_counts = collections.Counter()
            for status in statuses:
                status_counts[status['status']] += 1

                if status['status'] in ('tempfail', 'remotefail',):
                    retries[status['domain']] += 1
                    if retries[status['domain']] <= max_attempts:
                        new_domains.add(status['domain'])
            print('status_counts:', status_counts)
            print(f'new domains + retries are {len(new_domains)} domains')

            if len(new_domains) > 0:
                inputfile = f'{output_dir}/{run_name}-inputs-{attempts}.txt'
                outputsfile = f'{output_dir}/{run_name}-outputs-{attempts}.txt'

                with open(inputfile, 'w') as newinputs:
                    print(f'Writing {len(new_domains)} into {inputfile} ...')
                    for domain in new_domains:
                        print(domain, file = newinputs)
            else:
                break
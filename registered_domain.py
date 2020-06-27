import tldextract
import sys

for line in sys.stdin:
    try:
        sld = tldextract.extract(line.strip()).registered_domain
        if sld:
            print(sld)
    except:
        pass
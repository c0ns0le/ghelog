#!/usr/bin/env python
# -*- mode: python -*-
#
import logging
from pprint import pprint
import json
import requests
import sys
import datetime

log = logging.getLogger(__name__)

# TODO: hostname

def get_index_name(indexname, es_timestamp):
    """Generate an index name for ES that enables data
    retention.
    The format is: "teamcity-year.month.day"
    """
    ts = time.strptime(es_timestamp, "%Y-%m-%dT%H:%M:%S")
    daystring = time.strftime("%Y.%m.%d", ts)
    fullname = "%s-%s" % (indexname, daystring)
    return fullname


def send_to_es(data, indexname="exceptions", documenttype="exceptions", es_url="http://localhost:9200"):
    args = {"url": es_url,
            "indexname": indexname,
            "documenttype": documenttype}
    es_url = "%(url)s/%(indexname)s/%(documenttype)s" % args
    jsondata = json.dumps(data, indent=2)
    requests.post(es_url, data=jsondata, timeout=10)



def exceptions_reader(row):
    data = json.loads(row)
    # created_at":"2014-10-16T10:41:44.870553Z
    data["@timestamp"] = data["created_at"][0:-5]
    del data["created_at"]
    data['hostname'] = sys.argv[1]
    send_to_es(data, "exceptions", "exceptions", es_url="http://awseu3-docker-a1.cb-elk.cloud.spotify.net:9200")

def audit_reader(row):
    (mon_str, day_str, tm_str, host, src, rest) = row.split(" ", 5)
    data = json.loads(rest)
    mon_lookup = {"jan":1, "feb":2, "mar":3, "apr":4, "may":5, "jun":6, "jul":7, "aug":8, "sep":9, "oct":10, "nov":11, "dec":12}
    month = mon_lookup[mon_str.lower()]
    data["@timestamp"] = "%.4d-%.2d-%.2dT%s.00" % (datetime.datetime.now().year, month, int(day_str), tm_str)
    data['hostname'] = host
    if 'cmdline' in data:
        data['cmd'] = data['cmdline'].split(' ')[0]
    send_to_es(data, "audit", "audit", es_url="http://awseu3-docker-a1.cb-elk.cloud.spotify.net:9200")

def main():
    logging.basicConfig()
    while True:
        row = sys.stdin.readline().strip()
        if not row:
            break
        try:
#            exceptions_reader(row)
            if row:
                audit_reader(row)
            print '.'
        except:
            log.exception("Failed with row: %s" % repr(row))

if __name__ == "__main__":
    main()

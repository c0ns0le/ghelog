#!/usr/bin/env python
# -*- mode: python -*-

import logging
from pprint import pprint
import json
import requests
import sys
import datetime
import Queue
import threading

log = logging.getLogger(__name__)
queue = Queue.Queue(500)

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

def worker():
    while True:
        arg = queue.get()
        requests.post(arg[0], data=arg[1], timeout=10)
        print ':'

[ threading.Thread(target=worker).start() for i in range(10)]

def send_to_es(data, indexname, documenttype, es_url):
    args = {"url": es_url,
            "indexname": indexname,
            "documenttype": documenttype}
    es_url = "%(url)s/%(indexname)s/%(documenttype)s" % args
    jsondata = json.dumps(data, indent=2)
    try:
        queue.put([es_url, jsondata], True)
    except:
        print "Failed, queue full"

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
    data['hostname'] = sys.argv[1]
    if 'cmdline' in data:
        data['cmd'] = data['cmdline'].split(' ')[0]
    send_to_es(data, "audit", "audit", es_url="http://awseu3-docker-a1.cb-elk.cloud.spotify.net:9200")


def parse_generic(row):
    data = {}
    while True:
        try:
            idx = row.index('=')
        except ValueError:
            return data
        key = row[0:idx].strip()
        row = row[idx+1:].strip()
        if row[0]=='"':
            split = row[1:].split('"', 1)
            value = split[0]
            try:
                row = split[1]
            except IndexError:
                row=''
        else:
            split = row.split(' ', 1)
            value = split[0]
            try:
                row = split[1]
            except IndexError:
                row=''

        data[key] = value


def get_reader(name):
    if name == 'audit':
        return audit_reader
    if name == 'exceptions':
        return exceptions_reader
    def reader(row):
        if not row.startswith('app'):
            return
        data = parse_generic(row)
        if 'now' in data:
            data["@timestamp"] = data['now'][0:-1] + ".00"
            del data['now']
        data['hostname'] = sys.argv[1]
        print data
#        send_to_es(data, name, name, es_url="http://awseu3-docker-a1.cb-elk.cloud.spotify.net:9200")
    return reader


def main():
    logging.basicConfig()
    reader = get_reader(sys.argv[2])
    while True:
        row = sys.stdin.readline()
        if not row:
            break
        row = row.strip()
        try:
            if row:
                reader(row)
            print '.'
        except:
            log.exception("Failed with row: %s" % repr(row))


if __name__ == "__main__":
    main()

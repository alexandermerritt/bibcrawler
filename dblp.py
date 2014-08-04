#! /usr/bin/env python
# -*- encoding: utf-8 -*-
# author: Alexander Merritt, merritt.alex@gatech.edu
# fetches ACM bibtex entries for a conference, workshop, or journal
import re
import httplib
import sys
import xml.etree.ElementTree as ET
import os.path
import time

siteurl = 'dblp.uni-trier.de'
confbase = '/db/conf/'
confnames = [ 'eurosys', 'osdi', 'sosp', 'vldb', 'gpgpu',
              'nsdi', 'usenix', 'sc', 'isca', 'socc',
              'hpca', 'ccgrid', 'xsede',
            ]

url_re = re.compile('http://[a-zA-Z0-9./~\-]+')

def status(*objs):
    s = ''
    for i in objs:
        s += str(i) + ' '
    sys.stderr.write('> ' + s + '\n')

def error(*objs):
    s = ''
    for i in objs:
        s += str(i) + ' '
    sys.stderr.write('> Error: ' + s + '\n')

def stripURL(url):
    url = url.lstrip('http://')
    url = url[ url.find('/') : ]
    return url

# HTTP GET and return page body
def fetch(siteurl, loc):
    ret = None

    status('GET', siteurl, loc)

    conn = httplib.HTTPConnection(siteurl)
    conn.request(method='GET', url=loc)
    resp = conn.getresponse()
    stat = resp.status

    if stat == 200:
        status('got OK')
        ret = resp.read()
    elif stat == 301 or stat == 302:
        status('got REDIRECT')
        loc = resp.getheader('location')
        # assumption: redirect within same site
        ret = fetch(siteurl, stripURL(loc))
    else:
        error('got', str(resp.status), str(resp.reason),
                'for', siteurl, loc)
        if stat == 403:
            error(resp.read())

    time.sleep(1)

    conn.close()
    return ret

def extract_pre(html):
    pre = html

    start = pre.find('<pre>') + 5
    end = pre.find('</pre>')
    pre = pre[ start : end ]

    # dblp inserts some stupid href in the citation name
    start = pre.find('<a')
    end = pre.find('a>:') + 3
    pre = pre[ : start ] + pre[ end : ]

    return pre

def processConf(confURL):
    #root = ET.fromstring('<?xml version="1.0"?><dblp></dblp>')
    filename = os.path.basename(confURL).split('.')[0] + '.bib'

    # no updates exist once proceedings have been fetched already
    if os.path.exists(filename):
        status('Skipping', confURL)
        return
    status('Fetching', confURL)
    out = ''

    page = fetch(siteurl, confURL)
    if not page:
        error('fetching conf at', confURL)
        sys.exit(1)

    bibURLs = set()
    for url in url_re.findall(page):
        if '/rec/bibtex/conf/' not in url:
            continue
        if url.endswith('.xml'):
            continue
        bibURLs.add(stripURL(url))

    for bibURL in bibURLs:
        html = fetch(siteurl, bibURL)
        out += extract_pre(html) + '\n'

    f = open(filename, 'w')
    f.write(out)
    f.close()
    status('wrote bibtex of', confURL, 'to', filename)

def processAll():
    for confname in confnames:
        status('Processing', confname)
        page = fetch(siteurl, confbase + confname + '/')
        if not page:
            error('fetch root page for', confname)
            sys.exit(1)

        urls = url_re.findall(page)
        if len(urls) == 0:
            error('no urls found in listing for', confname)
            sys.exit(1)

        sub = confbase + confname
        confURLs = set()
        for url in urls:
            if sub in url:
                confURLs.add( stripURL(url) )
        
        for url in confURLs:
            processConf(url)

# --------- 8< -----------
processAll()


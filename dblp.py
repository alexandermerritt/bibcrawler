#! /usr/bin/env python2.7
# -*- coding: utf-8 -*-
# author: Alexander Merritt, merritt.alex@gatech.edu
# fetches ACM bibtex entries for a conference, workshop, or journal
import re
import httplib
import sys
import xml.etree.ElementTree as ET
import os.path

siteurl = 'dblp.uni-trier.de'
confbase = '/db/conf/'
confname = 'eurosys'

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

def fetch(siteurl, loc):
    ret = None

    status('GET', siteurl, loc)

    conn = httplib.HTTPConnection(siteurl)
    conn.request('GET', loc)
    resp = conn.getresponse()
    stat = resp.status

    if stat == 200:
        status('OK')
        ret = resp.read()
    elif stat == 301 or stat == 302:
        status('REDIRECT')
        loc = resp.getheader('location')
        # assumption: redirect within same site
        ret = fetch(siteurl, stripURL(loc))
    else:
        error(str(resp.status), str(resp.reason))
        if stat == 403:
            error(resp.read())

    conn.close()
    return ret

# list of all conf instances
page = fetch(siteurl, confbase + confname)
if not page:
    error('fetching root page')
    sys.exit(1)

urls = url_re.findall(page)
if len(urls) == 0:
    error('conf url has no embedded urls')
    sys.exit(1)

allConfURLs = set()
for url in url_re.findall(page):
    sub = confbase + confname
    if sub in url:
        allConfURLs.add(stripURL(url))

for confURL in allConfURLs:
    root = ET.fromstring('<?xml version="1.0"?><dblp></dblp>')
    filename = os.path.basename(confURL).split('.')[0] + '.xml'
    if os.path.exists(filename):
        continue

    page = fetch(siteurl, confURL)
    if not page:
        error('fetching conf url')
        sys.exit(1)
    bibURLs = set()
    for url in url_re.findall(page):
        if '/rec/bibtex/conf/' not in url:
            continue
        if confname not in url:
            continue
        if not url.endswith('.xml'):
            continue
        bibURLs.add(stripURL(url))
    for bibURL in bibURLs:
        bibXML = fetch(siteurl, bibURL)
        tree = ET.fromstring(bibXML)
        for child in tree:
            root.append(child)

    tree = ET.ElementTree(root)
    tree.write(filename)


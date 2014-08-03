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
    conn.request('GET', loc)
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

    conn.close()
    return ret

def processConf(confURL):
    root = ET.fromstring('<?xml version="1.0"?><dblp></dblp>')
    filename = os.path.basename(confURL).split('.')[0] + '.xml'

    # no updates exist once proceedings have been fetched already
    if os.path.exists(filename):
        status('Skipping', confURL)
        return
    status('Fetching', confURL)

    page = fetch(siteurl, confURL)
    if not page:
        error('fetching conf at', confURL)
        sys.exit(1)

    bibURLs = set()
    for url in url_re.findall(page):
        if '/rec/bibtex/conf/' not in url:
            continue
        if not url.endswith('.xml'):
            continue
        bibURLs.add(stripURL(url))

    for bibURL in bibURLs:
        bibXML = fetch(siteurl, bibURL)
        tree = ET.fromstring(bibXML)
        for child in tree: # top-level is <dblp></dblp>
            root.append(child)

    tree = ET.ElementTree(root)
    tree.write(filename)
    status('wrote bib xmls of', confURL, 'to', filename)

def processAll():
    for confname in confnames:
        status('Processing', confname)
        page = fetch(siteurl, confbase + confname)
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


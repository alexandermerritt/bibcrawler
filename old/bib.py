#! /usr/bin/env python2.7
# -*- coding: utf-8 -*-
# author: Alexander Merritt, merritt.alex@gatech.edu
# fetches ACM bibtex entries for a conference, workshop, or journal
import re
import httplib
import sys
import time
import random

sys.path.append('/Users/alex/src/python-libs')
import html5lib

cit_regex = re.compile('href="(citation.cfm[a-zA-Z0-9&.=?]+)"')
tex_regex = re.compile('exportformats.cfm\?id=[0-9]+&expformat=bibtex')

acm_conn = httplib.HTTPConnection('dl.acm.org')
random.seed(acm_conn)

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

def fetch(loc, isRedirect = False):
    ret = None

    if loc.find('http:') == 0: # full url
        if loc.find('dl.acm.org/') > 0:
            loc = loc.split('dl.acm.org/')[1]
        else:
            error('redirect to outside acm')
            sys.exit(1)

    acm_conn.request('GET', '/' + loc)
    resp = acm_conn.getresponse()
    stat = resp.status

    if stat == 200:
        status('OK')
        ret = resp.read()
    elif stat == 301 or stat == 302:
        status('REDIRECT')
        loc = resp.getheader('location')
        # assumption: redirect is bound to acm.org
        ret = fetch(loc, True)
    else:
        error(str(resp.status), str(resp.reason))
        if stat == 403:
            error(resp.read())

    # pretend to be human so dl.acm doesn't block us
    if not isRedirect:
        t = random.randint(1,4)
        status('human pause', str(t))
        time.sleep(t)

    return ret

def extract_pre(html):
    doc = html5lib.parse(html)
    n = doc
    for child in n:
        if child.tag.endswith('body'):
            n = child
            break
    for child in n:
        if child.tag.endswith('pre'):
            n = child
            break
    return n.text

def start(conf_url):
    status('fetching conference url "' + conf_url + '"')
    page = fetch(conf_url + '&preflayout=flat')
    if not page:
        error('fetching page')
        sys.exit(1)

    paper_urls = cit_regex.findall(page)
    status('there are', len(paper_urls) - 1, 'papers')
    for paper_url in paper_urls:
        status('fetching paper url')
        page = fetch(paper_url)
        if not page:
            sys.exit(1)
    
        # locate bibtex url
        m = tex_regex.search(page)
        if not m:
            sys.exit(1)
        bibtex_url = m.group(0)
    
        # get bibtex url
        status('paper bibtex url')
        page = fetch(bibtex_url)
        if not page:
            sys.exit(1)
    
        # extract bibtex text
        tex = extract_pre(page)
        print tex.encode('utf8', 'replace')

if len(sys.argv) != 2:
    sys.stderr.write('Usage: ' + sys.argv[0] + ' acmurl \n')
    sys.exit(1)

start(sys.argv[1])


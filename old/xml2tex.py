#! /usr/bin/env python2.7
# -*- coding: utf-8 -*-
# author: Alexander Merritt, merritt.alex@gatech.edu
# convert bib entries from XML to bibtex format
import sys
import xml.etree.ElementTree as ET
import os.path
import codecs

spacer = ' ' * 3
def convert(name):
    if not os.path.isfile(name):
        sys.exit(1)

    sys.stderr.write(name + '\n')
    f = codecs.open(name)
    xml = f.read()
    f.close()

    root = ET.fromstring(xml)
    for citation in root:
        print '@' + citation.tag, '{', citation.attrib['key'], ','

        authors = []
        for auth in citation.findall('author'):
            authors.append(auth.text)
        print spacer, 'author = {',
        print u' and '.join(authors), '},'

        for e in citation:
            if 'author' in e.tag:
                continue
            if 'cite' in e.tag:
                continue
            if 'crossref' in e.tag:
                print spacer, e.tag, '= {', 'DBLP:' + e.text, '},'
                print spacer, 'bibsource = { DBLP, http://dblp.uni-trier.de }'
                continue
            print spacer, e.tag, '= {', e.text, '},'

        print '}'

def convertAll(path):
    if not os.path.isdir(path):
        sys.exit(1)
    files = os.listdir(path)
    for name in files:
        if not name.endswith('.xml'):
            continue
        convert(name)

# -------- 8< -------------
convertAll('./')


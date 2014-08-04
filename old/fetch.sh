#! /usr/bin/env bash
set -e
set -u

while read line
do
    conf=$(echo $line | cut -d ' ' -f 1)
    url=$(echo $line | cut -d ' ' -f 2)

    filename=${conf}.bib
    [ -e $filename ] && continue
    : > $filename

    ./bib.py "$url" > $filename
done

#!/bin/sh
set -e
cd $HOME/src/hcevents
/usr/local/bin/python3 hcevents.py
cp hcevents.ics /usr/local/www/data/hcevents/

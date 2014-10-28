#!/usr/bin/bash
# This one is intended to be run from git bash shell!!
rm -rf dist
mkdir dist
cp -r maps dist

# these files are now specified in setup.py
# KW.ico, LICENSE.txt, README.txt

py -3.4 setup.py py2exe

#!/usr/bin/python3
# -*- coding: utf8 -*-
import sys
import os

# we need to redirect some pipes BEFORE importing wx.
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

import autosaverapp
autosaverapp.main( 'cnc3', 'config_cnc3.ini', icon='cnc3.ico' )

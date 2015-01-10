#!/usr/bin/python3
# -*- coding: utf8 -*-
import sys
import os

# we need to redirect some pipes BEFORE importing wx.
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

import autosaverapp
autosaverapp.main( 'ra3', 'config_ra3.ini', icon='ra3.ico' )

#!/usr/bin/python3
# -*- coding: utf8 -*-
import sys
import os

# we need to redirect some pipes BEFORE importing wx.
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

from autosaverapp import main
autosaverapp.main()

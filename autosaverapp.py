#!/usr/bin/python3
# -*- coding: utf8 -*-
import sys
import os

# we need to redirect some pipes BEFORE importing wx.
#sys.stdout = open(os.devnull, 'w')
#sys.stderr = open(os.devnull, 'w')
# I've decided to move the burden of pipe meddling away from this script.
# This script will now only contain methods to run this tray app.
# Meddling will be done by other "main" scripts.
# By this way, running this script will allow debugging runs with console,
# without having to modify this script.

import wx
import wx.adv

# my own classes
from args import Args
from watcher import Watcher
from replayviewer import ReplayViewer



class AutoSaverApp( wx.adv.TaskBarIcon ) :
	def __init__( self, iconf ) :
		#super(AutoSaverApp, self).__init__()
		super().__init__()

		self.POLL_INTERVAL = 2000 # in msec
		self.CONFIGF = 'config.ini'
		self.args = Args( self.CONFIGF )
		self.watcher = Watcher( self.args.last_replay )

		#
		# now wx stuff
		#

		self.set_icon( iconf )
		self.add_username = None # pointer to add_username check menu, for ease of access.

		# timer for polling for replay change
		self.timer = wx.Timer( self )
		self.timer.Start( self.POLL_INTERVAL )

		# event bindings
		self.Bind( wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.on_left_dclick )
		# might show replay manager in the future, but not now.

		self.Bind( wx.EVT_TIMER, self.on_timer, self.timer )
	
	def on_timer( self, event ) :
		if self.watcher.poll() :
			newf = self.watcher.do_renaming( self.watcher.last_replay, self.args.add_username )
			print( "Copied to", newf ) # shown on console!

	def create_menu_item( self, menu, label, func ) :
		item = wx.MenuItem(menu, -1, label)
		menu.Bind(wx.EVT_MENU, func, id=item.GetId())
		menu.Append(item)
		return item

	def on_add_username( self, event ) :
		# toggle configuration status
		# has hidden cfg inside, must use the set function.
		self.args.set_add_username( not self.args.add_username )

	def CreatePopupMenu( self ) :
		menu = wx.Menu()

		# checkable thingy
		self.add_username = menu.AppendCheckItem( wx.ID_ANY, 'Add user name',
				'Append player names to the replay name' )
		self.add_username.Check( self.args.add_username ) # check status should follow the config.
		# context menu check items DO NOT have internal state!!
		# we must set checkedness here
		menu.Bind( wx.EVT_MENU, self.on_add_username, id=self.add_username.GetId() )

		# change last replay file
		self.create_menu_item( menu, 'Change last replay file', self.on_set_last_replay )

		# Replay Manager thingy
		self.create_menu_item( menu, 'Open replay manager', self.on_left_dclick )

		# -----------------
		menu.AppendSeparator()

		# exit
		self.create_menu_item( menu, 'Exit', self.on_exit )
		return menu

	def set_icon( self, iconf ) :
		#icon = wx.IconFromBitmap( wx.Bitmap( iconf ) )
		icon = wx.Icon( iconf, wx.BITMAP_TYPE_ICO )
		self.SetIcon( icon, "Kane's Wrath replay auto saver" )
	
	def open_replay_viewer( self ) :
		path = os.path.dirname( self.args.last_replay )
		replay_viewer = ReplayViewer( self, path )
		replay_viewer.Show( True )

	def on_left_dclick( self, event ) :
		self.open_replay_viewer()

	def on_set_last_replay( self, event ) :
		self.args.set_last_replay() # invoke open dialog
		self.watcher.last_replay = self.args.last_replay # and pass the information to watcher.

	def on_exit(self, event):
		self.args.save_to_file( self.CONFIGF )
		wx.CallAfter( self.Destroy )
	

def main() :
	ICONF = 'KW.ico'
	app = wx.App( False )
	ico = AutoSaverApp( ICONF )
	app.MainLoop()

###
### main
###
main()
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
import download
from args import Args
from watcher import Watcher
from replayviewer import ReplayViewer
from dateformatcustomizer import DateFormatCustomizer



class AutoSaverAppIcon( wx.adv.TaskBarIcon ) :
	def __init__( self, frame, iconf ) :
		super().__init__()

		self.POLL_INTERVAL = 2000 # in msec
		self.CONFIGF = 'config.ini'
		self.frame = frame
		self.args = Args( self.CONFIGF )
		self.watcher = Watcher( self.args.last_replay )

		#
		# now wx stuff
		#
		self.set_icon( iconf )

		self.add_username = None # pointer to add_username check menu, for ease of access.
		self.add_faction = None # pointer to add_faction check menu, for ease of access.
		self.add_vs_info = None # pointer to add_vs_info check menu, for ease of access.

		# timer for polling for replay change
		self.timer = wx.Timer( self )
		self.timer.Start( self.POLL_INTERVAL )

		# event bindings
		self.Bind( wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.on_left_dclick )
		# might show replay manager in the future, but not now.

		self.Bind( wx.EVT_TIMER, self.on_timer, self.timer )
	
	def on_timer( self, event ) :
		if self.watcher.poll() :
			newf = self.watcher.do_renaming( self.watcher.last_replay,
					add_username=self.args.add_username,
					add_faction=self.args.add_faction,
					add_vs_info=self.args.add_vs_info,
					custom_date_format=self.args.custom_date_format )
			print( "Copied to", newf ) # shown on console!

	def create_menu_item( self, menu, label, func ) :
		item = wx.MenuItem(menu, -1, label)
		menu.Bind(wx.EVT_MENU, func, id=item.GetId())
		menu.Append(item)
		return item

	def on_add_username( self, event ) :
		# toggle configuration status
		# has hidden cfg inside, must use the set function.
		self.args.set_var( 'add_username', not self.args.add_username )

	def on_add_faction( self, event ) :
		# toggle configuration status
		# has hidden cfg inside, must use the set function.
		self.args.set_var( 'add_faction', not self.args.add_faction )

	def on_add_vs_info( self, event ) :
		# toggle configuration status
		# has hidden cfg inside, must use the set function.
		self.args.set_var( 'add_vs_info', not self.args.add_vs_info )

	# Overridden function
	def CreatePopupMenu( self ) :
		menu = wx.Menu()

		# checkable thingy
		self.add_username = menu.AppendCheckItem( wx.ID_ANY, 'Add user name',
				'Append player names to the replay name' )
		self.add_faction = menu.AppendCheckItem( wx.ID_ANY, 'Add factions',
				'Append faction information to each player' )
		self.add_vs_info = menu.AppendCheckItem( wx.ID_ANY, 'Add [1v1], [2v2] [FFA]',
				'Append game type information.' )

		# check status should follow the config.
		# context menu check items DO NOT have internal state!!
		# we must set checkedness here
		self.add_username.Check( self.args.add_username )
		self.add_faction.Check( self.args.add_faction )
		self.add_vs_info.Check( self.args.add_vs_info )

		# event binding
		menu.Bind( wx.EVT_MENU, self.on_add_username, id=self.add_username.GetId() )
		menu.Bind( wx.EVT_MENU, self.on_add_faction, id=self.add_faction.GetId() )
		menu.Bind( wx.EVT_MENU, self.on_add_vs_info, id=self.add_vs_info.GetId() )

		# custom date format
		self.create_menu_item( menu, 'Customize date time format', self.on_customize_date_format )

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
	
	def on_customize_date_format( self, event ) :
		# parent pointer looks wonky but it works!
		dfc = DateFormatCustomizer( wx.GetApp().TopWindow, self.args )
		result = dfc.ShowModal()
		if result == wx.ID_OK :
			fmt = dfc.text_ctrl_format.GetValue()
			self.args.set_var( 'custom_date_format', fmt )
		dfc.Destroy()
	
	def open_replay_viewer( self ) :
		# parent pointer looks wonky but it works!
		replay_viewer = ReplayViewer( wx.GetApp().TopWindow, self.args )
		replay_viewer.Show( True )

	def on_left_dclick( self, event ) :
		self.open_replay_viewer()

	def on_set_last_replay( self, event ) :
		self.args.set_last_replay() # invoke open dialog
		self.watcher.last_replay = self.args.last_replay # and pass the information to watcher.

	def on_exit(self, event):
		self.args.save()
		self.Destroy() # self kill
		self.frame.Destroy() # parent kill
		# These two kills will kill all frames of the app, exiting the app!



###
### For single instance running.
### http://wiki.wxpython.org/OneInstanceRunning
###
class AutoSaverApp( wx.App ) :
	def OnInit( self ) :
		self.name = "KWRAS-" + wx.GetUserId()
		self.instance = wx.SingleInstanceChecker( self.name )
		if self.instance.IsAnotherRunning() :
			wx.MessageBox( "An instance of KWRAS is already running", "ERROR" )
			return False
		return True

###
### It seems, on Linux, tray apps need a dummy form at least.
### "A wxPython application automatically exits when the last top level window
### ( Frame or Dialog), is destroyed. Put any application-wide cleanup code in
### AppConsole.OnExit (this is a method, not an event handler)."
### It says on the docs.
###
class AutoSaverForm( wx.Frame ) :
	def __init__( self, iconf ) :
		super().__init__( None )
		self.tray_icon = AutoSaverAppIcon( self, iconf )
		#self.Bind( wx.EVT_CLOSE, self.on_close )
	
	#def on_close( self, event ) :
	#	self.tray_icon.Destroy() #causes segfault. Don't need this!
	#	event.skip() # proceed to close.

def download_maps( mapf ) :
	url = 'http://github.com/forcecore/KWReplayAutoSaver/'
	url += 'releases/download/map_v1.0.0/maps.zip'
	msg = 'Map preview data is downloading, please wait'
	result = download.download( url, mapf, msg )
	if not result :
		# clear partially downloaded zip file
		if os.path.isfile( mapf ) :
			os.remove( mapf )
		wx.MessageBox( "Map preview data must be downloaded!", "Error",
			wx.OK|wx.ICON_ERROR )
	return result

def main() :
	ICONF = 'KW.ico'
	MAPF = 'maps.zip'
	app = AutoSaverApp()
	
	if not os.path.isfile( MAPF ) :
		msg = "Download map preview data?"
		result = wx.MessageBox( msg, "Confirm",
				wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT )
		if result == wx.YES :
			download_maps( MAPF )

	frame = AutoSaverForm( ICONF )

	#frame.Show( show=False ) dont need this, hidden app!
	app.MainLoop()

###
### main
###
main()

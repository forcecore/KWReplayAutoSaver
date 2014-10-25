#!/usr/bin/python3
# -*- coding: utf8 -*-
import os, time, shutil
import configparser
import wx
import io


###
### Configuration
###

###
### This class holds config vars of the program + keeps them synced on disk.
### (config written back when program exits)
###
class Args :
	def __init__( self, fname ) :
		self.dirty = False # Has non-saved + changed options?
		self.cfg_fname = fname # for saving to disk on exit.

		self.last_replay = None
		self.add_username = True
		self.add_faction = False
		self.custom_date_format = None

		self.cfg = self.load_from_file( fname )
	
	def __str__( self ) :
		s = io.StringIO()
		print( "last_replay:", self.last_replay, file=s )
		print( "add_username:", self.add_username, file=s )
		print( "add_faction:", self.add_faction, file=s )
		print( "custom_date_format:", self.custom_date_format, file=s )
		return s.getvalue()

	def set_var( self, key, val ) :
		self.cfg[ 'options' ][ key ] = str( val ) # set it in cfg.
		self.__dict__[ key ] = val # set self var.
		self.dirty = True
	
	# get variable.
	# returns default if not in cfg.
	def get_var( self, key, default=None ) :
		if not self.cfg.has_section( 'options' ) :
			self.cfg.add_section( 'options' )
			return default

		if not key in self.cfg[ 'options' ] :
			return default

		return self.cfg[ 'options' ][ key ]

	# Same as get var (actually uses get_var) but converts them to bool
	def get_bool( self, key, default=None ) :
		# awwwwwwww this is so confusing.
		# So, if I invoke get_var with no default value, then I should get
		# 'None' when section or key doesn't exist.
		# Then I shall return default val.
		# Otherwise it means some bool value exists to parse.
		# I may use getboolean function safely,
		# which will do 'on/off', 'true/false', 'yes/no' parsing burden.
		val = self.get_var( key )

		if val == None :
			return default
		else :
			return self.cfg.getboolean( 'options', key )

	# Make user to choose the last replay file.
	def set_last_replay( self ) :
		# Well, I'll turn to wxPython for dialogs.
		# It is asserted that some kind of wx.App() instance is initialized by
		# the user of this class.
		diag = wx.FileDialog( None, "Open the last replay file", "", "",
			"Kane's Wrath Replays (*.KWReplay)|*.KWReplay",
			wx.FD_OPEN | wx.FD_FILE_MUST_EXIST )
		
		if diag.ShowModal() == wx.ID_OK :
			# if dialog set properly, set it.
			self.set_var( 'last_replay', diag.GetPath() )
		else :
			# if not set properly and if we have a proper value of last_replay
			# somehow, we may continue.
			if not self.last_replay :
				# if we may not continue... we quit the app.
				wx.MessageBox( "You must select the last replay file!, exiting." )
				exit( 1 )

		diag.Destroy()
	
	def load_from_file( self, fname ) :
		self.cfg = configparser.ConfigParser()
		self.cfg.read( fname )

		self.last_replay = self.get_var( 'last_replay' )
		if not self.last_replay :
			wx.MessageBox( "Please select the last replay file!" )
			self.set_last_replay() # ask the user for it. it is a critical var!

		self.add_username = self.get_bool( 'add_username', True )
		self.add_faction = self.get_bool( 'add_faction', False )
		self.custom_date_format = self.get_var( 'custom_date_format' )

		return self.cfg

	def save_to_file( self, fname ) :
		f = open( fname, 'w' )
		self.cfg.write( f )
		f.close()
		


def main() :
	# Open config
	app = wx.App( None ) # needed for event processing for the MsgBox.
	args = Args( "config.ini" )
	print( args )



###
### main
###

if __name__ == "__main__" :
	main()

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
		#self.dirty = False # Has non-saved + changed options?
		self.cfg_fname = fname # for saving to disk on exit.

		self.last_replay = None
		self.add_vs_info = False
		self.add_username = True
		self.add_faction = False
		self.custom_date_format = None
		self.mcmap = dict() # map crc to 1.02+R dict.

		self.cfg = self.load_from_file( fname )
	
	def __str__( self ) :
		s = io.StringIO()
		print( "last_replay:", self.last_replay, file=s )
		print( "add_vs_info:", self.add_vs_info, file=s )
		print( "add_username:", self.add_username, file=s )
		print( "add_faction:", self.add_faction, file=s )
		print( "custom_date_format:", self.custom_date_format, file=s )
		print( "mcmap:", self.mcmap, file=s )
		return s.getvalue()

	def set_var( self, key, val ) :
		self.__dict__[ key ] = val # set self var.
		if key == 'custom_date_format' :
			val = val.replace( "%", "%%" )
			# The % symbols all mess up setting this variable. :(
		self.cfg[ 'options' ][ key ] = str( val ) # set it in cfg.
	
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
			"Kane's Wrath Replays (*.KWReplay)|*.KWReplay" +
			"|Tiberium Wars Replays (*.CNC3Replay)|*.CNC3Replay" +
			"|RA3 Replays (*.RA3Replay)|*.RA3Replay", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST )
		
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
		self.cfg.optionxform = str # make it case sensitive.

		# List default options here.
		# Currently, it only specifies map CRC settings.
		# Note that, read_dict() must come before read()
		defaults = {
				'102mc': {
						'14':'R10b',
						'13':'R10',
						'11':'R9',
						'F':'R8',
						'D':'R7',
						'B':'R6'
					}
			}
		self.cfg.read_dict( defaults )

		self.cfg.read( fname )

		self.last_replay = self.get_var( 'last_replay' )
		if not self.last_replay :
			wx.MessageBox( "Please select the last replay file!" )
			self.set_last_replay() # ask the user for it. it is a critical var!

		self.add_username = self.get_bool( 'add_username', True )
		self.add_faction = self.get_bool( 'add_faction', False )
		self.add_vs_info = self.get_bool( 'add_vs_info', False )
		self.custom_date_format = self.get_var( 'custom_date_format' )
		if self.custom_date_format == None :
			self.custom_date_format = "[%Y-%m-%dT%H%M]"

		self.cfg = self.load_mc( self.cfg ) # please call this before cfg.read()!!

		return self.cfg

	# Loads CRC values for 1.02+ maps
	def load_mc( self, cfg ) :
		section = cfg[ '102mc' ]
		for option in section :
			self.mcmap[ option ] = section[ option ]
			#print( option, section[ option ] )
		return cfg
	
	def save( self ) :
		self.save_to_file( self.cfg_fname )

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

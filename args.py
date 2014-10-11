#!/usr/bin/python3
# -*- coding: utf8 -*-
import os, time, shutil
import configparser
import wx


###
### Configuration
###

class Args :
	def __init__( self, fname ) :
		self.last_replay = None
		self.cfg = self.load_from_file( fname )
	
	def __str__( self ) :
		lines = []
		if self.last_replay :
			lines.append( "last_replay: " + self.last_replay )
		else :
			lines.append( "last_replay: None" )
		return '\n'.join( lines )

	def set_last_replay( self ) :
		diag = wx.FileDialog( None, "Open the last replay file", "", "",
			"Kane's Wrath Replays (*.KWReplay)|*.KWReplay",
			wx.FD_OPEN | wx.FD_FILE_MUST_EXIST )
		
		if diag.ShowModal() == wx.ID_OK :
			self.last_replay = diag.GetPath()
		else :
			if not self.last_replay :
				wx.MessageBox( "You must select the last replay file!, exiting." )
				exit( 1 )

		# Well, I'll turn to wxPython
		self.cfg.set( 'options', 'last_replay', self.last_replay )

		diag.Destroy()
	
	def set_add_username( self, tf ) :
		if tf == True :
			tfstr = 'true'
		else :
			tfstr = 'false'
		self.cfg[ 'options' ][ 'add_username' ] = tfstr
		self.add_username = tf

	def load_from_file( self, fname ) :
		self.cfg = configparser.ConfigParser()
		self.cfg.read( fname )

		written = False

		if not self.cfg.has_section( 'options' ) :
			self.cfg.add_section( 'options' )
			written = True

		# read last replay fname
		if not self.cfg.has_option( 'options', 'last_replay' ) :
			wx.MessageBox( "Please select the last replay file!" )
			self.set_last_replay()
			written = True
		else :
			self.last_replay = self.cfg[ 'options' ][ 'last_replay' ]

		# get add_username option
		if not self.cfg.has_option( 'options', 'add_username' ) :
			written = True
			self.set_add_username( True )
		else :
			self.add_username = self.cfg.getboolean( 'options', 'add_username' )
			#print( self.add_username )

		# if newly written, save.
		if written :
			self.save_to_file( fname )

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

#!/usr/bin/python3
import os
import zipfile
import io
import wx

class MapZip() :
	def __init__( self, fname ) :
		self.fname = fname
		if not os.path.isfile( fname ) :
			self.zipf = None
			self.namelist = []
		else :
			self.zipf = zipfile.ZipFile( fname, 'r' )
			self.namelist = self.zipf.namelist()
	
	def hasfile( self, fname ) :
		return fname in self.namelist

	# load fname and return as wx.Image
	def load( self, fname ) :
		assert self.hasfile( fname )
		zs = self.zipf.open( fname ) # open stream

		# but zs doesn't support seek() operation.
		# read onto a buffer to support seek().
		s = io.BytesIO( zs.read() )

		img = wx.Image()
		img.LoadFile( s )
		s.close()
		zs.close()
		return img

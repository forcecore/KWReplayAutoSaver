#!/usr/bin/python3
# coding: utf8

###
### http://www.gamereplays.org/community/index.php?showtopic=706067&st=0&p=7863248&#entry7863248
### The decoding of the replays format is credited to R Schneider.
###

import struct # bin file enc/dec
import sys
import re
import io
import codecs
import datetime
import time
from kwreplay import KWReplay, read_byte, read_uint32, time_code2str

CMDLENS = {
	0x01: -2,
	0x02: -2,
	0x03: -2,
	0x04: -2,
	0x05: -2,
	0x06: -2,
	0x07: -2,
	0x08: -2,
	0x09: -2,
	0x0B: -2,
	0x0C: -2,
	0x0D: -2,
	0x0F: -2,
	0x10: -2,
	0x11: -2,
	0x12: -2,
	0x17: -2,

	0x27: -34,
	0x29: 28,
	0x2B: -11,
	0x2C: 17,
	0x2E: 22,
	0x2F: 17,
	0x30: 17,
	0x34: 8,
	0x35: 12,
	0x36: 13,
	0x3C: 21,
	0x3E: 16,
	0x3D: 21,
	0x43: 12,
	0x44: 8,
	0x45: 21,
	0x46: 16,
	0x47: 16,
	0x48: 16,
	0x5B: 16,
	0x61: 20,
	0x72: -2,
	0x73: -2,
	0x77: 3,
	0x7A: 29,
	0x7E: 12,
	0x7F: 12,
	0x87: 8,
	0x89: 8,
	0x8C: 45,
	0x8D: 1049,
	0x8E: 16,
	0x8F: 40,
	0x90: 16,
	0x91: 10,

	0x28: 0,
	0x2D: 0,
	0x31: 0,
	0x8B: 0,

	0x26: -15,
	0x4C: -2,
	0x4D: -2,
	0x92: -2,
	0x93: -2,
	0xF5: -4,
	0xF6: -4,
	0xF8: -4,
	0xF9: -2,
	0xFA: -2,
	0xFB: -2,
	0xFC: -2,
	0xFD: -2,
	0xFE: -2,
	0xFF: -2
}

CMDNAMES = {
	0x2D: "not quit game... dunno",
	0x31: "Place down building?",
	0x34: "sell?",
	0x3D: "attack?",
	0x61: "30s heartbeat",
	0x8F: "'scroll'",
	0xF5: "drag selection box and/or select units/structures",
	0xF8: "left click"
}



class Chunk :
	def __init__( self ) :
		self.time_code = 0
		self.ty = 0
		self.size = 0
		self.data = None

		# decoded data
		self.time = 0
		self.paylaod = None

		# for ty == 1
		self.ncmd = 0

		# for ty == 2
		# player number, index in the player list in the plain-text game info
		self.player_number = 0
		self.time_code_payload = 0 # another timecode, in the paylaod.
		self.ty2_payload = None
	
	def decode_fixed_len( self, f, cmdlen ) :
		# that cmdlen includes the terminator and cmd code+0xff Thus, -3.
		cmdlen -= 3
		code = f.read( cmdlen )
		print( "fixed len, code:", code )
	
	def decode_var_len( self, f, cmdlen ) :
		cmdlen *= -1
		f.read( cmdlen-2 )
		print( "varlen:", cmdlen )
	
	def decode_commands( self, ncmd, payload ) :
		f = io.BytesIO( payload )
		print( "COMMANDS payload:", payload )

		for i in range( ncmd ) :
			cmd_id = read_byte( f )
			if cmd_id in CMDNAMES :
				print( "---" )
				print( CMDNAMES[ cmd_id ] )
				print( "---" )
			player_id = read_byte( f )
			print( "player_id:", player_id )
			print( "cmd_id: 0x%X" % cmd_id )
			# resolved the name.

			cmdlen = CMDLENS[ cmd_id ]

			if cmdlen < 0 :
				# var len cmds!
				self.decode_var_len( f, cmdlen )
				return

			# more var len commands
			if cmd_id == 0x31 :
				unknown = f.read( 10 )
				l = read_byte( f )
				more_unknown = f.read( 18*l )
				cmdlen = 3
				more_unknown = f.read( 3 )
			elif cmd_id == 0x2D :
				return
				#unknown = f.read( 5 )
				#some_code = read_byte( f )
				#if some_code == 0xFF :
				#	return # just, terminated.
				#else :
				#	buf = f.read( 17 )
				#	print( buf )
			else :
				# fixed len
				self.decode_fixed_len( f, cmdlen )

			terminator = read_byte( f )
			if terminator != 0xFF :
				print( "TERMINATOR:" )
				print( terminator )
				print( f.read() )
			assert terminator == 0xFF


	
	def decode( self ) :
		self.time = time_code2str( self.time_code/15 )
		if self.ty == 1 :
			f = io.BytesIO( self.data )
			one = read_byte( f )
			assert one == 1
			if self.data[ -1 ] != 0xFF :
				print( "Some unknown command format:" )
				print( "data:", self.data )
				self.payload = f.read()
			else :
				self.ncmd = read_uint32( f )
				self.payload = f.read()
				self.decode_commands( self.ncmd, self.payload )

		elif self.ty == 2 :
			f = io.BytesIO( self.data )
			# This is camera data or heart beat data.
			# I'll not try too hard to decode this.
			one = read_byte( f ) # should be ==1
			zero = read_byte( f ) # should be ==0
			self.player_number = read_uint32( f ) # uint32
			self.time_code_payload = read_uint32( f ) # time code...
			self.ty2_payload = f.read() # the payload
	
	def print( self ) :
		self.decode()

		if self.ty == 1 :
			print( "time:", self.time )
			print( "ncmd:", self.ncmd )
			print( "payload:" )
			for i in range( len( self.payload ) ) :
				print( "0x%02X" % self.payload[i], end=" " )
				if i % 16 == 0 :
					print()
			print()
			print()
			print()
		elif self.ty == 2 :
			#print( "Camera data." )
			pass
			#print( "\tplayer#:", self.player_number )
			#print( "\ttimecode:", self.time_code_payload )
		else :
			# From eareplay.html:
			# Chunk types 3 and 4 only appear to be present in replays with a
			# commentary track, and it seems that type 3 contains the audio
			# data and type 4 the telestrator data.
			pass
			#print( "type:", self.ty )
			#print( "size:", self.size )
			#print( "data:", self.data )
	


class ReplayBody :
	def __init__( self, f ) :
		self.chunks = []
		self.loadFromStream( f )
	
	def read_chunk( self, f ) :
		chunk = Chunk()
		chunk.time_code = read_uint32( f )
		#print( chunk.time_code )
		if chunk.time_code == 0x7FFFFFFF :
			return None

		chunk.ty = read_byte( f )
		chunk.size = read_uint32( f )
		chunk.data = f.read( chunk.size )
		zero = read_uint32( f )

		chunk.print()

		assert zero == 0
		return chunk
	
	def loadFromStream( self, f ) :
		while True :
			chunk = self.read_chunk( f )
			if chunk == None :
				break
			self.chunks.append( chunk )



class KWReplayWithCommands( KWReplay ) :
	def __init__( self, fname=None, verbose=False ) :
		self.replay_body = None

		# self.footer_str ... useless
		self.final_time_code = 0
		self.footer_data = None # I have no idea what this is. I'll keep it as it is.
		#self.footer_length = 0

		super().__init__( fname=fname, verbose=verbose )

	def read_footer( self, f ) :
		footer_str = self.read_cstr( f, self.FOOTER_MAGIC_SIZE )
		self.final_time_code = read_uint32( f )
		self.footer_data = f.read()
		if self.verbose :
			print( "footer_str:", footer_str )
			print( "final_time_code:", self.final_time_code )
			print( "footer_data:", self.footer_data )
			print()

	def loadFromFile( self, fname ) :
		f = open( fname, 'rb' )
		self.loadFromStream( f )
		self.replay_body = ReplayBody( f )
		self.read_footer( f )
		f.close()



###
###
###
def main() :
	fname = "1.KWReplay"
	if len( sys.argv ) >= 2 :
		fname = sys.argv[1]
	kw = KWReplayWithCommands( fname=fname, verbose=False )
	#kw = KWReplay()
	#kw.modify_desc( fname, "2.KWReplay", "매치 설명 있음" )
	#kw.modify_desc_inplace( "2.KWReplay", "show me the money 오예" )

if __name__ == "__main__" :
	main()

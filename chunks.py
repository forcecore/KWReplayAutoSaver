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
from kwreplay import KWReplay
from utils import *



class Command :

	verbose = False     # manually make this True if you want to debug...

	# Command type consts
	NONE = 0
	HOLD = 1
	SELL = 2
	GG = 3
	POWER_DOWN = 4
	QUEUE = 5 # queue unit production
	SKILL_2XY = 6
	SKILL_XY = 7
	SKILL_TARGETLESS = 8
	SKILL_TARGET = 9
	UPGRADE = 10
	PLACEDOWN = 11
	EOG = 12 # end of game marker
	FORMATION_MOVE = 13
	MOVE = 14
	REVERSE_MOVE = 15



	def __init__( self ) :
		self.cmd_id = 0
		self.time_code = 0
		self.player_id = 0 # dunno if it really is player_id.
		self.payload = None # raw command

		self.cmd_ty = Command.NONE # not decoded at all! Decoded command type.
		# other info are dynamically allocated when necessary.
		# self.substructures = []



	def decode_sell_cmd( self ) :
		self.cmd_ty = Command.SELL
		self.target = uint42int( self.payload[ 1:5 ] )



	def decode_powerdown_cmd( self ) :
		self.decode_sell_cmd() # this works for powerdown, too.
		self.cmd_ty = Command.POWER_DOWN



	def decode_queue_cmd( self, UNITNAMES, AFLD_UNITS ) :
		self.cmd_ty = Command.QUEUE
		data = self.payload

		if ( not data ) or ( len( data ) <= 18 ) : # Just "" for net payload (Only FF in payload)
			# end of game marker?
			self.cmd_ty = Command.EOG
			self.target = self.player_id
		else :
			self.factory = uint42int( data[ 1:5 ] )
			self.unit_ty = uint42int( data[ 8:12 ] ) # This one is pretty sure
			self.cnt = 1 # how many queued?
			fivex = data[ 17 ]
			if fivex :
				if self.unit_ty in AFLD_UNITS :
					self.cnt = 4
					# Actually, fivex just tells us that it is
					# shift + click on the unit produciton button.
					# For normal units, it is definitely 5x.
					# But for these air units, it could be
					# 1 ~ 4, depending on the space left on the landing pad.
				else :
					self.cnt = 5

			if self.unit_ty in UNITNAMES :
				self.unit_ty = UNITNAMES[ self.unit_ty ]
			else :
				self.unit_ty = "0x%08X" % self.unit_ty



	def decode_gg( self ) :
		cmd.cmd_ty = Command.GG
		cmd.target = cmd.payload[1]



	def decode_skill_xy( self, POWERNAMES ) :
		self.cmd_ty = Command.SKILL_XY
		data = self.payload
		self.x = uint42float( data[ 6:10] )
		self.y = uint42float( data[ 10:14] )
		self.power = uint42int( data[ 0:4 ] )

		if self.power in POWERNAMES :
			self.power = POWERNAMES[ self.power ]
		else :
			self.power = "0x%08X" % self.power



	def decode_skill_2xy( self, POWERNAMES ) :
		self.cmd_ty = Command.SKILL_2XY
		data = self.payload
		self.x1 = uint42float( data[ 16:20] )
		self.y1 = uint42float( data[ 20:24] )
		self.x2 = uint42float( data[ 28:32] )
		self.y2 = uint42float( data[ 32:36] )
		self.power = uint42int( data[ 0:4 ] )

		if self.power in POWERNAMES :
			self.power = POWERNAMES[ self.power ]
		else :
			self.power = "0x%08X" % self.power



	def decode_skill_targetless( self, POWERNAMES ) :
		self.cmd_ty = Command.SKILL_TARGETLESS
		data = self.payload
		self.power = uint42int( data[ 0:4 ] )

		if self.power in POWERNAMES :
			self.power = POWERNAMES[ self.power ]
		else :
			self.power = "0x%08X" % self.power



	def decode_skill_target( self, POWERNAMES ) :
		self.cmd_ty = Command.SKILL_TARGET
		data = self.payload
		self.power = uint42int( data[ 0:4 ] )
		# dunno about target, but it is certain that this is only used on walling
		# structures -_-

		if self.power in POWERNAMES :
			self.power = POWERNAMES[ self.power ]
		else :
			self.power = "0x%08X" % self.power



	def decode_upgrade_cmd( self, UPGRADENAMES ) :
		self.cmd_ty = Command.UPGRADE
		data = self.payload
		self.upgrade = uint42int( data[1:5] )

		if self.upgrade in UPGRADENAMES :
			self.upgrade = UPGRADENAMES[ self.upgrade ]
		else :
			self.upgrade = "0x%08X" % self.upgrade



	def decode_hold_cmd( self, UNITNAMES ) :
		self.cmd_ty = Command.HOLD
		data = self.payload
		self.factory = uint42int( data[ 1:5 ] )
		self.unit_ty = uint42int( data[ 8:12 ] )
		self.cancel_all = data[13] # remove all build queue of this type

		if self.unit_ty in UNITNAMES :
			self.unit_ty = UNITNAMES[ self.unit_ty ]
		else :
			self.unit_ty = "0x%08X" % self.unit_ty
	


	def decode_formation_move_cmd( self ) :
		self.decode_move_cmd() # seems to work, though there are more parameters.
		self.cmd_ty = command.FORMATION_MOVE
		#data = self.payload
		#self.x = uint42float( data[ 1:5 ] )
		#self.y = uint42float( data[ 5:9 ] )

	def decode_move_cmd( self ) :
		self.cmd_ty = Command.MOVE
		data = self.payload
		self.x = uint42float( data[ 1:5 ] )
		self.y = uint42float( data[ 5:9 ] )
		#self.z = uint42float( data[ 9:13 ] ) # it really seems to be Z;;;

	def decode_reverse_move_cmd( self ) :
		self.decode_move_cmd() # this will do
		self.cmd_ty = Command.REVERSE_MOVE
	


	def decode_placedown_cmd( self, UNITNAMES ) :
		self.cmd_ty = Command.PLACEDOWN
		data = self.payload
		self.building_type = uint42int( data[6:10] )
		self.substructure_cnt = data[10]
		self.substructures = []

		# substructure X and Y decoding.
		pos = 11
		for i in range( self.substructure_cnt ) :
			pos += 4
			self.x = uint42float( data[pos:pos+4] )
			pos += 4
			self.y = uint42float( data[pos:pos+4] )
			pos += 4

		if self.building_type in UNITNAMES :
			self.building_type = UNITNAMES[ self.building_type ]
		else :
			self.building_type = "0x%08X" % self.building_type



		#print( "\tLocation: %f, %f" % (x, y) )
		#print( "substructure_cnt:", substructure_cnt )

		# subcomponent ID, x, y, orientation
		# I don't know how 18 bytes are made of...
		# I know x and y. What about the rest of 10 bytes?
		# there should be building orientation... which shoulbe float, 4 bytes.
		# or it sould be one byte? 0~255 enough?

		# For normal buildings, we don't get var length.
		# But for Nod defenses... shredder turrets, laser turrets,
		# SAM turrets... we get multiple coordinates.
		# That's why we get var len commands.
		# The multiplier 18 must be related to coordinates.
		# 8 for 2*4bytes (=2 floats) of x-y coords.
		# or... z coord?! dunno?!



	def print_bo( self ) :
		time = time_code2str( self.time_code/15 )
		print( time, end="\t" )
		print( "P" + str( self.player_id ), end="\t" )
		print( self )



	# Return build order commands as str.
	def __str__( self ) :
		if self.cmd_ty == Command.NONE :
			return "Unknown Command"
		elif self.cmd_ty == Command.HOLD :
			return "Hold/Cancel " + self.unit_ty
		elif self.cmd_ty == Command.SELL :
			return "Sell"
		elif self.cmd_ty == Command.GG :
			return "GG " + str( self.target )
		elif self.cmd_ty == Command.GG :
			return "GG " + str( self.target )
		elif self.cmd_ty == Command.POWER_DOWN :
			return "Power down building"
		elif self.cmd_ty == Command.QUEUE :
			return "Queue " + str( self.cnt ) + "x " + self.unit_ty
		elif Command.SKILL_2XY <= self.cmd_ty and self.cmd_ty <= Command.SKILL_TARGET :
			return self.power
		elif self.cmd_ty == Command.UPGRADE :
			return self.upgrade
		elif self.cmd_ty == Command.PLACEDOWN :
			return self.building_type
		elif self.cmd_ty == Command.EOG :
			return "End of game"
		else :
			return "Unknown Command"



class Splitter :
	def split_fixed_len( cmd, f, cmdlen ) :
		# that cmdlen includes the terminator and cmd code+0xff Thus, -3.
		cmdlen -= 3
		cmd.payload = f.read( cmdlen )

		if Command.verbose :
			print( "fixed len. payload:" )
			print_bytes( cmd.payload )
			print()



	def split_placedown_cmd( cmd, f ) :
		payload = io.BytesIO()
		buf = f.read( 10 ) # dunno what this is.
		payload.write( buf )
		substructure_cnt = f.read( 1 )
		payload.write( substructure_cnt )
		substructure_cnt = byte2int( substructure_cnt )
		payload.write( f.read( 18 * substructure_cnt ) )
		payload.write( f.read( 3 ) ) # more unknown stuff

		cmd.payload = payload.getbuffer()



	def split_var_len( cmd, f, cmdlen ) :
		payload = f.getbuffer() # cursor unaffected buffer, w00t.
		opos = f.tell()

		#if Command.verbose :
		#	print( "Varlen input:" )
		#	print( "Len info @:", cmdlen )
		#	print( "Cheat: ", end="" )
		#	print_bytes( payload )

		pos = f.tell() - 2 + (-cmdlen)

		while payload[ pos ] != 0xFF and pos < len( payload ) :
			adv = ( payload[ pos ] >> 4 ) + 1
			pos += 4*adv + 1

		read_cnt = pos-opos
		cmd.payload = f.read( read_cnt )

		if Command.verbose :
			print( "cmd_id: 0x%02X" % cmd.cmd_id )
			print( "cheat: ", end="" )
			print_bytes( payload )
			print( "opos ~ pos:", opos, pos )
			print( "read", read_cnt, "bytes" )
			print( "Read varlen command: ", end="" )
			print_bytes( cmd.payload )
			print()



	def split_chunk1_uuid( cmd, f ) :
		cheat = f.getbuffer()

		f.read( 1 )
		l = read_byte( f )
		s1 = read_cstr( f, l )

		if Command.verbose :
			print_bytes( cheat )
			print( "chunk thingy:" )
			print( "0x%02X" % cmd.cmd_id )
			print( "cheat:" )
			print()
			print( "s1:", s1 )

		f.read( 1 ) # skip
		l = read_byte( f )
		if l > 0 :
			s2 = read_tb_str( f, length=l )
			#buf = f.read( 2 ) # terminating two bytes of 0.
			if Command.verbose :
				print( "s2:", s2 )
			#print( "term0: %02X %02X" % ( buf[0], buf[1] ) )

		buf = f.read( 5 ) # consume til 0xFF?
		#print( "what is left:" )
		#print_bytes( buf )



	def split_var_len2( cmd, f, cnt_skip, skip_after ) :
		payload = io.BytesIO()

		dunno = f.read( cnt_skip )
		l = read_byte( f )
		payload.write( dunno )
		payload.write( struct.pack( "B", l ) )
		
		payload.write( f.read( l*4 ) )
		payload.write( f.read( skip_after ) ) # consume
		cmd.payload = payload.getvalue()



	def split_0x2c( cmd, f ) : # 0x2c of KW.
		cmd.split_var_len2( f, 5, 4 )



	def split_ff_crawl( cmd, f ) :
		# 00 42 03 6C 1A 00 00 FF (8)

		# 00 2A 33 9F 16 00 00 CC 16 00 00 A6 17 00 00 8A
		# 17 00 00 FF (20)

		# 00 32 13 63 05 00 00 69 05 00 00 FF (12)

		# 00 22 33 51 08 00 00 9A 07 00 00 85 07 00 00 5F
		# 07 00 00 FF (20)

		# From what I have observed, there seems to be no length rule.
		# It's not a null terminated string either.
		# Lots of periodic 00 00 ... hmm...

		# For now, I'll just seek FF, it seems to be the only
		# feasible way, as there is no length info.

		buf = f.getbuffer()
		pos = f.tell()
		end = pos
		while buf[ end ] != 0xFF :
			end += 1

		cmd.payload = f.read( end-pos )



	def split_production_cmd( cmd, f ) :
			# either short or long...
			# length 8 or length 26, it seems, refering to cnc3reader_impl.cpp.

			cheat = f.getbuffer()
		
			if Command.verbose :
				print( "Production splitting" )
				print( "0x%02X" % cmd.cmd_id )
				print( "cheat:" )
				print_bytes( cheat )
				print()

			if cheat[ f.tell() ] == 0xFF :
				# 0x2D command with NOTHING in int.
				cmd.payload = None # stub command can happen... omg
			elif cheat[ f.tell() + 5 ] == 0xFF :
				cmd.payload = f.read( 5 )
			else :
				cmd.payload = f.read( 23 )



	# this skill targets one exact unit.
	# sonic/laser fence that is.
	def split_skill_target( cmd, f ) :
		buf = f.getbuffer()
		cnt = buf[ f.tell() + 15 ]
		end = f.tell() + 4*(cnt+1) + 30
		cmd.payload = f.read( end - f.tell() - 1 )

		if Command.verbose :
			print( "split_skill_target" )
			print( "0x%02X" % cmd.cmd_id )
			print( "cheat: ", end="" )
			print_bytes( buf )
			print( "end:", end )
			print( "payload:", end="" )
			print_bytes( cmd.payload )
			print()



class Chunk :

	def __init__( self ) :
		self.time_code = 0
		self.ty = 0
		self.size = 0
		self.data = None

		self.time = 0 # decoded time (str)

		# for ty == 1
		self.ncmd = 0
		self.payload = None # undecoded payload
		self.commands = []

		# for ty == 2
		# player number, index in the player list in the plain-text game info
		self.player_number = 0
		self.time_code_payload = 0 # another timecode, in the payload.
		self.ty2_payload = None



	def split( self, game ) :
		if self.ty != 1 :
			# I only care about game affecting stuff.
			return

		f = io.BytesIO( self.data )
		one = read_byte( f )
		assert one == 1
		if self.data[ -1 ] != 0xFF :
			if Command.verbose :
				print( "Some unknown command format:" )
				print( "data:" )
				print_bytes( self.data )
				print()
		else :
			self.ncmd = read_uint32( f )
			self.payload = f.read()
			self.split_commands( self.ncmd, self.payload, game )

			if len( self.commands ) != self.ncmd :
				self.fix_mismatch()

			for cmd in self.commands :
				cmd.time_code = self.time_code
	


	def fix_mismatch( self ) :
		# Override this one.
		# If you can't fix, make sure you can print out this warning.
		print( "Warning: chunk/command count mismatch!", file=sys.stderr )



	# Just try splitting commands by "FF".
	def split_commands( self, ncmd, payload, game ) :
		# FSM modes
		CMD_ID = 0
		PID = 1
		CONTENT = 2


		c = None # command of interest
		mode = CMD_ID
		start = 0
		end = 0

		for i, byte in enumerate( payload ) :
			if mode == CMD_ID :
				c = Command()
				self.commands.append( c )
				c.cmd_id = byte

				mode = PID

			elif mode == PID :
				# 3 for CNC3/KW. for RA3, k should be 2.
				if game == "KW" or game == "CNC3" :
					k = 3
				else :
					k = 2
				self.player_id = int( byte / 8 ) - k

				mode = CONTENT
				start = i+1 # start of the cmd payload.

			elif mode == CONTENT :
				# Well, do nothing.
				if byte == 0xFF :
					end = i+1 # +1 to include 0xFF as well.
					c.payload = payload[ start:end ]

					if ncmd != 1 :
						# When ncmd ==1, we don't need to split!
						mode = CMD_ID

			else :
				assert 0, "Shouldn't see me! split_commands() of ChunkOtherGames"
	


	def is_bo_cmd( self, cmd ) :
		return False



	def is_known_cmd( self, cmd ) :
		# not build order cmd... But I know what this is!
		# e.g, scroll.
		return False



	def resolve_known( self, cmd ) :
		# Override this one.
		# Returns the description of the known function as str.
		return ""



	def has_bo_cmd( self ) :
		for cmd in self.commands :
			if self.is_bo_cmd( cmd ) :
				return True
		return False



	def decode_cmd( self, cmd ) :
		# You need to override this function.
		pass



	def print_bo( self ) :
		if self.ty == 1 :
			if not self.has_bo_cmd() :
				return

			if self.ncmd != len( self.commands ) :
				print( "Warning: improper split of commands, not decoding", file=sys.stderr )
				return

			for cmd in self.commands :
				self.decode_cmd( cmd )
				if self.is_bo_cmd( cmd ) :
					cmd.print_bo()

		# I don't care about these!!
		#elif self.ty == 2 :
		#	f = io.BytesIO( self.data )
		#	# This is camera data or heart beat data.
		#	# I'll not try too hard to decode this.
		#	one = read_byte( f ) # should be ==1
		#	zero = read_byte( f ) # should be ==0
		#	self.player_number = read_uint32( f ) # uint32
		#	self.time_code_payload = read_uint32( f ) # time code...
		#	self.ty2_payload = f.read() # the payload
	


	def dump_commands( self ) :
		# print( "Time\tPlayer\tcmd_id\tparams" )
		if self.ncmd != len( self.commands ) :
			print( "Warning: ncmd & # command mismatch: %d:%d" %
				(self.ncmd, len( self.commands ) ) )
			print( "Just printing the chunk." )
			print( "time_code:", self.time_code )
			print( "ncmd:", self.ncmd )
			print_bytes( self.payload )
			print()
		else :
			for cmd in self.commands :
				if self.is_bo_cmd( cmd ) :
					self.decode_cmd( cmd )
					cmd.print_bo()
					print()
				else :
					if self.is_known_cmd( cmd ) :
						print( self.resolve_known( cmd ) )
					else :
						print( "unknown command" )
					print( cmd.time_code, end="\t" )
					print( cmd.player_id, end="\t" )
					print( "0x%02X" % cmd.cmd_id, end="\t" )
					print_bytes( cmd.payload, break16=False )
					print()
	


class ReplayBody :
	def __init__( self, f, game="KW" ) :
		self.chunks = []
		self.game = game
		self.loadFromStream( f )
	
	def read_chunk( self, f ) :
		if self.game == "KW" :
			import kwchunks
			chunk = kwchunks.KWChunk()
		elif self.game == "CNC3" :
			import twchunks
			chunk = twchunks.TWChunk()
		else :
			chunk = ChunkOtherGames()
		chunk.time_code = read_uint32( f )
		if chunk.time_code == 0x7FFFFFFF :
			return None

		chunk.ty = read_byte( f )
		chunk.size = read_uint32( f )
		chunk.data = f.read( chunk.size )
		unknown = read_uint32( f ) # mostly 0, but not always.

		# chunk debugging stuff:
		#print( "chunk pos: 0x%08X" % f.tell() )
		#print( "read_chunk.time_code: 0x%08X" % chunk.time_code )
		#print( "read_chunk.ty: 0x%02X" % chunk.ty )
		#print( "read_chunk.size:", chunk.size )
		#print( "chunk.data:" )
		#print_bytes( chunk.data )
		#print()
	
		chunk.split( self.game )
		return chunk
	
	def loadFromStream( self, f ) :
		while True :
			chunk = self.read_chunk( f )
			if chunk == None :
				break
			self.chunks.append( chunk )
	
	def print_bo( self ) :
		print( "Dump of known build order related commands" )
		print( "Time\tPlayer\tAction" )
		for chunk in self.chunks :
			chunk.print_bo()
	
	def dump_commands( self ) :
		print( "Dump of commands" )
		print( "Time\tPlayer\tcmd_id\tparams" )
		for chunk in self.chunks :
			chunk.dump_commands()



class KWReplayWithCommands( KWReplay ) :
	def __init__( self, fname=None, verbose=False ) :
		self.replay_body = None

		# self.footer_str ... useless
		self.final_time_code = 0
		self.footer_data = None # I have no idea what this is. I'll keep it as it is.
		#self.footer_length = 0

		super().__init__( fname=fname, verbose=verbose )

	def read_footer( self, f ) :
		footer_str = read_cstr( f, self.FOOTER_MAGIC_SIZE )
		self.final_time_code = read_uint32( f )
		self.footer_data = f.read()
		if self.verbose :
			print( "footer_str:", footer_str )
			print( "final_time_code:", self.final_time_code )
			print( "footer_data:", self.footer_data )
			print()
	
	def loadFromFile( self, fname ) :
		self.guess_game( fname )
		f = open( fname, 'rb' )
		self.loadFromStream( f )
		self.replay_body = ReplayBody( f, game=self.game )
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
	print( fname )
	print()
	kw.replay_body.print_bo()
	print()
	kw.replay_body.dump_commands()

if __name__ == "__main__" :
	main()

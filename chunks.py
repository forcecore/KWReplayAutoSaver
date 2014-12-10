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
from kwreplay import KWReplay, read_byte, read_uint32, read_float, \
	read_cstr, time_code2str, read_tb_str
from consts import *



KNOWN_COMMANDS = [ 0x31, 0x26, 0x27, 0x28, 0x2B, 0x2D, 0x2E, 0x8A, 0x34, 0x91 ]



def byte2int( byte ) :
	return struct.unpack( 'B', byte )[0]



def uint42int( bys ) :
	return struct.unpack( 'I', bys )[ 0 ]



def uint42float( bys ) :
	return struct.unpack( 'f', bys )[ 0 ]



def print_bytes( bys, break16=True ) :
	if not bys :
		print( "None" )
		return

	i = 0
	for b in bys :
		print( "%02X " % b, end="" )
		i += 1
		if break16 :
			if i >= 16 :
				i = 0
				print()
	print()



class Command :

	verbose = False     # manually make this True if you want to debug...

	def __init__( self ) :
		self.cmd_id = 0
		self.time_code = 0
		self.player_id = 0 # dunno if it really is player_id.
		self.payload = None # raw command

		# these are dynamically alloced.
		# self.substructures = []

	def split_fixed_len( self, f, cmdlen ) :
		# that cmdlen includes the terminator and cmd code+0xff Thus, -3.
		cmdlen -= 3
		self.payload = f.read( cmdlen )

		if Command.verbose :
			print( "fixed len. payload:" )
			print_bytes( self.payload )
			print()



	def split_var_len( self, f, cmdlen, ncmd ) :
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
		self.payload = f.read( read_cnt )

		if Command.verbose :
			print( "cmd_id: 0x%02X" % self.cmd_id )
			print( "spit_var_len.ncmd:", ncmd )
			print( "cheat: ", end="" )
			print_bytes( payload )
			print( "opos ~ pos:", opos, pos )
			print( "read", read_cnt, "bytes" )
			print( "Read varlen command: ", end="" )
			print_bytes( self.payload )
			print()



	def split_chunk1_uuid( self, f ) :
		cheat = f.getbuffer()

		f.read( 1 )
		l = read_byte( f )
		s1 = read_cstr( f, l )

		if Command.verbose :
			print_bytes( cheat )
			print( "chunk thingy:" )
			print( "0x%02X" % self.cmd_id )
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



	def split_var_len2( self, f, cnt_skip, skip_after ) :
		payload = io.BytesIO()

		dunno = f.read( cnt_skip )
		l = read_byte( f )
		payload.write( dunno )
		payload.write( struct.pack( "B", l ) )
		
		payload.write( f.read( l*4 ) )
		payload.write( f.read( skip_after ) ) # consume
		self.payload = payload.getvalue()

	def split_0x2c( self, f ) :
		self.split_var_len2( f, 5, 4 )



	def split_0x00( self, f ) :
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

		self.payload = f.read( end-pos )



	def split_command( self, f, ncmd ) :
		self.cmd_id = read_byte( f )
		player_id = read_byte( f )
		self.player_id = int( player_id / 8 ) - 3 # 3 for KW.  for RA3, it should be 2.
		# Probably, that offset must be that neutral factions. (initial spike owners)

		if not self.cmd_id in CMDLENS :
			print( "Unknown command:" )
			print( "0x%02X" % self.cmd_id )
			print_bytes( f.getbuffer() )
			print()
			assert 0

		cmdlen = CMDLENS[ self.cmd_id ]

		if cmdlen > 0 :
			self.split_fixed_len( f, cmdlen )
		# more var len commands
		elif cmdlen < 0 :
			# var len cmds!
			self.split_var_len( f, cmdlen, ncmd )
		else :
			if self.cmd_id <= 0x03 or self.cmd_id >= 0xFA :
				# group designation command.
				assert self.cmd_id >= 0
				assert self.cmd_id <= 0xFF
				self.split_0x00( f )
			elif 0x04 <= self.cmd_id and self.cmd_id <= 0x0D :
				# group selection command.
				# I usually get 0x0A 0x?? 0xFF (length=3).
				# I sometimes get (rarely) 0x0A 0x00 0x00 0xFF
				self.split_0x00( f ) # same as 0x00, creep until FF.

			elif self.cmd_id == 0x0E :
				self.split_0x00( f ) # same as 0x00, creep until FF.
			elif self.cmd_id == 0x2D :
				#print( "split_cmd.ncmd:", ncmd )
				self.split_production_cmd( f )
			elif self.cmd_id == 0x28 :
				self.split_skill_target( f )
			elif self.cmd_id == 0x2C :
				self.split_0x2c( f )
			elif self.cmd_id == 0x31 :
				self.split_placedown_cmd( f )
			elif self.cmd_id == 0x36 :
				self.split_var_len2( f, 1, 4 )
			elif self.cmd_id == 0x8B :
				self.split_chunk1_uuid( f )
			else :
				print( "Unhandled command:" )
				print( "0x%02X" % self.cmd_id )
				print_bytes( f.getbuffer() )
				print()
				assert 0



	def split_production_cmd( self, f ) :
		# either short or long...
		# length 8 or length 26, it seems, refering to cnc3reader_impl.cpp.

		cheat = f.getbuffer()
	
		if Command.verbose :
			print( "Production splitting" )
			print( "0x%02X" % self.cmd_id )
			print( "cheat:" )
			print_bytes( cheat )
			print()

		if cheat[ f.tell() ] == 0xFF :
			# 0x2D command with NOTHING in int.
			self.payload = None # stub command can happen... omg
		elif cheat[ f.tell() + 5 ] == 0xFF :
			self.payload = f.read( 5 )
		else :
			self.payload = f.read( 23 )



	def decode_production_cmd( self ) :
		# either short or long...
		# length 8 or length 26, it seems, refering to cnc3reader_impl.cpp.

		if Command.verbose :
			print( "Production decoding" )
			print_bytes( self.payload )
		data = self.payload

		if not data :
			print( "End of game?" )
		elif len( data ) == 5 :
			print( "End of game?" )
		else :
			produced_by = uint42int( data[ 1:5 ] ) # probably.
			produced = uint42int( data[ 8:12 ] ) # This one is pretty sure
			cnt = data[ 17 ]

			if cnt > 0 :
				print( "5x ", end="" )
			if produced in UNITNAMES :
				#print( "Production of %s from 0x%08X" % (UNITNAMES[produced], produced_by) )
				print( "queue %s" % (UNITNAMES[produced]) )
			else :
				#print( "Production of 0x%08X from 0x%08X" % (produced, produced_by) )
				print( "queue 0x%08X" % produced )
			#print()



	# this skill targets GROUND.
	def decode_skill_xy( self ) :
		data = self.payload

		if Command.verbose :
			print( "decode_skill_xy" )
			print_bytes( data )

		x = uint42float( data[ 6:10] )
		y = uint42float( data[ 10:14] )
		power = uint42int( data[ 0:4 ] )

		if power in POWERNAMES :
			#print( "Skill use %s at (%f, %f)" % (POWERNAMES[power], x, y) )
			print( "%s" % POWERNAMES[power] )
		else :
			#print( "Skill use 0x%08X at (%f, %f)" % (power, x, y) )
			print( "skill 0x%08X" % (power) )



	# this skill targets GROUND, with two positions.
	# Obviously, only wormhole does that.
	def decode_skill_2xy( self ) :
		data = self.payload

		if Command.verbose :
			print( "decode_skill_2xy" )
			print_bytes( data )

		x1 = uint42float( data[ 16:20] )
		y1 = uint42float( data[ 20:24] )
		x2 = uint42float( data[ 28:32] )
		y2 = uint42float( data[ 32:36] )
		power = uint42int( data[ 0:4 ] )

		if power in POWERNAMES :
			#print( "Skill use %s at (%f, %f)-(%f, %f)" % (POWERNAMES[power], x1, y1, x2, y2) )
			print( "%s" % (POWERNAMES[power]) )
		else :
			print( "skill 0x%08X" % power )



	def decode_skill_targetless( self ) :
		data = self.payload

		if Command.verbose :
			print( "decode_skill_targetless" )
			print_bytes( data )

		power = uint42int( data[ 0:4 ] )
		# dunno about target, but it is certain that this is only used on walling
		# structures -_-

		if power in POWERNAMES :
			#print( "Skill use %s" % POWERNAMES[power] )
			print( "%s" % POWERNAMES[power] )
		else :
			#print( "Skill use 0x%08X" % power )
			print( "skill 0x%08X" % power )



	# this skill targets one exact unit.
	# sonic/laser fence that is.
	def split_skill_target( self, f ) :
		buf = f.getbuffer()
		cnt = buf[ f.tell() + 15 ]
		end = f.tell() + 4*(cnt+1) + 30
		self.payload = f.read( end - f.tell() - 1 )

		if Command.verbose :
			print( "split_skill_target" )
			print( "0x%02X" % self.cmd_id )
			print( "cheat: ", end="" )
			print_bytes( buf )
			print( "end:", end )
			print( "payload:", end="" )
			print_bytes( self.payload )
			print()



	# this skill targets GROUND.
	def decode_skill_target( self ) :
		data = self.payload

		if Command.verbose :
			print( "decode_skill_target" )
			print_bytes( data )

		power = uint42int( data[ 0:4 ] )
		# dunno about target, but it is certain that this is only used on walling
		# structures -_-

		if power in POWERNAMES :
			#print( "Skill use %s" % POWERNAMES[power] )
			print( "%s" % POWERNAMES[power] )
		else :
			#print( "Skill use 0x%08X" % power )
			print( "skill 0x%08X" % power )



	def decode_upgrade_cmd( self ) :
		data = self.payload

		if Command.verbose :
			print( "decode_upgrade_cmd" )
			print_bytes( data )

		upgrade = uint42int( data[1:5] )
		if upgrade in UPGRADENAMES :
			#print( "Upgrade purchase of %s" % UPGRADENAMES[upgrade] )
			print( "%s" % UPGRADENAMES[upgrade] )
		else :
			#print( "Upgrade purchase of 0x%08X" % upgrade )
			print( "upgrade 0x%08X" % upgrade )
	


	def split_placedown_cmd( self, f ) :
		payload = io.BytesIO()
		buf = f.read( 10 ) # dunno what this is.
		payload.write( buf )
		substructure_cnt = f.read( 1 )
		payload.write( substructure_cnt )
		substructure_cnt = byte2int( substructure_cnt )
		payload.write( f.read( 18 * substructure_cnt ) )
		payload.write( f.read( 3 ) ) # more unknown stuff

		self.payload = payload.getbuffer()



	def decode_placedown_cmd( self ) :
		if Command.verbose :
			print( "PLACE DOWN" )
			print_bytes( self.payload )

		data = self.payload
		building_type = uint42int( data[6:10] )
		substructure_cnt = data[10]
		self.substructures = []

		pos = 11
		for i in range( substructure_cnt ) :
			pos += 4
			x = uint42float( data[pos:pos+4] )
			pos += 4
			y = uint42float( data[pos:pos+4] )
			pos += 6

		if building_type in UNITNAMES :
			#print( "building_type: %s" % UNITNAMES[building_type] )
			print( "%s" % UNITNAMES[building_type] )
		else :
			#print( "building_type: 0x%08X" % building_type )
			print( "place 0x%08X" % building_type )
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

		# old code...
		#unknown = f.read( 10 )
		#l = read_byte( f )
		#more_unknown = f.read( 18*l )
		#cmdlen = 3
		#more_unknown = f.read( 3 )
	


	def print_known( self ) :
		if not self.cmd_id in KNOWN_COMMANDS :
			return

		time = time_code2str( self.time_code/15 )
		print( time, end="\t" )
		print( "P" + str( self.player_id ), end="\t" )
		if self.cmd_id == 0x31 :
			self.decode_placedown_cmd()
		elif self.cmd_id == 0x26 :
			self.decode_skill_targetless()
		elif self.cmd_id == 0x27 :
			self.decode_skill_xy()
		elif self.cmd_id == 0x28 :
			self.decode_skill_target()
		elif self.cmd_id == 0x2B :
			self.decode_upgrade_cmd()
		elif self.cmd_id == 0x2D :
			self.decode_production_cmd()
		elif self.cmd_id == 0x2E :
			print( "hold/cancel/cancel_all production" )
		elif self.cmd_id == 0x8A :
			self.decode_skill_2xy()
		elif self.cmd_id == 0x34 :
			print( "sell" )
		elif self.cmd_id == 0x91 :
			print( "P" + str(self.payload[1]) + " GG" )
		#print()



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
	
	def split( self ) :
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
			self.split_commands( self.ncmd, self.payload )
			assert len( self.commands ) == self.ncmd

			for cmd in self.commands :
				cmd.time_code = self.time_code



	# Currently, I can't decode very well.
	# I only extract what I can... T.T
	def split_commands( self, ncmd, payload ) :
		f = io.BytesIO( payload )
		#print( "COMMANDS payload:", payload )

		for i in range( ncmd ) :
			c = Command()
			self.commands.append( c )
			c.split_command( f, ncmd )

			terminator = read_byte( f )
			#terminator = 0xFF
			if terminator != 0xFF :
				print( "Decode error" )
				print( "ncmd:", ncmd )
				print( "cmd_id: 0x%02X" % c.cmd_id )
				print( "Payload:" )
				print_bytes( payload )
				print( "TERMINATOR: 0x%02X" % terminator )
				print( f.read() )
			assert terminator == 0xFF



	def print( self ) :
		self.decode()

		if self.ty == 1 :
			if cmd_id in CMDNAMES :
				print( "---" )
				print( CMDNAMES[ cmd_id ] )
				print( "---" )
			print( "player_id:", player_id )
			print( "cmd_id: 0x%X" % cmd_id )

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
	
	def has_known( self ) :
		for cmd in self.commands :
			if cmd.cmd_id in KNOWN_COMMANDS :
				return True
		return False
	
	def dump_commands( self ) :
		# print( "Time\tPlayer\tcmd_id\tparams" )
		for cmd in self.commands :
			# Skipping stuff
			# print tag or interpretation for readability.
			if cmd.cmd_id == 0x8F :
				# print( "Lets not see scrolls" )
				continue
			elif cmd.cmd_id == 0x61 :
				# skip heartbeat
				continue
			#elif cmd.cmd_id == 0x2F :
			#	continue
			#elif cmd.cmd_id == 0xF8 :
			#	continue
			#elif cmd.cmd_id == 0xF5 : # select unit command.
			#	continue
			# * Even if nothing gets selected by the drag selection,
			#   it does appear in the command list!
			# * It seems the units that are selected are listed in the selection.
			#   The command gets longer as more units are selected.

			elif cmd.cmd_id in KNOWN_COMMANDS :
				cmd.print_known()
			elif cmd.cmd_id in CMDNAMES :
				print( CMDNAMES[ cmd.cmd_id ] )
			else :
				print( "unknown command" )

			print( cmd.time_code, end="\t" )
			print( cmd.player_id, end="\t" )
			print( "0x%02X" % cmd.cmd_id, end="\t" )
			print_bytes( cmd.payload, break16=False )
			print()
	
	def print_known( self ) :
		if self.ty == 1 :
			if not self.has_known() :
				return

			for cmd in self.commands :
				cmd.print_known()

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
	
	

class ReplayBody :
	def __init__( self, f ) :
		self.chunks = []
		self.loadFromStream( f )
	
	def read_chunk( self, f ) :
		chunk = Chunk()
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
	
		chunk.split()
		return chunk
	
	def loadFromStream( self, f ) :
		while True :
			chunk = self.read_chunk( f )
			if chunk == None :
				break
			self.chunks.append( chunk )
	
	def print_known( self ) :
		print( "Dump of known build order related commands" )
		print( "Time\tPlayer\tAction" )
		for chunk in self.chunks :
			chunk.print_known()
	
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
	#kw.replay_body.print_known()
	#kw.replay_body.dump_commands()

if __name__ == "__main__" :
	main()

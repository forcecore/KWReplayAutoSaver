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



# Build order affecting commands (Which will be drawn in the time line)
BO_COMMANDS = [ 0x31, 0x26, 0x27, 0x28, 0x2B, 0x2D, 0x2E, 0x8A, 0x34, 0x91 ]



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
			print( "Warning: unknown command. FF creeping." )
			self.split_0x00( f ) # same as 0x00, creep until FF.
			return

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
			elif self.cmd_id == 0x1F :
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
			elif self.cmd_id == 0x7F :
				self.split_0x00( f ) # same as 0x00, creep until FF.
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
	


	def decode_sell_cmd( self ) :
		self.target = uint42int( self.payload[ 1:5 ] )

	def decode_powerdown_cmd( self ) :
		self.decode_sell_cmd() # this works for powerdown, too.



	def decode_queue_cmd( self ) :
		data = self.payload

		if not data :
			self.unit_ty = None # end of game marker?
		elif len( data ) == 5 :
			self.unit_ty = None # end of game marker?
		else :
			self.factory = uint42int( data[ 1:5 ] )
			self.unit_ty = uint42int( data[ 8:12 ] ) # This one is pretty sure
			self.cnt = 1 # how many queued?
			fivex = data[ 17 ]
			if fivex :
				if self.unit_ty in [ 
						0x6AA59D16, # Nod vertigo
						0x393E446C, # MoK vertigo
						0xB587039F, # GDI orca
						0xB3363EA3, # GDI firehawk
						0x6BD7B8AB, # ST orca
						0x42D55831, # ST FH
						0xFAA68740, # Zorca
						0x12E1C8C8, # ZCM FH
						0xF6E707D5, # SC storm rider
						0x1DF82E16, # R17 storm rider
						0xECA08561 # T59 storm rider
						] :
					self.cnt = 4
					# Actually, fivex just tells us that it is
					# shift + click on the unit produciton button.
					# For normal units, it is definitely 5x.
					# But for these air units, it could be
					# 1 ~ 4, depending on the space left on the landing pad.
				else :
					self.cnt = 5



	# queue units to be built from the factory,
	# or resume build (from suspended building)
	def print_queue_cmd( self ) :
		# either short or long...
		# length 8 or length 26, it seems, refering to cnc3reader_impl.cpp.

		if Command.verbose :
			print( "Production decoding" )
			print_bytes( self.payload )

		self.decode_queue_cmd()

		if not self.unit_ty :
			print( "End of game?" )
		else :
			if self.cnt > 1 :
				print( str(self.cnt) + "x ", end="" )
			if self.unit_ty in UNITNAMES :
				#print( "Production of %s from 0x%08X" % (UNITNAMES[produced], produced_by) )
				print( "queue %s" % (UNITNAMES[self.unit_ty]) )
			else :
				#print( "Production of 0x%08X from 0x%08X" % (produced, produced_by) )
				print( "queue 0x%08X" % self.unit_ty )
			#print()



	def decode_skill_xy( self ) :
		data = self.payload
		self.x = uint42float( data[ 6:10] )
		self.y = uint42float( data[ 10:14] )
		self.power = uint42int( data[ 0:4 ] )

	# this skill targets GROUND.
	def print_skill_xy( self ) :
		if Command.verbose :
			print( "print_skill_xy" )
			print_bytes( data )

		self.decode_skill_xy()

		if self.power in POWERNAMES :
			#print( "Skill use %s at (%f, %f)" % (POWERNAMES[power], x, y) )
			print( "%s" % POWERNAMES[self.power] )
		else :
			#print( "Skill use 0x%08X at (%f, %f)" % (power, x, y) )
			print( "skill 0x%08X" % (self.power) )



	def decode_skill_2xy( self ) :
		data = self.payload
		self.x1 = uint42float( data[ 16:20] )
		self.y1 = uint42float( data[ 20:24] )
		self.x2 = uint42float( data[ 28:32] )
		self.y2 = uint42float( data[ 32:36] )
		self.power = uint42int( data[ 0:4 ] )

	# this skill targets GROUND, with two positions.
	# Obviously, only wormhole does that.
	def print_skill_2xy( self ) :
		if Command.verbose :
			print( "print_skill_2xy" )
			print_bytes( data )

		self.decode_skill_2xy()

		if self.power in POWERNAMES :
			#print( "Skill use %s at (%f, %f)-(%f, %f)" % (POWERNAMES[power], x1, y1, x2, y2) )
			print( "%s" % (POWERNAMES[self.power]) )
		else :
			print( "skill 0x%08X" % self.power )
	


	def decode_skill_targetless( self ) :
		data = self.payload
		self.power = uint42int( data[ 0:4 ] )



	def print_skill_targetless( self ) :
		if Command.verbose :
			print( "print_skill_targetless" )
			print_bytes( data )

		self.decode_skill_targetless()

		if self.power in POWERNAMES :
			#print( "Skill use %s" % POWERNAMES[power] )
			print( "%s" % POWERNAMES[self.power] )
		else :
			#print( "Skill use 0x%08X" % power )
			print( "skill 0x%08X" % self.power )



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



	def decode_skill_target( self ) :
		data = self.payload
		self.power = uint42int( data[ 0:4 ] )
		# dunno about target, but it is certain that this is only used on walling
		# structures -_-

	# this skill targets GROUND.
	def print_skill_target( self ) :
		if Command.verbose :
			print( "print_skill_target" )
			print_bytes( data )

		self.decode_skill_target()

		if self.power in POWERNAMES :
			#print( "Skill use %s" % POWERNAMES[power] )
			print( "%s" % POWERNAMES[self.power] )
		else :
			#print( "Skill use 0x%08X" % power )
			print( "skill 0x%08X" % self.power )



	def decode_upgrade_cmd( self ) :
		data = self.payload
		self.upgrade = uint42int( data[1:5] )

	def print_upgrade_cmd( self ) :
		if Command.verbose :
			print( "decode_upgrade_cmd" )
			print_bytes( data )

		self.decode_upgrade_cmd()

		if self.upgrade in UPGRADENAMES :
			#print( "Upgrade purchase of %s" % UPGRADENAMES[upgrade] )
			print( "%s" % UPGRADENAMES[self.upgrade] )
		else :
			#print( "Upgrade purchase of 0x%08X" % upgrade )
			print( "upgrade 0x%08X" % self.upgrade )
	


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
	


	def decode_hold_cmd( self ) :
		data = self.payload
		self.factory = uint42int( data[ 1:5 ] )
		self.unit_ty = uint42int( data[ 8:12 ] )
		self.cancel_all = data[13] # remove all build queue of this type
	


	def decode_formation_move_cmd( self ) :
		self.decode_move_cmd() # seems to work, though there are more parameters.
		#data = self.payload
		#self.x = uint42float( data[ 1:5 ] )
		#self.y = uint42float( data[ 5:9 ] )

	def decode_move_cmd( self ) :
		data = self.payload
		self.x = uint42float( data[ 1:5 ] )
		self.y = uint42float( data[ 5:9 ] )
		#self.z = uint42float( data[ 9:13 ] ) # it really seems to be Z;;;

	def decode_reverse_move_cmd( self ) :
		self.decode_move_cmd() # this will do
	


	def decode_placedown_cmd( self ) :
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



	def print_placedown_cmd( self ) :
		if Command.verbose :
			print( "PLACE DOWN" )
			print_bytes( self.payload )

		self.decode_placedown_cmd()

		if self.building_type in UNITNAMES :
			#print( "building_type: %s" % UNITNAMES[building_type] )
			print( "%s" % UNITNAMES[self.building_type] )
		else :
			#print( "building_type: 0x%08X" % building_type )
			print( "place 0x%08X" % self.building_type )
		#print( "pos: %f, %f" % (self.x, self.y) )



	def print_bo( self ) :
		if not self.cmd_id in BO_COMMANDS :
			return

		time = time_code2str( self.time_code/15 )
		print( time, end="\t" )
		print( "P" + str( self.player_id ), end="\t" )
		if self.cmd_id == 0x31 :
			self.print_placedown_cmd()
		elif self.cmd_id == 0x26 :
			self.print_skill_targetless()
		elif self.cmd_id == 0x27 :
			self.print_skill_xy()
		elif self.cmd_id == 0x28 :
			self.print_skill_target()
		elif self.cmd_id == 0x2B :
			self.print_upgrade_cmd()
		elif self.cmd_id == 0x2D :
			self.print_queue_cmd()
		elif self.cmd_id == 0x2E :
			print( "hold/cancel/cancel_all production" )
		elif self.cmd_id == 0x8A :
			self.print_skill_2xy()
		elif self.cmd_id == 0x34 :
			print( "sell" )
		elif self.cmd_id == 0x91 :
			print( "P" + str(self.payload[1]) + " GG" )
		#print()



class OldChunk :
	# I split commands, before decoding anything.
	# Not on the fly. It makes command decoding/hacking much easier.
	def split_commands( self, ncmd, payload, game ) :
		f = io.BytesIO( payload )
		#print( "COMMANDS payload:", payload )

		for i in range( ncmd ) :
			c = Command()
			self.commands.append( c )
			c.split_command( f, ncmd )

			# If you see error here, it means, command length specification
			# in consts.py is wrong. You need to work out the format of the
			# command.
			try :
				terminator = read_byte( f )
				if terminator != 0xFF :
					raise IOError
			except :
				# or if you reach here, again, command length is wrong.
				print( "Decode error" )
				print( "ncmd:", ncmd )
				print( "cmd_id: 0x%02X" % c.cmd_id )
				print( "Payload:" )
				print_bytes( payload )
				#print( "TERMINATOR: 0x%02X" % terminator )
				#print( f.read() )
				assert 0, "Command terminator not 0xFF"


	
	def has_known( self ) :
		for cmd in self.commands :
			if cmd.cmd_id in BO_COMMANDS :
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

			elif cmd.cmd_id in BO_COMMANDS :
				cmd.decode()
				cmd.print_bo()
			elif cmd.cmd_id in CMDNAMES :
				print( CMDNAMES[ cmd.cmd_id ] )
			else :
				print( "unknown command" )

			print( cmd.time_code, end="\t" )
			print( cmd.player_id, end="\t" )
			print( "0x%02X" % cmd.cmd_id, end="\t" )
			print_bytes( cmd.payload, break16=False )
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
				print( "Warning: chunk/command count mismatch!" )

			for cmd in self.commands :
				cmd.time_code = self.time_code



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



	def has_bo_cmd( self ) :
		return False



	def print_bo( self ) :
		if self.ty == 1 :
			if not self.has_bo_cmd() :
				return

			for cmd in self.commands :
				cmd.decode()
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
			print( "time_code:", self.time_code )
			print( "ncmd:", self.ncmd )
			print_bytes( self.payload )
			print()

		for cmd in self.commands :
			if self.is_bo_cmd( cmd ) :
				cmd.decode()
				cmd.print_bo()
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

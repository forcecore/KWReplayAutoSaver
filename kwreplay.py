#!/usr/bin/python3
# coding: utf8

###
### http://www.gamereplays.org/community/index.php?showtopic=706067&st=0&p=7863248&#entry7863248
### The decoding of the replays format is credited to R Schneider.
###

import struct # bin file enc/dec
import sys
import os
import re
import io
import codecs
import datetime
import time
import hashlib



def encrypt( ip ) :
	m = hashlib.md5()
	m.update( ip.encode() )
	ip = m.hexdigest()
	#print( ip )
	return ip



def read_cstr( f, length ) :
	data = f.read( length )
	#s = struct.unpack( "18s", data )
	data = data.decode( "utf-8" )
	return data



def read_tb_str( f, length=-1 ) :
	buf = ""
	while True :
		l = f.read( 2 )
		l = struct.unpack( 'H', l )[ 0 ]
		if length == -1 and l == 0 :
			break
		buf += chr( l )

		if length != -1 and len( buf ) == length :
			break

	#data = buf.decode( "utf-16" )
	return buf



def read_byte( f ) :
	data = f.read( 1 )
	data = struct.unpack( 'B', data )[0]
	return data



def read_float( f ) :
	data = f.read( 4 )
	data = struct.unpack( 'f', data )[0]
	return data



def read_uint32( f ) :
	tmp = f.read( 4 )
	i = struct.unpack( 'I', tmp )[ 0 ]
	return i



def time_code2str( tc ) :
	t = time.gmtime( tc )
	return time.strftime( "%H:%M:%S", t )



class Player :
	kw_faction_tab = [
		'Rnd', 'Obs', 'PostCommentator',
		'f3', 'f4', 'GDI',
		'ST', 'ZCM', 'Nod',
		'BH', 'MoK', 'Sc',
		'R17', 'T59'
	]

	cnc3_faction_tab = [
		'Rnd', 'Obs', 'PostCommentator',
		'f3', 'f4', 'GDI',
		'Nod', 'Sc'
	]

	ra3_faction_tab = [
		'Obs', 'E', 'PostCommentator',
		'A', 'f4', 'f5',
		'Rnd', 'S'
	]

	ai_personality_tab = [
		'Rnd_pers', 'invalid',
		'Balanced', 'Rusher', 'Turtle', 'Guerilla', 'Streamroller'
	]

	kw_color_tab = [
		'Rnd_color', 'Blue', 'Yellow',
		'Green', 'Orange', 'Pink',
		'Purple', 'Red', 'Cyan'
	]

	ra3_color_tab = [
		'Rnd_color', 'Blue', 'Yellow',
		'Green', 'Orange', 'Pink',
		'Purple', 'Red', 'Cyan'
	]

	def decode_color( self ) :
		try :
			if self.game == "RA3" :
				color_tab = Player.ra3_color_tab
			else :
				color_tab = Player.kw_color_tab

			return color_tab[ self.color + 1 ]
		except IndexError :
			return "Unknown"

	def decode_ai_personality( pers ) :
		return Player.ai_personality_tab[ pers + 2 ]

	def decode_faction( self ) :
		faction_tab = Player.kw_faction_tab
		if self.game == "RA3" :
			faction_tab = Player.ra3_faction_tab
		elif self.game == "CNC3" :
			faction_tab = Player.cnc3_faction_tab

		return faction_tab[ self.faction-1 ]

	def __init__( self, game="KW" ) :
		self.is_ai = False
		#self.id = "" # gamespy ID, which we will abandon.
		self.name = ""
		self.team = -1
		self.ip = "" # human only
		self.tt_or_ft = "" # human only
		self.faction = -1
		self.team = -1
		self.clan = "" # human only
		self.color = ""
		self.handicap = 0
		self.game = game
	
	def decode_human( self, data ) :
#형중주한 vs 정우영찬
#   name            ip             ?    ?   color, side,   ?  team  hcap            clan
#['HMacroHard',    '932E796D', '8094', 'TT', '-1',  '2', '-1', '-1', '0', '1', '-1', '']
#['HHeo',          '932E72E3', '8094', 'TT', '-1',  '6',  '4',  '3', '0', '1', '-1', '']
#['Hshj',          '932E7265', '8094', 'TT', '-1', '10',  '0',  '0', '0', '1', '-1', '']
#['Hjskang',       '932E722A', '8094', 'TT', '-1',  '2', '-1', '-1', '0', '1', '-1', '']
#['H마크오브루루', '932E836F', '8094', 'TT', '-1',  '9',  '5',  '0', '0', '1', '-1', '']
#['H최      자',   '932E7D34', '8094', 'TT', '-1', '13',  '1',  '3', '0', '1', '-1', '']
		self.ip = encrypt( data[1] )
		unknown = data[2]
		self.tt_or_ft = data[3]
		self.color = data[4]
		self.faction = data[5]
		unknown = data[6]
		self.team = data[7]
		unknown = data[8]
		self.handicap = data[9]
		unknown = data[10]
		self.clan = data[11]
		self.name = self.name[1:]
	
	def is_observer( self ) :
		if self.game == "RA3" :
			return self.faction == 1
		else :
			return self.faction == 2

	def is_commentator( self ) :
		if self.name == "post Commentator" :
			return True
		if self.faction == 3 :
			return True
		return False

	# An AI is a player.
	def is_player( self ) :
		if self.is_ai :
			return True
		else :
			return self.is_human_player()

	# By 'player', observer is not a player.
	# Nobody needs to consider post Commentator.
	def is_human_player( self ) :
		if self.is_ai :
			return False
		if self.is_commentator() :
			return False
		if self.is_observer() :
			return False
		return True
	
	def decode_ai( self, data ) :
		# 0  1 2  3  4   5 6
		# CH,6,1,-1,-1,-35,0
		self.is_ai = True
		self.color = data[1]
		self.faction = data[2]
		unknown = data[3]
		self.team = data[4]
		self.handicap = data[5]
		ai_personality = data[6]

		name = self.name
		if name == "CE" :
			name = "Easy (AI)"
		elif name == "CM" :
			name = "Medium (AI)"
		elif name == "CH" :
			name = "Hard (AI)"
		elif name == "CB" :
			name = "Brutal (AI)"
		self.name = name

		self.ai_personality = int( ai_personality )

	def decode( self, p ) :
		#print( p )
		data = p.split( "," )
		self.name = data[0]
		if self.name.startswith( "H" ) :
			self.decode_human( data )
		elif self.name.startswith( "C" ) :
			self.decode_ai( data )
		else :
			# what is this? dunno.
			return None

		# some post touches.
		self.faction = int( self.faction )
		self.team = int( self.team ) + 1
		self.color = int( self.color )
		return self

	def __str__( self ) :
		props = [ self.name, self.decode_color(),
			self.decode_faction(), "team" + str( self.team ) ]

		if self.is_ai :
			props.append( Player.decode_ai_personality( self.ai_personality ) )
		return " ".join( props )



class KWReplay :
	def __init__( self, fname=None, verbose=False, game=None ) :
		self.game = game
		# game == "CNC3" for Tiberium Wars

		# These are Kane's Wrath constants
		self.MAGIC_SIZE = 18
		self.U1_SIZE = 33
		self.U2_SIZE = 19
		self.FOOTER_MAGIC_SIZE = 18 # for KW/CNC3

		self.verbose = verbose

		self.magic = None
		self.hnumber1 = 0

		self.vermajor = 0
		self.verminor = 0
		self.buildmajor = 0
		self.buildminor = 0

		self.title = ""
		self.desc = ""
		self.map_name = ""
		self.map_id = ""
		self.map_path = ""
		self.mc = "" # map CRC

		self.mod_info = None # only in RA3/TW

		self.replay_saver = 0
		self.player_cnt = 0
		self.players = None

		self.timestamp = 0

		if fname :
			self.loadFromFile( fname )



	# Opens a file fname and modifies the description part.
	# No reading other info, but just does hex editing to desc part only.
	# Warning: the file is modified, in place!
	def modify_desc( self, srcf, destf, desc ) :
		f = open( srcf, 'rb' )
		g = open( destf, 'wb' )

		self.modify_desc_stream( f, g, desc )

		f.close()
		g.close()

	def modify_desc_inplace( self, fname, desc ) :
		g = io.BytesIO()
		f = open( fname, 'rb' )
		self.modify_desc_stream( f, g, desc )
		f.close()

		f = open( fname, 'wb' )
		f.write( g.getbuffer() )
		f.close()
		g.close()

	# ummm... I think I can read all game data then write again,
	# in the future...
	def modify_desc_stream( self, f, g, desc ) :
		# these are based on loadFromFile function.
		self.magic = read_cstr( f, self.MAGIC_SIZE ) # magic
		self.write_cstr( g, self.magic ) # write to dest

		self.hnumber1 = self.game_network_info( f ) # skip network info
		self.write_game_network_info( g, self.hnumber1 )

		self.set_ver_info( f ) # skip ver info
		self.write_ver_info( g )

		self.title = read_tb_str( f ) # game title
		self.write_tb_str( g, self.title )

		# now here comes the game description
		old_desc = read_tb_str( f )
		self.write_tb_str( g, desc ) # write new description

		# now copy the rest of the stream as is.
		buf = f.read()
		g.write( buf )

	def decode_timestamp( self, stamp, date_format=None ) :
		t = datetime.datetime.fromtimestamp( stamp )
		if date_format == None :
			stamp = t.strftime("%Y-%m-%dT%H%M")
		else :
			stamp = t.strftime( date_format )
		return stamp
	


	def guess_game( self, fname ) :
		if self.game == None :
			# Guess game replay type from the extension.
			# Defaults to KW.
			prefix, ext = os.path.splitext( fname )
			ext = ext.lower()

			if ext == ".cnc3replay" :
				self.game = "CNC3"
			elif ext == ".ra3replay" :
				self.game = "RA3"
				self.MAGIC_SIZE = 17
				self.U1_SIZE = 31
				self.U2_SIZE = 20
			else :
				self.game = "KW"

		if self.verbose :
			print( "Replay for game:", self.game )



	def loadFromFile( self, fname ) :
		self.guess_game( fname )
		f = open( fname, 'rb' )
		self.loadFromStream( f )
		f.close()



	def loadFromStream( self, f ) :
		self.magic = read_cstr( f, self.MAGIC_SIZE )
		if self.verbose :
			print( "-- header" )
			print( self.magic )
			print()

		self.hnumber1 = self.game_network_info( f )
		
		self.set_ver_info( f )

		# match title
		self.title = read_tb_str( f )
		if self.verbose :
			print( "-- game title" )
			print( self.title )
			print()

		# match description
		self.desc = read_tb_str( f )
		if self.verbose :
			print( "-- game description" )
			print( self.desc )
			print()

		# map name
		self.map_name = read_tb_str( f )
		if self.verbose :
			print( "-- map name" )
			print( self.map_name )
			print()

		# map ID
		self.map_id = read_tb_str( f )
		if self.verbose :
			print( "-- map ID" )
			print( self.map_id )
			print()

		# Players...
		#print( "-- players:" )
		self.player_cnt = read_byte( f )
		#self.players = []
		for i in range( self.player_cnt + 1 ) : # one extra dummy player exists!
			# We don't have much info here.
			# We'll read much more info from plain text player info.
			self.read_player( f )
		#print()

		offset = read_uint32( f )
		str_repl_length = read_uint32( f ) # always == 8
		repl_magic = read_cstr( f, str_repl_length )

		if self.game == "CNC3" or self.game == "RA3" :
			self.mod_info = read_cstr( f, 22 )

		if self.verbose :
			print( "-- replay magic:" )
			print( str_repl_length )
			print( repl_magic )
			print()

		# not TW nor RA3, no mod_info[22].
		#mod_info = f.read( 22 )
		#print( "-- mod info" )
		#print( mod_info )
		#print()

		self.timestamp = read_uint32( f )
		if self.verbose :
			print( "-- timestamp" )
			print( self.decode_timestamp( self.timestamp ) )
			print()

		data = f.read( self.U1_SIZE )
		if self.verbose :
			print( "-- unknown 1" )
			print( data )
			print()

		header_len = read_uint32( f )
		header = read_cstr( f, header_len )
		if self.verbose :
			print( "-- header" )
			print( header_len )
			print( header )
			print()

		self.replay_saver = read_byte( f )
		if self.verbose :
			print( "-- replay saver" )
			print( self.replay_saver )
			print()

		zero3 = read_uint32( f )
		zero4 = read_uint32( f )
		#assert zero3 == 0
		#assert zero4 == 0

		filename_length = read_uint32( f )
		filename = read_tb_str( f, length=filename_length )
		if self.verbose :
			print( "-- original replay file name: " )
			print( filename_length )
			print( filename )
			print()

		date_time = read_tb_str( f, length=8 )
		if self.verbose :
			print( "-- date time" )
			#print( date_time )
			print( "not printing..." ) # 'cos it induces encoding error.
			# which is not impossible but a tedious work to fix.
			print()



		vermagic_len = read_uint32( f )
		vermagic = read_cstr( f, vermagic_len )
		if self.verbose :
			print( "vermagic:", vermagic )

		magic_hash = read_uint32( f )

		zero5 = f.read( 1 ) # well, the second zero4, in eareplay.html

		data = f.read( self.U2_SIZE*4 ) # uint32_t of length U2_SIZE

		self.decode_header_and_set( header )
	


	def decode_header_and_set( self, header ) :
		if self.verbose :
			print( "-- header decoding" )
			print( header )

		data = header.split( ";" )
		for info in data :
			pair = info.split( "=" )
			#print( pair )

			if len( pair ) == 2 :
				self.decode_pair( pair )



	def decode_header_player( self, p ) :
		player = Player( game=self.game )
		player = player.decode( p )
		return player




	def decode_header_players( self, txt ) :
		result = []

		players = txt.split( ":" )

		if self.verbose :
			print()
			print( "-- Raw player info" )
			for p in players :
				print( p )

		for p in players :
			player = self.decode_header_player( p )
			if player != None :
				result.append( player )

		return result



	def decode_pair( self, pair ) :
		lhs = pair[ 0 ]
		rhs = pair[ 1 ]

		if lhs == "M" :
			# full map path!!!
			lhs = "Map"
			self.map_path = rhs
		elif lhs == "MC" :
			lhs = "Map CRC"
			self.mc = rhs
		elif lhs == "MS" :
			lhs = "Map file size"
		elif lhs == "SD" :
			lhs = "Seed?"
		elif lhs == "GSID" :
			lhs = "Gamespy match ID"
		elif lhs == "GT" :
			lhs = "Game Type?"
		elif lhs == "PC" :
			lhs = "Post Commentator"
		elif lhs == "RU" :
			lhs = "Game initialization information (starting money... etc.)"
		elif lhs == "S" :
			lhs = "Players"
			rhs_data = self.decode_header_players( rhs )
			self.players = rhs_data

			if self.verbose :
				print( "-- decoded player info" )
				for p in self.players :
					print( p )
				print()
			#print( rhs_data )

		if self.verbose :
			print( lhs + ":\n\t" + rhs )
	


	def read_player( self, f ) :
		player_id = read_uint32( f )
		player_name = read_tb_str( f )

		if self.hnumber1 == 5 : # internet game has "team info".
			team = read_byte( f )
		else :
			team = 0
	
		if self.verbose :
			print( "\t", player_id, player_name, team )
	


	def write_ver_info( self, f ) :
		self.write_uint32( f, self.vermajor )
		self.write_uint32( f, self.verminor )
		self.write_uint32( f, self.buildmajor )
		self.write_uint32( f, self.buildminor )

	def set_ver_info( self, f ) :
		self.vermajor = read_uint32( f )
		self.verminor = read_uint32( f )
		self.buildmajor = read_uint32( f )
		self.buildminor = read_uint32( f )

		if self.verbose :
			print( "-- build info" )
			print( "Version Major:", self.vermajor )
			print( "Version Minor:", self.verminor )
			print( "Build Major:", self.buildmajor )
			print( "Build Minor:", self.buildminor )
			print()



	def write_uint32( self, f, val ) :
		data = struct.pack( 'I', val )
		f.write( data )
	


	def write_tb_str( self, f, string, write_len=False ) :
		if write_len :
			self.write_uint32( len( string ) )

		# string data
		data = string.encode( "utf-16le" )
		f.write( data )

		if not write_len :
			# 2 bytes of zero for null termination.
			self.write_byte( f, 0 )
			self.write_byte( f, 0 ) # null termination, if not writing len.



	def write_byte( self, f, data ) :
		data = struct.pack( 'b', data )
		f.write( data )



	def game_network_info( self, f ) :
		data = read_byte( f )

		if self.verbose :
			print( "-- game network info" )
			if data == 5 :
				print( "Internet game" )
			elif data == 4 :
				print( "Network game" )
			else :
				print( "Skirmish? Dunno:", data )
			print()

		return data

	def write_game_network_info( self, f, hnumber1 ) :
		self.write_byte( f, hnumber1 )

	def write_cstr( self, f, data ) :
		#data = data.encode( "utf-8" )
		data = data.encode( "ascii" ) # cstr is meant to be ascii.
		f.write( data )

###
###
###
def main() :
	fname = "1.KWReplay"
	if len( sys.argv ) >= 2 :
		fname = sys.argv[1]
	kw = KWReplay( fname=fname, verbose=True )
	#kw = KWReplay()
	#kw.modify_desc( fname, "2.KWReplay", "매치 설명 있음" )
	#kw.modify_desc_inplace( "2.KWReplay", "show me the money 오예" )

if __name__ == "__main__" :
	main()

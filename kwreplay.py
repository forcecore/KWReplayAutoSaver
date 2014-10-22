#!/usr/bin/python3
# coding: utf8

###
### http://www.gamereplays.org/community/index.php?showtopic=706067&st=0&p=7863248&#entry7863248
### The decoding of the replays format is credited to R Schneider.
###

import struct # bin file enc/dec
import sys
import re
import codecs
import datetime



class Player :
	faction_tab = [
		'Rnd_faction', 'Obs', 'PostCommentator',
		'f3', 'f4', 'GDI',
		'ST', 'ZCM', 'Nod',
		'BH', 'MoK', 'Sc',
		'R17', 'T59'
	]

	ai_personality_tab = [
		'Rnd_pers', 'invalid',
		'Balanced', 'Rusher', 'Turtle', 'Guerilla', 'Streamroller'
	]

	color_tab = [
		'Rnd_color', 'Blue', 'Yellow',
		'Green', 'Orange', 'Pink',
		'Purple', 'Red', 'Cyan'
	]

	def decode_color( color ) :
		return Player.color_tab[ color + 1 ]

	def decode_ai_personality( pers ) :
		return Player.ai_personality_tab[ pers + 2 ]

	def decode_faction( fact ) :
		return Player.faction_tab[ fact-1 ]

	def __init__( self ) :
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
	
	def decode_human( self, data ) :
#형중주한 vs 정우영찬
#   name            ip             ?    ?   color, side,   ?  team  hcap            clan
#['HMacroHard',    '932E796D', '8094', 'TT', '-1',  '2', '-1', '-1', '0', '1', '-1', '']
#['HHeo',          '932E72E3', '8094', 'TT', '-1',  '6',  '4',  '3', '0', '1', '-1', '']
#['Hshj',          '932E7265', '8094', 'TT', '-1', '10',  '0',  '0', '0', '1', '-1', '']
#['Hjskang',       '932E722A', '8094', 'TT', '-1',  '2', '-1', '-1', '0', '1', '-1', '']
#['H마크오브루루', '932E836F', '8094', 'TT', '-1',  '9',  '5',  '0', '0', '1', '-1', '']
#['H최      자',   '932E7D34', '8094', 'TT', '-1', '13',  '1',  '3', '0', '1', '-1', '']
		self.ip = data[1]
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
		return self.faction == 2
	
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
		props = [ self.name, Player.decode_color( self.color ),
			Player.decode_faction( self.faction ), "team" + str( self.team ) ]
		if self.is_ai :
			props.append( Player.decode_ai_personality( self.ai_personality ) )
		return " ".join( props )



class KWReplay :
	def __init__( self, fname=None, verbose=False ) :
		# These are Kane's Wrath constants
		self.MAGIC_SIZE = 18
		self.U1_SIZE = 33
		self.U2_SIZE = 19

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

	# ummm... I think I can read all game data then write again,
	# in the future...
	def modify_desc_stream( self, f, g, desc ) :
		# these are based on loadFromFile function.
		self.magic = self.read_cstr( f, self.MAGIC_SIZE ) # magic
		self.write_cstr( g, self.magic ) # write to dest

		self.hnumber1 = self.game_network_info( f ) # skip network info
		self.write_game_network_info( g, self.hnumber1 )

		self.set_ver_info( f ) # skip ver info
		self.write_ver_info( g )

		self.title = self.read_tb_str( f ) # game title
		print( self.title )
		self.write_tb_str( g, self.title )

		# now here comes the game description
		old_desc = self.read_tb_str( f )
		self.write_tb_str( g, desc ) # write new description

		# now copy the rest of the stream as is.
		buf = f.read()
		g.write( buf )

	def decode_timestamp( self, stamp ) :
		t = datetime.datetime.fromtimestamp( stamp )
		stamp = t.strftime("%Y-%m-%dT%H%M")
		return stamp
	


	def loadFromFile( self, fname ) :
		f = open( fname, 'rb' )

		self.magic = self.read_cstr( f, self.MAGIC_SIZE )
		if self.verbose :
			print( "-- header" )
			print( self.magic )
			print()

		self.hnumber1 = self.game_network_info( f )
		
		self.set_ver_info( f )

		# match title
		self.title = self.read_tb_str( f )
		if self.verbose :
			print( "-- game title" )
			print( self.title )
			print()

		# match description
		self.desc = self.read_tb_str( f )
		if self.verbose :
			print( "-- game description" )
			print( self.desc )
			print()

		# map name
		self.map_name = self.read_tb_str( f )
		if self.verbose :
			print( "-- map name" )
			print( self.map_name )
			print()

		# map ID
		self.map_id = self.read_tb_str( f )
		if self.verbose :
			print( "-- map ID" )
			print( self.map_id )
			print()

		# Players...
		#print( "-- players:" )
		self.player_cnt = self.read_byte( f )
		#self.players = []
		for i in range( self.player_cnt + 1 ) : # one extra dummy player exists!
			# We don't have much info here.
			# We'll read much more info from plain text player info.
			self.read_player( f )
		#print()

		offset = self.read_uint32( f )
		str_repl_length = self.read_uint32( f ) # always == 8
		repl_magic = self.read_cstr( f, str_repl_length )

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

		self.timestamp = self.read_uint32( f )
		if self.verbose :
			print( "-- timestamp" )
			print( self.decode_timestamp( self.timestamp ) )
			print()

		data = f.read( self.U1_SIZE )
		if self.verbose :
			print( "-- unknown 1" )
			print( data )
			print()

		header_len = self.read_uint32( f )
		header = self.read_cstr( f, header_len )
		if self.verbose :
			print( "-- header" )
			print( header_len )
			print( header )
			print()

		self.replay_saver = self.read_byte( f )
		if self.verbose :
			print( "-- replay saver" )
			print( self.replay_saver )
			print()

		zero3 = self.read_uint32( f )
		zero4 = self.read_uint32( f )

		filename_length = self.read_uint32( f )
		filename = self.read_tb_str( f, length=filename_length )
		if self.verbose :
			print( "-- original replay file name: " )
			print( filename_length )
			print( filename )
			print()

		date_time = self.read_tb_str( f, length=8 )
		if self.verbose :
			print( "-- date time" )
			#print( date_time )
			print( "not printing..." ) # 'cos it induces encoding error.
			# which is not impossible but a tedious work to fix.
			print()

		self.decode_header_and_set( header )

		f.close()
	


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
		player = Player()
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
			lhs = "Map"
		elif lhs == "MC" :
			lhs = "Map CRC"
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
		player_id = self.read_uint32( f )
		player_name = self.read_tb_str( f )

		if self.hnumber1 == 5 : # internet game has "team info".
			team = self.read_byte( f )
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
		self.vermajor = self.read_uint32( f )
		self.verminor = self.read_uint32( f )
		self.buildmajor = self.read_uint32( f )
		self.buildminor = self.read_uint32( f )

		if self.verbose :
			print( "-- build info" )
			print( "Version Major:", self.vermajor )
			print( "Version Minor:", self.verminor )
			print( "Build Major:", self.buildmajor )
			print( "Build Minor:", self.buildminor )
			print()



	def read_uint32( self, f ) :
		tmp = f.read( 4 )
		i = struct.unpack( 'I', tmp )[ 0 ]
		return i

	def write_uint32( self, f, val ) :
		data = struct.pack( 'I', val )
		f.write( data )
	


	def read_tb_str( self, f, length=-1 ) :
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



	def read_byte( self, f ) :
		data = f.read( 1 )
		data = struct.unpack( 'b', data )[0]
		return data

	def write_byte( self, f, data ) :
		data = struct.pack( 'b', data )
		f.write( data )



	def game_network_info( self, f ) :
		data = self.read_byte( f )

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

	def read_cstr( self, f, length ) :
		data = f.read( length )
		#s = struct.unpack( "18s", data )
		data = data.decode( "utf-8" )
		return data

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
	#kw = KWReplay( fname=fname, verbose=True )
	kw = KWReplay()
	kw.modify_desc( fname, "2.KWReplay", "매치 설명 있음" )

if __name__ == "__main__" :
	main()

#!/usr/bin/python3
import os
import sys
import io
import shutil
from chunks import KWReplayWithCommands, uint42int, print_bytes
from kwreplay import KWReplay, read_byte, read_uint32, read_float, \
	read_cstr, time_code2str, read_tb_str

class KWReplayRepair( KWReplayWithCommands ) :

	def __init__( self, verbose=False ) :
		super().__init__( verbose=verbose )



	def read_footer( self, buf ) :
		end = len( buf )
		footer_len = uint42int( buf[ end-4:end ] )
		footer_data = buf[ end-footer_len:end ]
		print( "footer:" )
		print_bytes( footer_data )

		check = self.check_magic( footer_data, footer_len )
		if check :
			print( "Footer seems good" )
		else :
			print( "Bad footer" )
			print()
		return check
	


	def check_magic( self, footer_data, footer_len ) :
		stream = io.BytesIO( footer_data )
		if self.game == "RA3" :
			self.FOOTER_MAGIC_SIZE = 17
		magic = read_cstr( stream, self.FOOTER_MAGIC_SIZE )

		if self.game == "KW" or self.game == "CNC3" :
			if magic != "C&C3 REPLAY FOOTER" :
				return False
		elif self.game == "RA3" :
			if magic != "RA3 REPLAY FOOTER" :
				return False

		self.final_time_code = read_uint32( stream )

		data_len = footer_len - self.FOOTER_MAGIC_SIZE - 8

		data = stream.read( data_len )
		print( "footer_data:" )
		print_bytes( data )

		left_over = stream.read()
		sz = uint42int( left_over )
		if sz != footer_len :
			return False
	
		return True



	def repair( self, fname, game="KW" ) :
		self.game = game
		self.fname = fname

		# backup first.
		shutil.copyfile( fname, fname + ".bak" )

		f = open( fname, "rb" )
		buf = f.read()
		f.close()

		# Let's check footer.
		try :
			check = self.read_footer( buf )
			if check :
				print( "The replay seems good." )
				return
		except :
			print( "The footer is corrupt." )
			pass
	
		print( "Attempting repair" )

		# Open buf as stream again.
		f = io.BytesIO( buf )
		try :
			self.loadFromStream( f ) # This one goes through header.
		except :
			print( "The replay is beyond repair!" )
			sys.exit( 1 )

		print( "Header reading passed." )
		print( "Erm... aaaa TODO" )
		f.close()



def main() :
	corrupt = "corrupt/1.KWReplay"
	fine = "1.KWReplay"
	too_bad = "corrupt/fsck.KWReplay" # just make or copy any file that is not replay.
	kwr = KWReplayRepair()
	kwr.repair( corrupt )



if __name__ == "__main__" :
	main()

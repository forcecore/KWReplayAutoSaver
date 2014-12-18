#!/usr/bin/python3
import os
import sys
import io
import shutil
import struct
import traceback
from chunks import KWReplayWithCommands, uint42int, print_bytes, ReplayBody
from kwreplay import KWReplay, read_byte, read_uint32, read_float, \
	read_cstr, time_code2str, read_tb_str



def write_cstr( f, s, null_terminate = False ) :
	f.write( bytes( s, "UTF-8" ) ) # Erm... not exactly UTF-8 but it will work.



class HealingReplayBody( ReplayBody ) :
	def __init__( self, f ) :
		self.chunks = []
		self.creep_chunks( f )
	
	def creep_chunks( self, f ) :
		good_chunk_cnt = 0
		try :
			while True :
				pos = f.tell()
				chunk = self.read_chunk( f )
				if chunk == None :
					break
				chunk.pos = pos
				self.chunks.append( chunk )
				good_chunk_cnt += 1
		except struct.error :
			# This is the limit we reach. We stop reading chunks.
			pass
		except :
			print( "If you see me, please send the Replay to the developer so that" )
			print( "it might be repaired in the future." )
			raise
		print( "Last good chunk is Chunk #%d." % good_chunk_cnt )



class KWReplayRepair( KWReplayWithCommands ) :

	def __init__( self, verbose=False, force=False ) :
		super().__init__( verbose=verbose )
		self.force = force # force repair on good replays?



	def read_footer( self, buf ) :
		end = len( buf )
		footer_len = uint42int( buf[ end-4:end ] )
		if footer_len > 16*8 :
			print( "footer too long. Probably bad." )
			return False

		footer_data = buf[ end-footer_len:end ]
		print( "footer:" )
		print_bytes( footer_data )

		check = self.check_magic( footer_data, footer_len )
		if check :
			print( "Footer seems good" )
			print( "Not repairing." )
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
		if data_len > 16*8 :
			print( "footer too long. Probably bad." )
			return False

		data = stream.read( data_len )
		print( "footer_data:" )
		print_bytes( data )

		left_over = stream.read()
		sz = uint42int( left_over )
		if sz != footer_len :
			return False
	
		return True



	def creep_chunks( self, f ) :
		self.replay_body = HealingReplayBody( f )
	


	def repair( self, fname, ofname, game="KW" ) :
		self.game = game

		f = open( fname, "rb" )
		buf = f.read()
		f.close()

		# Let's check footer.
		try :
			check = self.read_footer( buf )
			if check :
				print( "The replay seems good." )
				if self.force :
					print( "Forced repair is set." )
				else :
					return
		except Exception as e:
			print( "The footer is corrupt as follows:" )
			traceback.print_exc()
	
		print( "Attempting repair" )

		# Open buf as stream again.
		f = io.BytesIO( buf )
		try :
			self.loadFromStream( f ) # This one goes through the header.
		except :
			print( "The replay is beyond repair! Even the header is corrupt." )
			sys.exit( 1 )

		self.creep_chunks( f ) # Read in good chunks
		f.close()



		# attempt repair
		prefix, fname = os.path.split( fname )

		f = open( ofname, "wb" )

		# At least 2 chunks to be meaningful;;
		assert len( self.replay_body.chunks ) > 2

		last_chunk = self.replay_body.chunks[-1]
		pos = last_chunk.pos

		print( "We discard one chunk, just in case the last one is bad." )
		good_stuff = buf[:pos] # If we do this, we are not actually writing the last chunk. This is intentional.
		f.write( good_stuff )

		last_written_chunk = self.replay_body.chunks[-2]

		# Lets write footer... hahahaha
		self.write_uint32( f, 0x7fffffff ) # chunk termination code.

		footer_len = 0

		if self.game == "KW" or self.game == "CNC3" :
			footer_len += 18
			write_cstr( f, "C&C3 REPLAY FOOTER" )
		elif self.game == "RA3" :
			footer_len += 17
			write_cstr( f, "RA3 REPLAY FOOTER" )

		# Write final time code.
		footer_len += 4
		self.write_uint32( f, last_written_chunk.time_code )

		# Write footer len.
		footer_len += 4
		self.write_uint32( f, footer_len )

		f.close()
		print( "Repaired. Hopefully." )



def main() :
	corrupt = "corrupt/1.KWReplay"
	fine = "1.KWReplay"
	too_bad = "corrupt/fsck.KWReplay" # just make or copy any file that is not replay.
	kwr = KWReplayRepair()
	kwr.repair( corrupt, "out.KWReplay" )



def mass_test() :
	prefix = "corrupt/bad_"
	for i in range( 200 ) :
		fname = prefix + str(i) + ".KWReplay"
		print( fname )
		kwr = KWReplayRepair()
		kwr.repair( fname, ofname )



if __name__ == "__main__" :
	main()
	#mass_test()

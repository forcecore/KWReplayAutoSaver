#!/usr/bin/python3
# -*- coding: utf8 -*-
import os, time, shutil
from kwreplay import KWReplay, Player



class FileSignature :
	def __init__( self ) :
		self.ctime = 0
		self.mtime = 0
		self.size = 0
	
	def __str__( self ) :
		return str( self.ctime ) + " " + str( self.mtime) + " " + str( self.size )



class Watcher :
	def __init__( self, fname, verbose=False ) :
		self.verbose = verbose
		self.last_replay = fname
		self.sig = self.get_file_signature( fname )

	def get_file_signature( self, fname ) :
		if not os.path.isfile( fname ) :
			return None
		sig = FileSignature()
		sig.ctime = os.path.getctime( fname )
		sig.mtime = os.path.getmtime( fname )
		sig.size = os.path.getsize( fname )
		return sig

	# returns true when polled and replay has been modified.
	# false otherwise.
	def poll( self ) :
		# If not exists, then still fine.
		if not os.path.isfile( self.last_replay ) :
			return False

		new_sig = self.get_file_signature( self.last_replay )

		# replay is in writing process
		if self.is_writing( self.last_replay ) :
			return False

		if not new_sig :
			# non-existent or something.
			self.sig = None
			return False

		# empty replay
		if new_sig.size == 0 :
			return False
	
		if self.sig == None : # implicitly new_sig != None
			self.sig = new_sig
			return True
	
		# no change
		if self.sig.mtime == new_sig.mtime :
			return False

		self.sig = new_sig
		return True



	###
	### copy the last replay to a tmp replay
	### then use the replay's time stamp to give the tmp replay a proper name.
	### Setting add_username to True will append user name to the replay name.
	###
	def do_renaming( self, fname, add_username ) :
		# where the replay dir is.
		path = os.path.dirname( fname )

		# Latch the replay file to a tmp file.
		tmpf = "tmp.kwr"
		shutil.copyfile( self.last_replay, tmpf )

		# analyze the replay and deduce its name
		r = KWReplay( fname=tmpf )
		newf = r.decode_timestamp( r.timestamp )

		if add_username :
			newf += " " + Watcher.player_list( r )

		newf += ".KWReplay" # don't forget the extension!

		# sanitize the names.
		for char in [ "<", ">", ":", "\"", "/", "\\", "|", "?", "*" ] :
			newf = newf.replace( char, "_" )

		newf = os.path.join( path, newf )

		os.replace( tmpf, newf )
		return newf
	


	# returns a nice readable list of players.
	# Actually only returns count and one player's name but anyway :S
	# r: da replay class
	def player_list( r ) :
		# count AI players.
		ai = 0
		h = 0
		for p in r.players :
			if p.is_ai :
				ai += 1
			else :
				# don't count post commentator!
				if p.name == "post Commentator" :
					continue
				if p.is_observer() : # don't count observer
					continue
				h += 1

		if h == 0 :
			# this can happen, when you observe and watch AIs fight each other, theoretically.
			return "AI only"
		elif h == 1 :
			if ai == 0 :
				return "Sandbox"
			else :
				return "vs AI"
		elif h == 2 :
			return "vs " + Watcher.find_a_nonsaver( r ).name
		else :
			return str( h ) + "p game with " + Watcher.find_a_nonsaver( r ).name



	# find any human player who is not the saver.
	# r: da replay class
	def find_a_nonsaver( r ) :
		for i, p in enumerate( r.players ) :
			# if non ai non saver non observer...
			if (not p.is_ai) and (i != r.replay_saver) and (not p.is_observer()) :
				return p
		return None



	###
	### Determine if the latest replay is occupied by the game.
	###
	def is_writing( self, fname ) :
		return not os.access( fname, os.W_OK )



def main() :
	watcher = Watcher( "최종 리플레이.KWReplay", verbose=True )
	# monitor file size change.
	print( watcher.sig )
	print( "Started monitoring" )

	while True :
		time.sleep (2)
		if watcher.poll() :
			newf = watcher.do_renaming( watcher.last_replay, True )
			print( watcher.sig )
			print( "Copied to", newf )



###
### main
###

if __name__ == "__main__" :
	main()

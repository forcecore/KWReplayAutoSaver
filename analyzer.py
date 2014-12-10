#!/usr/bin/python3

import sys
from chunks import KWReplayWithCommands



class KWReplayAnalyzer() :
	def __init__( self, kwr_chunks ) :
		self.kwr = kwr_chunks
		self.nplayers = len( self.kwr.players )



	# just group commands by time.
	def group_command_by_time( self, cmds_at_second, cmd ) :
		second = int( cmd.time_code / 15 )

		# alloc, if needed.
		while len( cmds_at_second ) <= second :
			#print( len(cmds_at_second), second, "appending" )
			cmds_at_second.append( [] )
		command_list = cmds_at_second[ second ]

		command_list.append( cmd )

	def group_commands_by_time( self ) :
		cmds_at_second = []
		# cmds_at_second[ sec ] = list of commands at that second.

		# except for heat beat, all are commands.
		for chunk in self.kwr.replay_body.chunks :
			for cmd in chunk.commands :
				self.group_command_by_time( cmds_at_second, cmd )

		return cmds_at_second

	

	def count_player_actions( self, interval, cmds_at_second ) :
		counts_at_second = [ [0]*self.nplayers for i in range( len( cmds_at_second ) ) ]
		# counts_at_second[ sec ][ pid ] = action counts at sec for that player.

		for sec in range( len( cmds_at_second ) ) :
			left = max( 0, sec - interval )

			# count commands!
			for t in range( left, sec+1 ) : # range [left, sec+1)
				for cmd in cmds_at_second[ sec ] :
					if cmd.cmd_id == 0x61 : # 30s heat beat
						continue
					pid = cmd.player_id
					assert pid <= 7 # real checker here hehe
					counts_at_second[ t ][ pid ] += 1

		return counts_at_second
	


	def emit_apm_csv( self, interval, file=sys.stdout ) :
		# actions counted for that second...
		counts_at_second = self.count_actions( interval )

		# print header
		print( "t", end=",", file=file )
		for player in self.kwr.players :
			print( player.name, end=",", file=file )
		print( file=file )

		for t in range( len( counts_at_second ) ) :
			counts = counts_at_second[ t ]
			print( t, end=",", file=file )
			for i in range( self.nplayers ) :
				apm = counts[ i ]
				apm *= 60/interval
				print( apm, end=",", file=file )
			print( file=file )



	# interval: collect this much commands to calculate APM.
	def count_actions( self, interval ) :
		cmds_at_second = self.group_commands_by_time()
		return self.count_player_actions( interval, cmds_at_second )



if __name__ == "__main__" :
	fname = "2.KWReplay"
	if len( sys.argv ) >= 2 :
		fname = sys.argv[1]
	kw = KWReplayWithCommands( fname=fname, verbose=False )
	#kw.replay_body.dump_commands()
	ana = KWReplayAnalyzer( kw )
	ana.emit_apm_csv( 60, file=sys.stdout )

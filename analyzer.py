#!/usr/bin/python3

import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from chunks import KWReplayWithCommands
from consts import UNITCOST, POWERCOST, UPGRADECOST



# Build queue simulator.
class BuildQ() :
	def __init__( self ) :
		# countdown[ UNIT_UID ] = time left for production complete.
		self.countdown = {}

		# counts of units to produce
		self.counts[ UNIT_UID ] = {}

		# the order of user input
		self.order = []



class ResourceAnalyzer() :
	def __init__( self, kwr_chunks ) :
		self.kwr = kwr_chunks
		self.nplayers = len( self.kwr.players )
		self.queues = [] # build queues (dynamic!)

		self.spents = [ None ] * self.nplayers # remember who spent what.
		# spents[ pid ] = [ (t1, cost1), (t2, cost2), ... ]



	def calc( self ) :
		# step 1. just collect how much is spent at time t, as a list.
		for chunk in self.kwr.replay_body.chunks :
			for cmd in chunk.commands :
				self.feed( cmd )



	def collect( self, pid, t, cost ) :
		if self.spents[ pid ] == None :
			self.spents[ pid ] = []
		spent = self.spents[ pid ]

		# OK, if the latest entry has the same t,
		# we merge the costs hehehe
		if len( spent ) > 1 :
			(old_t, old_cost) = spent[-1]
			if old_t == t :
				spent.pop()
				cost += old_cost

		spent.append( (t, cost) )



	def feed( self, cmd ) :
		t = int( cmd.time_code / 15 ) # in seconds
		if cmd.cmd_id == 0x31 : # place down building
			cmd.decode_placedown_cmd()
			if cmd.building_type in UNITCOST :
				self.collect( cmd.player_id, t, UNITCOST[ cmd.building_type ] )
		elif 0x26 <= cmd.cmd_id and cmd.cmd_id <= 0x28 : # use skill
			# decode 'em
			if cmd.cmd_id == 0x26 :
				cmd.decode_skill_targetless()
			elif cmd.cmd_id == 0x27 :
				cmd.decode_skill_xy()
			elif cmd.cmd_id == 0x28 :
				cmd.decode_skill_target()
			elif cmd.cmd_id == 0x8A :
				cmd.decode_skill_2xy()

			# collection.
			if cmd.power in POWERCOST :
				self.collect( cmd.player_id, t, POWERCOST[ cmd.power ] )
		elif cmd.cmd_id == 0x2B :
			cmd.decode_upgrade_cmd()
			if cmd.upgrade in UPGRADECOST :
				self.collect( cmd.player_id, t, UPGRADECOST[ cmd.upgrade ] )
		elif cmd.cmd_id == 0x2D :
			# production Q simulation thingy
			pass
		elif cmd.cmd_id == 0x2E :
			# production Q simulation thingy
			pass



	def split( self, spent ) :
		ts = []
		costs = []
		for t, cost in spent :
			ts.append( t )

			# accumulate cost
			if len( costs ) > 0 :
				acc = costs[-1]
			else :
				acc = 0
			costs.append( acc + cost )
		return ts, costs



	def plot( self, font_fname=None ) :
		plt.xlabel( "Time (s)" )
		plt.ylabel( "$$$ spent" )

		plots = []
		for i in range( self.nplayers ) :
			player = self.kwr.players[i]
			if not player.is_player() :
				continue

			ts, costs = self.split( self.spents[ i ] )

			plot, = plt.plot( ts, costs, label=player.name )
			plots.append( plot )

		#fp = font_manager.FontProperties()
		#fp.set_family( 'Gulim' )
		if font_fname :
			fp = font_manager.FontProperties( fname = font_fname )
			plt.legend( handles=plots, loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=4, prop=fp )
		else :
			# legend at bottom.
			plt.legend( handles=plots, loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=4 )

		# shrink plot so that legend will be shown.
		if len( plots ) > 4 :
			plt.subplots_adjust( bottom=0.2 )
		else :
			plt.subplots_adjust( bottom=0.2 )
		plt.show()



class APMAnalyzer() :
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
					counts_at_second[ t ][ pid ] += 1

		return counts_at_second
	


	def emit_apm_csv( self, interval, file=sys.stdout ) :
		# actions counted for that second...
		counts_at_second = self.count_actions( interval )

		# print header
		print( "t", end=",", file=file )
		for player in self.kwr.players :
			if not player.is_player() :
				continue
			print( '"' + player.name + '"', end=",", file=file )
		print( file=file )

		for t in range( len( counts_at_second ) ) :
			counts = counts_at_second[ t ]
			print( t, end=",", file=file )
			for i in range( self.nplayers ) :
				player = self.kwr.players[i]
				if not player.is_player() :
					continue
				apm = counts[ i ]
				apm *= 60/interval
				print( apm, end=",", file=file )
			print( file=file )



	def plot( self, interval, font_fname=None ) :
		# actions counted for that second...
		counts_at_second = self.count_actions( interval )
		ts = [ t for t in range( len( counts_at_second ) ) ]
		apmss = self.make_apmss( interval, counts_at_second )
		#apmss[pid][t] = apm at time t, of player pid.

		plt.xlabel( "Time (s)" )
		plt.ylabel( "APM" )

		plots = []
		for i in range( self.nplayers ) :
			player = self.kwr.players[i]
			if not player.is_player() :
				continue

			plot, = plt.plot( ts, apmss[ i ], label=player.name )
			plots.append( plot )

		#fp = font_manager.FontProperties()
		#fp.set_family( 'Gulim' )
		if font_fname :
			fp = font_manager.FontProperties( fname = font_fname )
			plt.legend( handles=plots, loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=4, prop=fp )
		else :
			# legend at bottom.
			plt.legend( handles=plots, loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=4 )

		# shrink plot so that legend will be shown.
		if len( plots ) > 4 :
			plt.subplots_adjust( bottom=0.2 )
		else :
			plt.subplots_adjust( bottom=0.2 )
		plt.show()



	def make_apmss( self, interval, counts_at_second ) :
		apmss = []
		for i in range( self.nplayers ) :
			apmss.append( [0] * len( counts_at_second ) )

		#apmss[pid][t] = apm at time t, of player pid.

		for t in range( len( counts_at_second ) ) :
			counts = counts_at_second[ t ]
			for i in range( self.nplayers ) :
				player = self.kwr.players[i]
				if not player.is_player() :
					continue
				apm = counts[ i ]
				apm *= 60/interval
				apmss[ i ][ t ] = apm

		return apmss



	# interval: collect this much commands to calculate APM.
	# returns almost APM... we only need to apply weight and emit the data.
	def count_actions( self, interval ) :
		cmds_at_second = self.group_commands_by_time()
		return self.count_player_actions( interval, cmds_at_second )



if __name__ == "__main__" :
	fname = "test.KWReplay"
	if len( sys.argv ) >= 2 :
		fname = sys.argv[1]
	kw = KWReplayWithCommands( fname=fname, verbose=False )
	#kw.replay_body.dump_commands()

	ana = APMAnalyzer( kw )
	#ana.emit_apm_csv( 10, file=sys.stdout )
	ana.plot( 10, font_fname = 'c:\\windows\\fonts\\gulim.ttc' )

	res = ResourceAnalyzer( kw )
	res.calc()
	res.plot()

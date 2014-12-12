#!/usr/bin/python3

import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from chunks import KWReplayWithCommands, Command
from consts import UNITCOST, POWERCOST, UPGRADECOST, UNITNAMES



# Build queue simulator.
class Factory() :
	def __init__( self ) :
		self.player_id = 0 # owner
		self.factory_id = 0 # ID this factory

		# countdown[ UNIT_UID ] = time left for production complete.
		self.countdown = {} # if construction goes to hold status, remember
			# the progress here.
			# countdown[ UNIT_UID ] = progress (in time_code)

		# counts of units to produce
		#self.counts[ UNIT_UID ] = {}
		self.is_constructing = False
		self.was_constructing = 0 # the factory was producing this unit.
		# remember this in case of power down (or judging if new const has begun)

		# the order of user input
		self.order = []



EVT_CONS_COMPLETE = 0x01
EVT_QUEUE = 0x2D
EVT_HOLD = 0x2E



# event driven simulator?! w00t
class FactorySim() :
	def __init__( self ) :
		self.factories = {}
		self.events = [] # priority queue of events. time in time_code.
		self.t = 0 # current time (in time code)
		self.end_time = 0 # game end time (in time code)



	def insert_hold_evt( self, cmd ) :
		assert cmd.factory in self.factories
		self.insert_event( cmd )



	def insert_build_evt( self, cmd ) :
		fid = cmd.factory
		# allocate queue if needed.
		if not fid in self.factories :
			fa = Factory()
			self.factories[ fid ] = fa
			fa.factory_id = fid

		fa = self.factories[ fid ]

		# the factory can be captured, u know.
		if fa.player_id != cmd.player_id :
			# flush current queue and events.
			self.remove_evt_with_factory( factory )
			fa.player_id = cmd.player_id
			fa.countdown = {}
			fa.was_constructing = 0
			fa.order = []

		print( "Factory 0x%08X" % fa.factory_id )
		fivex = ""
		if cmd.fivex :
			fivex = "5x "
		print( "\tp%d queues %s%s @%d" % ( cmd.player_id, fivex,
			UNITNAMES[ cmd.unit_ty ], cmd.time_code ) )
		print()

		self.insert_event( cmd )
	


	def remove_evt_with_factory( self, factory ) :
		i = len( self.events ) - 1
		while i >= 0 :
			evt = self.events[ i ]
			if evt.factory == factory :
				del self.events[ i ]
			i -= 1



	def pop_factory( self, fa ) :
		unit_ty = fa.order[ 0 ]
		if not unit_ty in UNITCOST :
			# just ignore this event.
			return
		fa.is_constructing = True

		# build_time is proportional to unit cost.
		# 15 for second -> time_code conversion.
		build_time = 15 * int( UNITCOST[unit_ty]/100 )

		evt = Command()
		evt.cmd_id = EVT_CONS_COMPLETE
		evt.time_code = self.t + build_time
		evt.player_id = fa.player_id
		evt.unit_ty = unit_ty
		evt.factory = fa.factory_id

		print( "Factory 0x%08X" % fa.factory_id )
		print( "\tevt insert, end construction of", UNITNAMES[ unit_ty ] )
		print( "\tevt @", evt.time_code )
		print()
		self.insert_event( evt )



	def insert_event( self, cmd ) :
		if cmd.time_code > self.end_time :
			print( "unit production past end of game. not inserting." )
			return

		# find insertion point
		index = 0
		for i in range( len( self.events ) ) :
			e = self.events[ i ]
			if e.time_code > cmd.time_code :
				index = i
				break

		self.events.insert( index, cmd )
	


	def process_evt_queue( self, cmd ) :
		fa = self.factories[ cmd.factory ]
		# queue the entries to the factory.
		if cmd.fivex :
			cnt = 5
		else :
			cnt = 1
		for i in range( cnt ) :
			fa.order.append( cmd.unit_ty )

		# if no queue is running, start building.
		if not fa.is_constructing :
			self.pop_factory( fa )
	


	def process_evt_cons_complete( self, evt ) :
		#for (key, val) in evt.__dict__.items() :
		#	print( "\t"+key+":", val )
		#print()

		factory = self.factories[ evt.factory ]
		factory.is_constructing = False

		# construction done, without being held or canceled.
		# it is now safe to pop.
		factory.order.pop( 0 )

		# proceed, if anything in factory queue.
		if len( factory.order ) > 0 :
			self.pop_factory( factory )

		print( "Factory 0x%08X" % factory.factory_id )
		print( "\tp%d built %s @%d" % ( evt.player_id,
			UNITNAMES[ evt.unit_ty ], evt.time_code ) )
		print()

		return (evt.player_id, evt.time_code, UNITCOST[ evt.unit_ty ])



	def run( self ) :
		if len( self.events ) == 0 :
			return None

		evt = self.events.pop( 0 )
		self.t = evt.time_code # make time go.

		if evt.cmd_id == EVT_QUEUE :
			return self.process_evt_queue( evt )
		elif evt.cmd_id == EVT_CONS_COMPLETE :
			return self.process_evt_cons_complete( evt )
		else :
			return None



class ResourceAnalyzer() :
	def __init__( self, kwr_chunks ) :
		self.kwr = kwr_chunks
		self.nplayers = len( self.kwr.players )
		self.sim = FactorySim()

		self.spents = [ None ] * self.nplayers # remember who spent what.
		# spents[ pid ] = [ (t1, cost1), (t2, cost2), ... ]



	def calc( self ) :
		# determine end time of Q simulation.
		# Must be done before step 1.
		if len( self.kwr.replay_body.chunks ) > 0 :
			chunk = self.kwr.replay_body.chunks[-1]
			self.sim.end_time = chunk.time_code
			print( "end_time:", self.sim.end_time )

		# step 1. just collect how much is spent at time t, as a list.
		for chunk in self.kwr.replay_body.chunks :
			for cmd in chunk.commands :
				self.feed( cmd )

		# step 2. Run build queue simulation.
		while len( self.sim.events ) > 0 :
			spent = self.sim.run()
			if spent :
				pid, time_code, cost = spent
				t = int( time_code / 15 )
				self.spents[ pid ].append( (t, cost) )

		# step 3. Sort events by time.
		for spent in self.spents :
			if not spent :
				continue
			spent.sort( key=lambda pair: pair[0] ) # sort by time



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
			# upgrades are actually, like units, they are Queue commands.
			# Dunno if it gets completed or not.
			# But... being only an approximation, I just add 'em immediately,
			# without queue or anything.
			cmd.decode_upgrade_cmd()
			if cmd.upgrade in UPGRADECOST :
				self.collect( cmd.player_id, t, UPGRADECOST[ cmd.upgrade ] )
		elif cmd.cmd_id == 0x2D :
			# production Q simulation thingy
			cmd.decode_queue_cmd()
			if cmd.unit_ty :
				self.sim.insert_build_evt( cmd )
		elif cmd.cmd_id == 0x2E :
			# hold.
			cmd.decode_hold_cmd()
			self.sim.insert_hold_evt( cmd )
			pass
		elif cmd.cmd_id == 0x34 :
			# could be factory sell.
			pass
		elif cmd.cmd_id == 0x89 :
			# could be factory powerdown.
			pass



	def split( self, spent ) :
		# This means, no $$$ consumption data!
		# Game just terminated.
		if not spent :
			return

		ts = []
		costs = []
		for t, cost in spent :
			if len( ts ) == 0 :
				# initial element
				ts.append( t )
				costs.append( cost )
			else :
				if ts[-1] == t :
					# $$ spent at the same moment.
					costs[-1] += cost
				else :
					# new spending at new time.
					ts.append( t )
					costs.append( costs[-1] + cost )

		return ts, costs



	def plot( self, font_fname=None ) :
		plt.xlabel( "Time (s)" )
		plt.ylabel( "$$$ spent" )

		plots = []
		for i in range( self.nplayers ) :
			player = self.kwr.players[i]
			if not player.is_player() :
				continue

			pair = self.split( self.spents[ i ] )
			if not pair :
				continue
			ts, costs = pair

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

	#ana = APMAnalyzer( kw )
	#ana.plot( 10 )
	#ana.emit_apm_csv( 10, file=sys.stdout )

	res = ResourceAnalyzer( kw )
	res.calc()
	res.plot()

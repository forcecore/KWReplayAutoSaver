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
		self.held = {} # is this unit production blocked by hold?
			# check by unit_ty in held.
			# "set" should be the correct choice of data structure but
			# i can't bother to do even that.

		self.is_powered_down = False
		self.was_constructing = 0 # the factory was producing this unit.
		# remember this in case of power down (or judging if new const has begun)

		# the construction order of units in the building queue.
		self.order = []
	
	# True if and only if some EVT_CONS_COMPLETE is in factorysim.events.
	def all_held( self ) :
		# := if not everything is on hold hehe
		return self.find_unheld() == -1
	
	def cancel_one( self, ty ) :
		for i in reversed( range( fa.order ) ) :
			if fa.order[ i ] == ty :
				fa.pop( i )
				return
		assert 0

	def cancel_all( self, ty ) :
		for i in reversed( range( len( self.order ) ) ) :
			if self.order[ i ] == ty :
				self.order.pop( i )
		del self.held[ ty ]

		# Well, countdown might not have begun.
		# 1. build loads of riflemen
		# 2. queue up missilemen too.
		# 3. while riflemen are trained, cancel all missielemen.
		if ty in self.countdown :
			del self.countdown[ ty ]
	
	def flush( self ) :
		self.countdown = {}
		self.held = {}
		self.is_powered_down = False
		self.was_constructing = 0
		self.order = []

	def find_unheld( self ) :
		for i in range( len( self.order ) ) :
			ty = self.order[i]
			if not ty in self.held :
				print( "find_unheld:", i )
				return i
		print( "find_unheld:", -1 )
		return -1



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
		# thin check is fine.
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
			fa.player_id = cmd.player_id
			self.remove_evt_with_factory( factory )
			fa.flush()

		#if 0 :
		#	print( "Factory 0x%08X" % fa.factory_id )
		#	fivex = ""
		#	if cmd.fivex :
		#		fivex = "5x "
		#	print( "\tp%d queues %s%s @%d" % ( cmd.player_id, fivex,
		#		UNITNAMES[ cmd.unit_ty ], cmd.time_code ) )
		#	print( "\t0x%08X" % cmd.unit_ty )
		#	print()

		self.insert_event( cmd )
	


	def remove_evt_with_factory( self, factory ) :
		for i in reversed( range( len( self.events ) ) ) :
			evt = self.events[ i ]
			if evt.factory == factory :
				del self.events[ i ]
	


	def pop_factory( self, fa ) :
		# find something that is not held.
		index = fa.find_unheld()
		if index < 0 :
			# everything is on hold. do nothing.
			print( "pop_factory: everything on hold" )
			print()
			return

		# if something is already in construction...
		if self.find_evt_cons_complete( fa.factory_id ) != -1 :
			# something is already in construction.
			# DONT QUEUE ANY MORE COMPLETION EVENT.
			return

		unit_ty = fa.order[ index ]
		if not unit_ty in UNITCOST :
			# just ignore this event.
			print( "no data for this unit 0x%08X" % unit_ty )
			return

		if unit_ty in fa.countdown :
			# use remaining time, if any.
			build_time = fa.countdown[ unit_ty ]
			del fa.countdown[ unit_ty ]
		else :
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
		print( "\t0x%08X" % unit_ty )
		print( "\tevt @", evt.time_code )
		print()
		self.insert_event( evt )



	def insert_event( self, cmd ) :
		if cmd.time_code > self.end_time :
			print( "unit production past end of game. not inserting." )
			return

		# find insertion point
		index = -1
		for i in range( len( self.events ) ) :
			e = self.events[ i ]
			if e.time_code > cmd.time_code :
				index = i
				break

		if index == -1 :
			self.events.append( cmd )
		else :
			self.events.insert( index, cmd )



	def process_evt_queue( self, evt ) :
		fa = self.factories[ evt.factory ]

		if evt.unit_ty in fa.held :
			print( "Factory 0x%08X" % fa.factory_id )
			print( "\tResuming construction of", UNITNAMES[ evt.unit_ty ] )
			print()
			del fa.held[ evt.unit_ty ] # unblock this thingy
		else :
			# queue the entries to the factory.
			if evt.fivex :
				cnt = 5
			else :
				cnt = 1
			for i in range( cnt ) :
				fa.order.append( evt.unit_ty )

			if 1 :
				print( "Factory 0x%08X" % fa.factory_id )
				fivex = ""
				if evt.fivex :
					fivex = "5x "
				print( "\tp%d queues %s%s @%d" % ( evt.player_id, fivex,
					UNITNAMES[ evt.unit_ty ], evt.time_code ) )
				print( "\t0x%08X" % evt.unit_ty )
				print()

		# start building, if possible.
		# (possibility is checked in pop_factory())
		self.pop_factory( fa )



	def process_evt_cons_complete( self, evt ) :
		#for (key, val) in evt.__dict__.items() :
		#	print( "\t"+key+":", val )
		#print()

		factory = self.factories[ evt.factory ]

		# shouldn't find anything, as we only queue one at a time.
		index = self.find_evt_cons_complete( evt.factory )
		assert index == -1

		# construction done, without being held or canceled.
		# it is now safe to pop.
		index = factory.order.index( evt.unit_ty )
		factory.order.pop( index )

		# proceed, if anything in factory queue.
		if len( factory.order ) > 0 :
			self.pop_factory( factory )

		print( "Factory 0x%08X" % factory.factory_id )
		print( "\tp%d built %s @%d" % ( evt.player_id,
			UNITNAMES[ evt.unit_ty ], evt.time_code ) )
		print()

		return (evt.player_id, evt.time_code, UNITCOST[ evt.unit_ty ])
	


	def find_evt_cons_complete( self, factory ) :
		# find EVT_CONS_COMPLETE from this factory.
		cnt = 0
		index = -1
		for i in range( len( self.events ) ) :
			e = self.events[ i ]

			if e.factory != factory :
				continue

			if e.cmd_id != EVT_CONS_COMPLETE :
				continue

			index = i
			cnt += 1

		print( "find_evt_cons_complete:", cnt )
		assert 0 <= cnt and cnt <= 1

		return index



	# modify factory to hold status.
	def process_evt_hold( self, evt ) :
		fa = self.factories[ evt.factory ]
		print( "Factory 0x%08X, trying to hold." % fa.factory_id )
		print( "\t0x%08X" % evt.unit_ty )
		print( "\t", UNITNAMES[ evt.unit_ty ] )
		print( "\t@", evt.time_code )

		index = self.find_evt_cons_complete( fa.factory_id )

		if evt.unit_ty in fa.held :
			assert index == -1

			# already on hold!
			if evt.cancel_all :
				# cancel all
				print( "\tAttempting cancel all" )
				fa.cancel_all( evt.unit_ty )
			else :
				# cancel one...
				print( "\tcancel one of this." )
				fa.cancel_one( evt.unit_ty )
		else :
			# remove building completion event.
			# assert index != -1 wrong...
			# why? something can be going on while i'm canceling.
			# I can hold missile squad and reduce their number while
			# riflemen are being trained.

			compl = self.events[ index ]
			if compl.unit_ty == evt.unit_ty :
				# if unit type same, remove hold event.
				# CAN be held, without even starting build.
				# in that case we may have unequal case too.
				self.events.pop( index )
				remaining_time = compl.time_code - evt.time_code
				fa.countdown[ evt.unit_ty ] = remaining_time

				print( "\tRemoving completion evt of", UNITNAMES[compl.unit_ty] )

			fa.held[ evt.unit_ty ] = True # value doesn't matter, though.

		print()

		# Multiple units may be queued already.
		# In case of that, proceed to the next queued buildable type.
		self.pop_factory( fa )



	def run( self ) :
		if len( self.events ) == 0 :
			return None

		#print( "time codes:" )
		#for evt in self.events :
		#	print( evt.time_code, end=" " )
		#print()
		#print()

		evt = self.events.pop( 0 )
		self.t = evt.time_code # make time go.

		if evt.cmd_id == EVT_QUEUE :
			return self.process_evt_queue( evt )
		elif evt.cmd_id == EVT_CONS_COMPLETE :
			return self.process_evt_cons_complete( evt )
		elif evt.cmd_id == EVT_HOLD :
			return self.process_evt_hold( evt )
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

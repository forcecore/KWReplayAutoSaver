#!/usr/bin/python3

import sys
from gnuplot import Gnuplot
from chunks import KWReplayWithCommands, Command
from consts import UNITCOST, POWERCOST, UPGRADECOST, UNITNAMES



def merge_lines( f, players, xss, yss ) :
	# data check.
	for xs, ys in zip( xss, yss ) :
		assert len(xs) == len(ys)

	# Lets extend short ones...
	# find the longest.
	max_len = 0
	for xs in xss :
		max_len = max( max_len, len( xs ) )

	# extend shorter ones.
	for xs in xss :
		while len( xs ) < max_len :
			xs.append( -1 )
	for ys in yss :
		while len( ys ) < max_len :
			ys.append( -1 )
	
	# We are now ready to dump.
	for player in players :
		print( "%s,," % player, end="", file=f )
	print( file=f )

	# print merged! finally.
	for i in range( max_len ) :
		line = []
		for xs, ys in zip( xss, yss ) :
			if xs[i] >= 0 :
				line.append( str( xs[i] ) )
			else :
				line.append( "" )
			if ys[i] >= 0 :
				line.append( str( ys[i] ) )
			else :
				line.append( "" )
		print( ",".join( line ), file=f )



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
		for i in reversed( range( len( self.order ) ) ) :
			if self.order[ i ] == ty :
				self.order.pop( i )
				break

		# if nothing is left of that ty...
		# I can no longer say it is on hold.
		if not ty in self.order :
			if ty in self.countdown :
				del self.countdown[ ty ]
			if ty in self.held :
				del self.held[ ty ]



	def cancel_all( self, ty ) :
		for i in reversed( range( len( self.order ) ) ) :
			if self.order[ i ] == ty :
				self.order.pop( i )

		# I can just shift right click, without anything queued.
		if ty in self.held :
			del self.held[ ty ]

		# Well, countdown might not have begun.
		# 1. build loads of riflemen
		# 2. queue up missilemen too.
		# 3. while riflemen are trained, cancel all missielemen.
		if ty in self.countdown :
			del self.countdown[ ty ]

		# print( self.order )



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
				return i
		return -1



EVT_CONS_COMPLETE = 0x01
EVT_QUEUE = 0x2D
EVT_HOLD = 0x2E
EVT_SELL = 0x34
EVT_POWERDOWN = 0x89



# event driven simulator?! w00t
class FactorySim() :
	verbose = False

	def __init__( self ) :
		self.factories = {}
		self.events = [] # priority queue of events. time in time_code.
		self.t = 0 # current time (in time code)
		self.end_time = 0 # game end time (in time code)



	def insert_hold_evt( self, cmd ) :
		if cmd.factory in self.factories :
			# well. we can have hold without queueing anything but...
			# that's not too usual.
			self.insert_event( cmd )



	def insert_sell_evt( self, cmd ) :
		# thin check is fine.
		# Well, we can have sells that is NOT factories.
		if cmd.target in self.factories :
			self.insert_event( cmd )

	def insert_powerdown_evt( self, cmd ) :
		# we can power down non-factories, you know!
		if cmd.target in self.factories :
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
			self.remove_evt_with_factory( fa.factory_id )
			fa.flush()

		self.insert_event( cmd )
	


	def remove_evt_with_factory( self, factory ) :
		for i in reversed( range( len( self.events ) ) ) :
			evt = self.events[ i ]
			if not hasattr( evt, "factory" ) :
				continue
			if evt.factory == factory :
				del self.events[ i ]
	


	def pop_factory( self, fa ) :
		# find something that is not held.
		index = fa.find_unheld()
		if index < 0 :
			# everything is on hold. do nothing.
			if FactorySim.verbose :
				print( "pop_factory: everything on hold" )
				print()
			return

		unit_ty = fa.order[ index ]

		# if something is already in construction...
		# perhaps we need to defer building it.
		# (but not hold or cancel.)
		index = self.find_evt_cons_complete( fa.factory_id )
		if index >= 0 :
			under_const = self.events[ index ]

			# unheld + in progress. doesn't matter.
			# don't have to do anything.
			if unit_ty == under_const.unit_ty :
				return

			self.events.pop( index ) # remove this.
			remaining_time = under_const.time_code - self.t
			fa.countdown[ unit_ty ] # save it to remaining time.

		if not unit_ty in UNITCOST :
			# just ignore this event.
			if FactorySim.verbose :
				print( "no data for this unit 0x%08X" % unit_ty )
			return

		if unit_ty in fa.countdown :
			# use remaining time, if any.
			build_time = fa.countdown[ unit_ty ]
			del fa.countdown[ unit_ty ]
		else :
			# build_time is proportional to unit cost.
			# 15 for second -> time_code conversion.
			build_time = 15 * int( UNITCOST[unit_ty]/100 ) + 6 # extra 6 for unit exit delay;;;;;;;

		evt = Command()
		evt.cmd_id = EVT_CONS_COMPLETE
		evt.time_code = self.t + build_time
		evt.player_id = fa.player_id
		evt.unit_ty = unit_ty
		evt.factory = fa.factory_id

		if FactorySim.verbose :
			print( "Factory 0x%08X" % fa.factory_id )
			print( "\tevt insert, end construction of", UNITNAMES[ unit_ty ] )
			print( "\t0x%08X" % unit_ty )
			print( "\tevt @", evt.time_code )
			print()
		self.insert_event( evt )



	def insert_event( self, cmd ) :
		if cmd.time_code > self.end_time :
			if FactorySim.verbose :
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
			if FactorySim.verbose :
				print( "Factory 0x%08X" % fa.factory_id )
				print( "\tResuming construction of", UNITNAMES[ evt.unit_ty ] )
				print()
			del fa.held[ evt.unit_ty ] # unblock this thingy

			# Well... lets start building rifle men and
			# hold it. then build missile men and hold it.
			# unhold missile man than unhold rifleman.
			# What you get is, rifleman resuming first then missileman getting blocked until rifleman is done.
			# If you change the order of unholding, the results are same.
			# First queued is built first.
		else :
			# queue the entries to the factory.
			if evt.fivex :
				# these units, when 5x'ed, they are subject to
				# limit of the airfields.
				# Well, the limit may limit them to 2x when the airfield
				# is half full, but oh well, this is only an estimation.
				if evt.unit_ty in [ 
						0x6AA59D16, # Nod vertigo
						0x393E446C, # MoK vertigo
						0xB587039F, # GDI orca
						0xB3363EA3, # GDI firehawk
						0x6BD7B8AB, # ST orca
						0x1348CA0A, # ST FH
						0x37F0A5F5, # Zorca
						0x12E1C8C8, # ZCM FH
						0xF6E707D5, # SC storm rider
						0x1DF82E16, # R17 storm rider
						0xECA08561 # T59 storm rider
						] :
					cnt = 4
				else :
					cnt = 5
			else :
				cnt = 1
			for i in range( cnt ) :
				fa.order.append( evt.unit_ty )

			if FactorySim.verbose :
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
		factory = self.factories[ evt.factory ]

		# shouldn't find anything, as we only queue one at a time.
		index = self.find_evt_cons_complete( evt.factory )
		assert index == -1

		# construction done, without being held or canceled.
		# it is now safe to pop.
		index = factory.order.index( evt.unit_ty )
		factory.order.pop( index )

		if FactorySim.verbose :
			print( "Factory 0x%08X" % factory.factory_id )
			print( "\tp%d built %s @%d" % ( evt.player_id,
				UNITNAMES[ evt.unit_ty ], evt.time_code ) )
			print()

		# proceed, if anything in factory queue.
		if len( factory.order ) > 0 :
			self.pop_factory( factory )

		return (evt.player_id, evt.time_code, UNITCOST[ evt.unit_ty ], evt.unit_ty)
	


	def find_evt_cons_complete( self, factory ) :
		# find EVT_CONS_COMPLETE from this factory.
		cnt = 0
		index = -1
		for i in range( len( self.events ) ) :
			e = self.events[ i ]

			if not hasattr( e, "factory" ) :
				continue

			if e.factory != factory :
				continue

			if e.cmd_id != EVT_CONS_COMPLETE :
				continue

			index = i
			cnt += 1

		if FactorySim.verbose :
			print( "find_evt_cons_complete:", cnt )
		assert 0 <= cnt and cnt <= 1

		return index



	def process_evt_sell( self, evt ) :
		# Kill all events associated with this factory.
		for i in reversed( range( len( self.events ) ) ) :
			e = self.events[ i ]
			if not hasattr( e, "factory" ) :
				continue
			if e.factory == evt.target :
				self.events.pop( i )

	def process_evt_powerdown( self, evt ) :
		fa = self.factories[ evt.target ]

		# toggle power
		fa.is_powered_down = not fa.is_powered_down

		if fa.is_powered_down :
			index = self.find_evt_cons_complete( fa.factory_id )
			if index >= 0 :
				self.events.pop( index )
		else :
			self.pop_factory( fa )



	# modify factory to hold status.
	def process_evt_hold( self, evt ) :
		fa = self.factories[ evt.factory ]
		if FactorySim.verbose :
			print( "Factory 0x%08X, trying to hold." % fa.factory_id )
			print( "\t0x%08X" % evt.unit_ty )
			print( "\t", UNITNAMES[ evt.unit_ty ] )
			print( "\t@", evt.time_code )

		# When I just right click on the interfact (without even starting the build)
		# I get evt_hold!!!!!
		# It means that I can't assert too much about index.

		index = self.find_evt_cons_complete( fa.factory_id )

		if evt.unit_ty in fa.held :
			# wrong... assert index == -1
			# I could be canceling units XX while YY is being built.
			if index != -1 :
				assert self.events[ index ].unit_ty != evt.unit_ty

			# already on hold!
			if evt.cancel_all :
				# cancel all
				if FactorySim.verbose :
					print( "\tAlready on hold. Attempting cancel all" )
				fa.cancel_all( evt.unit_ty )
			else :
				# cancel one...
				if FactorySim.verbose :
					print( "\tAlready on hold. Cancel one of this." )
				fa.cancel_one( evt.unit_ty )
		elif index != -1 :
			# can just right click on the side bar with nothing being built;;

			compl = self.events[ index ]
			if compl.unit_ty == evt.unit_ty :
				# if unit type same, remove hold event.
				# CAN be held, without even starting build.
				# in that case we may have unequal case too.
				self.events.pop( index )
				remaining_time = compl.time_code - evt.time_code
				fa.countdown[ evt.unit_ty ] = remaining_time

				if FactorySim.verbose :
					print( "\tRemoving completion evt of", UNITNAMES[compl.unit_ty] )

			fa.held[ evt.unit_ty ] = True # value doesn't matter, though.

		if FactorySim.verbose :
			print()

		# Multiple units may be queued already.
		# In case of that, proceed to the next queued buildable type.
		self.pop_factory( fa )



	def run( self ) :
		if len( self.events ) == 0 :
			return None

		evt = self.events.pop( 0 )
		self.t = evt.time_code # make time go.

		if evt.cmd_id == EVT_QUEUE :
			return self.process_evt_queue( evt )
		elif evt.cmd_id == EVT_CONS_COMPLETE :
			return self.process_evt_cons_complete( evt )
		elif evt.cmd_id == EVT_HOLD :
			return self.process_evt_hold( evt )
		elif evt.cmd_id == EVT_SELL :
			return self.process_evt_sell( evt )
		elif evt.cmd_id == EVT_POWERDOWN :
			return self.process_evt_powerdown( evt )
		else :
			return None



class ResourceAnalyzer() :
	def __init__( self, kwr_chunks ) :
		self.kwr = kwr_chunks
		self.nplayers = len( self.kwr.players )
		self.sim = FactorySim()

		self.spents = [ [] for i in range( self.nplayers ) ] # remember who spent what.
		self.units = [ {} for i in range( self.nplayers ) ] # remember who built what how many.
		# spents[ pid ] = [ (t1, cost1), (t2, cost2), ... ]



	def calc( self ) :
		# determine end time of Q simulation.
		# Must be done before step 1.
		if len( self.kwr.replay_body.chunks ) > 0 :
			chunk = self.kwr.replay_body.chunks[-1]
			self.sim.end_time = chunk.time_code

		# step 1. just collect how much is spent at time t, as a list.
		for chunk in self.kwr.replay_body.chunks :
			for cmd in chunk.commands :
				self.feed( cmd )

		# step 2. Run build queue simulation.
		while len( self.sim.events ) > 0 :
			spent = self.sim.run()
			if spent :
				pid, time_code, cost, unit = spent
				t = int( time_code / 15 )
				self.spents[ pid ].append( (t, cost) )

				# count units produced, too, for histogram.
				histo = self.units[ pid ]
				if unit in histo :
					histo[ unit ] += 1
				else :
					histo[ unit ] = 1

		# step 3. Sort events by time.
		for spent in self.spents :
			if not spent :
				continue
			spent.sort( key=lambda pair: pair[0] ) # sort by time
	


	def print_unit_distribution( self ) :
		print( "Unit distribution" )

		for i in range( self.nplayers ) :
			player = self.kwr.players[i]
			if not player.is_player() :
				continue
			print( player.name )

			histo = self.units[ i ]
			for unit, cnt in histo.items() :
				print( UNITNAMES[ unit ] + "," + str( cnt ) )

			print()
			print()
			print()
	


	def plot_unit_distribution( self ) :
		color = 1
		for i in range( self.nplayers ) :
			player = self.kwr.players[i]
			if not player.is_player() :
				continue

			histo = self.units[ i ]

			plt = Gnuplot()
			plt.open()

			plt.write( 'set style fill solid\n' )
			plt.write( 'set key off\n' )
			plt.write( 'set boxwidth 0.5\n' )
			plt.write( 'set title "%s"\n' % player.name )

			n_kinds = len( histo )
			plt.write( 'set xrange[-1:%d]\n' % n_kinds )

			# set X tics, 45 degress rotated.
			cmd = "set xtics ("
			i = 0
			items = []
			for unit, cnt in histo.items() :
				items.append( '"%s" %d' % ( UNITNAMES[ unit ], i ) )
				i += 1
			cmd += ", ".join( items )
			cmd += ") rotate by 45 right\n"
			plt.write( cmd )

			# write values on the graph (labels)
			#i = 0
			#for unit, cnt in histo.items() :
			#	cmd = 'set label "%d" at %d,%d\n' % ( cnt, i, cnt+5 )
			#	plt.write( cmd )
			#	i += 1

			# feed data
			cmd = 'plot "-" using 0:1 with boxes linecolor %s, ' % color
			cmd += "'-' using 0:1:1 with labels offset 0, 1\n"
			plt.write( cmd )
			for unit, cnt in histo.items() :
				plt.write( str(cnt) + "\n" )
			plt.write( 'e\n' )
			for unit, cnt in histo.items() :
				plt.write( str(cnt) + "\n" )
			plt.write( 'e\n' )

			plt.close()

			color += 1



	def collect( self, pid, t, cost ) :
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
		elif cmd.cmd_id == 0x8A :
			cmd.decode_skill_2xy()
			if cmd.power in POWERCOST :
				self.collect( cmd.player_id, t, POWERCOST[ cmd.power ] )
		elif cmd.cmd_id == 0x34 :
			# could be factory sell.
			cmd.decode_sell_cmd()
			self.sim.insert_sell_evt( cmd )
		elif cmd.cmd_id == 0x89 :
			# could be factory powerdown.
			cmd.decode_powerdown_cmd()
			self.sim.insert_powerdown_evt( cmd )



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
		plt = Gnuplot()
		plt.open()

		plt.xlabel( "Time (s)" )
		plt.ylabel( "$$$ spent" )
		plt.set_style( "linespoints" )

		plots = []
		labels = []
		for i in range( self.nplayers ) :
			player = self.kwr.players[i]
			if not player.is_player() :
				continue

			pair = self.split( self.spents[ i ] )
			if not pair :
				continue
			ts, costs = pair

			plt.plot( ts, costs )
			labels.append( player.name )

		plt.legend( labels )
		plt.show()
		plt.close()
	


	def emit_csv( self, file=None ) :
		if file == None :
			file=sys.stdout

		xss = []
		yss = []
		players = []

		for i in range( self.nplayers ) :
			player = self.kwr.players[i]
			if not player.is_player() :
				continue

			pair = self.split( self.spents[ i ] )
			if not pair :
				continue
			ts, costs = pair

			xss.append( ts )
			yss.append( costs )
			players.append( player.name )

		print( "t,$$$ spent", file=file )
		merge_lines( file, players, xss, yss )



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

		# except for heart beat, all are commands.
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
					if cmd.cmd_id == 0x61 : # 30s heart beat
						continue
					pid = cmd.player_id
					counts_at_second[ t ][ pid ] += 1

		return counts_at_second
	


	def emit_apm_csv( self, interval, file=None ) :
		if file == None :
			file = sys.stdout

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
		plt = Gnuplot()
		plt.open()

		# actions counted for that second...
		counts_at_second = self.count_actions( interval )
		ts = [ t for t in range( len( counts_at_second ) ) ]
		apmss = self.make_apmss( interval, counts_at_second )
		#apmss[pid][t] = apm at time t, of player pid.

		plt.xlabel( "Time (s)" )
		plt.ylabel( "APM" )

		labels = []

		for i in range( self.nplayers ) :
			player = self.kwr.players[i]
			if not player.is_player() :
				continue

			plt.plot( ts, apmss[ i ] )
			labels.append( player.name )

		# touch up label of the curve

		# draw legend
		plt.legend( labels )

		plt.show()
		plt.close()



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



class PositionDumper() :
	def __init__( self, kwr_chunks ) :
		self.kwr = kwr_chunks
		self.nplayers = len( self.kwr.players )
		self.commandss = None # populated by calc()



	def group_commands_by_pid( self ) :
		commandss = [ [] for i in range( self.nplayers ) ]

		# except for heart beat, all are commands.
		for chunk in self.kwr.replay_body.chunks :
			for cmd in chunk.commands :
				commands = commandss[ cmd.player_id ]
				commands.append( cmd )

		return commandss



	def decode_commands( self, commands ) :
		for cmd in commands :
			if cmd.cmd_id == 0x27 : # use skill
				cmd.decode_skill_xy()

			elif cmd.cmd_id == 0x31 : # place down building
				cmd.decode_placedown_cmd()

			elif 0x46 <= cmd.cmd_id and cmd.cmd_id <= 0x48 :
				cmd.decode_move_cmd() # this works for 'em all.

			elif cmd.cmd_id == 0x7A : # formation move
				cmd.decode_formation_move_cmd()

			elif cmd.cmd_id == 0x8A : # wormhole
				cmd.decode_skill_2xy()

			elif cmd.cmd_id == 0x8E : # move
				cmd.decode_move_cmd()



	def filter_commands( self, commands ) :
		result = []
		for cmd in commands :
			if cmd.cmd_id in [ 0x27, 0x31, 0x46, 0x47, 0x48, 0x7A, 0x8A, 0x8E ] :
				result.append( cmd )
		return result



	def calc( self ) :
		commandss = self.group_commands_by_pid()
		for i in range( len( commandss ) ) :
			commandss[ i ] = self.filter_commands( commandss[ i ] )
			self.decode_commands( commandss[ i ] )

		self.commandss = commandss



	def dump_csv( self ) :
		for pid in range( self.nplayers ) :
			player = self.kwr.players[ pid ]
			if not player.is_player() :
				continue

			print( "p" + str(pid ) )
			commands = self.commandss[ pid ]

			for cmd in commands :
				if cmd.cmd_id == 0x8A : # wormhole
					#print( "0x%08X" % cmd.cmd_id )
					print( "%f,%f" % (cmd.x1, cmd.y1 ) )
					print( "%f,%f" % (cmd.x2, cmd.y2 ) )
				else :
					#print( "0x%08X" % cmd.cmd_id )
					print( "%f,%f" % (cmd.x, cmd.y ) )

			print()
			print()
			print()



if __name__ == "__main__" :
	fname = "1.KWReplay"
	if len( sys.argv ) >= 2 :
		fname = sys.argv[1]
	kw = KWReplayWithCommands( fname=fname, verbose=False )
	#kw.replay_body.dump_commands()

	#ana = APMAnalyzer( kw )
	#ana.plot( 10 )
	# or ana.emit_apm_csv( 10, file=sys.stdout )

	res = ResourceAnalyzer( kw )
	res.calc()
	#res.print_unit_distribution()
	res.plot_unit_distribution()
	#res.emit_csv()
	#res.plot()

	#pos = PositionDumper( kw )
	#pos.calc()
	#pos.dump_csv()

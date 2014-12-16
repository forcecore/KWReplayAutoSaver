#!/usr/bin/python3
import wx
import wx.lib.scrolledpanel
import sys
import os
from kwreplay import time_code2str
from mapzip import MapZip
from chunks import KWReplayWithCommands
from analyzer import PositionDumper
from args import Args
from consts import UNITNAMES, POWERNAMES, UPGRADENAMES



UNIT_COLORS = [
		'#FF0000', # R
		'#0066ff', # B, cos pure blue 0000FF sucks
		'#00FF00', # G
		'#FFFF00', # Y
		'#ff7f00', # Orange
		'#00ffff', # Cyan
		'#ff7fff', # Pink
	]

BLDG_COLORS = [
		'#7f0000', # R
		'#00007f', # B
		'#007f00', # G
		'#7f7f00', # Y
		'#7f3f00', # Orange
		'#007f7f', # Cyan
		'#7f667f', # Pink
	]
	


class MiniMap( wx.Panel ) :
	def __init__( self, parent, map_zip_fname ) :
		super().__init__( parent )

		self.t = 0
		self.posa = None
		self.kwr = None

		self.colors = None
		self.bldg_colors = None
		self.scale = 0 # scale factor VS pos and image pixels.
		self.x_offset = 0
		self.y_offset = 0

		self.mapzip = MapZip( map_zip_fname )
		self.Bitmap = None
		self.SetBackgroundColour( (0,0,0) )

		self.Bind( wx.EVT_PAINT, self.OnPaint )



	# show map preview
	def load_minimap( self, kwr ) :
		# Examine the replay, determine what map it is.
		#print( kwr.map_id ) always says fake map id, useless.
		#print( kwr.map_name ) depends on language, not good.
		fname = kwr.map_path # this is one is the best shot.
		fname = os.path.basename( fname )
		fname += ".png"
		#print( fname )

		# file doesn't exist...
		if not self.mapzip.hasfile( fname ) :
			# well, try jpg.
			fname = fname.replace( ".png", ".jpg" )

		# file really doesn't exist...
		if not self.mapzip.hasfile( fname ) :
			black = wx.Image( 200, 200 )
			self.Bitmap = wx.Bitmap( black )
			self.SetSize( self.Bitmap.GetSize() )
			return

		# lets load from zip.
		# now we show proper image.
		# I get "iCCP: known incorrect sRGB profile" for some PNG files.
		# Lets silence this with log null object.
		no_log = wx.LogNull()
		img = self.mapzip.load( fname )
		del no_log # restore
		self.Bitmap = wx.Bitmap( img )
		self.SetSize( self.Bitmap.GetSize() )



	def calc_scale_factor( self ) :
		# get X and Y.
		X = 0
		Y = 0
		for commands in self.posa.commandss :
			for cmd in commands :
				if cmd.cmd_id == 0x8A :
					X = max( X, cmd.x1 )
					X = max( X, cmd.x2 )
					Y = max( Y, cmd.y1 )
					Y = max( Y, cmd.y2 )
				else :
					X = max( X, cmd.x )
					Y = max( Y, cmd.y )

		bmp = self.Bitmap
		W = bmp.GetWidth()
		H = bmp.GetHeight()

		fx = W/X
		fy = H/Y

		self.scale = min( fx, fy )


	def draw_dot( self, dc, x, y, color ) :
		x = int( self.scale * x ) + self.x_offset
		y = dc.Y - int( self.scale * y ) + self.y_offset
		dc.SetPen( wx.Pen( color ) )
		dc.DrawLine( x-3, y, x+3, y )
		dc.DrawLine( x, y-3, x, y+3 )
	
	def draw_building( self, dc, x, y, color ) :
		x = int( self.scale * x ) + self.x_offset
		y = dc.Y - int( self.scale * y ) + self.y_offset
		dc.SetPen( wx.Pen( wx.BLACK ) )
		dc.SetBrush( wx.Brush( color ) )
		dc.DrawCircle( x, y, 3 )



	def draw_positions( self, t ) :
		self.t = t
		self.Refresh()

	def OnPaint( self, evt ) :
		if not self :
			return
		if self.scale == 0 :
			return
		if self.posa == None :
			return

		bmp = self.Bitmap # internal data! careful not to modify this!

		#self.unit_view.show( self.kwr, scale=False ) # remove previous dots.
		#self.minimap.SetBitmap( self.map_bmp )
		#self.SetBitmap( self.bmp )
		dc = wx.PaintDC( self )
		dc.DrawBitmap( bmp, 0, 0 )
		#trans_brush = wx.Brush( wx.BLACK, style=wx.BRUSHSTYLE_TRANSPARENT )
		#dc.SetBackground( trans_brush )
		#dc.Clear()
		#bmp = wx.Bitmap( self.map_bmp )
		#dc = wx.MemoryDC( bmp )
		null, dc.Y = bmp.GetSize()

		# draw buildings
		for i in range( 0, self.t ) :
			commands = self.posa.structures[ i ]

			for cmd in commands :
				pid = cmd.player_id
				player = self.kwr.players[ pid ]
				if not player.is_player() :
					continue
				self.draw_building( dc, cmd.x, cmd.y, BLDG_COLORS[pid] )


		# Draw movement dots
		for i in range( max( 0, self.t-10 ), self.t ) :
			commands = self.posa.commands[ i ]

			for cmd in commands :
				pid = cmd.player_id
				player = self.kwr.players[ cmd.player_id ]
				if not player.is_player() :
					continue

				if cmd.cmd_id == 0x8A : # wormhole
					#print( "0x%08X" % cmd.cmd_id )
					self.draw_dot( dc, cmd.x1, cmd.y1, UNIT_COLORS[pid] )
					self.draw_dot( dc, cmd.x2, cmd.y2, UNIT_COLORS[pid] )
				else :
					self.draw_dot( dc, cmd.x, cmd.y, UNIT_COLORS[pid] )

		del dc
		#self.SetBitmap( bmp )



class TimelineAnalyzer() :
	def __init__( self, kwr_chunks, length ) :
		self.t = -1
		self.length = length
		self.eventsss = None
		self.kwr = kwr_chunks
		# eventsss[pid][t] = events of that player at time t.

		self.process()



	def feed( self, t, cmd ) :
		self.eventsss[ cmd.player_id ][ t ].append( cmd )



	def decode_and_feed( self ) :
		eventsss = [ None ] * self.nplayers
		self.eventsss = eventsss
		for i in range( len( eventsss ) ) :
			# eventss[pid] = events.
			eventss = [ [] for i in range( self.length ) ]
			eventsss[ i ] = eventss

		for chunk in self.kwr.replay_body.chunks :
			time = int( chunk.time_code/15 )
			for cmd in chunk.commands :
				if cmd.cmd_id == 0x31 :
					cmd.decode_placedown_cmd()
					self.feed( time, cmd )
				elif cmd.cmd_id == 0x26 :
					cmd.decode_skill_targetless()
					self.feed( time, cmd )
				elif cmd.cmd_id == 0x27 :
					cmd.decode_skill_xy()
					self.feed( time, cmd )
				elif cmd.cmd_id == 0x28 :
					cmd.decode_skill_target()
					self.feed( time, cmd )
				elif cmd.cmd_id == 0x2B :
					cmd.decode_upgrade_cmd()
					self.feed( time, cmd )
				elif cmd.cmd_id == 0x2D :
					cmd.decode_queue_cmd()
					self.feed( time, cmd )
				elif cmd.cmd_id == 0x2E :
					# hold/cancel/cancel all production
					cmd.decode_hold_cmd()
					self.feed( time, cmd )
				elif cmd.cmd_id == 0x8A :
					cmd.decode_skill_2xy()
					self.feed( time, cmd )
				elif cmd.cmd_id == 0x34 :
					self.feed( time, cmd ) # sell
				elif cmd.cmd_id == 0x91 :
					cmd.pid = cmd.payload[1]
					cmd.player_id = cmd.pid # override owner!
					self.feed( time, cmd )

		#print( eventsss )
		#for t in range( len( eventsss ) ) :
		#	print( "t:", t )
		#	for pid in range( self.nplayers ) :
		#		print( eventsss[t][pid] )
		#	print()
	
		return eventsss



	# populate eventsss
	def process( self ) :
		self.nplayers = len( self.kwr.players )
		self.n_active_players = 0

		# count active players.
		for player in self.kwr.players :
			if player.is_player() :
				self.n_active_players += 1

		# compute eventsss
		self.eventsss = self.decode_and_feed()

		# assign "offset" to the commands. (label height in timeline)
		for pid in range( self.nplayers ) :
			eventss = self.eventsss[ pid ]
			offset = 0
			for events in eventss :
				for cmd in events :
					cmd.offset = offset
					offset += 1

		# Lets get enough canvas, vertically.
		#self.H = self.row_height * self.n_active_players + 50
		#w, h = self.Parent.GetSize()
		#self.SetSize( (w, self.H) )
		#self.Parent.SetVirtualSize( self.GetSize() )

		# Set parent's scroll info so that the timeline can be shown properly.
		#self.Parent.FitInside()
		#self.Parent.SetupScrolling()



class Timeline( wx.Panel ) :
	H = 250 # we want the timeline drawing area to be this high.
	Y = 200 # Draw time grid at this level.
	pin_spacing = 40 # 80 pixels == one second!
	cycle = 5 #label height cycle

	def __init__( self, parent, eventss, length, size=(100,100) ) :
		super().__init__( parent, size=size )
		self.SetBackgroundColour( (0,0,0) )
		#self.nplayers = 0
		#self.n_active_players = 0
		self.eventss = eventss
		self.length = length

		self.t = -1
		self.player_name = "Noname"
		self.pid = 0 # player ID
		self.draw_key = False

		self.Bind( wx.EVT_PAINT, self.OnPaint )
	


	def draw_midline( self, dc ) :
		line_spacing = 20
		line_len = 5

		x = self.mid
		y = 0
		dc.SetPen( wx.Pen( "#ff7fff" ) ) # pink
		while y < self.h :
			dc.DrawLine( x, y, x, y + line_len )
			y += line_spacing
	

	
	def draw_time_pin( self, dc, t, x, Y, pin_len ) :
		dc.DrawLine( x, Y, x, Y-pin_len )
		time_label = time_code2str(t)
		# space conservation trick
		if time_label.startswith( "00:" ) :
			time_label = time_label[3:]
		dc.DrawText( time_label, x, Y+5 )



	def draw_time_grid( self, dc ) :
		Y = Timeline.Y

		pin_spacing = self.pin_spacing
		pin_len = 5 # 5 pixels.
		
		dc.SetPen( wx.Pen( wx.WHITE ) )
		dc.SetTextForeground( wx.WHITE )

		# major time line
		dc.DrawLine( 0, Y, self.w-1, Y )

		# grids
		mid = self.mid
		x = self.w - pin_spacing * int( self.w / pin_spacing )
		t = self.t - int( mid/pin_spacing )

		# But, to draw time pins, we need to check if we can fit those number labels.
		(tw, th) = dc.GetTextExtent( "00:00" )
		if tw >= Timeline.pin_spacing :
			# OK, how many pins can we fit in them?
			mult = int( tw / Timeline.pin_spacing ) + 1
		else :
			mult = 1

		while x < self.w :
			if t < 0 :
				t += mult
				x += mult * pin_spacing
				continue
			self.draw_time_pin( dc, t, x, Y, pin_len )
			t += mult
			x += mult *pin_spacing
	


	def draw_events( self, dc ) :
		cnt = int( self.mid/Timeline.pin_spacing )
		t = self.t - cnt

		while t <= self.t + cnt and t < self.length :
			self.draw_events_at_second( dc, self.eventss[t] )
			t += 1



	def draw_events_at_second( self, dc, events ) :
		for cmd in events :
			xoffset = int( ( cmd.time_code - 15*self.t )*self.pin_spacing/15 )
			x = self.mid + xoffset

			# Draw text & line here.
			y = cmd.offset % self.cycle * 20 # cycle of 5
			y += self.Y - 140
			self.cmd_desc( dc, cmd, x, y )



	def cmd_desc( self, dc, cmd, x, y ) :
		if cmd.cmd_id == 0x31 :
			dc.SetTextForeground( wx.CYAN )
			dc.SetPen( wx.Pen( wx.CYAN ) )

			if cmd.building_type in UNITNAMES :
				name = UNITNAMES[ cmd.building_type ]
			else :
				name ="bldg 0x%08X" % cmd.building_type
			dc.DrawText( name, x-10, y )

			dc.DrawLine( x, self.Y, x, y+20 )


		elif cmd.cmd_id in [0x26, 0x27, 0x28, 0x8A] :
			dc.SetTextForeground( wx.GREEN )
			dc.SetPen( wx.Pen( wx.GREEN ) )

			if cmd.power in POWERNAMES :
				name = POWERNAMES[ cmd.power ]
			else :
				name = "skill 0x%08X" % cmd.power
			dc.DrawText( name, x-10, y )

			dc.DrawLine( x, self.Y, x, y+20 )

		elif cmd.cmd_id == 0x2B :
			dc.SetTextForeground( wx.YELLOW )
			dc.SetPen( wx.Pen( wx.YELLOW ) )

			if cmd.upgrade in UPGRADENAMES :
				name = UPGRADENAMES[ cmd.upgrade ]
			else :
				name = "upgrade 0x%08X" % cmd.power
			dc.DrawText( name, x-10, y )

			dc.DrawLine( x, self.Y, x, y+20 )

		elif cmd.cmd_id == 0x2D :
			# hold/cancel
			dc.SetTextForeground( wx.RED )
			dc.SetPen( wx.Pen( wx.RED ) )

			if not cmd.unit_ty :
				dc.SetTextForeground( "#9a0eea" )
				dc.SetPen( wx.Pen( "#9a0eea" ) ) # violet
				dc.DrawText( "GG?", x-10, y )
				dc.DrawLine( x, self.Y, x, y+20 )
			else :
				if cmd.unit_ty in UNITNAMES :
					name = UNITNAMES[ cmd.unit_ty ]
				else :
					name = "unit 0x%08X" % cmd.unit_ty

				if cmd.fivex :
					dc.DrawText( "5x Q " + name, x-10, y )
				else :
					dc.DrawText( "Q " + name, x-10, y )

				dc.DrawLine( x, self.Y, x, y+20 )


		elif cmd.cmd_id == 0x2E :
			# hold/cancel
			dc.SetTextForeground( '#ff7fff' )
			dc.SetPen( wx.Pen( '#ff7fff' ) )

			if cmd.unit_ty :
				if cmd.unit_ty in UNITNAMES :
					name = UNITNAMES[ cmd.unit_ty ]
				else :
					name = "unit 0x%08X" % cmd.unit_ty

				if cmd.cancel_all :
					dc.DrawText( "CA " + name, x-10, y )
				else :
					dc.DrawText( "C/H" + name, x-10, y )

				dc.DrawLine( x, self.Y, x, y+20 )


		elif cmd.cmd_id == 0x34 : # sell
			dc.SetTextForeground( wx.YELLOW )
			dc.SetPen( wx.Pen( wx.YELLOW ) )

			dc.DrawText( "sell", x-10, y )
			dc.DrawLine( x, self.Y, x, y+20 )


		elif cmd.cmd_id == 0x91 : # GG!
			dc.SetTextForeground( "#9a0eea" )
			dc.SetPen( wx.Pen( "#9a0eea" ) ) # violet
			dc.DrawText( "GG", x-10, y )
			dc.DrawLine( x, self.Y, x, y+20 )




	def draw_player_timeline( self, dc ) :
		dc.SetTextForeground( UNIT_COLORS[ self.pid ] )
		#dc.DrawText( self.kwr.players[pid].name, 10, self.Y-170 )
		dc.DrawText( self.player_name, 10, Timeline.Y-170 )
		self.draw_time_grid( dc )
		self.draw_events( dc )



	def OnPaint( self, evt ) :
		if not self :
			return
		if self.t < 0 :
			return

		w, h = self.Parent.GetSize()
		self.mid = int( w/2 )
		self.SetSize( (w, self.H) )
	
		dc = wx.PaintDC( self )

		self.w, self.h = dc.GetSize()
		self.mid = int( self.w/2 )

		if self.draw_key :
			dc.SetTextForeground( wx.WHITE )
			dc.DrawText( "C/H: Cancel or Hold", w-200, 10 )
			dc.DrawText( "CA: Cancel all", w-200, 20 )
			dc.DrawText( "Q: Queue unit production", w-200, 30 )

		# draw vertical line at the center.
		self.draw_midline( dc )
		self.draw_player_timeline( dc )

		del dc



class TimelineViewer( wx.Frame ) :
	def __init__( self, parent, maps_zip='maps.zip' ) :
		super().__init__( parent, title='Replay Movement Viewer', size=(500,500) )
		self.parent = parent
		self.MAPS_ZIP = maps_zip

		self.kwr = None
		self.pos_analyzer = None
		self.length = 100 # default

		self.movementss = None
		self.buildingss = None
		# buildingss[ pid ] = buildings
		# buildings = [ (t1, loc1), (t2, loc2) ]
		# loc = (x, y) pair.

		self.minimap = None
		self.slider = None
		self.timelines = []
		self.time = None
		self.do_layout()
		self.event_bindings()
	


	def create_top_panel( self, parent ) :
		#panel = wx.Panel( parent, -1 )
		#panel.SetBackgroundColour( (255,0,0) )

		sizer = wx.BoxSizer( wx.HORIZONTAL )

		# map view
		lpanel = wx.Panel( parent, -1 )
		self.minimap = MiniMap( lpanel, self.MAPS_ZIP )

		# map control panel
		rpanel = wx.Panel( parent, -1 )

		lbl_scale = wx.StaticText( rpanel, label="Scale:", pos=(5,5) )
		lbl_xoffset = wx.StaticText( rpanel, label="x offset:", pos=(5,35) )
		lbl_yoffset = wx.StaticText( rpanel, label="y offset:", pos=(5,65) )
		lbl_time_scale = wx.StaticText( rpanel, label="pixels/s", pos=(75,100) )

		# time mark
		lbl_time = wx.StaticText( rpanel, label="time:", pos=(5,155) )
		self.time = wx.StaticText( rpanel, label="", pos=(50,155) )

		self.txt_scale   = wx.TextCtrl( rpanel, size=(60,-1), pos=(50,5) )
		self.txt_xoffset = wx.TextCtrl( rpanel, size=(60,-1), pos=(50,35) )
		self.txt_yoffset = wx.TextCtrl( rpanel, size=(60,-1), pos=(50,65) )
		self.txt_time_scale = wx.TextCtrl( rpanel, size=(60,-1), pos=(5,95) )

		self.btn_apply = wx.Button( rpanel, label="Apply", pos=(120,35) )

		sizer.Add( lpanel, 0 )
		sizer.Add( rpanel, 1, wx.EXPAND )
		#panel.SetSizer( sizer )
		return sizer
	



	def do_layout( self ) :
		sizer = wx.BoxSizer( wx.VERTICAL )
		#panel = wx.Panel( self )
		#panel.SetBackgroundColour( (255,0,0) )
		self.slider = wx.Slider( self, minValue=0, maxValue=100, pos=(20, 20), size=(250, -1) )

		# Map view + controls sizer panel
		top_sizer = self.create_top_panel( self )

		# OK... scrollable timeline shit.
		self.timelines_panel = wx.lib.scrolledpanel.ScrolledPanel( self )
		self.timelines_panel.SetBackgroundColour( wx.BLACK )
		self.timeline_sizer = wx.BoxSizer( wx.VERTICAL )
		self.timelines_panel.SetSizer( self.timeline_sizer )
		self.timelines_panel.SetAutoLayout( 1 )
		self.timelines_panel.SetupScrolling()

		sizer.Add( top_sizer, 0, wx.EXPAND )
		sizer.Add( self.timelines_panel, 1, wx.EXPAND )
		sizer.Add( self.slider, 0, wx.EXPAND )
		self.SetSizer( sizer )



	def event_bindings( self ) :
		self.slider.Bind( wx.EVT_SCROLL, self.on_scroll )
		self.btn_apply.Bind( wx.EVT_BUTTON, self.on_apply )
	


	def on_apply( self, evt ) :
		self.minimap.scale = float( self.txt_scale.GetValue() )
		self.minimap.x_offset = float( self.txt_xoffset.GetValue() )
		self.minimap.y_offset = float( self.txt_yoffset.GetValue() )
		Timeline.pin_spacing = int( self.txt_time_scale.GetValue() )
		self.minimap.Refresh()
		for timeline in self.timelines :
			timeline.Refresh()



	def on_scroll( self, evt ) :
		t = evt.GetPosition()
		self.time.SetLabel( time_code2str( t ) )
		self.minimap.draw_positions( t )
		for timeline in self.timelines :
			timeline.t = t
			timeline.Refresh()
	


	def digest_pos_analyzer( self, posa ) :
		posa.calc()

		# lets collect commands by SECONDS.
		posa.commands = [ [] for i in range (self.length) ]
		posa.structures = [ [] for i in range( self.length ) ]

		for commands in posa.commandss :
			for cmd in commands :
				sec = int( cmd.time_code / 15 )

				if cmd.cmd_id == 0x31 : # buildings
					posa.structures[ sec ].append( cmd )
				else :
					posa.commands[ sec ].append( cmd )



	def load( self, kwr ) :
		self.kwr = kwr
		assert len( kwr.replay_body.chunks ) > 0
		# +1 second so that we can see the END of the replay.
		self.length = int( kwr.replay_body.chunks[-1].time_code/15 ) + 1
		self.slider.SetMax( self.length )
		self.slider.SetValue( 0 )
		self.time.SetLabel( "00:00:00" )

		# pass the events to the timeline class.
		ta = TimelineAnalyzer( self.kwr, self.length )
		for pid in range( len( self.kwr.players ) ) :
			player = self.kwr.players[ pid ]
			if not player.is_player() :
				continue

			eventss = ta.eventsss[ pid ]

			w, h = self.timelines_panel.GetSize()

			timeline = Timeline( self.timelines_panel, eventss, self.length,
					size=(w, Timeline.H) )

			timeline.t = 0
			timeline.pid = self.kwr.players.index( player )
			timeline.player_name = player.name
			
			self.timelines.append( timeline )
			self.timeline_sizer.Add( timeline, 0, wx.ALIGN_LEFT )
		self.timelines[0].draw_key = True

		# analyze positions
		posa = PositionDumper( kwr )
		self.pos_analyzer = posa
		self.digest_pos_analyzer( posa )

		# drawing related things
		self.minimap.posa = posa
		self.minimap.kwr = kwr
		self.minimap.load_minimap( kwr )
		self.minimap.calc_scale_factor()

		# populate the text boxes with the factors.
		self.txt_xoffset.SetValue( str( self.minimap.x_offset ) )
		self.txt_yoffset.SetValue( str( self.minimap.y_offset ) )
		self.txt_scale.SetValue( str( self.minimap.scale ) )
		self.txt_time_scale.SetValue( str( Timeline.pin_spacing ) )



def main() :
	fname = "1.KWReplay"
	if len( sys.argv ) >= 2 :
		fname = sys.argv[1]

	kw = KWReplayWithCommands( fname=fname, verbose=False )

	app = wx.App()
	
	frame = TimelineViewer( None )
	frame.load( kw )
	#frame.Layout() # do layout again.
	frame.Show( True )
	app.MainLoop()

if __name__ == "__main__" :
	main()

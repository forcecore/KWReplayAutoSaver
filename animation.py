#!/usr/bin/python3
import wx
import wx.lib.scrolledpanel
import sys
import os
from args import Args
from kwreplay import time_code2str
from mapzip import MapZip
from chunks import KWReplayWithCommands
from analyzer import PositionDumper
from args import Args


CANCEL_ALL = -1

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



	def get_margins( self, bmp ) :
		# Well. lets count black pixels, to calc real width/height.
		dc = wx.MemoryDC( bitmap=bmp )
		W, H = dc.GetSize()
		ymid = int( H/2 )
		xmid = int( W/2 )

		# x direction.
		xmar = 0
		for x in range( W ) :
			color = dc.GetPixel( x, ymid ).Get()
			color = color[0:3]
			if max( color ) < 5 :
				xmar += 1

		# y direction
		ymar = 0
		for y in range( H ) :
			color = dc.GetPixel( xmid, y ).Get()
			color = color[0:3]
			if max( color ) < 5 :
				ymar += 1
		del dc

		xmar = int( xmar/2 )
		ymar = int( ymar/2 )

		return (xmar, -ymar)



	def calc_scale_factor( self ) :
		# get X and Y.
		X = 0
		Y = 0
		for commands in self.posa.commandss :
			for cmd in commands :
				if cmd.has_2pos() :
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

		xmar, ymar = self.get_margins( bmp )

		W -= 2*xmar
		H -= 2*ymar
		self.x_offset = xmar
		self.y_offset = ymar

		assert W >= 0
		assert H >= 0

		if W == 0 : # all black! == unknown map.
			W = bmp.GetWidth()
			self.x_offset = 0
		if H == 0 : # all black! == unknown map.
			H = bmp.GetWidth()
			self.y_offset = 0

		if X == 0 :
			fx = 1
		else :
			fx = W/X
		if Y == 0 :
			fy = 1
		else :
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

		#self.unit_view.show( self.kwr, scale=False ) # remove previous dots.
		#self.minimap.SetBitmap( self.map_bmp )
		#self.SetBitmap( self.bmp )
		dc = wx.PaintDC( self )
		self.draw_on_dc( dc, self.t )
		del dc
	


	# draw map at t, as bmp and return it.
	def bitmap( self, t ) :
		w, h = self.GetSize()
		bmp = wx.Bitmap( w, h )
		dc = wx.MemoryDC( bitmap=bmp )
		self.draw_on_dc( dc, t )
		del dc
		return bmp



	def draw_on_dc( self, dc, t ) :
		bmp = self.Bitmap # internal data! careful not to modify this!
		dc.DrawBitmap( bmp, 0, 0 )
		null, dc.Y = bmp.GetSize()

		# draw buildings
		for i in range( 0, t ) :
			commands = self.posa.structures[ i ]

			for cmd in commands :
				pid = cmd.player_id
				player = self.kwr.players[ pid ]
				if not player.is_player() :
					continue
				self.draw_building( dc, cmd.x, cmd.y, BLDG_COLORS[pid] )


		# Draw movement dots
		for i in range( max( 0, t-10 ), t ) :
			commands = self.posa.commands[ i ]

			for cmd in commands :
				pid = cmd.player_id
				player = self.kwr.players[ cmd.player_id ]
				if not player.is_player() :
					continue

				if cmd.has_2pos() : # wormhole
					self.draw_dot( dc, cmd.x1, cmd.y1, UNIT_COLORS[pid] )
					self.draw_dot( dc, cmd.x2, cmd.y2, UNIT_COLORS[pid] )
				else :
					self.draw_dot( dc, cmd.x, cmd.y, UNIT_COLORS[pid] )



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
				chunk.decode_cmd( cmd )
				if cmd.cmd_ty :
					if cmd.is_eog() :
						cmd.player_id = cmd.target # override owner!
					elif cmd.is_gg() :
						cmd.player_id = cmd.target # override owner!
					self.feed( time, cmd )

		#print( eventsss )
		#for t in range( len( eventsss ) ) :
		#	print( "t:", t )
		#	for pid in range( self.nplayers ) :
		#		print( eventsss[t][pid] )
		#	print()
	
		return eventsss
	


	def merge_productions_in_sec( self, events ) :
		merged = [] # merged events

		# Let's define cnt for cancels.
		for evt in events :
			if evt.is_hold() :
				# cnt of 0 = hold. >0 is cancel
				# and... um... cancel all is obviously cancel all.
				# prev.cnt == CANCEL_ALL
				evt.cnt = 0

		for evt in events :
			if len( merged ) == 0 :
				merged.append( evt )
				continue

			prev = merged[-1]

			if prev.cmd_id != evt.cmd_id :
				merged.append( evt )
				continue

			if evt.is_queue() :
				if evt.unit_ty and evt.unit_ty == prev.unit_ty :
					prev.cnt += evt.cnt
			elif evt.is_hold() :
				if evt.unit_ty and evt.unit_ty == prev.unit_ty :
					if evt.cancel_all :
						evt.cnt = CANCEL_ALL
						prev.cnt = CANCEL_ALL
					elif prev.cnt == CANCEL_ALL :
						pass
					else :
						prev.cnt += 1

		return merged



	def merge_productions( self, eventsss ) :
		# eventsss[ pid ] = eventss
		# eventss[t] = events in that second.
		for eventss in eventsss :
			for t, events in enumerate( eventss ) :
				events = self.merge_productions_in_sec( events )
				eventss[ t ] = events



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

		# merge queue and holds
		self.merge_productions( self.eventsss )

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
	pin_spacing = 10 # 10 pixels == one second!
	cycle = 5 #label height cycle



	def draw_time_pin( dc, t, x, Y, pin_len ) :
		dc.DrawLine( x, Y, x, Y-pin_len )
		time_label = time_code2str(t)
		# space conservation trick
		if time_label.startswith( "00:" ) :
			time_label = time_label[3:]
		dc.DrawText( time_label, x, Y+5 )
	


	def calc_grid_mult( dc ) :
		(tw, th) = dc.GetTextExtent( "00:00" )
		if tw >= Timeline.pin_spacing :
			# OK, how many pins can we fit in them?
			mult = int( tw / Timeline.pin_spacing ) + 1
		else :
			mult = 1
		return mult


	
	def draw_time_grid( dc, Y, mid_t, end_time ) :
		w, h = dc.GetSize()
		mid = int( w/2 )

		pin_spacing = Timeline.pin_spacing
		pin_len = 5 # 5 pixels.
		
		dc.SetPen( wx.Pen( wx.WHITE ) )
		dc.SetTextForeground( wx.WHITE )

		# major time line
		dc.DrawLine( 0, Y, w-1, Y )

		# grids
		x = w - pin_spacing * int( w / pin_spacing )
		t = mid_t - int( mid/pin_spacing )

		# But, to draw time pins, we need to check if we can fit those number labels.
		mult = Timeline.calc_grid_mult( dc )
		while x < w :
			if t < 0 :
				t += mult
				x += mult * pin_spacing
				continue
			if t > end_time :
				break
			Timeline.draw_time_pin( dc, t, x, Y, pin_len )
			t += mult
			x += mult *pin_spacing
	


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
		self.Bind( wx.EVT_RIGHT_UP, self.on_right_click )
	


	def on_move_up( self, evt ) :
		self.move_timeline( -1 )

	def on_move_down( self, evt ) :
		self.move_timeline( 1 )

	def move_timeline( self, offset ) :
		# offset == +1 or -1.
		# +1 moves it down, -1 moves it up.
		timelines_panel = self.GetParent()
		sizer = timelines_panel.GetSizer()
		timelines = sizer.GetChildren()
		index = -1
		for timeline in timelines :
			if timeline.GetWindow() == self :
				index = timelines.index( timeline )
				break
		assert index >= 0

		new_pos = index + offset
		if new_pos < 0 :
			# you can't move up when you are at the top.
			return
		if new_pos >= sizer.GetItemCount() :
			# you can't move down when you are at the bottom.
			return

		affected = timelines[ new_pos ].GetWindow() # remember the affected one.
		sizer.Detach( self )
		sizer.Insert( new_pos, self )

		if new_pos == 0 :
			# move this job
			self.draw_key = True
			affected.draw_key = False

		# Since the windows swapped pos, we need to do Layout again.
		# Calling Refresh() won't do.
		timelines_panel.Layout()
		timelines_panel.Refresh()

	

	def on_right_click( self, evt ) :
		menu = wx.Menu()

		# move up
		item = wx.MenuItem( menu, wx.ID_ANY, "Move &up" )
		menu.Bind( wx.EVT_MENU, self.on_move_up, id=item.GetId() )
		menu.Append( item )

		# move down
		item = wx.MenuItem( menu, wx.ID_ANY, "Move &down" )
		menu.Bind( wx.EVT_MENU, self.on_move_down, id=item.GetId() )
		menu.Append( item )

		# export build order
		item = wx.MenuItem( menu, wx.ID_ANY, "Save &build order of this player" )
		menu.Bind( wx.EVT_MENU, self.on_bo_dump, id=item.GetId() )
		menu.Append( item )

		self.PopupMenu( menu, evt.GetPosition() )
		menu.Destroy() # prevent memory leak



	def on_bo_dump( self, evt ) :
		diag = wx.FileDialog( self, "Save build order as text", "", "",
			"Text File (*.txt)|*.txt",
			wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT )
		diag.SetFilename( self.player_name + ".txt" )
		
		if diag.ShowModal() != wx.ID_OK :
			return None

		ofname = diag.GetPath()
		diag.Destroy()

		# in time order, no need to worry!
		tmp = sys.stdout # intercept stdout temporarily.
		f = open( ofname, "w" )
		sys.stdout = f
		print( "Build order dump of", self.player_name, file=f )
		print( file=f )
		for events in self.eventss :
			for cmd in events :
				cmd.print_bo()
		f.close()
		sys.stdout = tmp



	def draw_midline( self, dc ) :
		line_spacing = 20
		line_len = 5

		x = self.mid
		y = 0
		dc.SetPen( wx.Pen( "#ff7fff" ) ) # pink
		while y < self.h :
			dc.DrawLine( x, y, x, y + line_len )
			y += line_spacing
	


	def draw_events( self, dc ) :
		cnt = int( self.mid/Timeline.pin_spacing )
		t = max( 0, self.t - cnt )

		assert self.length <= len( self.eventss )

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
		if cmd.is_placedown() :
			dc.SetTextForeground( wx.CYAN )
			dc.SetPen( wx.Pen( wx.CYAN ) )

			name = cmd.building_type
			dc.DrawText( name, x-10, y )

			dc.DrawLine( x, self.Y, x, y+20 )

		
		elif cmd.is_science() :
			dc.SetTextForeground( wx.GREEN )
			dc.SetPen( wx.Pen( wx.GREEN ) )

			name = str( cmd )
			dc.DrawText( name, x-10, y )

			dc.DrawLine( x, self.Y, x, y+20 )



		elif cmd.is_skill_use() :
			dc.SetTextForeground( wx.GREEN )
			dc.SetPen( wx.Pen( wx.GREEN ) )

			name = cmd.power
			dc.DrawText( name, x-10, y )

			dc.DrawLine( x, self.Y, x, y+20 )


		elif cmd.is_upgrade() :
			dc.SetTextForeground( wx.YELLOW )
			dc.SetPen( wx.Pen( wx.YELLOW ) )

			name = cmd.upgrade
			dc.DrawText( name, x-10, y )

			dc.DrawLine( x, self.Y, x, y+20 )


		elif cmd.is_eog() :
			dc.SetTextForeground( "#9a0eea" )
			dc.SetPen( wx.Pen( "#9a0eea" ) ) # violet
			dc.DrawText( "GG?", x-10, y )
			dc.DrawLine( x, self.Y, x, y+20 )


		elif cmd.is_queue() :
			# hold/cancel
			dc.SetTextForeground( wx.RED )
			dc.SetPen( wx.Pen( wx.RED ) )

			name = cmd.unit_ty

			if cmd.cnt > 1 :
				dc.DrawText( str(cmd.cnt) + "x Q " + name, x-10, y )
			else :
				dc.DrawText( "Q " + name, x-10, y )

			dc.DrawLine( x, self.Y, x, y+20 )


		elif cmd.is_hold() :
			# hold/cancel
			dc.SetTextForeground( '#ff7fff' )
			dc.SetPen( wx.Pen( '#ff7fff' ) )

			name = cmd.unit_ty

			if cmd.cnt == CANCEL_ALL :
				dc.DrawText( "CA " + name, x-10, y )
			elif cmd.cnt == 0 or cmd.cnt == 1 :
				dc.DrawText( "C/H " + name, x-10, y )
			elif cmd.cnt > 1 :
				dc.DrawText( str(cmd.cnt) + "x C/H " + name, x-10, y )
			else :
				assert 0, "strange, U shouldnt get here"

			dc.DrawLine( x, self.Y, x, y+20 )


		elif cmd.is_sell() :
			dc.SetTextForeground( wx.YELLOW )
			dc.SetPen( wx.Pen( wx.YELLOW ) )

			dc.DrawText( "sell", x-10, y )
			dc.DrawLine( x, self.Y, x, y+20 )


		elif cmd.is_gg() :
			dc.SetTextForeground( "#9a0eea" )
			dc.SetPen( wx.Pen( "#9a0eea" ) ) # violet
			dc.DrawText( "GG", x-10, y )
			dc.DrawLine( x, self.Y, x, y+20 )




	def draw_player_timeline( self, dc ) :
		dc.SetTextForeground( UNIT_COLORS[ self.pid ] )
		#dc.DrawText( self.kwr.players[pid].name, 10, self.Y-170 )
		dc.DrawText( self.player_name, 10, Timeline.Y-170 )
		self.draw_events( dc )
	


	def draw_on_dc( self, dc, midline=True ) :
		self.w, self.h = dc.GetSize()
		self.mid = int( self.w/2 )

		if self.draw_key :
			dc.SetTextForeground( wx.WHITE )
			dc.DrawText( "C/H: Cancel or Hold", self.w-200, 10 )
			dc.DrawText( "CA: Cancel all", self.w-200, 20 )
			dc.DrawText( "Q: Queue unit production", self.w-200, 30 )

		# draw vertical line at the center.
		if midline :
			self.draw_midline( dc )
		Timeline.draw_time_grid( dc, Timeline.Y, self.t, self.length )
		self.draw_player_timeline( dc )



	def OnPaint( self, evt ) :
		if not self :
			return
		if self.t < 0 :
			return

		w, h = self.Parent.GetSize()
		self.mid = int( w/2 )
		self.SetSize( (w, self.H) )
	
		dc = wx.PaintDC( self )
		self.draw_on_dc( dc )
		del dc



class TimelineViewer( wx.Frame ) :
	def __init__( self, parent, maps_zip='maps.zip' ) :
		super().__init__( parent, title='Replay Movement Viewer', size=(800,600) )
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
		lbl_time = wx.StaticText( rpanel, label="time:", pos=(5,185) )
		self.time = wx.StaticText( rpanel, label="", pos=(50,185) )

		self.txt_scale   = wx.TextCtrl( rpanel, size=(60,-1),
				pos=(50,5), style=wx.TE_PROCESS_ENTER )
		self.txt_xoffset = wx.TextCtrl( rpanel, size=(60,-1),
				pos=(50,35), style=wx.TE_PROCESS_ENTER )
		self.txt_yoffset = wx.TextCtrl( rpanel, size=(60,-1),
				pos=(50,65), style=wx.TE_PROCESS_ENTER )
		self.txt_time_scale = wx.TextCtrl( rpanel, size=(60,-1),
				pos=(5,95), style=wx.TE_PROCESS_ENTER )

		self.btn_apply = wx.Button( rpanel, label="Apply", pos=(120,35) )
		self.btn_export = wx.Button( rpanel, label="Export Time+Map as Image", pos=(5,125) )

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
	


	def on_size( self, evt ) :
		for timeline in self.timelines :
			timeline.Refresh()
		evt.Skip()
		# OK, if this gets heavy, then I can move on to EVT_IDLE instead.
		# But before that... I'm just redrawing all the time.
	


	def mv_time( self, offset ) :
		val = self.slider.GetValue() + offset
		if val < 0 :
			val = 0
		if val > self.slider.GetMax() :
			val = self.slider.GetMax()
		self.slider.SetValue( val )
		evt = wx.ScrollEvent()
		evt.SetPosition( val )
		self.on_scroll( evt )



	def on_timeline_mousewheel( self, evt ) :
		delta = evt.GetWheelRotation()
		if delta > 0 :
			self.mv_time( -2 )
		else :
			self.mv_time( 2 )

	def on_timeline_key_down( self, evt ) :
		key_code = evt.GetKeyCode()
		if key_code == wx.WXK_UP :
			self.timelines_panel.ScrollLines( -3 )
		elif key_code == wx.WXK_DOWN :
			self.timelines_panel.ScrollLines( 3 )
		elif key_code == wx.WXK_LEFT :
			self.mv_time( -1 )
		elif key_code == wx.WXK_RIGHT :
			self.mv_time( 1 )
		elif key_code == wx.WXK_PAGEUP :
			self.mv_time( -10 )
		elif key_code == wx.WXK_PAGEDOWN :
			self.mv_time( 10 )
		elif key_code == wx.WXK_HOME :
			self.mv_time( -self.slider.GetMax() )
		elif key_code == wx.WXK_END :
			self.mv_time( self.slider.GetMax() )
		else :
			evt.Skip()
	


	def make_map_line( self, w, minimap, scaled_size ) :
		mw, mh = scaled_size

		margin = 10
		timeline_h = 25
		H = margin + mh + margin + timeline_h # top, bottom margin and timeline space.
		Y = H-timeline_h
		mid = int( w/2 )
		end_time = self.length
		mid_t = int( end_time / 2 )

		bmp = wx.Bitmap( w, H )
		dc = wx.MemoryDC( bitmap=bmp )
		dc.SetBackground( wx.Brush( wx.BLACK ) )
		dc.Clear()

		pin_spacing = Timeline.pin_spacing
		
		dc.SetPen( wx.Pen( wx.WHITE ) )
		dc.SetTextForeground( wx.WHITE )

		# font
		small = wx.Font( 9, wx.FONTFAMILY_SWISS, # sans serif
				wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD )
		dc.SetFont( small )
		Timeline.draw_time_grid( dc, Y, mid_t, self.length )

		# draw many maps hhhhh
		x = w - pin_spacing * int( w / pin_spacing )
		t = mid_t - int( mid/pin_spacing )

		# calc multiplier of grid location.
		mult = Timeline.calc_grid_mult( dc )

		# we put this code here, otherwise
		# we have to do this increment thing on every continue.
		t -= mult
		x -= mult * pin_spacing
		start_x_lb = 0
		while x < w :
			t += mult
			x += mult * pin_spacing

			# Don't draw off the limits.
			if t < 0 :
				continue
			if t > end_time :
				break

			# OK, we are in the limits. But can we draw the map
			# without getting clipped?

			start_x = x - int(mw/2)
			start_y = margin

			if start_x < start_x_lb :
				continue

			# scale to fit
			map_at_t = minimap.bitmap( t )
			img = map_at_t.ConvertToImage()
			img = img.Scale( mw, mh )
			map_at_t = wx.Bitmap( img )

			dc.DrawBitmap( map_at_t, start_x, start_y )
			start_x_lb = start_x + mw + 10

			# with map drawn, draw line.
			dc.SetPen( wx.Pen( wx.WHITE ) )
			dc.DrawLine( x, margin+mh+1, x, margin+mh+margin )

		del dc
		return bmp
	


	def draw_timeline( self, width, timeline ) :
		# font
		small = wx.Font( 9, wx.FONTFAMILY_SWISS, # sans serif
				wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD )

		old_t = timeline.t
		timeline.t = int( self.length / 2 )

		b = wx.Bitmap( width, Timeline.H )
		memdc = wx.MemoryDC( bitmap=b )
		memdc.SetBackground( wx.Brush( wx.BLACK ) )
		memdc.Clear()

		# lets draw with small font.
		memdc.SetFont( small )

		timeline.draw_on_dc( memdc, midline=False )
		del memdc

		timeline.t = old_t

		return b



	def on_export( self, evt ) :
		diag = wx.FileDialog( self, "Export timeline as PNG...", "", "",
			"Portable Network Graphics (*.png)|*.png",
			wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT )

		if diag.ShowModal() != wx.ID_OK :
			return

		# get timelines, in current order.
		timelines = []
		sizer = self.timelines_panel.GetSizer()
		children = sizer.GetChildren()
		for child in children :
			timelines.append( child.GetWindow() )

		# calc width.
		margin = 20*Timeline.pin_spacing  # *2 for both sides.
		width = timelines[0].length * Timeline.pin_spacing + margin

		# calc height
		height = len( timelines ) * Timeline.H

		# map line = bitmap is returned.
		map_line = self.make_map_line( width, self.minimap, (200,200) )
		mw, mh = map_line.GetSize()

		height += mh

		# allocate bitmap
		bmp = wx.Bitmap( width, height )
		dc = wx.MemoryDC( bitmap=bmp )
		dc.DrawBitmap( map_line, 0, 0 )

		# Draw on them.
		for i, timeline in enumerate( timelines ) :
			b = self.draw_timeline( width, timeline )
			dc.DrawBitmap( b, 0, mh+i*Timeline.H )
			del b

		del dc

		bmp.SaveFile( diag.GetPath(), type=wx.BITMAP_TYPE_PNG )
		diag.Destroy
	


	def event_bindings( self ) :
		self.slider.Bind( wx.EVT_SCROLL, self.on_scroll )
		self.btn_apply.Bind( wx.EVT_BUTTON, self.on_apply )
		self.btn_export.Bind( wx.EVT_BUTTON, self.on_export )
		self.Bind( wx.EVT_SIZE, self.on_size )

		# text box enter keys
		self.txt_scale.Bind( wx.EVT_TEXT_ENTER, self.on_apply )
		self.txt_xoffset.Bind( wx.EVT_TEXT_ENTER, self.on_apply )
		self.txt_yoffset.Bind( wx.EVT_TEXT_ENTER, self.on_apply )
		self.txt_time_scale.Bind( wx.EVT_TEXT_ENTER, self.on_apply )



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

				if cmd.is_placedown() :
					posa.structures[ sec ].append( cmd )
				else :
					posa.commands[ sec ].append( cmd )



	def make_timelines( self ) :
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
			timeline.player_name = Args.args.akaed_name( player )
			
			self.timelines.append( timeline )
			self.timeline_sizer.Add( timeline, 0, wx.ALIGN_LEFT )

			# arrow keys on the time line
			timeline.Bind( wx.EVT_KEY_DOWN, self.on_timeline_key_down )
			timeline.Bind( wx.EVT_MOUSEWHEEL, self.on_timeline_mousewheel )
		self.timelines[0].draw_key = True # key drawing job is on this one.



	def load( self, kwr ) :
		self.kwr = kwr
		assert len( kwr.replay_body.chunks ) > 0
		# +1 second so that we can see the END of the replay.
		self.length = int( kwr.replay_body.chunks[-1].time_code/15 ) + 1
		self.slider.SetMax( self.length )
		self.slider.SetValue( 0 )
		self.time.SetLabel( "00:00:00" )

		self.make_timelines()

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

	args = Args( 'config.ini' )
	app = wx.App()
	
	frame = TimelineViewer( None )
	frame.load( kw )
	#frame.Layout() # do layout again.
	frame.Show( True )

	# export debug
	#frame.on_export( None )
	#frame.Close()

	app.MainLoop()


if __name__ == "__main__" :
	main()

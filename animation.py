#!/usr/bin/python3
import wx
import sys
from kwreplay import time_code2str
from replayviewer import MapView
from chunks import KWReplayWithCommands
from analyzer import PositionDumper
from args import Args



class PosViewer( wx.Frame ) :
	def __init__( self, parent, args, maps_zip='maps.zip' ) :
		super().__init__( parent, title='Replay Movement Viewer', size=(500,500) )
		self.parent = parent
		self.args = args
		self.MAPS_ZIP = maps_zip

		self.kwr = None
		self.pos_analyzer = None
		self.length = 100 # default

		self.movementss = None
		self.buildingss = None
		# buildingss[ pid ] = buildings
		# buildings = [ (t1, loc1), (t2, loc2) ]
		# loc = (x, y) pair.

		self.map_view = None
		self.map_bmp = None # remember how it was before drawing anything on it.
		self.slider = None
		self.time = None
		self.do_layout()
		self.event_bindings()

		self.colors = None
		self.bldg_colors = None
		self.scale = 0 # scale factor VS pos and image pixels.
		self.x_offset = 0
		self.y_offset = 0
		self.make_palette()
	


	def make_palette( self ) :
		self.colors = [
				'#FF0000', # R
				'#0000FF', # B
				'#00FF00', # G
				'#FFFF00', # Y
				'#ff7f00', # Orange
				'#00ffff', # Cyan
				'#ff7fff', # Pink
			]

		self.bldg_colors = [
				'#7f0000', # R
				'#00007f', # B
				'#007f00', # G
				'#7f7f00', # Y
				'#7f6600', # Orange
				'#007f7f', # Cyan
				'#7f667f', # Pink
			]


	def create_top_panel( self, parent ) :
		panel = wx.Panel( parent )
		panel.SetBackgroundColour( (0,0,0) )

		sizer = wx.BoxSizer( wx.HORIZONTAL )

		# map view
		self.map_view = MapView( panel, self.MAPS_ZIP, self.args.mcmap, size=(400,400) )

		# map control panel
		panel_map_ctrl = wx.Panel( self )
		panel_map_ctrl.SetBackgroundColour( (255,0,0) )
		sizer.Add( self.map_view, 0, wx.ALIGN_LEFT|wx.ALIGN_TOP )
		sizer.Add( panel_map_ctrl, 1, wx.EXPAND )

		panel.SetSizer( sizer )
		return panel

	def do_layout( self ) :
		sizer = wx.BoxSizer( wx.VERTICAL )
		panel = wx.Panel( self )
		self.slider = wx.Slider( self, minValue=0, maxValue=100, pos=(20, 20), size=(250, -1) )
		self.time = wx.StaticText( self, label="" )

		# Map view + controls sizer panel
		top_panel = self.create_top_panel( self )

		sizer.Add( top_panel, 1, wx.EXPAND )
		sizer.Add( self.time, 0, wx.EXPAND )
		sizer.Add( self.slider, 0, wx.EXPAND )
		self.SetSizer( sizer )



	def event_bindings( self ) :
		self.slider.Bind( wx.EVT_SCROLL, self.on_scroll )



	def on_scroll( self, evt ) :
		t = evt.GetPosition()
		self.time.SetLabel( time_code2str( t ) )
		self.draw_positions( t )
	


	def draw_dot( self, dc, x, y, color ) :
		x = int( self.scale * x ) + self.x_offset
		y = dc.Y - int( self.scale * y ) + self.y_offset
		dc.SetPen( wx.Pen( color ) )
		dc.DrawLine( x-2, y, x+2, y )
		dc.DrawLine( x, y-2, x, y+2 )
	
	def draw_building( self, dc, x, y, color ) :
		x = int( self.scale * x ) + self.x_offset
		y = dc.Y - int( self.scale * y ) + self.y_offset
		dc.SetPen( wx.Pen( color ) )
		dc.SetBrush( wx.Brush( color ) )
		dc.DrawCircle( x, y, 3 )
	


	def calc_scale_factor( self ) :
		# get X and Y.
		X = 0
		Y = 0
		for commands in self.pos_analyzer.commandss :
			for cmd in commands :
				if cmd.cmd_id == 0x8A :
					X = max( X, cmd.x1 )
					X = max( X, cmd.x2 )
					Y = max( Y, cmd.y1 )
					Y = max( Y, cmd.y2 )
				else :
					X = max( X, cmd.x )
					Y = max( Y, cmd.y )

		bmp = self.map_view.GetBitmap()
		W = bmp.GetWidth()
		H = bmp.GetHeight()

		fx = W/X
		fy = H/Y

		self.scale = max( fx, fy )
		print( "SCALE:", self.scale )
		#self.scale = 0.045
		#self.y_offset = -25
	


	def draw_positions( self, t ) :
		#self.unit_view.show( self.kwr, scale=False ) # remove previous dots.
		#self.map_view.SetBitmap( self.map_bmp )
		#dc = wx.PaintDC( self.map_view )
		#trans_brush = wx.Brush( wx.BLACK, style=wx.BRUSHSTYLE_TRANSPARENT )
		#dc.SetBackground( trans_brush )
		#dc.Clear()
		bmp = wx.Bitmap( self.map_bmp )
		dc = wx.MemoryDC( bmp )
		null, dc.Y = dc.GetSize()

		posa = self.pos_analyzer

		# draw buildings
		for i in range( 0, t ) :
			commands = posa.structures[ i ]

			for cmd in commands :
				pid = cmd.player_id
				player = self.kwr.players[ pid ]
				if not player.is_player() :
					continue
				self.draw_building( dc, cmd.x, cmd.y, self.bldg_colors[pid] )


		# Draw movement dots
		for i in range( t-10, t ) :
			commands = posa.commands[ i ]

			for cmd in commands :
				pid = cmd.player_id
				player = self.kwr.players[ cmd.player_id ]
				if not player.is_player() :
					continue

				if cmd.cmd_id == 0x8A : # wormhole
					#print( "0x%08X" % cmd.cmd_id )
					self.draw_dot( dc, cmd.x1, cmd.y1, self.colors[pid] )
					self.draw_dot( dc, cmd.x2, cmd.y2, self.colors[pid] )
				else :
					self.draw_dot( dc, cmd.x, cmd.y, self.colors[pid] )

		del dc
		self.map_view.SetBitmap( bmp )



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

		# analyze positions
		posa = PositionDumper( kwr )
		self.pos_analyzer = posa
		self.digest_pos_analyzer( posa )

		# drawing related things
		self.map_view.show( kwr, scale=False, watermark=False )
		self.calc_scale_factor()

		self.map_bmp = self.map_view.GetBitmap()
		# At this point, the original state will be captured in the overlay.
		#odc.Clear()



def main() :
	fname = "1.KWReplay"
	if len( sys.argv ) >= 2 :
		fname = sys.argv[1]

	kw = KWReplayWithCommands( fname=fname, verbose=False )
	#kw.replay_body.dump_commands()

	#ana = APMAnalyzer( kw )
	#ana.plot( 10 )
	# or ana.emit_apm_csv( 10, file=sys.stdout )

	#res = ResourceAnalyzer( kw )
	#res.calc()
	#res.plot()

	#pos = PositionDumper( kw )
	#pos.dump_csv()
	app = wx.App()
	
	# debug settings
	CONFIGF = 'config.ini'
	args = Args( CONFIGF )

	frame = PosViewer( None, args )
	frame.load( kw )
	frame.Layout() # do layout again.
	frame.Show( True )
	app.MainLoop()

if __name__ == "__main__" :
	main()

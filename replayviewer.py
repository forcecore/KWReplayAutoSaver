#!/usr/bin/python3
from args import Args
from kwreplay import Player, KWReplay
import os
import datetime
import wx

class ReplayViewer( wx.Frame ) :
	def __init__( self, parent, path ) :
		super().__init__( parent, title='Replay Info Viewer', size=(1024,800) )
		self.do_layout()
		self.event_bindings()

		self.path = path
		self.populate_replay_list( path )
	
	def scan_replay_files( self, path ) :
		fs = []
		for f in os.listdir( path ) :
			if not os.path.isfile( os.path.join( path, f ) ) :
				continue

			# must be a kwreplay file.
			if not f.lower().endswith( ".kwreplay" ) :
				continue

			fs.append( f )
		return fs

	def add_replay( self, path, rep ) :
		fname = os.path.join( path, rep )
		kwr = KWReplay( fname )

		# we need map, name, game desc, time and date.
		# Fortunately, only time and date need computation.
		t = datetime.datetime.fromtimestamp( kwr.timestamp )
		time = t.strftime("%X")
		date = t.strftime("%x")

		index = self.rep_list.GetItemCount()
		pos = self.rep_list.InsertItem( index, kwr.map_name ) # map name
		self.rep_list.SetItem( pos, 1, rep ) # replay name
		self.rep_list.SetItem( pos, 2, kwr.desc ) # desc
		self.rep_list.SetItem( pos, 3, time ) # time
		self.rep_list.SetItem( pos, 4, date ) # date
	
	def populate_replay_list( self, path ) :
		# destroy all existing items
		self.rep_list.DeleteAllItems()

		# now read freshly.
		reps = self.scan_replay_files( path )
		for rep in reps :
			self.add_replay( path, rep )

	def populate_faction_info( self, pos ) :
		assert pos >= 0
		assert self.path
		self.player_list.DeleteAllItems()
		rep = self.rep_list.GetItem( pos, 1 ).GetText() # the replay fname
		fname = os.path.join( self.path, rep )
		kwr = KWReplay( fname )

		for p in kwr.players :
			# p is the Player class. You are quite free to do anything!
			if p.name == "post Commentator" :
				# don't need to see this guy
				continue

			index = self.player_list.GetItemCount()
			if p.team == 0 :
				team = "-"
			else :
				team = str( p.team )
			pos = self.player_list.InsertItem( index, team )
			self.player_list.SetItem( pos, 1, p.name )
			self.player_list.SetItem( pos, 2, Player.decode_faction( p.faction ) )
			self.player_list.SetItem( pos, 3, Player.decode_color( p.color ) )



	def do_layout( self ) :
		self.SetMinSize( (1024, 800) )
		box1 = wx.BoxSizer(wx.VERTICAL)
		hbox = wx.BoxSizer(wx.HORIZONTAL)

		# player list
		self.player_list = wx.ListCtrl( self, size=(-1,200), style=wx.LC_REPORT )
		self.player_list.InsertColumn( 0, 'Team' )
		self.player_list.InsertColumn( 1, 'Name' )
		self.player_list.InsertColumn( 2, 'Faction' )
		self.player_list.InsertColumn( 3, 'Color' )
		self.player_list.SetColumnWidth( 1, 400 )

		# player list
		self.rep_list = wx.ListCtrl( self, size=(-1,200), style=wx.LC_REPORT )
		self.rep_list.InsertColumn( 0, 'Map' )
		self.rep_list.InsertColumn( 1, 'Name' )
		self.rep_list.InsertColumn( 2, 'Description' )
		self.rep_list.InsertColumn( 3, 'Time' )
		self.rep_list.InsertColumn( 4, 'Date' )
		self.rep_list.SetColumnWidth( 0, 180 )
		self.rep_list.SetColumnWidth( 1, 400 )
		self.rep_list.SetColumnWidth( 2, 200 )
		self.rep_list.SetColumnWidth( 3, 100 )
		self.rep_list.SetColumnWidth( 4, 100 )

		# refresh, description editing
		desc_panel = wx.Panel( self, -1 ) #, style=wx.SUNKEN_BORDER )
		ref_panel = wx.Panel( self, -1 ) #, style=wx.SUNKEN_BORDER )
		#panel.SetBackgroundColour("GREEN")
		self.opendir_btn = wx.Button( ref_panel, label="Open Folder", pos=(0,0) )
		self.refresh_btn = wx.Button( ref_panel, label="Rescan Folder", pos=(90,0) )
		game_desc = wx.StaticText( desc_panel, label="Game Description:", pos=(5,5) )
		self.desc_text = wx.TextCtrl( desc_panel, size=(400,-1), pos=(115,2) )
		self.modify_btn = wx.Button( desc_panel, label="Modify!", pos=(525,0) )
		hbox.Add( desc_panel, 1, wx.EXPAND )
		hbox.Add( ref_panel, 0 )

		# hierarchy
		box1.Add( self.player_list, 1, wx.EXPAND )
		box1.Add( hbox, 0, wx.EXPAND)
		box1.Add( self.rep_list, 1, wx.EXPAND)

		self.SetAutoLayout(True)
		self.SetSizer(box1)
		self.Layout()



	def on_refresh_btnClick( self, event ) :
		self.populate_replay_list( self.path )
	
	def on_rep_listClick( self, event ) :
		pos = self.rep_list.GetFocusedItem()
		if pos < 0 :
			return
		# get the selected item and fill desc_text.
		txt = self.rep_list.GetItem( pos, 2 ).GetText()
		self.desc_text.SetValue( txt )

		# fill faction info
		self.populate_faction_info( pos )
	
	def event_bindings( self ) :
		self.refresh_btn.Bind( wx.EVT_BUTTON, self.on_refresh_btnClick )
		self.rep_list.Bind( wx.EVT_LIST_ITEM_SELECTED, self.on_rep_listClick )



def main() :
	app = wx.App()

	# debug settings
	CONFIGF = 'config.ini'
	args = Args( CONFIGF )
	path = os.path.dirname( args.last_replay )

	frame = ReplayViewer( None, path )
	frame.Show( True )
	app.MainLoop()

if __name__ == "__main__" :
	main()

#!/usr/bin/python3
from args import Args
from kwreplay import Player, KWReplay
from watcher import Watcher
import os
import datetime
import subprocess
import wx

class ReplayViewer( wx.Frame ) :
	def __init__( self, parent, path ) :
		super().__init__( parent, title='Replay Info Viewer', size=(1024,800) )
		self.do_layout()
		self.event_bindings()
		self.create_accel_tab()

		self.path = path
		self.populate_replay_list( path )

		self.names = None # scratch memory for replay renaming presets (for context menu)
		self.old_name = "" # lets have a space for the old replay name too.
	
	def change_dir( self ) :
		anyf = "Select_Any_File"
		diag = wx.FileDialog( None, "Select Folder", "", "",
			"Any File (*.*)|*.*",
			wx.FD_OPEN )
		diag.SetFilename( anyf )
		
		if diag.ShowModal() == wx.ID_OK :
			self.path = os.path.dirname( diag.GetPath() )
			self.populate_replay_list( self.path ) # refresh list

		diag.Destroy()

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
		kwr = KWReplay( fname=fname )

		# we need map, name, game desc, time and date.
		# Fortunately, only time and date need computation.
		t = datetime.datetime.fromtimestamp( kwr.timestamp )
		time = t.strftime("%X")
		date = t.strftime("%x")

		index = self.rep_list.GetItemCount()
		pos = self.rep_list.InsertItem( index, rep ) # replay name
		self.rep_list.SetItem( pos, 1, kwr.map_name ) # replay name
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
		rep = self.rep_list.GetItem( pos, 0 ).GetText() # the replay fname
		fname = os.path.join( self.path, rep )
		kwr = KWReplay( fname=fname )

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

	# Generate the context menu when rep_list is right clicked.
	def replay_context_menu( self, event ) :
		pos = event.GetIndex()
		if pos < 0 :
			return

		# get the replay file name
		# handled by "select" event: EVT_LIST_ITEM_SELECTED
		# ... I thought so but in fact, I can right click and rename multiple times without
		# generating EVT_LIST_ITEM_SELECTED.
		# Do it here again!
		rep_name = self.rep_list.GetItem( pos, 0 ).GetText()
		fname = os.path.join( self.path, rep_name )
		self.old_name = fname

		# generate some predefined replay renamings
		kwr = KWReplay( fname=self.old_name )
		self.names = []
		self.names.append( kwr.decode_timestamp( kwr.timestamp ) )
		self.names.append( self.names[0] + " " + Watcher.player_list( kwr ) )

		# make context menu
		menu = wx.Menu()
		# context menu using self.names :
		for i, txt in enumerate( self.names ) :
			item = wx.MenuItem( menu, i, "Rename as " + txt )
			menu.Bind( wx.EVT_MENU, self.replay_context_menu_presetClicked, id=item.GetId() )
			menu.Append( item )

		# custom rename menu
		item = wx.MenuItem( menu, -1, "&Rename (F2)" )
		menu.Bind( wx.EVT_MENU, self.replay_context_menu_rename, id=item.GetId() )
		menu.Append( item )

		# delete replay menu
		item = wx.MenuItem( menu, -1, "&Delete (Del)" )
		menu.Bind( wx.EVT_MENU, self.replay_context_menu_delete, id=item.GetId() )
		menu.Append( item )

		# open contaning folder
		item = wx.MenuItem( menu, -1, "&Open containing folder" )
		menu.Bind( wx.EVT_MENU, self.open_containing_folder, id=item.GetId() )
		menu.Append( item )
		
		self.rep_list.PopupMenu( menu, event.GetPoint() ) # popup the context menu.
		menu.Destroy() # prevents memory leaks haha
	
	def open_containing_folder( self, event ) :
		# not relying wxPython!
		cmd = 'explorer /select,"%s"' % (self.old_name)
		#print( cmd )
		subprocess.Popen( cmd )
	
	def replay_context_menu_rename( self, event ) :
		item = self.rep_list.GetFocusedItem()
		self.rep_list.EditLabel( item )

	# Delete this replay?
	def replay_context_menu_delete( self, event ) :
		pos = self.rep_list.GetFocusedItem()
		if pos < 0 :
			return
		rep_name = self.rep_list.GetItem( pos, 0 ).GetText()

		diag = wx.MessageDialog( self,
				"Really delete " + rep_name + "?",
				"Confirm Deletion",
				wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION )
		result = diag.ShowModal()
		diag.Destroy()

		if result == wx.ID_YES :
			# delete the file
			# the context menu should have old_name correct by now.
			assert self.old_name
			os.remove( self.old_name )
			# delete the list.
			self.rep_list.DeleteItem( pos )

	def replay_context_menu_presetClicked( self, event ) :
		assert self.names
		index = event.GetId()
		rep_name = self.names[ index ]
		self.rename_with_stem( rep_name )
	
	def rename_with_stem( self, rep_name ) :
		# Add extension if not exists
		if not rep_name.lower().endswith( ".kwreplay" ) :
			rep_name += ".KWReplay"

		# sanitize invalid char
		for char in [ "<", ">", ":", "\"", "/", "\\", "|", "?", "*" ] :
			rep_name = rep_name.replace( char, "_" )

		# this is the full name.
		fname = os.path.join( self.path, rep_name )

		# see if it already exits.
		if os.path.isfile( fname ) :
			diag = wx.MessageDialog( self, fname + "\nalready exists! Not renaming.", "Error",
					wx.OK|wx.ICON_ERROR )
			diag.ShowModal()
			diag.Destroy()
		else :
			# rename the file
			self.do_renaming( rep_name )

	# Given new rep_name
	# do renaming in the file system and
	# update the entry in the viewer.
	def do_renaming( self, rep_name ) :
		# rename in the file system.
		assert self.old_name
		# self.old_name is already with full path.
		if not os.path.isfile( self.old_name ) :
			# for some reason the old one may not exist.
			# perhaps due to not refreshed list.
			msg = "Replay does not exists! Please rescan the folder!"
			diag = wx.MessageDialog( self, msg, "Error", wx.OK|wx.ICON_ERROR )
			diag.ShowModal()
			diag.Destroy()
			return

		fname = os.path.join( self.path, rep_name )
		os.rename( self.old_name, fname )

		# rename in the viewer
		pos = self.rep_list.GetFocusedItem()
		if pos < 0 :
			return
		# get the selected item and fill desc_text.
		self.rep_list.SetItem( pos, 0, rep_name ) # replay name
	
	def custom_rename( self, event ) :
		pos = self.rep_list.GetFocusedItem()
		if pos < 0 :
			return
		old_stem = self.rep_list.GetItem( pos, 0 ).GetText()
		event.Veto() # undos all edits from the user, for now.
		# if valid, the edit is accepted and updated by some update function.

		stem = event.GetText() # newly edited text
		if old_stem == stem :
			# user pressed esc or something
			return

		if not stem.lower().endswith( ".kwreplay" ) :
			stem += ".KWReplay"

		# Check for invalid char
		for char in [ "<", ">", ":", "\"", "/", "\\", "|", "?", "*" ] :
			if char in stem :
				msg = "File name must not contain the following:\n"
				msg += "<>:\"/\\|?*"
				diag = wx.MessageDialog( self, msg, "Error", wx.OK|wx.ICON_ERROR )
				diag.ShowModal()
				diag.Destroy()
				return

		# Accepted.
		self.rename_with_stem( stem )

		# You can keep renaming without generating right click or left click events.
		# Update old_name to compensate for this.
		self.old_name = os.path.join( self.path, stem )



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

		# replay list
		self.rep_list = wx.ListCtrl( self, size=(-1,200), style=wx.LC_REPORT|wx.LC_EDIT_LABELS )
		self.rep_list.InsertColumn( 0, 'Name' )
		self.rep_list.InsertColumn( 1, 'Map' )
		self.rep_list.InsertColumn( 2, 'Description' )
		self.rep_list.InsertColumn( 3, 'Time' )
		self.rep_list.InsertColumn( 4, 'Date' )
		self.rep_list.SetColumnWidth( 0, 400 )
		self.rep_list.SetColumnWidth( 1, 180 )
		self.rep_list.SetColumnWidth( 2, 200 )
		self.rep_list.SetColumnWidth( 3, 100 )
		self.rep_list.SetColumnWidth( 4, 100 )

		# refresh, description editing
		desc_panel = wx.Panel( self, -1 ) #, style=wx.SUNKEN_BORDER )
		ref_panel = wx.Panel( self, -1 ) #, style=wx.SUNKEN_BORDER )
		#panel.SetBackgroundColour("GREEN")
		self.opendir_btn = wx.Button( ref_panel, label="Change Folder", pos=(0,0) )
		self.refresh_btn = wx.Button( ref_panel, label="Rescan Folder", pos=(100,0) )
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

	def create_accel_tab( self ) :
		# Accelerator table (short cut keys)
		self.id_rename = wx.NewId()
		self.id_del = wx.NewId()

		self.Bind( wx.EVT_MENU, self.replay_context_menu_rename, id=self.id_rename )
		self.Bind( wx.EVT_MENU, self.replay_context_menu_delete, id=self.id_del )

		accel_tab = wx.AcceleratorTable([
				( wx.ACCEL_NORMAL, wx.WXK_F2, self.id_rename ),
				( wx.ACCEL_NORMAL, wx.WXK_DELETE, self.id_del )
			])
		self.SetAcceleratorTable( accel_tab )



	def on_refresh_btnClick( self, event ) :
		self.populate_replay_list( self.path )

	def on_opendir_btnClick( self, event ) :
		self.change_dir()
	
	def on_rep_listRightClick( self, event ) :
		self.replay_context_menu( event )

	def on_rep_listClick( self, event ) :
		pos = event.GetIndex()
		if pos < 0 :
			return
		# get the selected item and fill desc_text.
		txt = self.rep_list.GetItem( pos, 2 ).GetText()
		self.desc_text.SetValue( txt )

		# remember the old name
		rep = self.rep_list.GetItem( pos, 0 ).GetText()
		self.old_name = os.path.join( self.path, rep )

		# fill faction info
		self.populate_faction_info( pos )
	
	def on_rep_list_end_label_edit( self, event ) :
		self.custom_rename( event )
	
	def event_bindings( self ) :
		self.refresh_btn.Bind( wx.EVT_BUTTON, self.on_refresh_btnClick )

		self.opendir_btn.Bind( wx.EVT_BUTTON, self.on_opendir_btnClick)

		self.rep_list.Bind( wx.EVT_LIST_ITEM_SELECTED, self.on_rep_listClick )
		self.rep_list.Bind( wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_rep_listRightClick )
		self.rep_list.Bind( wx.EVT_LIST_END_LABEL_EDIT, self.on_rep_list_end_label_edit )



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

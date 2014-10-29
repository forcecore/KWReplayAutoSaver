#!/usr/bin/python3
from args import Args
from kwreplay import Player, KWReplay
from watcher import Watcher
import os
import io
import time
import datetime
import zipfile
import subprocess
import wx

KWICO='KW.ico'

# Not just the replay class, this class is for ease of management in rep_list.
class ReplayItem() :
	def __init__( self ) :
		self.fname = None # without path!!! = not full path!
		self.kwr = None

class ReplayItems() :
	def __init__( self ) :
		self.items = []

	def append( self, it ) :
		self.items.append( it )

	# delete the replay with fname from items
	def find( self, fname ) :
		fname = os.path.basename( fname ) # incase...
		for it in self.items :
			if it.fname == fname :
				return it
		raise KeyError

	def remove( self, fname ) :
		it = self.find( fname )
		self.items.remove( it )

	# rename it.fname
	def rename( self, src, dest ) :
		it = self.find( src ) # find does basename for me.
		dest = os.path.basename( dest )
		it.fname = dest

	# finds the item with fname and replace it
	def replace( self, fname, new_kwr ) :
		it = self.find( fname )
		it.kwr = new_kwr

class MapZip() :
	def __init__( self, fname ) :
		self.fname = fname
		self.zipf = zipfile.ZipFile( fname, 'r' )
		self.namelist = self.zipf.namelist()
	
	def hasfile( self, fname ) :
		return fname in self.namelist

	# load fname and return as wx.Image
	def load( self, fname ) :
		assert self.hasfile( fname )
		zs = self.zipf.open( fname ) # open stream

		# but zs doesn't support seek() operation.
		# read onto a buffer to support seek().
		s = io.BytesIO( zs.read() )

		img = wx.Image()
		img.LoadFile( s )
		s.close()
		zs.close()
		return img

	# from rep_list, retrieve selected items' indices.

class MapView( wx.StaticBitmap ) :
	def __init__( self, parent, maps, size=(200,200) ) :
		super().__init__( parent, size=size )

		# Like self.replay_items, load map images into memory and keep them
		# it doesn't load everything from the beginning. it is loaded on request in
		# set_map_preview().
		self.map_previews = {} # holder!
		self.mapzip = MapZip( maps )

	# ui: statisbitmap to fit in.
	# img: img that will go into ui.
	def calc_best_wh( self, img ) :
		(w, h) = self.GetSize()
		(x, y) = img.GetSize()

		# lets try fitting ...
		#x1 = w # x/x*w
		y1 = int( y*w/x )

		x2 = int( x*h/y )
		#y2 = h # y/y*h

		if y1 < h and x2 < x :
			# if both sizes fit, go for larger area.
			area1 = w*y1
			area2 = x2*h
			if area1 > area2 :
				return (w, y1)
			else :
				return (x2, h)
		elif y1 <= h :
			return (w, y1)
		elif x2 <= w :
			return (x2, h)
		else :
			assert 0 # one of them should fit!!

	def set_map_preview( self, fname ) :
		# clear the image area first.
		# w, h may change. we generate it on every map change for sure.
		# Well, I can do that on size change but can't be bothered to do that...
		(w, h) = self.GetSize()
		black = wx.Image( w, h, clear=True )
		self.SetBitmap( wx.Bitmap( black ) )
		if not fname :
			return

		if fname in self.map_previews :
			# use previously loaded image
			img = self.map_previews[ fname ]
		else :
			# now we show proper image.
			# I get "iCCP: known incorrect sRGB profile" for some PNG files.
			# Lets silence this with log null object.
			no_log = wx.LogNull()
			img = self.mapzip.load( fname )
			del no_log # restore
			self.map_previews[ fname ] = img # keep it in memory

		(w, h) = self.calc_best_wh( img )
		resized = img.Scale( w, h)
		self.SetBitmap( wx.Bitmap( resized ) )
	
	# show map preview
	def show( self, kwr ) :
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
			fname = None
			# copy the name to clipboard so we can actually insert item to DB!
			data = wx.TextDataObject( kwr.map_path )
			wx.TheClipboard.Open()
			wx.TheClipboard.SetData( data )
			wx.TheClipboard.Close()

		# Load it and show it on the interface.
		self.set_map_preview( fname )



# "selected" iterator for listctrls!
class selected( object ) :
	def __init__( self, list_ctrl ) :
		self.index = -1
		self.list_ctrl = list_ctrl

	def __iter__( self ) :
		return self

	def __next__( self ) :
		return self.next()

	def next( self ) :
		self.index = self.list_ctrl.GetNextSelected( self.index )
		if self.index == -1 :
			raise StopIteration()
		else :
			return self.index

class PlayerList( wx.ListCtrl ) :
	def __init__( self, parent ) :
		super().__init__( parent, size=(600,200), style=wx.LC_REPORT )
		self.InsertColumn( 0, 'Team' )
		self.InsertColumn( 1, 'Name' )
		self.InsertColumn( 2, 'Faction' )
		self.InsertColumn( 3, 'Color' )
		self.SetColumnWidth( 1, 400 )
		#self.SetMinSize( (600, 200) )
	
	def populate( self, kwr ) :
		self.DeleteAllItems()
		for p in kwr.players :
			# p is the Player class. You are quite free to do anything!
			if p.name == "post Commentator" :
				# don't need to see this guy
				continue

			index = self.GetItemCount()
			if p.team == 0 :
				team = "-"
			else :
				team = str( p.team )
			pos = self.InsertItem( index, team )
			self.SetItem( pos, 1, p.name )
			self.SetItem( pos, 2, Player.decode_faction( p.faction ) )
			self.SetItem( pos, 3, Player.decode_color( p.color ) )



class ReplayList( wx.ListCtrl ) :
	def __init__( self, parent ) :
		super().__init__( parent, size=(-1,200),
				style=wx.LC_REPORT|wx.LC_EDIT_LABELS )
		self.InsertColumn( 0, 'Name' )
		self.InsertColumn( 1, 'Map' )
		self.InsertColumn( 2, 'Description' )
		self.InsertColumn( 3, 'Time' )
		self.InsertColumn( 4, 'Date' )
		self.SetColumnWidth( 0, 400 )
		self.SetColumnWidth( 1, 180 )
		self.SetColumnWidth( 2, 200 )
		self.SetColumnWidth( 3, 100 )
		self.SetColumnWidth( 4, 100 )
		#self.SetMinSize( (600, 200) )
	
	def populate( self, reps, filter=None ) :
		# destroy all existing items
		self.DeleteAllItems()

		# now read freshly.
		for rep in reps.items :
			self.add_replay( rep, filter=filter )

		# managing sort state XD
		self.last_clicked_col = -1 # last clicked column number
		self.ascending = True # sort by ascending order?

	def add_replay( self, rep, filter=None ) :
		fname = rep.fname
		kwr = rep.kwr

		if self.filter_hit( filter, kwr, fname ) :
			# we need map, name, game desc, time and date.
			# Fortunately, only time and date need computation.
			t = datetime.datetime.fromtimestamp( kwr.timestamp )
			time = t.strftime("%X")
			date = t.strftime("%x")

			index = self.GetItemCount()
			pos = self.InsertItem( index, fname ) # replay name
			self.SetItem( pos, 1, kwr.map_name ) # replay name
			self.SetItem( pos, 2, kwr.desc ) # desc
			self.SetItem( pos, 3, time ) # time
			self.SetItem( pos, 4, date ) # date

	# determine if filter hit -> show in rep_list.
	def filter_hit( self, filter, kwr, fname ) :
		if not filter :
			# either filter == None or empty string!
			return True

		# lower case everything
		fname = fname.lower()
		map_name = kwr.map_name.lower()
		words = filter.lower().split()
		players = []
		desc = kwr.desc.lower()
		for player in kwr.players :
			players.append( player.name.lower() )

		for word in words :
			# matches filename
			if word in fname :
				return True
			
			# matches map name
			if word in map_name :
				return True

			# matches description
			if word in desc :
				return True

			# matches player name
			for player in players :
				if word in player :
					return True

		return False

	def key_func( self, item, col ) :
		if col == 4 :
			# date!!!
			return time.strptime( item[ col ], "%x" )
		else :
			return item[ col ]
	
	def sort( self, col, asc ) :
		items = self.retrieve_rep_list_items()
		items.sort( key=lambda item: self.key_func( item, col ) )
		if not asc :
			items.reverse()
		self.DeleteAllItems()
		self.insert_rep_list_items( items )

	def insert_rep_list_items( self, items ) :
		for item in items :
			index = self.GetItemCount()
			pos = self.InsertItem( index, item[0] ) # replay name
			for i in range( 1, 5 ) :
				# other items
				self.SetItem( pos, i, item[i] )

	def retrieve_rep_list_items( self ) :
		# turn all items into a list.
		items = []
		for i in range( self.GetItemCount() ) :
			item = []
			for j in range( 5 ) : # there are 5 cols
				item.append( self.GetItem( i, j ).GetText() )
			items.append( item )
		return items

	# sort by clicked column
	def on_col_click( self, event ) :
		# determine ascending or descending.
		if self.last_clicked_col == event.GetColumn() :
			self.ascending = not self.ascending
		else :
			self.ascending = True
		self.last_clicked_col = event.GetColumn()

		# now lets do the sorting
		self.sort( event.GetColumn(), self.ascending )



class ReplayViewer( wx.Frame ) :
	def __init__( self, parent, args ) :
		super().__init__( parent, title='Replay Info Viewer', size=(1024,800) )

		self.MAPS_ZIP = 'maps.zip' # the name of the zip file that has map previews
		self.do_layout()
		self.event_bindings()
		self.create_accel_tab()
		self.set_icon()

		self.args = args
		self.path = os.path.dirname( args.last_replay )
		self.replay_items = self.scan_replay_files( self.path )

		# don't need DB. we just set the image name right.
		#self.map_db = self.load_map_db( 'MapDB.txt' )

		self.rep_list.populate( self.replay_items )

		self.names = None # scratch memory for replay renaming presets (for context menu)
		self.ctx_old_name = "" # lets have a space for the old replay name too.
			# this one is for remembering click/right clicked ones only.
			# i.e, context menus.
		self.custom_old_name = ""
			# this one, is for remembering the old fname for custom renames.
	
	def load_map_db( self, fname ) :
		f = open( fname )
		txt = f.read()
		f.close()
		#print( txt )
		# variable db is defined in txt!;;;;

		# looks funny that I can't use locals() as globals() in the parameter directly.
		# See this for details:
		# http://stackoverflow.com/questions/1463306/how-does-exec-work-with-locals
		ldict = locals()
		exec( txt, globals(), ldict )
		db = ldict[ 'db' ] # must pull it out from ldict explicitly!!;;;
		return db
	
	def change_dir( self ) :
		anyf = "Select_Any_File"
		diag = wx.FileDialog( None, "Select Folder", "", "",
			"Any File (*.*)|*.*",
			wx.FD_OPEN )
		diag.SetFilename( anyf )
		
		if diag.ShowModal() == wx.ID_OK :
			self.path = os.path.dirname( diag.GetPath() )
			self.refresh_path()

		diag.Destroy()

	# scan a folder and return the replays as ReplayItem.
	def scan_replay_files( self, path ) :
		fs = []
		for f in os.listdir( path ) :
			if not os.path.isfile( os.path.join( path, f ) ) :
				continue

			# must be a kwreplay file.
			if not f.lower().endswith( ".kwreplay" ) :
				continue

			fs.append( f )

		replays = ReplayItems()
		for f in fs :
			i = ReplayItem()
			i.fname = f
			full_name = os.path.join( self.path, f )
			i.kwr = KWReplay( fname=full_name )
			replays.append( i )
		return replays

	# Generate the context menu when rep_list is right clicked.
	def replay_context_menu( self, event ) :
		cnt = self.rep_list.GetSelectedItemCount()
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
		self.ctx_old_name = fname

		# generate some predefined replay renamings
		kwr = KWReplay( fname=self.ctx_old_name )
		self.names = []
		# having only date seems silly but for people with custom date format, it may be useful.
		# I'm keeping it.
		self.names.append( Watcher.calc_name( kwr,
				add_username=False, add_faction=False, add_vs_info=False,
				custom_date_format=self.args.custom_date_format ) )
		#self.names.append( Watcher.calc_name( kwr,
		#		add_username=False, add_faction=True, custom_date_format=self.args.custom_date_format ) )
		# add_faction is meaningless without add_username, duh!
		self.names.append( Watcher.calc_name( kwr,
				add_username=True, add_faction=False, add_vs_info=False,
				custom_date_format=self.args.custom_date_format ) )
		self.names.append( Watcher.calc_name( kwr,
				add_username=True, add_faction=True, add_vs_info=False,
				custom_date_format=self.args.custom_date_format ) )
		self.names.append( Watcher.calc_name( kwr,
				add_username=True, add_faction=False, add_vs_info=True,
				custom_date_format=self.args.custom_date_format ) )
		self.names.append( Watcher.calc_name( kwr,
				add_username=True, add_faction=True, add_vs_info=True,
				custom_date_format=self.args.custom_date_format ) )

		# make context menu
		menu = wx.Menu()
		# context menu using self.names :
		for i, txt in enumerate( self.names ) :
			# variable txt is a copy of the variable. I may modify it safely without
			# affecting self.names!
			txt = txt.replace( "&", "&&" ) # Gotcha, in wx.
			# & indicates a shortcut key. I must say && to actually display & in the menu.
			if cnt > 1 :
				prefix = "Rename like "
			else :
				prefix = "Rename as "
			item = wx.MenuItem( menu, i, prefix + txt )
			menu.Bind( wx.EVT_MENU, self.replay_context_menu_presetClicked, id=item.GetId() )
			menu.Append( item )

		# custom rename menu
		if cnt == 1 :
			item = wx.MenuItem( menu, -1, "&Rename (F2)" )
			menu.Bind( wx.EVT_MENU, self.replay_context_menu_rename, id=item.GetId() )
			menu.Append( item )

		# delete replay menu
		item = wx.MenuItem( menu, -1, "&Delete (Del)" )
		menu.Bind( wx.EVT_MENU, self.replay_context_menu_delete, id=item.GetId() )
		menu.Append( item )

		# open contaning folder
		if cnt == 1 :
			item = wx.MenuItem( menu, -1, "&Open containing folder" )
			menu.Bind( wx.EVT_MENU, self.open_containing_folder, id=item.GetId() )
			menu.Append( item )
		
		self.rep_list.PopupMenu( menu, event.GetPoint() ) # popup the context menu.
		menu.Destroy() # prevents memory leaks haha
	
	def open_containing_folder( self, event ) :
		# not relying wxPython!
		cmd = 'explorer /select,"%s"' % (self.ctx_old_name)
		#print( cmd )
		subprocess.Popen( cmd )
	
	def replay_context_menu_rename( self, event ) :
		if not self.ctx_old_name :
			# pressed F2 without selecting any item!
			return
		item = self.rep_list.GetFocusedItem()
		self.rep_list.EditLabel( item )
	
	# Delete this replay?
	def replay_context_menu_delete( self, event ) :
		cnt = self.rep_list.GetSelectedItemCount()
		if cnt == 0 :
			return

		pos = self.rep_list.GetNextSelected( -1 ) # get first selected index
		rep_name = self.rep_list.GetItem( pos, 0 ).GetText()

		# confirmation message
		msg = "Really delete " + rep_name
		if cnt == 1 :
			msg += "?"
		else :
			msg += " and " + str( cnt-1 ) + " others?"

		# ICON_QUESTION will not show up...  It is intended by the library.
		# Read http://wxpython.org/Phoenix/docs/html/MessageDialog.html for more info.
		result = wx.MessageBox( msg, "Confirm Deletion",
				wx.ICON_QUESTION|wx.OK|wx.OK_DEFAULT|wx.CANCEL )
		if result != wx.OK :
			return

		for pos in reversed( list( selected( self.rep_list ) ) ) :
			rep_name = self.rep_list.GetItem( pos, 0 ).GetText()
			fname = os.path.join( self.path, rep_name )

			self.rep_list.DeleteItem( pos ) # delete from list
			self.replay_items.remove( rep_name ) # delete from mem
			os.remove( fname ) # delete the file
			self.ctx_old_name = None



	def replay_context_menu_presetClicked( self, event ) :
		assert self.names
		cnt = self.rep_list.GetSelectedItemCount()
		index = event.GetId() # menu index

		if cnt == 1 :
			pos = self.rep_list.GetFocusedItem()
			# Keeping self.names, for reading less from the disk.
			# I do think that it will be a neater code to remove this cnt==1 special case
			# but for the sake of performance, I'm keeping it.
			rep_name = self.names[ index ]
			self.rename_with_stem( pos, self.ctx_old_name, rep_name )
			return

		#
		# mass renaming case!
		#

		# compute parameter for calc_name.
		if index == 0 :
			au = False # add user info
			af = False # add faction info
			av = False # add vs info
		elif index == 1 :
			au = True
			af = False
			av = False
		elif index == 2 :
			au = True
			af = True
			av = False
		elif index == 3 :
			au = True
			af = False
			av = True
		elif index == 4 :
			au = True
			af = True
			av = True
		else :
			assert index <= 2

		# iterate list.
		for index in selected( self.rep_list ) :
			# old full name
			old_name = self.rep_list.GetItem( index, 0 ).GetText()
			old_name = os.path.join( self.path, old_name )

			it = self.replay_items.find( old_name )

			rep_name = Watcher.calc_name( it.kwr, add_username=au, add_faction=af,
					add_vs_info=av,
					custom_date_format=self.args.custom_date_format )

			self.rename_with_stem( index, old_name, rep_name )

	# given some user friendly name "rep_name" as stem,
	# canonicalize it.
	# pos = rep_list entry position to update
	def rename_with_stem( self, pos, old_name, rep_name ) :
		# Add extension if not exists
		if not rep_name.lower().endswith( ".kwreplay" ) :
			rep_name += ".KWReplay"

		# sanitize invalid char
		rep_name = Watcher.sanitize_name( rep_name )

		# this is the full name.
		fname = os.path.join( self.path, rep_name )

		# see if it already exits.
		if os.path.isfile( fname ) :
			diag = wx.MessageBox( fname + "\nalready exists! Not renaming.", "Error",
					wx.OK|wx.ICON_ERROR )
		else :
			# rename the file
			self.do_renaming( pos, old_name, rep_name )

	# Given new rep_name
	# do renaming in the file system and
	# update the entry in the viewer.
	# pos = rep_list entry position to update
	def do_renaming( self, pos, old_name, rep_name ) :
		assert pos >= 0
		# rename in the file system.
		assert old_name
		# self.custom_old_name is already with full path.
		if not os.path.isfile( old_name ) :
			# for some reason the old one may not exist.
			# perhaps due to not refreshed list.
			msg = "Replay does not exists! Please rescan the folder!"
			wx.MessageBox( msg, "Error", wx.OK|wx.ICON_ERROR )
			return

		fname = os.path.join( self.path, rep_name )
		os.rename( old_name, fname )

		# rename in the viewer
		self.rep_list.SetItem( pos, 0, rep_name ) # replay name
		# rename in the replay_items
		self.replay_items.rename( old_name, fname )

	def create_desc_panel( self, parent ) :
		desc_panel = wx.Panel( parent, -1 ) #, style=wx.SUNKEN_BORDER )
		game_desc = wx.StaticText( desc_panel, label="Game Description:", pos=(5,5) )
		self.desc_text = wx.TextCtrl( desc_panel, size=(400,-1),
				pos=(115,2), style=wx.TE_PROCESS_ENTER )
		self.modify_btn = wx.Button( desc_panel, label="Modify!", pos=(525,0) )
		return desc_panel
	
	def create_filter_panel( self, parent ) :
		filter_panel = wx.Panel( parent, -1 )
		filter_st = wx.StaticText( filter_panel, label="Filter", pos=(5,5) )
		self.filter_text = wx.TextCtrl( filter_panel, size=(400,-1),
				pos=(115,2), style=wx.TE_PROCESS_ENTER )
		self.apply_btn = wx.Button( filter_panel, label="Apply", pos=(525,0) )
		self.nofilter_btn = wx.Button( filter_panel, label="X",
				pos=(610,0), size=(50,wx.DefaultSize.y) )
		return filter_panel
	
	def create_ref_panel( self, parent ) :
		ref_panel = wx.Panel( parent, -1 ) #, style=wx.SUNKEN_BORDER )
		#panel.SetBackgroundColour("GREEN")
		self.opendir_btn = wx.Button( ref_panel, label="Change Folder", pos=(0,0) )
		self.refresh_btn = wx.Button( ref_panel, label="Rescan Folder", pos=(100,0) )
		return ref_panel

	def create_top_panel( self, parent ) :
		panel = wx.Panel( parent )

		self.player_list = PlayerList( panel )
		self.map_view = MapView( panel, self.MAPS_ZIP, size=(200,200) )
		self.map_view.SetMinSize( (200, 200) )

		# sizer code
		sizer = wx.BoxSizer( wx.HORIZONTAL )
		sizer.Add( self.player_list, 1, wx.EXPAND)
		sizer.Add( self.map_view, 0, wx.ALIGN_CENTER )

		panel.SetSizer( sizer )
		panel.SetMinSize( (600, 200) )
		return panel

	def do_layout( self ) :
		self.SetMinSize( (900, 700) )
		main_sizer = wx.BoxSizer( wx.VERTICAL )
		splitter = wx.SplitterWindow( self ) # must go into a sizer :S
		splitter.SetMinimumPaneSize( 20 )
		main_sizer.Add( splitter, 1, wx.EXPAND )

		# top part of the splitter.
		# creates self.player_list, self.map_view
		top_panel = self.create_top_panel( splitter )

		#
		# bottom part of the splitter
		#
		# for splitter box resizing...
		bottom_panel = wx.Panel( splitter, size=(500,500) )

		self.rep_list = ReplayList( bottom_panel )

		# description editing
		# creates self.desc_text, self.modify_btn also.
		desc_panel = self.create_desc_panel( bottom_panel )

		# replay filtering
		# creates self.{filter_text, apply_btn, nofilter_btn} also.
		filter_panel = self.create_filter_panel( bottom_panel )

		# change folder and rescan folder buttons
		# creates self.{opendir_btn, refresh_btn}
		ref_panel = self.create_ref_panel( bottom_panel )

		# filter and ref panel are actually small enough to be merged
		# into a single bar.
		hbox1 = wx.BoxSizer( wx.HORIZONTAL )
		hbox1.Add( filter_panel, 1, wx.EXPAND )
		hbox1.Add( ref_panel, 0 )

		# tie bottom elements into a sizer.
		bottom_box = wx.BoxSizer( wx.VERTICAL )
		bottom_box.Add( hbox1, 0, wx.EXPAND)
		bottom_box.Add( desc_panel, 0, wx.EXPAND)
		bottom_box.Add( self.rep_list, 1, wx.EXPAND)
		bottom_panel.SetSizer( bottom_box )
		#bottom_box.SetMinSize( (600, 400 ) )

		splitter.SplitHorizontally( top_panel, bottom_panel )
		#splitter.SetSashGravity( 0.5 )

		self.SetAutoLayout(True)
		self.SetSizer( main_sizer )
		bottom_box.Fit( bottom_panel )
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
	
	def set_icon( self ) :
		if os.path.isfile( KWICO ) :
			icon = wx.Icon( KWICO, wx.BITMAP_TYPE_ICO )
			self.SetIcon( icon )



	def on_refresh_btnClick( self, event ) :
		self.refresh_path()

	# removing filter is the same as refresh_path but doesn't rescan path's files.
	def on_nofilter_btnClick( self, event ) :
		self.filter_text.SetValue( "" ) # removes filter.
		self.rep_list.populate( self.replay_items )
	
	def refresh_path( self ) :
		self.filter_text.SetValue( "" ) # removes filter.
		self.replay_items = self.scan_replay_files( self.path )
		self.rep_list.populate( self.replay_items )

	def on_opendir_btnClick( self, event ) :
		self.change_dir()
	
	def on_rep_listRightClick( self, event ) :
		self.replay_context_menu( event )

	def on_rep_listClick( self, event ) :
		pos = event.GetIndex()
		if pos < 0 :
			return

		# get the selected item and fill desc_text for editing.
		txt = self.rep_list.GetItem( pos, 2 ).GetText()
		self.desc_text.SetValue( txt )

		# remember the old name (for other renaming routines)
		rep = self.rep_list.GetItem( pos, 0 ).GetText()
		self.ctx_old_name = os.path.join( self.path, rep )

		# get related replay.
		r = self.replay_items.find( rep )

		# fill faction info
		self.player_list.populate( r.kwr )

		# load map preview
		self.map_view.show( r.kwr )
	
	def on_rep_list_end_label_edit( self, event ) :
		event.Veto() # undos all edits from the user, for now.

		#pos = self.rep_list.GetFocusedItem()
		#if pos < 0 :
		#	return

		#if pos != event.GetIndex() :
		#	# User invoked renaming but clicked on another replay
		#	# In this case, silently quit edit.
		#	return

		pos = event.GetIndex() # maybe this is a more correct
		old_stem = self.rep_list.GetItem( pos, 0 ).GetText()
		# if valid, the edit is accepted and updated by some update function.

		stem = event.GetText() # newly edited text
		if old_stem == stem :
			# user pressed esc or something
			return

		if not stem.lower().endswith( ".kwreplay" ) :
			stem += ".KWReplay"

		# Check for invalid char
		sanitized = Watcher.sanitize_name( stem )
		if sanitized != stem :
			msg = "File name must not contain the following:\n"
			msg += "<>:\"/\\|?*"
			wx.MessageBox( msg, "Error", wx.OK|wx.ICON_ERROR )
			return

		# Accepted.
		self.rename_with_stem( pos, self.custom_old_name, stem )

	def on_rep_list_begin_label_edit( self, event ) :
		pos = event.GetIndex() # maybe this is a more correct
		stem = self.rep_list.GetItem( pos, 0 ).GetText()
		self.custom_old_name = os.path.join( self.path, stem )
		# remember the old name from custom renaming
	
	def on_modify_btnClick( self, event ) :
		if not self.ctx_old_name : 
			# pressed modify! button without selecting anything.
			return

		# I think I could use self.ctx_old_name but...
		pos = self.rep_list.GetFocusedItem()
		if pos < 0 :
			return
		rep = self.rep_list.GetItem( pos, 0 ).GetText()
		fname = os.path.join( self.path, rep )

		desc = self.desc_text.GetValue()

		# so, old_name should be quite valid by now.
		kwr = KWReplay()
		kwr.modify_desc_inplace( fname, desc )

		# update it in the interface.
		self.rep_list.SetItem( pos, 2, desc ) # desc
		kwr = KWReplay( fname ) # reload it.
		self.replay_items.replace( fname, kwr )
	
	def on_filter_applyClick( self, event ) :
		fil = self.filter_text.GetValue()
		self.rep_list.populate( self.replay_items, filter=fil )

	def event_bindings( self ) :
		self.refresh_btn.Bind( wx.EVT_BUTTON, self.on_refresh_btnClick )

		self.modify_btn.Bind( wx.EVT_BUTTON, self.on_modify_btnClick )
		self.desc_text.Bind( wx.EVT_TEXT_ENTER, self.on_modify_btnClick )

		self.opendir_btn.Bind( wx.EVT_BUTTON, self.on_opendir_btnClick )

		self.apply_btn.Bind( wx.EVT_BUTTON, self.on_filter_applyClick )
		self.nofilter_btn.Bind( wx.EVT_BUTTON, self.on_nofilter_btnClick )
		self.filter_text.Bind( wx.EVT_TEXT_ENTER, self.on_filter_applyClick )

		self.rep_list.Bind( wx.EVT_LIST_ITEM_SELECTED, self.on_rep_listClick )
		self.rep_list.Bind( wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_rep_listRightClick )
		self.rep_list.Bind( wx.EVT_LIST_END_LABEL_EDIT, self.on_rep_list_end_label_edit )
		self.rep_list.Bind( wx.EVT_LIST_BEGIN_LABEL_EDIT, self.on_rep_list_begin_label_edit )
		self.rep_list.Bind( wx.EVT_LIST_COL_CLICK, self.rep_list.on_col_click )



def main() :
	app = wx.App()

	# debug settings
	CONFIGF = 'config.ini'
	args = Args( CONFIGF )

	frame = ReplayViewer( None, args )
	frame.Show( True )
	app.MainLoop()

if __name__ == "__main__" :
	main()

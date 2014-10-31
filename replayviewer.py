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
import hashlib
import wx

KWICO='KW.ico'

# Not just the replay class, this class is for ease of management in rep_list.
class ReplayItem() :
	def __init__( self ) :
		self.fname = None # without path!!! = not full path!
		self.kwr = None
		self.id = -1

class ReplayItems() :
	def __init__( self ) :
		self.items = []
		self.id = 0 # Keep available UID for newly appended replays.

	def append( self, it ) :
		self.items.append( it )
		it.id = self.id
		self.id += 1

	# delete the replay with fname from items
	def find( self, fname=None, id=None ) :
		assert fname != None or id != None
		assert not ( fname != None and id != None )

		if fname :
			return self.find_fname( fname )
		else :
			return self.find_id( id )

	# Since I'm only appending items (not not shuffling them)
	# I should be able to do a binary search... but, nah, not now.
	def find_id( self, id ) :
		for it in self.items :
			if it.id == id :
				return it
		raise KeyError
	
	def find_fname( self, fname ) :
		fname = os.path.basename( fname ) # incase...
		for it in self.items :
			if it.fname == fname :
				return it
		raise KeyError

	# Happens when u delete a repaly from replay view.
	def remove( self, fname ) :
		it = self.find( fname )
		self.items.remove( it )

	# rename it.fname
	def rename( self, src, dest ) :
		it = self.find( src ) # find does basename for me.
		dest = os.path.basename( dest )
		it.fname = dest

	# scan a folder and return the replays as ReplayItem.
	def scan_path( self, path ) :
		fs = []
		for f in os.listdir( path ) :
			if not os.path.isfile( os.path.join( path, f ) ) :
				continue

			# must be a kwreplay file.
			if not f.lower().endswith( ".kwreplay" ) :
				continue

			fs.append( f )

		self.items = []
		for f in fs :
			i = ReplayItem()
			i.fname = f
			full_name = os.path.join( path, f )
			i.kwr = KWReplay( fname=full_name )
			self.append( i )

		self.touchup_ips()

	# for privacy reasons I don't want IP to show up directly on screen.
	# hash 'em.
	def touchup_ips( self ) :
		for item in self.items :
			kwr = item.kwr
			for player in kwr.players :
				if not player.is_ai : # is human
					player.ip = self.encrypt( player.ip )
	
	def encrypt( self, ip ) :
		m = hashlib.md5()
		m.update( ip.encode() )
		ip = m.hexdigest()
		#print( ip )
		return ip



class MapZip() :
	def __init__( self, fname ) :
		self.fname = fname
		if not os.path.isfile( fname ) :
			self.zipf = None
			self.namelist = []
		else :
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

	def draw_102( self, img ) :
		bmp = wx.Bitmap( img )
		dc = wx.MemoryDC( bitmap=bmp )

		# Set text props
		dc.SetTextForeground( wx.Colour( 255, 0, 255 ) )
		font = wx.Font( 40, wx.FONTFAMILY_SWISS,
			wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD )
		dc.SetFont( font )
		txt = "1.02+"

		(tw, th) = dc.GetTextExtent( txt )
		# but our text is 45 deg rotated.
		# we need to compute 45deg rotation!
		# oh, I was being too smart. don't need to these.
		#(tw, th) = ( tw/1.414, tw/1.424 + th/1.414 )

		# draw text, centered.
		(w, h) = dc.GetSize()
		dc.DrawRotatedText( txt, int((w-tw)/2), int((h+th)/2), 45 )
		#dc.DrawText( txt, int((w-tw)/2), int((h-th)/2) )

		img = bmp.ConvertToImage()
		del dc
		return img

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

			# if 1.02+, draw 1.02+ on the image
			if fname.find( "1.02+" ) >= 0 :
				img = self.draw_102( img )

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
	def __init__( self, parent, frame=None ) :
		super().__init__( parent, size=(600,200),
				style=wx.LC_REPORT|wx.LC_SINGLE_SEL )

		# parent frame to invoke event processing from upper level
		self.frame = frame
		self.kwr = None # remember the related replay.

		self.InsertColumn( 0, 'Team' )
		self.InsertColumn( 1, 'Name' )
		self.InsertColumn( 2, 'Faction' )
		self.InsertColumn( 3, 'Color' )
		self.SetColumnWidth( 1, 400 )
		#self.SetMinSize( (600, 200) )

		self.event_bindings()
	
	def populate( self, kwr ) :
		self.kwr = kwr # remember the replated replay
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

	# find replays involving a player, by context menu.
	def find_player( self, event ) :
		# retrieve name then pass them to frame to do the
		# rest of the job. ('cos player list knows not much)
		if self.GetSelectedItemCount() == 0 :
			return
		pos = self.GetFocusedItem()
		name = self.GetItem( pos, 1 ).GetText()

		# from the replay, find the player to retrieve uid (=ip)
		uid = None
		for player in self.kwr.players :
			if player.name == name :
				uid = player.ip
				break

		if not uid :
			msg = "Searching replays with AI is not supported!"
			wx.MessageBox( msg, "Error", wx.OK|wx.ICON_ERROR )
			return

		self.frame.find_player( name, uid ) # the frame will do the rest.

	# create context menu
	def on_item_righ_click( self, event ) :
		# right clickable on empty space. prevent that.
		if self.GetSelectedItemCount() == 0 :
			return

		menu = wx.Menu()
		item = wx.MenuItem( menu, wx.ID_ANY, "Find replays involving this player" )
		menu.Bind( wx.EVT_MENU, self.find_player, id=item.GetId() )
		menu.Append( item )
		self.PopupMenu( menu, event.GetPoint() )
		menu.Destroy() # prevent memory leak
	
	def event_bindings( self ) :
		self.Bind( wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_item_righ_click )
	
# I guess I don't have to inherit this,
# Python's dynamicness can handle this alright...
# having just one extra var of replay_item...
# Actually, this is done with SetItemData!!!
#class ReplayListItem( wx.ListItem ) :
#	def __init__( self ) :
#		super().__init( self )
#		self.replay_item = None

class ReplayList( wx.ListCtrl ) :
	def __init__( self, parent, frame, args ) :
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

		self.event_bindings()

		self.args = args
		self.frame = frame
		self.replay_items = None # This is shared with frame, beware!
		self.path = None
		self.replay_items = ReplayItems()
	
	def event_bindings( self ) :
		self.Bind( wx.EVT_LIST_ITEM_SELECTED, self.on_Click )
		self.Bind( wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_RightClick )
		self.Bind( wx.EVT_LIST_END_LABEL_EDIT, self.on_end_label_edit )
		self.Bind( wx.EVT_LIST_BEGIN_LABEL_EDIT, self.on_begin_label_edit )
		self.Bind( wx.EVT_LIST_COL_CLICK, self.on_col_click )

		# on key down doesn't work, for enter keys. :( :(
		#self.Bind( wx.EVT_LIST_KEY_DOWN, self.on_key_down )
	
	def set_path( self, path ) :
		self.path = path
		self.replay_items.scan_path( path )
		self.populate( self.replay_items )
		self.names = None # scratch memory for replay renaming presets (for context menu)
		self.ctx_old_name = "" # lets have a space for the old replay name too.
			# this one is for remembering click/right clicked ones only.
			# i.e, context menus.
		self.custom_old_name = ""
			# this one, is for remembering the old fname for custom renames.

	# reps: repaly_items
	def populate( self, reps, filter=None ) :
		self.replay_items = reps

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
			item = wx.ListItem()
			pos = self.InsertItem( index, fname ) # replay name
			self.SetItem( pos, 1, kwr.map_name ) # replay name
			self.SetItem( pos, 2, kwr.desc ) # desc
			self.SetItem( pos, 3, time ) # time
			self.SetItem( pos, 4, date ) # date
			self.SetItemData( pos, rep.id ) # associate replay

	# Modify the description of the replay which is currently selected.
	def modify_desc( self, desc ) :
		if self.GetSelectedItemCount() == 0 :
			# pressed modify! button without selecting anything.
			return

		# I think I could use self.ctx_old_name but...
		pos = self.GetFocusedItem()
		assert pos >= 0 # GetSelectedItemCount will assure it, but to be sure
		id = self.GetItemData( pos )

		rep = self.replay_items.find( id=id )
		fname = os.path.join( self.path, rep.fname )

		# so, old_name should be quite valid by now.
		kwr = KWReplay()
		kwr.modify_desc_inplace( fname, desc )

		# update it in the interface.
		self.SetItem( pos, 2, desc ) # desc
		kwr = KWReplay( fname ) # reload it.
		rep.kwr = kwr

	# determine if filter hit -> show in rep_list.
	def filter_hit( self, filter, kwr, fname ) :
		if not filter :
			# either filter == None or empty string!
			return True

		# lower case everything
		fname = fname.lower()
		map_name = kwr.map_name.lower()
		words = filter.lower().split()
		player_props = []
		desc = kwr.desc.lower()
		for player in kwr.players :
			player_props.append( player.name.lower() )
			player_props.append( player.ip )

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

			# matches player name/ip
			# Don't use word in player_props, it will not allow
			# substring match!
			for prop in player_props :
				if word in prop :
					return True

		return False
	
	def get_related_replay( self, pos ) :
		rep_id = self.GetItemData( pos )
		rep_item = self.replay_items.find( id=rep_id )
		return rep_item

	def key_func( self, rep_id1, rep_id2 ) :
		col = self.last_clicked_col
		asc = self.ascending

		# Since API's sorting function will sort by what I have
		# SetItemData'ed, rep1 and rep2 are my replay items.
		rep1 = self.replay_items.find( id=rep_id1 )
		rep2 = self.replay_items.find( id=rep_id2 )
		#print( rep1.fname )
		#print( rep2.fname )

		if col == 0 :
			# name
			data1 = rep1.fname
			data2 = rep2.fname
		elif col == 1 :
			data1 = rep1.kwr.map_name
			data2 = rep2.kwr.map_name
		elif col == 2 :
			data1 = rep1.kwr.desc
			data2 = rep2.kwr.desc
		elif col == 3 :
			# time of the day...
			# I'll just use timestamp, who cares?
			data1 = rep1.kwr.timestamp
			data2 = rep2.kwr.timestamp
		elif col == 4 :
			# date
			data1 = rep1.kwr.timestamp
			data2 = rep2.kwr.timestamp
		else :
			assert 0

		if data1 == data2 :
			result = 0
		elif data1 < data2 :
			result = -1
		else :
			result = 1

		if not asc :
			result *= -1

		return result
	
	def sort( self, col, asc ) :
		self.SortItems( self.key_func )

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

	def context_menu_rename( self, event ) :
		if not self.ctx_old_name :
			# pressed F2 without selecting any item!
			return
		item = self.GetFocusedItem()
		self.EditLabel( item )
	
	# Delete this replay?
	def context_menu_delete( self, event ) :
		cnt = self.GetSelectedItemCount()
		if cnt == 0 :
			return

		pos = self.GetNextSelected( -1 ) # get first selected index
		rep_name = self.GetItem( pos, 0 ).GetText()

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

		for pos in reversed( list( selected( self ) ) ) :
			rep_name = self.GetItem( pos, 0 ).GetText()
			fname = os.path.join( self.path, rep_name )

			self.DeleteItem( pos ) # delete from list
			self.replay_items.remove( rep_name ) # delete from mem
			os.remove( fname ) # delete the file
			self.ctx_old_name = None

	def open_containing_folder( self, event ) :
		# not relying wxPython!
		cmd = 'explorer /select,"%s"' % (self.ctx_old_name)
		#print( cmd )
		subprocess.Popen( cmd )
	
	# Generate the context menu when rep_list is right clicked.
	def on_RightClick( self, event ) :
		cnt = self.GetSelectedItemCount()
		pos = event.GetIndex()
		if pos < 0 :
			return

		# get the replay file name
		# handled by "select" event: EVT_LIST_ITEM_SELECTED
		# ... I thought so but in fact, I can right click and rename multiple times without
		# generating EVT_LIST_ITEM_SELECTED.
		# Do it here again!
		rep_name = self.GetItem( pos, 0 ).GetText()
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
			menu.Bind( wx.EVT_MENU, self.context_menu_presetClicked, id=item.GetId() )
			menu.Append( item )

		# custom rename menu
		if cnt == 1 :
			item = wx.MenuItem( menu, -1, "&Rename (F2)" )
			menu.Bind( wx.EVT_MENU, self.context_menu_rename, id=item.GetId() )
			menu.Append( item )

		# delete replay menu
		item = wx.MenuItem( menu, -1, "&Delete (Del)" )
		menu.Bind( wx.EVT_MENU, self.context_menu_delete, id=item.GetId() )
		menu.Append( item )

		# open contaning folder
		if cnt == 1 :
			item = wx.MenuItem( menu, -1, "&Open containing folder" )
			menu.Bind( wx.EVT_MENU, self.open_containing_folder, id=item.GetId() )
			menu.Append( item )

			item = wx.MenuItem( menu, -1, "&Play (Enter)" )
			menu.Bind( wx.EVT_MENU, self.play, id=item.GetId() )
			menu.Append( item )
		
		self.PopupMenu( menu, event.GetPoint() ) # popup the context menu.
		menu.Destroy() # prevents memory leaks haha
	
	def play( self, event ) :
		# Play this replay
		if self.GetSelectedItemCount() == 0 :
			return
		if self.GetSelectedItemCount() > 1 :
			# probably pressed Enter key or something
			msg = "Please select only one replay to play!"
			wx.MessageBox( msg, "Error", wx.OK|wx.ICON_ERROR )
			return

		pos = self.GetFocusedItem()
		rep_name = self.GetItem( pos, 0 ).GetText()
		fname = os.path.join( self.path, rep_name )
		os.startfile( fname ) # launch default app with file

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
		self.SetItem( pos, 0, rep_name ) # replay name
		# rename in the replay_items
		self.replay_items.rename( old_name, fname )

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

	def context_menu_presetClicked( self, event ) :
		assert self.names
		cnt = self.GetSelectedItemCount()
		index = event.GetId() # menu index

		if cnt == 1 :
			pos = self.GetFocusedItem()
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
		for index in selected( self ) :
			# old full name
			it = self.get_related_replay( index )
			old_name = it.fname
			old_name = os.path.join( self.path, old_name )

			rep_name = Watcher.calc_name( it.kwr, add_username=au, add_faction=af,
					add_vs_info=av,
					custom_date_format=self.args.custom_date_format )

			self.rename_with_stem( index, old_name, rep_name )


	def on_Click( self, event ) :
		pos = event.GetIndex()
		if pos < 0 :
			return

		# get the selected item and fill desc_text for editing.
		txt = self.GetItem( pos, 2 ).GetText()
		self.frame.desc_text.SetValue( txt )

		# get related replay.
		it = self.get_related_replay( pos )

		# remember the old name (for other renaming routines)
		self.ctx_old_name = os.path.join( self.path, it.fname )

		# fill faction info
		self.frame.player_list.populate( it.kwr )

		# load map preview
		self.frame.map_view.show( it.kwr )
	
	def on_end_label_edit( self, event ) :
		event.Veto() # undos all edits from the user, for now.

		#pos = self.GetFocusedItem()
		#if pos < 0 :
		#	return

		#if pos != event.GetIndex() :
		#	# User invoked renaming but clicked on another replay
		#	# In this case, silently quit edit.
		#	return

		pos = event.GetIndex() # maybe this is a more correct
		old_stem = self.GetItem( pos, 0 ).GetText()
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

	def on_begin_label_edit( self, event ) :
		pos = event.GetIndex() # maybe this is a more correct
		stem = self.GetItem( pos, 0 ).GetText()
		self.custom_old_name = os.path.join( self.path, stem )
		# remember the old name from custom renaming
	


class ReplayViewer( wx.Frame ) :
	def __init__( self, parent, args ) :
		super().__init__( parent, title='Replay Info Viewer', size=(1024,800) )
		self.args = args
		path = os.path.dirname( args.last_replay )

		self.MAPS_ZIP = 'maps.zip' # the name of the zip file that has map previews
		self.do_layout()
		self.event_bindings()
		self.create_accel_tab()
		self.set_icon()

		self.rep_list.set_path( path )

		# don't need DB. we just set the image name right.
		#self.map_db = self.load_map_db( 'MapDB.txt' )

	# Obsolete but, a working code. Keeping it in case I need it in future.
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
			path = os.path.dirname( diag.GetPath() )
			self.rep_list.set_path( path )

		diag.Destroy()

	# handles the request from PlayerList class and
	# tell filter object to find name and uid. (=ip)
	def find_player( self, name, uid ) :
		fil = name + " " + uid
		self.filter_text.SetValue( fil )
		self.rep_list.populate( self.rep_list.replay_items, filter=fil )
		
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

		self.player_list = PlayerList( panel, frame=self )
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

		self.rep_list = ReplayList( bottom_panel, self, self.args )

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

		self.Bind( wx.EVT_MENU, self.rep_list.context_menu_rename, id=self.id_rename )
		self.Bind( wx.EVT_MENU, self.rep_list.context_menu_delete, id=self.id_del )

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
		self.filter_text.SetValue( "" ) # removes filter.
		self.rep_list.set_path( self.rep_list.path )

	# removing filter is the same as refresh_path but doesn't rescan path's files.
	def on_nofilter_btnClick( self, event ) :
		self.filter_text.SetValue( "" ) # removes filter.
		self.rep_list.populate( self.rep_list.replay_items )
	
	def on_opendir_btnClick( self, event ) :
		self.change_dir()
	

	def on_modify_btnClick( self, event ) :
		desc = self.desc_text.GetValue()
		self.rep_list.modify_desc( desc )
	
	def on_filter_applyClick( self, event ) :
		fil = self.filter_text.GetValue()
		self.rep_list.populate( self.rep_list.replay_items, filter=fil )

	def event_bindings( self ) :
		self.refresh_btn.Bind( wx.EVT_BUTTON, self.on_refresh_btnClick )

		self.modify_btn.Bind( wx.EVT_BUTTON, self.on_modify_btnClick )
		self.desc_text.Bind( wx.EVT_TEXT_ENTER, self.on_modify_btnClick )

		self.opendir_btn.Bind( wx.EVT_BUTTON, self.on_opendir_btnClick )

		self.apply_btn.Bind( wx.EVT_BUTTON, self.on_filter_applyClick )
		self.nofilter_btn.Bind( wx.EVT_BUTTON, self.on_nofilter_btnClick )
		self.filter_text.Bind( wx.EVT_TEXT_ENTER, self.on_filter_applyClick )



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

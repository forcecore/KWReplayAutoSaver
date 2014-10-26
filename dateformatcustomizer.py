#!/usr/bin/python3
# -*- coding: utf8 -*-

from args import Args
from watcher import Watcher
import datetime
import wx
import wx.adv

class DateFormatCustomizer( wx.Dialog ) :
	def __init__( self, parent, args ) :
		super().__init__( parent, title='Customize DateTime Format' )
		self.do_layout()
		self.event_binding()
		self.Center() # show the dialog on the center of the screen
		self.text_ctrl_format.SetFocus() # set focus on the text edit.

		# Set default text for the text control.
		self.text_ctrl_format.SetValue( args.custom_date_format )

		# show preview!
	
	def on_preview( self, event ) :
		txt = self.check_format()
		if txt :
			self.text_ctrl_preview.SetValue( txt )

	# returns None on error.
	# returns a formatted string of time now on success.
	def check_format( self ) :
		fmt = self.text_ctrl_format.GetValue()
		t = datetime.datetime.now()
		try :
			txt = t.strftime( fmt )
		except ValueError :
			wx.MessageBox( "Invalid date time format!", "Error", style=wx.ICON_ERROR )
			return None

		if txt != Watcher.sanitize_name( txt ) :
			msg = "File name must not contain the following:\n"
			msg += "<>:\"/\\|?*"
			wx.MessageBox( msg, "Error", style=wx.ICON_ERROR )
			return None
	
		return txt

	def on_apply( self, event ) :
		txt = self.check_format()
		if txt :
			# Proceed to OnClose, only when format is fine.
			event.Skip()

	def event_binding( self ) :
		self.button_apply.Bind( wx.EVT_BUTTON, self.on_apply )

		# preview button/enter key event
		self.text_ctrl_format.Bind( wx.EVT_TEXT_ENTER, self.on_preview )
		self.button_preview.Bind( wx.EVT_BUTTON, self.on_preview )
		self.button_default.Bind( wx.EVT_BUTTON, self.on_default )
	
	def on_default( self, event ) :
		self.text_ctrl_format.SetValue( "[%Y-%m-%dT%H%M]" )
	
	def do_layout( self ) :
		hyperlink_format = wx.adv.HyperlinkCtrl(self, wx.ID_ANY,
				"Click here for format help", "https://docs.python.org/3.4/library/time.html#time.strftime")
		label_recommend = wx.StaticText(self, wx.ID_ANY,
				"Be sure to include all year, date and time of the day to ensure uniqueness"
				" of the replay file name!\n"
			)

		# Buttons
		self.button_apply = wx.Button( self, id=wx.ID_OK, label="Apply" )
		self.button_cancel = wx.Button( self, id=wx.ID_CANCEL, label="Cancel" )

		sizer_buttons = wx.BoxSizer( wx.HORIZONTAL )
		sizer_buttons.Add( self.button_apply )
		sizer_buttons.Add( self.button_cancel, flag=wx.LEFT, border=5 )

		# text ctrl
		panel1 = wx.Panel( self )
		self.text_ctrl_format = wx.TextCtrl( panel1, size=(200,-1), pos=(105,2), style=wx.TE_PROCESS_ENTER )
		self.button_preview = wx.Button( panel1, label="Preview", pos=(310,0) )
		self.button_default = wx.Button( panel1, label="Revert to Default", pos=(400,0) )
		label_format = wx.StaticText( panel1, label="Date Time Format:", pos=(0,4) )

		# preview text ctrl
		panel2 = wx.Panel( self )
		self.text_ctrl_preview = wx.TextCtrl( panel2, size=(200,-1), pos=(105,2), style=wx.TE_READONLY )
		label_preview = wx.StaticText( panel2, label="Preview:", pos=(0,4) )

		# Now add to VertSizer.
		VertSizer = wx.BoxSizer(wx.VERTICAL)
		VertSizer.Add( hyperlink_format, flag=wx.TOP|wx.LEFT|wx.RIGHT, border=10 )
		VertSizer.Add( label_recommend, flag=wx.LEFT|wx.RIGHT, border=10 )
		VertSizer.Add( panel1, flag=wx.LEFT|wx.RIGHT, border=10 )
		VertSizer.Add( panel2, flag=wx.LEFT|wx.RIGHT, border=10 )
		VertSizer.Add( sizer_buttons,  flag=wx.ALIGN_CENTER_HORIZONTAL|wx.TOP|wx.BOTTOM, border=10 )

		self.SetSizer(VertSizer)
		VertSizer.Fit(self)
		self.Layout()



if __name__ == "__main__" :
	app = wx.App()
	#wx.InitAllImageHandlers()

	# debug settings
	CONFIGF = 'config.ini'
	args = Args( CONFIGF )

	diag = DateFormatCustomizer( None, args )
	result = diag.ShowModal()
	diag.Destroy()

	app.MainLoop()

#!/usr/bin/python3
import wx

class ReplayViewer( wx.Frame ) :
	def __init__( self, parent ) :
		super().__init__( parent, title='Replay Info Viewer' )
		self.do_layout()
	
	def do_layout( self ) :
		box1 = wx.BoxSizer(wx.VERTICAL)
		box2 = wx.BoxSizer(wx.VERTICAL)

		panel2 = wx.Panel( self, -1, style=wx.SUNKEN_BORDER )
		panel3 = wx.Panel( self, -1, style=wx.SUNKEN_BORDER )

		# player list
		self.list_ctrl = wx.ListCtrl( self, size=(-1,200), style=wx.LC_REPORT )
		self.list_ctrl.InsertColumn( 0, 'Team' )
		self.list_ctrl.InsertColumn( 1, 'Name' )
		self.list_ctrl.InsertColumn( 2, 'Faction' )
		self.list_ctrl.InsertColumn( 3, 'Color' )

		panel2.SetBackgroundColour("GREEN")
		panel3.SetBackgroundColour("BLUE")

		box1.Add( self.list_ctrl, 1, wx.EXPAND )
		box1.Add( box2, 2, wx.EXPAND )
		box2.Add(panel2, 1, wx.EXPAND)
		box2.Add(panel3, 2, wx.EXPAND)

		self.SetAutoLayout(True)
		self.SetSizer(box1)
		self.Layout()



def main() :
	app = wx.App()
	frame = ReplayViewer( None )
	frame.Show( True )
	app.MainLoop()

if __name__ == "__main__" :
	main()

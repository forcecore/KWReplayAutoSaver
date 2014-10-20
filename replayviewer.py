#!/usr/bin/python3
import wx

class ReplayViewer( wx.Frame ) :
	def __init__( self, parent ) :
		super().__init__( parent, title='Replay Info Viewer' )
		self.do_layout()
	
	def do_layout( self ) :
		box1 = wx.BoxSizer(wx.VERTICAL)
		box2 = wx.BoxSizer(wx.VERTICAL)

		panel1 = wx.Panel(self,-1, style=wx.SUNKEN_BORDER)
		panel2 = wx.Panel(self,-1, style=wx.SUNKEN_BORDER)
		panel3 = wx.Panel(self,-1, style=wx.SUNKEN_BORDER)

		panel1.SetBackgroundColour("RED")
		panel2.SetBackgroundColour("GREEN")
		panel3.SetBackgroundColour("BLUE")

		box1.Add(panel1, 1, wx.EXPAND)
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

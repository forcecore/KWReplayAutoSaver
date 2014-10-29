#!/usr/bin/python3
import wx
import urllib, urllib.request
import os
import threading

# Got it from here!:
# http://wiki.wxpython.org/DownloadWidget

# urllib.request makes dlg cancel button unclickable.
# should resort to multi-threading.

def worker( url, dest, dlg ) :
	fURL = urllib.request.urlopen( url )
	header = fURL.info()
	size = None
	max = 100
	outFile = open( dest, 'wb' )
	keepGoing = True

	if "Content-Length" in header :
		size = int( header["Content-Length"] )
		kBytes = int( size/1024 )
		downloadBytes = int( size/max )
		count = 0
		while keepGoing:
			count += 1
			if count >= max:
				count  = 99
			(keepGoing, skip) = dlg.Update( count,
				"Downloaded "+str(count*downloadBytes/1024) +
				" of " + str( kBytes ) + "KB" )
			b = fURL.read(downloadBytes)
			if b:
				outFile.write(b)
			else:
				break
	else:
		while keepGoing :
			(keepGoing, skip) = dlg.UpdatePulse()
			b = fURL.read( 1024*8 )
			if b:
				outFile.write( b )
			else:
				break
	outFile.close()


def download(url, dest, msg):
	dlg = wx.ProgressDialog("Download Progress", msg,
		style = wx.PD_CAN_ABORT | wx.PD_APP_MODAL |
			wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME
		)
	dlg.Update( 0, msg )

	#t = threading.Thread( target=worker, args=(url, dest, dlg) )
	#t.start()
	keepGoing = worker( url, dest, dlg )

	dlg.Update( 99, "Downloaded " + str(os.path.getsize(dest)/1024)+"KB" )
	dlg.Destroy()
	return keepGoing

if __name__ == "__main__":
	app = wx.App()
	download( 'http://sometest.url', 'out.jpg' )

#!/usr/bin/python3
import sys
import os
import subprocess

class Gnuplot() :
	def __init__( self ) :
		self.gnuplot_path = Gnuplot.find_gnuplot()
		#self.linestyle_id = 0
		self.xss = []
		self.yss = []
		self.labels = []
		self.style = "lines"
	
	def open( self ) :
		assert self.gnuplot_path, "gnuplot not found"
		self.f = subprocess.Popen( [self.gnuplot_path, "-persistent"], stdin=subprocess.PIPE )
	
	def set_style( self, style ) :
		self.style = style
	
	def xlabel( self, s ) :
		self.write( 'set xlabel "%s"\n' % s )

	def ylabel( self, s ) :
		self.write( 'set ylabel "%s"\n' % s )
	
	def legend( self, labels ) :
		self.labels = labels
	
	def plot( self, xs, ys ) :
		self.xss.append( xs )
		self.yss.append( ys )
	
	def show( self ) :
		# specify line styles
		#self.linestyle_id += 1
		#self.write( 'set style line %d \n' % self.data_id )

		self.write( 'set key outside bottom center horizontal\n' )

		self.write( 'plot \\\n' )
		assert len( self.xss ) == len( self.yss )
		data_str = []
		for i in range( len( self.xss ) ) :
			data_str.append( '"-" using 1:2 with %s title "%s"' % ( self.style, self.labels[i] ) )
		data_str = ", ".join( data_str )
		self.write( data_str )
		self.write( "\n" )

		for xs, ys in zip( self.xss, self.yss ) :
			for x, y in zip( xs, ys ) :
				self.write( '%f %f\n' % (x, y) )
			self.write( 'e\n' )

	def close( self ) :
		del self.f
	
	def write( self, cmd ) :
		self.f.stdin.write( bytes( cmd, "UTF-8" ) )
		self.f.stdin.flush()
	
	def find_gnuplot() :
		is_win32 = (sys.platform == 'win32')
		if not is_win32:
			gnuplot = "/usr/bin/gnuplot"
			if os.path.isfile( gnuplot ) :
				return gnuplot
		else:
			# example for windows
			import winreg
			key = winreg.OpenKey( winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\wgnuplot.exe" )
			gnuplot = winreg.QueryValue( key, None )
			if not os.path.isfile( gnuplot ) :
				return None
			else :
				# I want pgnuplot.
				path = os.path.dirname( gnuplot )
				gnuplot = os.path.join( path, "gnuplot.exe" ) # piped gnuplot!
				return gnuplot

		return None

if __name__ == "__main__" :
	plt = Gnuplot()
	print( "found gnuplot:", plt.gnuplot_path )
	plt.open()
	plt.write('set xrange [0:10]; set yrange [-2:2]\n')
	plt.write('plot sin(x)\n')
	#plt.close()

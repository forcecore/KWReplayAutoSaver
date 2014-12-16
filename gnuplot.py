#!/usr/bin/python3
import sys
import os
import subprocess
import tempfile
from multiprocessing import Process



class Gnuplot() :
	temp_files = [] # for deletion, if anyone cares.

	def __init__( self ) :
		self.gnuplot_path = Gnuplot.find_gnuplot()
		#self.linestyle_id = 0
		self.xss = []
		self.yss = []
		self.labels = []
		self.style = "lines"
	
	def open( self ) :
		assert self.gnuplot_path, "gnuplot not found"
		self.f = tempfile.NamedTemporaryFile( delete=False )
		#self.f = subprocess.Popen( [self.gnuplot_path, "-p"], shell=False, stdin=subprocess.PIPE )
		self.write( 'set term wxt\n' )
	
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
		#self.write( "exit\n" )
		#self.f.stdin.close()
		#del self.f
		#p = Process( target=gnuplot_forked, args=( self.gnuplot_path, self.f.name ) )
		#p.start()
		self.f.close()
		subprocess.Popen( [self.gnuplot_path, self.f.name], shell=False )
		Gnuplot.temp_files.append( self.f.name )
		# launch gnuplot will get rid of the tmp file afterwards.
		# Tempfile, on win7, is here:
		# C:\Users\USERID\AppData\Local\Temp
	
	def write( self, cmd ) :
		#self.f.stdin.write( bytes( cmd, "UTF-8" ) )
		#self.f.stdin.flush()
		self.f.write( bytes( cmd, "UTF-8" ) )
	
	def find_gnuplot() :
		is_win32 = (sys.platform == 'win32')
		if not is_win32:
			gnuplot = "/usr/bin/gnuplot"
			if os.path.isfile( gnuplot ) :
				return gnuplot
		else:
			# example for windows
			import winreg
			try :
				key = winreg.OpenKey( winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\wgnuplot.exe" )
				gnuplot = winreg.QueryValue( key, None )
				if not os.path.isfile( gnuplot ) :
					return None
				else :
					# I want to try pgnuplot, gnuplot ...
					# until it is neat.
					path = os.path.dirname( gnuplot )
					gnuplot = os.path.join( path, "wgnuplot.exe" ) # piped gnuplot!
					return gnuplot
			except FileNotFoundError :
				return None

		return None



def debug_main() :
	plt = Gnuplot()
	print( "found gnuplot:", plt.gnuplot_path )
	plt.open()
	plt.write('set xrange [0:10]; set yrange [-2:2]\n')
	plt.write('plot sin(x)\n')
	plt.close()

	# then delete Gnuplot.temp_files...



def gnuplot_forked( gnuplot, fname ) :
	subprocess.call( [gnuplot, fname] )
	os.unlink( fname )



if __name__ == "__main__" :
	debug_main()

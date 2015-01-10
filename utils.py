#!/usr/bin/python3

import struct # bin file enc/dec
import hashlib
import datetime
import time
import subprocess
import os
import sys



def open_in_default_app( fname ) :
	if sys.platform.startswith( 'darwin' ) :
		subprocess.call( ('open', fname ) )
	elif os.name == 'nt' :
		os.startfile( fname )
	elif os.name == 'posix' :
		subprocess.call( ('xdg-open', fname) )



def encrypt( ip ) :
	m = hashlib.md5()
	m.update( ip.encode() )
	ip = m.hexdigest()
	#print( ip )
	return ip



def read_cstr( f, length ) :
	data = f.read( length )
	#s = struct.unpack( "18s", data )
	data = data.decode( "utf-8" )
	return data



def read_tb_str( f, length=-1 ) :
	buf = ""
	while True :
		l = f.read( 2 )
		l = struct.unpack( 'H', l )[ 0 ]
		if length == -1 and l == 0 :
			break
		buf += chr( l )

		if length != -1 and len( buf ) == length :
			break

	#data = buf.decode( "utf-16" )
	return buf



def read_byte( f ) :
	data = f.read( 1 )
	data = struct.unpack( 'B', data )[0]
	return data



def read_float( f ) :
	data = f.read( 4 )
	data = struct.unpack( 'f', data )[0]
	return data



def read_uint32( f ) :
	tmp = f.read( 4 )
	i = struct.unpack( 'I', tmp )[ 0 ]
	return i



def time_code2str( tc ) :
	t = time.gmtime( tc )
	return time.strftime( "%H:%M:%S", t )


def byte2int( byte ) :
	return struct.unpack( 'B', byte )[0]



def uint42int( bys ) :
	return struct.unpack( 'I', bys )[ 0 ]



def uint42float( bys ) :
	return struct.unpack( 'f', bys )[ 0 ]



def print_bytes( bys, break16=True ) :
	if not bys :
		print( "None" )
		return

	i = 0
	for b in bys :
		print( "%02X " % b, end="" )
		i += 1
		if break16 :
			if i >= 16 :
				i = 0
				print()
	print()

#!/usr/bin/python3

f = open( '1.KWReplay', "rb" )
buf = f.read()
f.close()

for i in range( 200 ) :
	buf = buf[:-1]
	ofname = "bad_" + str(i) + ".KWReplay"
	f = open( ofname, "wb" )
	f.write( buf )
	f.close()

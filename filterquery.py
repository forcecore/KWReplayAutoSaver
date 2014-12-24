#!/usr/bin/python3
import string

# Including library makes program bloat.
# I'm not gonna do that.
# Lets support simpler version of this google like search:
# https://cloud.google.com/appengine/docs/python/search/query_strings
class FilterQuery :
	def __init__( self, qstring ) :
		self.tree = self.compile( qstring )



	def compile( self, qstring ) :
		tokens = self.tokenize( qstring )
		print( tokens )



	def tokenize( self, qstring ) :
		# There are 3 states.
		S_WS = 0 # last read was white space
		S_PR = 1 # last read was printable
		S_QO = 2 # quote opened.

		state = S_WS

		tokens = []
		token = ""

		def flush_token( token, tokens ) :
			if token :
				tokens.append( token )
			return ""

		# The below code is an FSM... Don't bother reading this code.
		#
		# I've manually coded this...
		#
		# 5 inputs possible for each state transition.
		# (, ), whitespace, ", printable that are not ()".
		for char in qstring :
			if state == S_WS :
				if char == "\"" :
					token = flush_token( token, tokens )
					state = S_QO
				elif char == "(" :
					token = flush_token( token, tokens )
					tokens.append( "(" )
				elif char == ")" :
					token = flush_token( token, tokens )
					tokens.append( ")" )
				elif char in string.whitespace :
					token = flush_token( token, tokens )
				else :
					token += char
					state = S_PR

			elif state == S_PR :
				if char == "\"" :
					token = flush_token( token, tokens )
					state = S_QO
				elif char == "(" :
					token = flush_token( token, tokens )
					tokens.append( "(" )
					state = S_WS
				elif char == ")" :
					token = flush_token( token, tokens )
					tokens.append( ")" )
					state = S_WS
				elif char in string.whitespace :
					token = flush_token( token, tokens )
					state = S_WS
				else :
					token += char

			elif state == S_QO :
				# closing quote!
				if char == "\"" :
					token = flush_token( token, tokens )
					state = S_WS
				else :
					token += char

			else :
				assert 0, "Invalid state in FSM"

		# put left over into token.
		token = flush_token( token, tokens )

		return tokens



def main() :
	fq = FilterQuery( "kyky AND noonal" )
	fq = FilterQuery( "(NOT kyky) AND noonal \"OR noonal\"" )



if __name__ == "__main__" :
	main()

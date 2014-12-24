#!/usr/bin/python3
import string

# Including library makes program bloat.
# I'm not gonna do that.
# Lets support simpler version of this google like search:
# https://cloud.google.com/appengine/docs/python/search/query_strings
class FilterQuery :
	def __init__( self, qstring ) :
		self.postfix = self.compile( qstring )
		if 0 :
			print( qstring )
			print( self.postfix )
			print()
	


	# see if the replay is a hit to query.
	def match( self, props ) :
		if len( self.postfix ) == 0 :
			# empty query.
			return True

		operand_stack = []

		U = set( props ) # the whole set

		for item in self.postfix :
			if item == "not" :
				operand = operand_stack.pop()
				operand = U - operand # new inverted set
				operand_stack.append( operand )
			elif item == "and" :
				op1 = operand_stack.pop()
				op2 = operand_stack.pop()
				operand = op1 & op2
				operand_stack.append( operand )
			elif item == "or" :
				op1 = operand_stack.pop()
				op2 = operand_stack.pop()
				operand = op1 | op2
				operand_stack.append( operand )
			else : # string
				if item.startswith( "\"" ) and item.endswith( "\"" ) :
					item = item[1:-1]
				hits = set()
				for prop in props :
					if prop.find( item ) >= 0 :
						hits.add( prop )
				operand_stack.append( hits )
				print( operand_stack )

		assert len( operand_stack ) >= 1

		# if you just search gdi nod, then they automatically imply OR.
		# So, if any of the operand in the stack has len > 0, it is a hit.
		for operand in operand_stack :
			if len( operand ) > 0 :
				return True
		return False



	def compile( self, qstring ) :
		tokens = self.tokenize( qstring )
		# smaller case conversion.
		for i, tok in enumerate( tokens ) :
			tokens[ i ] = tok.lower()
		postfix = self.to_postfix( tokens )
		return postfix



	# http://en.wikipedia.org/wiki/Shunting-yard_algorithm
	# infix -> postfix conversion.
	def to_postfix( self, tokens ) :
		result = []

		operators = [ "(", "and", "or", "not" ]

		operator_stack = []

		# op percedence: not or then and.
		for tok in tokens :
			#print( operator_stack )

			if tok == "(" :
				operator_stack.append( tok )
			elif tok == ")" :
				# Until the token at the top of the stack is a left parenthesis,
				# pop operators off the stack onto the output queue.
				while operator_stack[-1] != "(" :
					# there SHOULD be a ( in the stack already.
					# Otherwise, it is a syntax error.
					result.append( operator_stack.pop() )
				lpar = operator_stack.pop()
				assert lpar == "("
			elif not tok in operators : # operand
				result.append( tok )
			else :
				while len( operator_stack ) > 0 and \
						operators.index( operator_stack[-1] ) >= operators.index( tok ) :
					result.append( operator_stack.pop() )
				operator_stack.append( tok )

		# pop left-overs.
		while len( operator_stack ) > 0 :
			if operator_stack[-1] == "(" :
				print( "Unmatched parenthesis" )
				raise SyntaxError
			else :
				result.append( operator_stack.pop() )

		return result



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
					tokens[-1] = "\"" + tokens[-1] + "\""
					# surround the token with "" for discerning operator and string.
					# e.g.
					# we need to see if it was AND or "AND".
					# quoted and = and string.
					# not quoted and = operater and.
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
	fq = FilterQuery( "(NOT \"lilibet 'oh\")    AND noonal \"OR noonal\"" )
	fq = FilterQuery( "1 OR 1 AND 3" )
	fq = FilterQuery( "1 AND 1 OR 3" )
	fq = FilterQuery( "(1 OR 1) AND 3" )
	fq = FilterQuery( "1 OR (1 AND 3)" )
	fq = FilterQuery( "gdi and not nod" )
	fq = FilterQuery( "not gdi and nod" )
	fq = FilterQuery( "not gdi or nod" )
	fq = FilterQuery( "(not gdi) or nod" )
	fq = FilterQuery( "not (gdi or nod)" )



if __name__ == "__main__" :
	main()

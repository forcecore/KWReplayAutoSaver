#!/usr/bin/python3
# coding: utf8

###
### http://www.gamereplays.org/community/index.php?showtopic=706067&st=0&p=7863248&#entry7863248
### The decoding of the replays format is credited to R Schneider.
###

import chunks



CMDNAMES = {
	0x07: "Start building soviet structure",
	0x09: "Place down soviet structure",
}

UNITNAMES = {
	0xA01D437D: "S Crane",
	0xCF8D9F20: "S Reactor",
	0x80D4EA1E: "S Barracks",
	0xC45AAEAB: "S Ref",
	0xD50C222E: "S Factory",
	0x524BBD01: "S Super reactor",
	0xB7377639: "S Battle lab",
	0xD25BB962: "S Airfield",
	0xA82CF003: "S Wall",
	0x6E1ABB35: "S Naval yard",
	0xD20552E1: "S Iron curtain",
	0x856C9DD6: "S Vaccum imploder",
	0xFA1F6466: "S Tesla coil",
	0x4DF5F9C1: "S Sentry gun",
	0x1769BE29: "S Flak cannon",
}

UNITCOST = {
}

BO_COMMANDS = [ 0x09 ]



class RA3Chunk( chunks.Chunk ) :

	def is_bo_cmd( self, cmd ) :
		return cmd.cmd_id in BO_COMMANDS

	def is_known_cmd( self, cmd ) :
		return cmd.cmd_id in CMDNAMES

	def resolve_known( self, cmd ) :
		return CMDNAMES[ cmd.cmd_id ]

	# Decode decodable commands
	def decode_cmd( self, cmd ) :
		if cmd.cmd_id == 0x09 :
			cmd.decode_placedown_cmd( UNITNAMES, UNITCOST )
		return

		if cmd.cmd_id == 0x27 :
			cmd.decode_placedown_cmd( UNITNAMES, UNITCOST )
		elif cmd.cmd_id == 0x23 :
			cmd.decode_queue_cmd( UNITNAMES, AFLD_UNITS, UNITCOST )
		elif cmd.cmd_id == 0x1C :
			cmd.decode_skill_targetless( POWERNAMES, POWERCOST )
		elif cmd.cmd_id == 0x1D :
			cmd.decode_skill_xy( POWERNAMES, POWERCOST )
		elif cmd.cmd_id == 0x80 :
			cmd.decode_skill_2xy( POWERNAMES, POWERCOST )
		elif cmd.cmd_id == 0x21 :
			cmd.decode_upgrade_cmd( UPGRADENAMES, UPGRADECOST )
		elif cmd.cmd_id == 0x26 :
			cmd.decode_hold_cmd( UNITNAMES )
		elif cmd.cmd_id == 0x2A :
			cmd.decode_sell_cmd()
		elif cmd.cmd_id == 0x3C :
			cmd.decode_move_cmd()
		elif cmd.cmd_id == 0x70 :
			cmd.decode_formation_move_cmd()
		elif cmd.cmd_id == 0x7F :
			cmd.decode_powerdown_cmd()
		elif cmd.cmd_id == 0x84 :
			cmd.decode_reverse_move_cmd()
		elif cmd.cmd_id == 0x2D :
			cmd.decode_gg()

		# Fortunately, we don't have target skill, in the sidebar skills, in TW.
		#elif cmd.cmd_id == 0x?? :
		#	cmd.decode_skill_target( POWERNAMES, POWERCOST )

#!/usr/bin/python3
# coding: utf8

###
### http://www.gamereplays.org/community/index.php?showtopic=706067&st=0&p=7863248&#entry7863248
### The decoding of the replays format is credited to R Schneider.
###

import chunks
from kwchunks import UNITNAMES, UNITCOST, AFLD_UNITS, POWERNAMES, UPGRADENAMES, POWERCOST, UPGRADECOST



CMDNAMES = {
	0x1C: "Skill (targetless)",
	0x1D: "Skill (with 1 target pos)",
	0x21: "Upgrade",
	0x23: "Queue a unit production",
	0x25: "Start construction of a structure",
	0x26: "Hold",
	0x27: "Place down a structure",
	0x2A: "Sell",
#	0x2D: "GG",
	0x3C: "Move",
	0x70: "Formation move",
	0x7F: "toggle power down/up",
	0x80: "Skill (with 2 target pos)",
	0x84: "Reverse move",
	0xF5: "Select units",
	0xF8: "Deselect units",
}

BO_COMMANDS = [ 0x1C, 0x1D, 0x23, 0x27, 0x80, 0x21, 0x26, 0x2A ]



class TWChunk( chunks.Chunk ) :

	def is_bo_cmd( self, cmd ) :
		return cmd.cmd_id in BO_COMMANDS

	def is_known_cmd( self, cmd ) :
		return cmd.cmd_id in CMDNAMES

	def resolve_known( self, cmd ) :
		return CMDNAMES[ cmd.cmd_id ]

	# Decode decodable commands
	def decode_cmd( self, cmd ) :
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
		#elif cmd.cmd_id == 0xFF :
		#	cmd.decode_gg()

		# Fortunately, we don't have target skill, in the sidebar skills, in TW.
		#elif cmd.cmd_id == 0x?? :
		#	cmd.decode_skill_target( POWERNAMES, POWERCOST )

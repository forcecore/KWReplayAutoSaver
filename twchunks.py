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
	0x27: "Place down a structure",
	0x80: "Skill (with 2 target pos)",
}

BO_COMMANDS = [ 0x1C, 0x1D, 0x23, 0x27, 0x80, 0x21 ]



class TWChunk( chunks.Chunk ) :

	def is_bo_cmd( self, cmd ) :
		return cmd.cmd_id in BO_COMMANDS



	def has_bo( self ) :
		for cmd in self.commands :
			if self.is_bo_cmd( cmd ) :
				return True
		return False



	# Decode decodable commands
	def decode_cmd( self, cmd ) :
		if not self.is_bo_cmd( cmd ) :
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
		if cmd.cmd_id == 0x21 :
			cmd.decode_upgrade_cmd( UPGRADENAMES, UPGRADECOST )
		# Fortunately, we don't have target skill, in the sidebar skills, in TW.
		#elif cmd.cmd_id == 0x?? :
		#	cmd.decode_skill_target( POWERNAMES, POWERCOST )

		return

		if cmd.cmd_id == 0x2E :
			cmd.decode_hold_cmd( UNITNAMES )
		elif cmd.cmd_id == 0x34 :
			cmd.decode_sell_cmd()
		elif cmd.cmd_id == 0x7A :
			cmd.decode_formation_move_cmd()
		elif cmd.cmd_id == 0x46 :
			cmd.decode_move_cmd()
		elif cmd.cmd_id == 0x8E :
			cmd.decode_reverse_move_cmd()
		elif cmd.cmd_id == 0x89 :
			cmd.decode_powerdown_cmd()
		elif cmd.cmd_id == 0x91 :
			cmd.decode_gg()



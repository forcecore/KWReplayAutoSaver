#!/usr/bin/python3
# coding: utf8

###
### http://www.gamereplays.org/community/index.php?showtopic=706067&st=0&p=7863248&#entry7863248
### The decoding of the replays format is credited to R Schneider.
###

import chunks



CMDNAMES = {
	0x01: "Skill with target unit",
	0x05: "Queue unit production",
	0x06: "Hold",
	0x07: "Start building soviet structure",
	0x09: "Place down soviet structure",
	0x0A: "Sell",
	0x14: "Move",
	0x21: "Scroll",
	0x2C: "Formation move",
	0x2F: "Alt down/up (waypoint mode)",
	0x36: "Reverse move",
	0x4E: "Select \"science\"",
	0xF5: "Select units",
	0xF8: "Deselect units",
	0xFF: "Use skill",
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

	0x33026FA1: "S War bear",
	0x19AB11AF: "S Conscript",
	0x2C358C61: "S Flak trooper",
	0xA08AABD3: "S Combat engineer",
	0x3E11865D: "S Tesla trooper",
	0x174F874F: "S Natasha",
	0xF6DAC2A4: "S Ore collector",
	0xBB686AE1: "S Sputnik",
	0xD741D327: "S Terror drone",
	0x60F0B4E9: "S Sickle",
	0x522BCB61: "S Bullfrog",
	0x94B3590B: "S Hammer tank",
	0x821381DE: "S V4 RL",
	0x9E45383C: "S Apocalypse",
	0xAF4C0DA5: "S MCV",
	0x40ACAD6D: "S Twinblade",
	0x7F54CED1: "S MiG",
	0xFFA811AE: "S Kirov",
	0x951764B9: "S Ore collector (NavYard)",
	0x92718B35: "S Sputnik (NavYard)",
	0xAFF62E78: "S Stringray",
	0xCCBD2C91: "S Bullfrog (NavYard)",
	0x8D0A384A: "S Akula",
	0xBCEF51B9: "S Dreadnaught",
	0x1545FAC2: "S MCV (NavYard)",
}

SCIENCENAMES = {
	0x9584D47B: "Grinder treads",
	0xDAB43816: "Toxic corrosion",
	0x02569A51: "Magnetic sat.",
	0x0507CBF7: "Mag. Sat. I",
	0xD775BE5A: "Mag. Sat. II",
	0x0AA8A772: "Mag. Sat. III",
	0x3A7E2F69: "Orbital I",
	0x084AAD6A: "Orbital II",
	0x0B8D24B4: "Orbital III",
	0xEBCC84BF: "Mass production",
	0x6D04D022: "Cash bounty",
	0x5CD95964: "Desolator airstrike I",
	0x473D95E9: "Desolator airstrike II",
	0x48DF61AA: "Desolator airstrike III",
	0x33354AD3: "Magnetic singularity",
}

UNITCOST = {
}

POWERNAMES = {
	0xDE6EBD00: "Cash bounty",
	0xC3FC9800: "Desolator airstrike I",
	0x3D3EF700: "Desolator airstrike II",
	0xD8778B00: "Desolator airstrike III",
	0xDF8D7100: "Orbital I",
	0xAEA53D00: "Orbital II",
	0xB53BE900: "Orbital III",
	0x69B1E200: "Mag. Sat. I",
	0x115EEE00: "Mag. Sat. II",
	0x8FA51900: "Mag. Sat. III",
	0x927E9C00: "Toxic corrosion",
	0x61360F00: "Iron curtain",
	0x2EB8F100: "Vaccum implosion",
	0x29BFB700: "Magnetic singularity",
}

POWERCOST = {
	0xDE6EBD00: 0,
	0xC3FC9800: 0,
	0xDF8D7100: 0,
	0x69B1E200: 0,
	0x927E9C00: 0,
	0x3D3EF700: 0,
	0xAEA53D00: 0,
	0x61360F00: 0,
	0x2EB8F100: 0,
	0x115EEE00: 0,
	0xB53BE900: 0,
	0xD8778B00: 0,
	0x29BFB700: 0,
	0x8FA51900: 0,
}

AFLD_UNITS = []

BO_COMMANDS = [ 0x05, 0x09, 0x0A, 0x4E, 0xFF, 0x01 ]



class RA3Chunk( chunks.Chunk ) :

	def is_bo_cmd( self, cmd ) :
		return cmd.cmd_id in BO_COMMANDS

	def is_known_cmd( self, cmd ) :
		return cmd.cmd_id in CMDNAMES

	def resolve_known( self, cmd ) :
		return CMDNAMES[ cmd.cmd_id ]

	# Decode decodable commands
	def decode_cmd( self, cmd ) :
		# hide some distracting commands
		if cmd.cmd_id == 0x21 :
			cmd.cmd_ty = chunks.Command.HIDDEN # lets forbid this from showing.

		if cmd.cmd_id == 0x09 :
			cmd.decode_placedown_cmd( UNITNAMES, UNITCOST )
		elif cmd.cmd_id == 0x05 :
			cmd.decode_ra3_queue_cmd( UNITNAMES, AFLD_UNITS, UNITCOST )
		elif cmd.cmd_id == 0x06 :
			cmd.decode_hold_cmd( UNITNAMES )
		elif cmd.cmd_id == 0x14 :
			cmd.decode_move_cmd()
		elif cmd.cmd_id == 0x0A :
			cmd.decode_sell_cmd()
		elif cmd.cmd_id == 0x2c :
			cmd.decode_formation_move_cmd()
		elif cmd.cmd_id == 0x36 :
			cmd.decode_reverse_move_cmd()
		elif cmd.cmd_id == 0x4E :
			cmd.decode_science_sel_cmd( SCIENCENAMES )
		elif cmd.cmd_id == 0xFF :
			cmd.decode_skill_xy( POWERNAMES, POWERCOST )
		elif cmd.cmd_id == 0x01 :
			# sometimes, GG
			cmd.decode_skill_target( POWERNAMES, POWERCOST )
		return

		if cmd.cmd_id == 0x1C :
			cmd.decode_skill_targetless( POWERNAMES, POWERCOST )
		elif cmd.cmd_id == 0x01 :
			cmd.decode_gg()
		elif cmd.cmd_id == 0x80 :
			cmd.decode_skill_2xy( POWERNAMES, POWERCOST )
		elif cmd.cmd_id == 0x21 :
			cmd.decode_upgrade_cmd( UPGRADENAMES, UPGRADECOST )

		# Fortunately, we don't have target skill, in the sidebar skills, in TW.
		#elif cmd.cmd_id == 0x?? :
		#	cmd.decode_skill_target( POWERNAMES, POWERCOST )

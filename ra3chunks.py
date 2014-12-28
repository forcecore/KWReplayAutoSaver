#!/usr/bin/python3
# coding: utf8

###
### http://www.gamereplays.org/community/index.php?showtopic=706067&st=0&p=7863248&#entry7863248
### The decoding of the replays format is credited to R Schneider.
###

import chunks



CMDNAMES = {
	0x00: "Deploy into a building (MCV/Core)",
	0x01: "Skill with target unit",
	0x03: "Upgrade",
	0x05: "Queue unit production",
	0x06: "Hold",
	0x07: "Start building structure",
	0x09: "Place down soviet structure",
	0x0A: "Sell",
	0x14: "Move",
	0x21: "Scroll",
	0x2C: "Formation move",
	0x2F: "Alt down/up (waypoint mode)",
	0x32: "Skill /w 2 target pos",
	0x36: "Reverse move",
	0x4E: "Select \"science\"",
	0xF5: "Select units",
	0xF8: "Deselect units",
	0xFE: "Skill targetless",
	0xFF: "Skill /w target pos",
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
	0x951764B9: "S Ore collector (NavYd)",
	0x92718B35: "S Sputnik (NavYd)",
	0xAFF62E78: "S Stringray",
	0xCCBD2C91: "S Bullfrog (NavYd)",
	0x8D0A384A: "S Akula",
	0xBCEF51B9: "S Dreadnaught",
	0x1545FAC2: "S MCV (NavYd)",

	0x89B86E3D: "A Power plant",
	0x509BD329: "A Barracks",
	0x8ECE261C: "A Ref",
	0x8209C058: "A Factory",
	0x7848F598: "A Naval yard",
	0x5B3008B7: "A Airfield",
	0xCA9257EB: "A Defense bureau",
	0x296799CF: "A Wall",
	0xEE3E07BD: "A Multigunner turret",
	0x69B62705: "A Spectrum tower",
	0xFD87E82A: "A Chronosphere",
	0x95D6E965: "A Proton collider",

	0xDDFC28DE: "A Dog",
	0x139CBC97: "A Peacekeeper",
	0x9C5D3BB8: "A Jav. Troop.",
	0x53E0EB12: "A Tanya",
	0x4AA5D515: "A Spy",
	0xE1E9179B: "A Engineer",
	0x2A196E71: "A Prospecter",
	0x4068B3D7: "A Riptide",
	0xBB06395A: "A IFV",
	0x07B91527: "A Guardian",
	0xD48ED838: "A Athena",
	0x52BFE9C5: "A Mirage",
	0x28DA574E: "A MCV",
	0xB74F8348: "A Vindicator",
	0x3C82B910: "A Appolo",
	0x509D5101: "A Cryocopter",
	0x83D5A86B: "A Century bomber",
	0x75288D70: "A Prospecter (NavYd)",
	0x8ACA3F75: "A Dolphin",
	0x1C331EB6: "A Riptide (NavYd)",
	0x2E211A99: "A Hydrofoil",
	0x5AE534FC: "A A. Destroyer",
	0x09705D80: "A A. Carrier",
	0x648D1440: "A MCV (NavYd)",

	0xF8C50039: "E Wall",
	0xC6B3F8AA: "E Generator core",
	0x57F07A3A: "E Dojo core",
	0xFF4A8B60: "E Ref core",
	0xA02E31D3: "E Mecha bay core",
	0xF0455D99: "E Docks core",
	0x78D3E32C: "E Mainframe core",
	0x1F496B6B: "E Defender core",
	0x2412FB82: "E Tower core",
	0x5FC93021: "E Nanoswarm core",
	0x5C1C0F0F: "E Psionic desolator core",

	0x12E7D7A4: "E Burst drone",
	0x0FB02C55: "E Imperial warrior",
	0x7D0549DD: "E Tank buster",
	0x20DBDFCC: "E Engineer",
	0xA768E216: "E Shinobi",
	0xD81C1012: "E Rocket angel",
	0x6586A5A0: "E Yuriko Omega",
	0x92CDE50F: "E Ore collector",
	0x1791E072: "E Sudden transport",
	0xC3986ED4: "E Taengu",
	0xCEB7DA1F: "E Tsunami tank",
	0x6E8C5FFF: "E Striker-VX",
	0x59908E62: "E King oni",
	0x90B81D3C: "E Wav. F. Artillary",
	0x1C2EF767: "E MCV",
	0xE27A88A0: "E Ore collector (NavYd)",
	0xCEDA61FD: "E Yari sub.",
	0xBA8E535F: "E Tsunami tank (NavYd)",
	0xB142DEC6: "E Sea wing",
	0x1A2CA9AB: "E Naginata cruiser",
	0xFC5E3314: "E Shogun battleship",
	0xD2ECDA2C: "E MCV (NavYd)",
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

	0x0A255943: "Surveillance sweep",
	0x71B847DE: "Surgical strike",
	0xC1AA9F15: "Chrono chasm I",
	0xADB8916A: "Chrono chasm II",
	0x31999CFD: "Chrono chasm III",
	0xDD6C4C5B: "Advanced aeronautics",
	0x9A4DA87F: "Cryobeam I",
	0x9F834B9B: "Cryobeam II",
	0x85ED35A2: "Cryobeam III",
	0x19E58EA3: "Free trade",
	0x3911B2A0: "High technology",
	0x4912E5F3: "Chrono swap",
	0xF99CAD9D: "Timebomb I",
	0x37233A54: "Timebomb II",
	0xBC51CA49: "Timebomb III",

	0x92ED4E4B: "Fortified Fleet",
	0x7E7D02D1: "Sleeper Ambush",
	0x9F4538FE: "Balloon bomb I",
	0x105CD263: "Balloon bomb II",
	0xBE7F685D: "Balloon bomb III",
	0xD40D5B6A: "Advanced rocket pods",
	0x31201046: "Final squadron I",
	0x4EA3BB59: "Final squadron II",
	0xC21217EF: "Final squadron III",
	0xF628B1AA: "Robotic aseembly",
	0xFBE46678: "Honorable discharge",
	0xC48071DD: "Point-defense drones",
	0x37183B56: "Emperor's Rage I",
	0xA3E51558: "Emperor's Rage II",
	0xB49139E0: "Emperor's Rage III",
}

UNITCOST = {
}

POWERNAMES = {
	0x10551A20: "Pack MCV",

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

	0x84694200: "Surveillance sweep",
	0x4796FE00: "Surgical strike",
	0x0A443400: "Chrono swap 1",
	0x91B16200: "Chrono swap 2",
	0x32421800: "Cryobeam I",
	0xEECD2500: "Cryobeam II",
	0x434A6E00: "Cryobeam III",
	0xC8266300: "Chrono chasm I",
	0x77DF0C00: "Chrono chasm II",
	0x3A3B1C00: "Chrono chasm III",
	0xB0D5B200: "Timebomb I",
	0x3ED71300: "Timebomb II",
	0x67C30E00: "Timebomb III",
	0xD795F100: "Proton collision",
	0x69AE6E00: "Chrono src",
	0x6C6DEF00: "Chrono dest",

	0x86CAC700: "Speeper ambush",
	0x52F31600: "Balloon bomb I",
	0x3DF40100: "Balloon bomb II",
	0xA6260C00: "Balloon bomb III",
	0x9B694F00: "Final squadron I",
	0xAAA4FC00: "Final squadron II",
	0x74BB9800: "Final squadron III",
	0xD6542C00: "Point-defense drones",
	0x299CC500: "Emperor's Rage I",
	0x1ECE0100: "Emperor's Rage II",
	0xF4169400: "Emperor's Rage III",
	0x69286300: "Nano swarm",
	0xCE19D800: "Psionic desolation",
}

POWERCOST = {}
for key, val in POWERNAMES.items() :
	POWERCOST[ key ] = 0

UPGRADENAMES = {
	0xB0ADE8C1: "A Clearance I",
	0xC2868D5F: "A Clearance II",
	0xBF3B8DE8: "Dojo II",
	0x3C7E2488: "Dojo III",
	0x17C0F29C: "Mechabay II",
	0xCF864AD9: "Mechabay III",
	0x7EEF69F2: "Docks II",
	0xB8E633CF: "Docks III",
}

UPGRADECOST = {
	0xB0ADE8C1: 1500,
	0xC2868D5F: 3000,
	0xBF3B8DE8: 250,
	0x3C7E2488: 500,
	0x17C0F29C: 500,
	0x7EEF69F2: 500,
}

AFLD_UNITS = []

BO_COMMANDS = [ 0x00, 0x01, 0x03, 0x05, 0x06, 0x09, 0x0A, 0x32, 0x4E, 0xFE, 0xFF ]



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
			cmd.decode_ra3_hold_cmd( UNITNAMES )
		elif cmd.cmd_id == 0x00 :
			cmd.decode_ra3_deploy_cmd()
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
		elif cmd.cmd_id == 0x03 :
			cmd.decode_upgrade_cmd( UPGRADENAMES, UPGRADECOST )
		elif cmd.cmd_id == 0xFE :
			cmd.decode_skill_targetless( POWERNAMES, POWERCOST )
		elif cmd.cmd_id == 0x32 :
			cmd.decode_skill_2xy( POWERNAMES, POWERCOST )

		#if cmd.cmd_id == 0x01 :
		#	cmd.decode_gg()
		# Fortunately, we don't have target skill, in the sidebar skills, in TW.
		#elif cmd.cmd_id == 0x?? :
		#	cmd.decode_skill_target( POWERNAMES, POWERCOST )

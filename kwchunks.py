#!/usr/bin/python3
# coding: utf8

###
### http://www.gamereplays.org/community/index.php?showtopic=706067&st=0&p=7863248&#entry7863248
### The decoding of the replays format is credited to R Schneider.
###

import io
import chunks
from utils import *



# Build order affecting commands (Which will be drawn in the time line)
BO_COMMANDS = [ 0x31, 0x26, 0x27, 0x28, 0x2B, 0x2D, 0x2E, 0x8A, 0x34, 0x91 ]



CMDLENS = {
	0x00: 0, # group designation
	0x01: 0,
	0x02: 0,
	0x03: 0,
	0x04: 0,
	0x05: 0,
	0x06: 0,
	0x07: 0,
	0x08: 0,
	0x09: 0,
	0x0A: 0, # group selection
	0x0B: 0,
	0x0C: 0,
	0x0D: 0,

	0x0E: 0, # really rare command... short+nolen. assume crawl to FF.
	0x0F: -2,
	0x10: -2,
	0x11: -2,
	0x12: -2,
	0x13: 24, # ??? rare too. Definitely not splitable with -2.
	0x17: -2,
	0x1F: 0, # var len, with FF crawl.

	0x27: -34,
	0x29: 28,
	0x2B: -11,
	0x2C: 0,
	0x2E: 22,
	0x2F: 17,
	0x30: 17,
	0x34: 8,
	0x35: 12,
	0x36: 0,
	0x3C: 21,
	0x3E: 16,
	0x3D: 21,
	0x43: 12,
	0x44: 8,
	0x45: 21,
	0x46: 16,
	0x47: 16,
	0x48: 16,
	0x5B: 16,
	0x61: 20,
	0x72: -2,
	0x73: -2,
	0x77: 3,
	0x7A: 29,
	0x7E: 12,
	#7F 2A 10 01 00 00 00 00 00 00 00 FF 
	#7F 00 00 8B 7F 00 00 F4 7D 00 00 06 6D 00 00 D7 69 00 00 7F 69 00 00 FF
	0x7F: 0, # 7F is a varlen command. FF seek it seems. Alt down/up cmd.
	0x87: 8,
	0x89: 8,
	0x8A: 53, # skill with 2xy designation. (wormhole)
	0x8C: 45,
	0x8D: 1049,
	0x8E: 16,
	0x8F: 40,
	0x90: 16,
	0x91: 10,

	0x28: 0, # target on structure...
	0x2D: 0,
	0x31: 0,
	0x8B: 0,

	0x26: -15,
	0x4C: -2,
	0x4D: -2,
	0x92: -2,
	0x93: -2,
	0xF5: -4,
	0xF6: -4,
	0xF8: -4,
	0xF9: -2,
	0xFA: 0,
	0xFB: 0,
	0xFC: 0,
	0xFD: 0,
	0xFE: 0,
	0xFF: 0
}

CMDNAMES = {
	0x00: "Assign selection to group 6",
	0x01: "Assign selection to group 7",
	0x02: "Assign selection to group 8",
	0x03: "Assign selection to group 9",
	0x04: "Select group 0",
	0x05: "Select group 1",
	0x06: "Select group 2",
	0x07: "Select group 3",
	0x08: "Select group 4",
	0x09: "Select group 5",
	0x0A: "Select group 6",
	0x0B: "Select group 7",
	0x0C: "Select group 8",
	0x0D: "Select group 9",

	0x26: "Skill (targetless)",
	0x27: "Skill",
	0x28: "Skill (with target unit)",
	0x2B: "Upgrade",
	0x2D: "queue/resume production",
	0x2E: "hold/cancel/cancel_all production",
	0x2F: "Start building construction",
	0x30: "Hold/Cancel construction",
	0x31: "Place down building",
	0x34: "sell",
	0x3D: "attack",
	0x3E: "force fire",
	0x43: "enter building (eng capture)????????",
	0x44: "return to the specified refinery",
	0x45: "harvest specific lump of tiberium",
	0x46: "move",
	0x47: "A-move",
	0x48: "G-move",
	0x4C: "stop",
	0x61: "30s heartbeat",
	0x72: "repair",
	0x73: "cancel repair",
	0x77: "Q select",
	0x7A: "formation move",
	0x7E: "set unit stance (aggresive, hold ground, hold fire...)",
	0x7F: "alt hold/release (waypoint)?",
	0x89: "toggle power down/up",
	0x8E: "reverse move",
	0x8F: "'scroll'",
	0x91: "GG?",

	0xF5: "drag selection box and/or select units/structures",
	0xF6: "w-select units??",
	0xF8: "left click (deselect stuff)",
	0xF9: "remove units from selection (right click on unit group icon)",

	0xFA: "Assign selection to group 0",
	0xFB: "Assign selection to group 1",
	0xFC: "Assign selection to group 2",
	0xFD: "Assign selection to group 3",
	0xFE: "Assign selection to group 4",
	0xFF: "Assign selection to group 5",
}

POWERNAMES = {
	0x4A529800: "Radar scan",
	0x7CBA6F00: "GDI paratroopers",
	0x8C523500: "ZOCOM paratroopers",
	0x77E6D800: "Orca strike",
	0xA84A4B00: "GDI Blood hound",
	0x9097F400: "ST blood hound",
	0xD6F29200: "ZOCOM blood hound",
	0x6D899600: "Zone raider drop pod",
	0xB1DC2400: "Sharp shooters",
	0x6C18B300: "Zone trooper pod drop",
	0x4783C500: "Shock wave artillary",
	0x73E8D600: "Orbital strike",
	0xEEF14800: "Sonic strike",
	0x49960E00: "Rail gun accelerator",
	0x02FB0C00: "Ion cannon",
	0xC0527800: "Sonic wall",

	0xA1819100: "Decoy army src",
	0x7668A300: "Decoy army dest",
	0xF1630D20: "Radar jamming",
	0xC21CA400: "Laser fence",
	0x34EAD100: "Nod cloaking field",
	0x7DBB9C00: "MoK cloaking field",
	0x7CCD5D00: "Mines",
	0x4256F200: "Redemption",
	0x7FFE2700: "Catalyst missile",
	0x7D860D00: "Seed tiberium",
	0x15293700: "Tib. vapour bomb",
	0x31031000: "Vein detonation",
	0xF595A200: "Nuke",
	0xD1CEE500: "Decoy temple",
	0xAF82A100: "Magnetic mines",
	0xFFB20600: "Shadow team",
	0x45217320: "Power scan",

	0xE37B6800: "Repair drone",
	0x940B1600: "Overlord's Wrath",
	0xA9CC4C00: "Buzzer swarm",
	0xDC9ACC00: "Ichor seed",
	0xD28EFC00: "Lightning spike",
	0xEEF15100: "Rift generator",
	0x8E430200: "Contaminate",
	0xC6F96000: "Stasis",
	0x1F467400: "Phase",
	0x57E75020: "Tib. vib. scan",
	0x0FA96520: "Tib. vib. scan R-17",
	0xE1E50B20: "Mothership",
	0xE930FD00: "Shock pod",
	0xFD88FC00: "Temporal wormhole",
	0xA0E6D800: "Wormhole (T59)",
	0x97ECA100: "Wormhole",

	0x63C6B820: "MCV Pack",
	0x3039C820: "MCV Unpack",
	0x769F4920: "Dig fox hole",
	0xB5F8AC20: "Return to a refinery",
}

UPGRADENAMES = {
	0x60737ED1: "GDI power plant upgrade",
	0xB44E9A3B: "ST power plant upgrade",
	0xA73AE932: "ZCM power plant upgrade",
	0x30D999CB: "AP ammo",
	0x252E5A6D: "Sensor pod",
	0xF244BC18: "Scanner pack",
	0x259526AE: "Aircraft hard point",
	0xA88B018A: "Strato fighter",
	0xDE945A9B: "Composite armor",
	0x82730C76: "EMP grenade",
	0x5DBB4B1B: "Power pack",
	0x6EC57B03: "Mortar",
	0x81902614: "Railgun",
	0x39EFD155: "Tungsten",
	0x7DC1C5B4: "Adaptive armor",
	0xCA8D43C1: "Tib resistant armor",
	0xE5C2A0EC: "Zorca sensor pod",
	0x5F9C9069: "Ceramic armor",
	0x6FB1DF0F: "Zone raider scanner pack",

	0x58B082E5: "Nod power plant upgrade",
	0xE0DD89F8: "BH power plant upgrade",
	0x6C96D5F1: "MoK power plant upgrade",
	0xB28800DF: "Dozer blade",
	0xD835BA8A: "Quad turrets",
	0x1A38AADD: "Signature generator (venom)",
	0x9562430C: "Disruption pod",
	0x263F7EFB: "Confessor",
	0x3129F082: "Tiberium infusion",
	0x7926BE22: "EMP coils",
	0xF6BAA511: "Laser capacitors",
	0x7F35210F: "Tiberium warhead missiles",
	0x062958A2: "Black disciples",
	0xEEA7CE69: "Purifying flames",
	0x9E6C330B: "Charged particle beams",
	0x0B66C4A4: "Cybernetic legs",
	0x2698DF3C: "Super charged particle beams",

	0x3409F073: "Scrin power plant upgrade",
	0xA98BDFE4: "R17 power plant upgrade",
	0x9E936CEA: "T59 power plant upgrade",
	0x269AF75A: "Attenuated shield",
	0x023714AD: "Blink pack",
	0x9B19AB1B: "Plasma disc launcher",
	0xE5A3374C: "Force shield generator",
	0x230E8321: "Shard launcher",
	0x673B860F: "R17 attenuated shield",
	0x88B36F31: "R17 force shield generator",
	0x62495112: "Blue shards",
	0x70427973: "Conversion beam res.",
	0xA921E313: "Advanced articulators",
	0x4FCCDACF: "Traveller engine",
}

FREEUNITS = {
	0xB5D275B6: 0x3A3D109A, # Nod ref & harv
	0x16A86D68: 0x0D258354, # GDI
	0x4C2E2C25: 0xF52AEEDF, # ST
	0x05F6FA50: 0x21661DFB, # BH
	0x40DCA116: 0xC3785BFE, # MoK
	0x0CA58AEF: 0x14E34DE2, # Sc
	0x7E291858: 0xC37F7227, # R17
	0xF4E73A51: 0x998395BF, # T59
	0xBA62677D: 0xC23B3A15, # ZCM
}

UNITNAMES = {
	0xA333C6A8: "Nod power plant",
	0x72407A4F: "Nod barracks",
	0xB5D275B6: "Nod refinery",
	0x22943F1D: "Nod factory",
	0xA46AA481: "Nod operations center",
	0xD5C63044: "Nod air tower",
	0x989B10EB: "Nod secret shrine",
	0xE630F233: "Nod tech center",
	0x8F61720F: "Nod tib chem plant",
	0x667CDE9C: "Nod crane",
	0xA78E52C1: "Nod redeemer eng. fac.",
	0x4E57EF4B: "Nod shredder turret",
	0xC04FB821: "Nod laser turret",
	0x821322AD: "Nod sam turret",
	0x5593CBD2: "Nod silo",
	0x5C9C4468: "Nod disruption tower",
	0x9C462965: "Nod voice of Kane",
	0x0E4953BD: "Nod air support tower",
	0xE69ACCA8: "Nod obelisk of light",
	0x638C1170: "Nod temple of Nod",

	0xBC36257A: "Nod militant",
	0x89C45844: "Nod mil. rocket",
	0xA35D835C: "Nod saboteur",
	0xBE7C389D: "Nod fanatics",
	0x0128ABF1: "Nod black hand",
	0xA6E10008: "Nod shadow team",
	0xDADFF0A0: "Nod commando",
	0xBB708BD5: "Nod attack bike",
	0x6354531D: "Nod buggy",
	0x02F9131D: "Nod scorpion",
	0x3A3D109A: "Nod harvester",
	0x084336F2: "Nod MCV",
	0xFD8822B1: "Nod flame tank",
	0x53024F73: "Nod reckoner",
	0x4F9DF943: "Nod beam cannon",
	0x0026538D: "Nod stealth tank",
	0x4D1CFBBD: "Nod spectre",
	0xBC0BF618: "Nod avatar",
	0xD8BE0529: "Nod redeemer",
	0x8B2AAF0B: "Nod venom",
	0x6AA59D16: "Nod vertigo",
	0x12CEBD57: "Nod emissary",

	0x6BF191EB: "GDI crane",
	0x239262C6: "GDI power",
	0x13D568B3: "GDI barracks",
	0x16A86D68: "GDI ref",
	0xE1659649: "GDI command post",
	0x115E0E31: "GDI armory",
	0x9ABD65AC: "GDI factory",
	0x8314C7A0: "GDI airfield",
	0x33B40C6F: "GDI tech center",
	0x51474781: "GDI rec. hub",
	0x8136F6F6: "GDI space uplink",
	0x3EA580F4: "GDI watch tower",
	0x3554B096: "GDI guardian cannon",
	0xAD54632A: "GDI AA battery",
	0x15043F6B: "GDI silo",
	0xCD0835A6: "GDI sonic emitter",
	0x9D247A0D: "GDI support airfield",
	0xF1F5671A: "GDI ion cannon",

	0x9096966E: "GDI riflemen",
	0xEF1252DB: "GDI missile squad",
	0x64EEDB5A: "GDI engineer",
	0x42896060: "GDI grenadier",
	0xBCB36A05: "GDI sniper",
	0xDCB85878: "GDI commando",
	0x5D5E5931: "GDI zone trooper",
	0x921C06CC: "GDI surveyer",
	0x6FF52808: "GDI putbull",
	0xE6EAD02C: "GDI predator",
	0xD01CFD88: "GDI APC",
	0x0D258354: "GDI harvester",
	0x52935296: "GDI MCV",
	0x2144BD64: "GDI shatterer",
	0xB54034FF: "GDI sling shot",
	0xB48BEDD2: "GDI rig",
	0xBC0A0849: "GDI mammoth tank",
	0x32488E32: "GDI juggernaught",

	0xB587039F: "GDI orca",
	0xB3363EA3: "GDI firehawk",
	0xA8C09808: "GDI hammer head",
	0x30354418: "GDI MARV",

	0xE5F7D19B: "ST power plant",
	0x349BBD51: "ST barracks",
	0x6F3D0449: "ST watch tower",
	0x4C2E2C25: "ST ref",
	0x296BE097: "ST command post",
	0xA0426848: "ST crane",
	0xEEAC5E37: "ST airfield",
	0x40A17081: "ST factory",
	0x0F640F30: "ST space uplink",
	0xEABA4298: "ST rec. hub",
	0x6C309FAB: "ST tech center",
	0x358EB5E4: "ST guardian cannon",
	0x5C80259B: "ST AA battery",
	0x2C6EB27C: "ST silo",
	0xDF57BC42: "ST support airfield",
	0x01644BAB: "ST ion cannon",

	0xCF35F1B4: "ST riflemen",
	0xEA23C76F: "ST missile",
	0x80DFF5D9: "ST engineer",
	0x0FC6A915: "ST grenadier",
	0x6BD7B8AB: "ST orca",
	0x1348CA0A: "ST firehawk",
	0xDADBFA6C: "ST hammer head",
	0xF3F183DD: "ST surveyer",
	0x0C6387E0: "ST pitbull",
	0x3C6842D0: "ST titan",
	0x7CC56843: "ST MRT",
	0xF52AEEDF: "ST harvester",
	0x3E7EE781: "ST MCV",
	0x4AFAC6E8: "ST slihgshot",
	0x5C43DE8F: "ST wolverine",
	0x82D6E5D8: "ST rig",
	0xC1B5AB13: "ST mammoth tank",
	0x53167D53: "ST behemoth",
	0x565BE825: "ST MARV",

	0x0A06D953: "BH crane",
	0x29BD08C8: "BH power plant",
	0x701FB486: "BH hand of nod",
	0x98F45D06: "BH shredder turrets",
	0x05F6FA50: "BH ref",
	0x2C62828E: "BH factory",
	0x23052F70: "BH operation center",
	0x0F62BDA5: "BH secret shrine",
	0x6F950650: "BH tech center",
	0x71F0EA3D: "BH redeemer eng. center",
	0x3232304B: "BH laser turrets",
	0xF5BD29E4: "BH SAM turrets",
	0xBCE723C7: "BH silo",
	0xCE205DD2: "BH tib. chem. plant",
	0xD78A3ED5: "BH voice of Kane",
	0xF2C0CB22: "BH obelisk of light",
	0x8D78D973: "BH temple of Nod",

	0x0FDEF5E7: "BH confessor cabal",
	0xC3011861: "BH mil. rocket",
	0x282A11E3: "BH saboteur",
	0x08E0F9C9: "BH fanatics",
	0x5F44F92F: "BH black hand",
	0x4E4C1963: "BH commando",
	0x297C2132: "BH attack bike",
	0x79609108: "BH buggy",
	0xA33F11AF: "BH scorpion",
	0x21661DFB: "BH harvester",
	0x5B6D5FE4: "BH MCV",
	0x1E1AEEBE: "BH flame tank",
	0x198BF501: "BH reckoner",
	0x7F5C5CDA: "BH beam cannon",
	0xF38615BD: "BH mantis",
	0x7A639A9A: "BH spectre",
	0x3C7C08FB: "BH purifier",
	0xCD5A5360: "BH redeemer",
	0x7D560AEC: "BH emissary",

	0x6753D4CA: "MoK crane",
	0xBDEA92DF: "MoK power plant",
	0x84B21B76: "MoK hand of nod",
	0x8161F095: "MoK shredder turrets",
	0x8ADF6801: "MoK secret shrine",
	0x40DCA116: "MoK ref.",
	0xE6D4B65C: "MoK factory",
	0xC6999B8E: "MoK operation center",
	0x8E42292A: "MoK air tower",
	0xF79AF4E3: "MoK tech center",
	0xF2A73707: "MoK Redeemer eng. fac.",
	0xD5326C9E: "MoK tib. chem. plant",
	0x3FC7B8E4: "MoK laser turrets",
	0x9D52F3D7: "MoK SAM turrets",
	0x17D5CAAA: "MoK silo",
	0x13517F79: "MoK voice of Kane",
	0x7CADE3A3: "MoK disruption tower",
	0x483EAEC0: "MoK obelisk of light",
	0xA12474B6: "MoK temple of Nod",
	0x75F7ECE5: "MoK support air tower",

	0x23E82509: "MoK venom",
	0x393E446C: "MoK vertigo",
	0xD5BE6F6C: "MoK awakened",
	0x020126F6: "MoK mil. rocket",
	0xA6A2C1D4: "MoK saboteur",
	0x6093B1BE: "MoK fanatics",
	0xE6E24EF7: "MoK tiberium trooper",
	0x6AEA240A: "MoK shadow team",
	0xB27DDF67: "MoK enlightened",
	0x406C94AC: "MoK commando",
	0x1DAE1C47: "MoK attack bike",
	0xE3C841B0: "MoK buggy",
	0x1B44D6AE: "MoK scorpion",
	0xC3785BFE: "MoK harvester",
	0xB3847303: "MoK MCV",
	0x3000821A: "MoK reckoner",
	0x3D143A57: "MoK beam cannon",
	0x1025B90B: "MoK stealth tank",
	0x9A533FC7: "MoK spectre",
	0xD53D8ABF: "MoK avatar",
	0x711A18DF: "MoK redeemer",
	0xBDC39D7D: "MoK emissary",

	0x95A33CC6: "Sc power plant",
	0x0CA58AEF: "Sc ref.",
	0x929BD6C1: "Sc barracks",
	0xFEFD8CB5: "Sc factory",
	0xEEBC2492: "Sc nerve center",
	0x468981C5: "Sc gravity stabilizer",
	0xC1AFF92C: "Sc stasis chamber",
	0x951B67BA: "Sc tech center",
	0xE315D4B3: "Sc signal transmitter",
	0x550E8876: "Sc crane",
	0x23BE7BC2: "Sc warp chasm",
	0x0416A92F: "Sc buzzer hive",
	0xF4B32C4E: "Sc photon cannon",
	0xB6046563: "Sc plasma battery",
	0xDFCF8D47: "Sc growth accelerator",
	0x425D00A4: "Sc storm column",
	0x384EA3E7: "Sc rift generator",

	0x8E2679EF: "Sc buzzer",
	0x2B9428D0: "Sc disint.",
	0xAA95429D: "Sc assimiliator",
	0x6495F509: "Sc shock trooper",
	0x32EA13B3: "Sc ravager",
	0xF601EB6C: "Sc master mind",
	0x01A54C1B: "Sc gunwalker",
	0xB8802763: "Sc seeker",
	0x14E34DE2: "Sc harvester",
	0xAF991372: "Sc devouer",
	0x77A0E8A9: "Sc corrupter",
	0xE2D7C037: "Sc tripod",
	0x0D396F28: "Sc mechapede",
	0x1D137C85: "Sc hexapod",
	0x30E33C29: "Sc drone ship",
	0xF6E707D5: "Sc storm rider",
	0x42E35730: "Sc devastator warship",
	0x14EACF09: "Sc carrier",
	0x4B93BEEC: "Sc explorer",

	0x3CDBD279: "R17 power plant",
	0x7E291858: "R17 ref.",
	0x38A4A9E0: "R17 barracks",
	0x9A917351: "R17 factory",
	0xEFB4E2C0: "R17 nerve center",
	0x3A64AE56: "R17 gravity stabilizer",
	0xEB2D33E3: "R17 stasis chamber",
	0xDFDD1DA9: "R17 tech center",
	0x0C371C2A: "R17 signal transmitter",
	0x3400D06F: "R17 crane",
	0x589D2B2B: "R17 warp chasm",
	0x27C3413C: "R17 buzzer hive",
	0xBA9657C9: "R17 photon cannon",
	0x0FD56363: "R17 plasma battery",
	0xDBE925A9: "R17 growth accelerator",
	0x6862DB83: "R17 storm column",
	0xA503835E: "R17 rift generator",

	# R17 buzzer, disint, assimiliators are shared with Scrin.
	0x40241AC3: "R17 shock trooper",
	0x7F2D0EF5: "R17 ravager",
	0x7FCCFDE3: "R17 shard walker",
	0xDB2B7D2F: "R17 seeker",
	0xC37F7227: "R17 harvester",
	0x416EFDFF: "R17 devouer",
	0xB187F87A: "R17 corrupter",
	0x4DD96105: "R17 tripod",
	0x0F108542: "R17 mechapede",
	0x146C2890: "R17 hexapod",
	0xEECD3E80: "R17 drone ship",
	0x1DF82E16: "R17 storm rider",
	0xF3E8F14F: "R17 explorer",

	0x1F633A81: "T59 power plant",
	0xF4E73A51: "T59 ref.",
	0xAD3B9CCD: "T59 barracks",
	0x5743BC5C: "T59 factory",
	0x74F0DB70: "T59 nerve center",
	0x714AFABF: "T59 gravity stabilizer",
	0x73D55ACC: "T59 stasis chamber",
	0x9AF79C8D: "T59 tech center",
	0x3E28732D: "T59 signal transmitter",
	0xDE06E6CF: "T59 crane",
	0xA69624CC: "T59 warp chasm",
	0xD56430FB: "T59 buzzer hive",
	0x6AA8919A: "T59 photon cannon",
	0x385D26A8: "T59 plasma battery",
	0x730EA95B: "T59 growth accelerator",
	0x62697C2C: "T59 storm column",
	0x4379775A: "T59 rift generator",

	# buzzer is shared with scrin
	0x00240FB1: "T59 disint.",
	0xDFDE337F: "T59 assimiliators",
	0x4803957E: "T59 shock trooper",
	0xC46CECA2: "T59 cultist",
	0x72A9F5D5: "T59 ravager",
	0x5F8004DF: "T59 progidy",
	0x51430053: "T59 gunwalker",
	0x7296891C: "T59 seeker",
	0x998395BF: "T59 harvester",
	0x91B5B69D: "T59 corrupter",
	0x748C4C22: "T59 tripod",
	0x7F3CEB99: "T59 mechapede",
	0xA4FD281B: "T59 hexapod",
	0x292DB333: "T59 drone ship",
	0xECA08561: "T59 storm rider",
	0xB15E754C: "T59 devastator warship",
	0x0F71843C: "T59 carrier",
	0x8C82B86C: "T59 explorer",

	0xDCD2D288: "ZCM crane",
	0x34E71EC6: "ZCM power plant",
	0xBA62677D: "ZCM ref",
	0x502F0AAA: "ZCM watch tower",
	0x50EB58F7: "ZCM barracks",
	0xD2E0D294: "ZCM command post",
	0x8F222FF5: "ZCM factory",
	0xF2B92697: "ZCM airfield",
	0x7D372A88: "ZCM armory",
	0xD2CA793C: "ZCM silo",
	0x622F00EB: "ZCM guardian cannon",
	0xF689DAA0: "ZCM support airfield",
	0xE76FAF0F: "ZCM tech center",
	0x1F54F6C2: "ZCM space uplink",
	0xEBDE1709: "ZCM rec. hub",
	0xF459C486: "ZCM AA battery",
	0x089DA349: "ZCM sonic emitter",

	0x0AC645E3: "ZCM riflemen",
	0x17A153BA: "ZCM missile",
	0x009260E6: "ZCM engineer",
	0xC43CF79F: "ZCM grenadier",
	0xB724E036: "ZCM sniper",
	0x2FA51492: "ZCM commando",
	0x0D213112: "ZCM zone raider",
	0xAD5F0217: "ZCM pitbull",
	0xF714BBD3: "ZCM predator",
	0x64BCB106: "ZCM APC",
	0xC23B3A15: "ZCM harvester",
	0x330CEC90: "ZCM MCV",
	0xAE73138F: "ZCM shatterer",
	0x5A6044BC: "ZCM slingshot",
	0x6FCB2318: "ZCM rig,",
	0x12E1C8C8: "ZCM mammoth",
	0x37F0A5F5: "ZCM MARV",
	0xFAA68740: "ZCM orca",
	0xFA477EAA: "ZCM hammer head",
	0x42D55831: "ZCM firehawk",
	0xFD890B01: "ZCM surveyer",
}

POWERCOST = {
	0x4A529800: 300, #"Radar scan",
	0x7CBA6F00: 1500, #"GDI paratroopers",
	0x8C523500: 1500, #"ZOCOM paratroopers",
	0x77E6D800: 500, #"Orca strike",
	0xA84A4B00: 3000, #"GDI Blood hound",
	0x9097F400: 3000, #"ST blood hound",
	0xD6F29200: 3000, #"ZOCOM blood hound",
	0x6D899600: 4500, #"Zone raider drop pod",
	0xB1DC2400: 3500, #"Sharp shooters",
	0x6C18B300: 4500, #"Zone trooper pod drop",
	0x4783C500: 2000, #"Shock wave artillary",
	0x73E8D600: 4000, #"Orbital strike",
	0xEEF14800: 1500, #"Sonic strike",
	0x49960E00: 1000, #"Rail gun accelerator",
	0x02FB0C00: 0, #"Ion cannon",
	0xC0527800: 500, #"Sonic wall",

	0xA1819100: 500, #"Decoy army",
	0x7668A300: 750, #"Radar jamming", # probably incorrect.
	0xF1630D20: 750, #"Radar jamming",
	0xC21CA400: 500, #"Laser fence",
	0x34EAD100: 3000, #"Nod cloaking field",
	0x7DBB9C00: 3000, #"MoK cloaking field",
	0x7CCD5D00: 1500, #"Mines",
	0x4256F200: 1500, #"Redemption",
	0x7FFE2700: 1500, #"Catalyst missile",
	0x7D860D00: 500, #"Seed tiberium",
	0x15293700: 3500, #"Tib. vapour bomb",
	0x31031000: 4000, #"Vein detonation",
	0xF595A200: 0, #"Nuke",
	0xD1CEE500: 1000, #"Decoy temple",
	0xAF82A100: 1500, #"Magnetic mines",
	0xFFB20600: 1600, #"Shadow team",
	0x45217320: 500, #"Power signature scan",

	0xE37B6800: 1500, #"Repair drone",
	0x940B1600: 4000, #"Overlord's Wrath",
	0xA9CC4C00: 1500, #"Buzzer swarm",
	0xDC9ACC00: 1000, #"Ichor seed",
	0xD28EFC00: 1000, #"Lightning spike",
	0xEEF15100: 0, #"Rift generator",
	0x8E430200: 1100, #"Infestation",
	0xC6F96000: 2000, #"Stasis shield",
	0x1F467400: 1500, #"Phase field",
	0x57E75020: 500, #"Tib. vib. scan",
	0x0FA96520: 0, #"Tib. vib. scan R-17",
	0xE1E50B20: 5000, #"Mothership",
	0xE930FD00: 3000, #"Shock pod",
	0xFD88FC00: 1200, #"Temporal wormhole",
	0xA0E6D800: 2000, #"Wormhole",

	0x769F4920: 100, #"Dig fox hole",
}

UPGRADECOST = {
	0x60737ED1: 300, #"GDI power plant upgrade",
	0xB44E9A3B: 300, #"ST power plant upgrade",
	0xA73AE932: 300, #"ZCM power plant upgrade",
	0x30D999CB: 2500, #"AP ammo",
	0x252E5A6D: 500, #"Sensor pod",
	0xF244BC18: 1000, #"Scanner pack",
	0x259526AE: 2500, #"Aircraft hard point",
	0xA88B018A: 2000, #"Strato fighter",
	0xDE945A9B: 2000, #"Composite armor",
	0x82730C76: 1000, #"EMP grenade",
	0x5DBB4B1B: 2000, #"Power pack",
	0x6EC57B03: 1000, #"Mortar",
	0x81902614: 5000, #"Railgun",
	0x39EFD155: 2000, #"Tungsten",
	0x7DC1C5B4: 1500, #"Adaptive armor",
	0xCA8D43C1: 2000, #"Tib. field suits",
	0xE5C2A0EC: 500, #"Zorca sensor pod",
	0x5F9C9069: 1000, #"Ceramic armor",
	0x6FB1DF0F: 1000, #"Zone raider scanner pack",

	0x58B082E5: 500, #"Nod power plant upgrade",
	0xE0DD89F8: 500, #"BH power plant upgrade",
	0x6C96D5F1: 500, #"MoK power plant upgrade",
	0xB28800DF: 2000, #"Dozer blade",
	0xD835BA8A: 1000, #"Quad turrets",
	0x1A38AADD: 100, #"Signature generator (venom)",
	0x9562430C: 500, #"Disruption pod",
	0x263F7EFB: 1000, #"Confessor",
	0x3129F082: 2000, #"Tiberium infusion",
	0x7926BE22: 1000, #"EMP coils",
	0xF6BAA511: 3000, #"Laser capacitors",
	0x7F35210F: 2000, #"Tiberium warhead missiles",
	0x062958A2: 2000, #"Black disciples",
	0xEEA7CE69: 3000, #"Purifying flames",
	0x9E6C330B: 1000, #"Charged particle beams",
	0x0B66C4A4: 1000, #"Cybernetic legs",
	0x2698DF3C: 4000, #"Super charged particle beams",

	0x3409F073: 400, #"Scrin power plant upgrade",
	0xA98BDFE4: 400, #"R17 power plant upgrade",
	0x9E936CEA: 400, #"T59 power plant upgrade",
	0x269AF75A: 2000, #"Attenuated shield",
	0x023714AD: 2000, #"Blink pack",
	0x9B19AB1B: 1000, #"Plasma disc launcher",
	0xE5A3374C: 5000, #"Force shield generator",
	0x230E8321: 3000, #"Shard launcher",
	0x673B860F: 2000, #"R17 attenuated shield",
	0x88B36F31: 5000, #"R17 force shield generator",
	0x62495112: 2500, #"Blue shards",
	0x70427973: 1000, #"Conversion beam res.",
	0xA921E313: 2000, #"Advanced articulators",
	0x4FCCDACF: 2000, #"Traveller engine",
}

UNITCOST = {
	0xA333C6A8: 500, #"Nod power plant",
	0x72407A4F: 500, #"Nod barracks",
	0xB5D275B6: 3000, #"Nod refinery",
	0x22943F1D: 2000, #"Nod factory",
	0xA46AA481: 1500, #"Nod operations center",
	0xD5C63044: 1000, #"Nod air tower",
	0x989B10EB: 1500, #"Nod secret shrine",
	0xE630F233: 4000, #"Nod tech center",
	0x8F61720F: 3000, #"Nod tib chem plant",
	0x667CDE9C: 1500, #"Nod crane",
	0xA78E52C1: 3000, #"Nod redeemer eng. fac.",
	0x4E57EF4B: 600, #"Nod shredder turret",
	0xC04FB821: 1200, #"Nod laser turret",
	0x821322AD: 800, #"Nod sam turret",
	0x5593CBD2: 500, #"Nod silo",
	0x5C9C4468: 1000, # Nod disruption tower,
	0x9C462965: 1000, #"Nod voice of Kane",
	0x0E4953BD: 500, #"Nod air support tower",
	0xE69ACCA8: 1800, #"Nod obelisk of light",
	0x638C1170: 5000, #"Nod temple of Nod",

	0xBC36257A: 200, #"Nod militant",
	0x89C45844: 400, #"Nod mil. rocket",
	0xA35D835C: 500, #"Nod saboteur",
	0xBE7C389D: 800, #"Nod fanatics",
	0x0128ABF1: 900, #"Nod black hand",
	0xA6E10008: 800, #"Nod shadow team",
	0xDADFF0A0: 2000, #"Nod commando",
	0xBB708BD5: 600, #"Nod attack bike",
	0x6354531D: 400, #"Nod buggy",
	0x02F9131D: 800, #"Nod scorpion",
	0x3A3D109A: 1400, #"Nod harvester",
	0x084336F2: 2500, #"Nod MCV",
	0xFD8822B1: 1200, #"Nod flame tank",
	0x53024F73: 900, #"Nod reckoner",
	0x4F9DF943: 1000, #"Nod beam cannon",
	0x0026538D: 1500, #"Nod stealth tank",
	0x4D1CFBBD: 1200, #"Nod spectre",
	0xBC0BF618: 2200, #"Nod avatar",
	0xD8BE0529: 5000, #"Nod redeemer",
	0x8B2AAF0B: 700, #"Nod venom",
	0x6AA59D16: 1800, #"Nod vertigo",
	0x12CEBD57: 1500, #"Nod emissary",

	0x6BF191EB: 1500, #"GDI crane",
	0x239262C6: 800, #"GDI power",
	0x13D568B3: 500, #"GDI barracks",
	0x16A86D68: 2000, #"GDI ref",
	0xE1659649: 1500, #"GDI command post",
	0x115E0E31: 1000, #"GDI armory",
	0x9ABD65AC: 2000, #"GDI factory",
	0x8314C7A0: 1000, #"GDI airfield",
	0x33B40C6F: 4000, #"GDI tech center",
	0x51474781: 3000, #"GDI rec. hub",
	0x8136F6F6: 3000, #"GDI space uplink",
	0x3EA580F4: 600, #"GDI watch tower",
	0x3554B096: 1200, #"GDI guardian cannon",
	0xAD54632A: 800, #"GDI AA battery",
	0x15043F6B: 500, #"GDI silo",
	0xCD0835A6: 2000, #"GDI sonic emitter",
	0x9D247A0D: 500, #"GDI support airfield",
	0xF1F5671A: 5000, #"GDI ion cannon",

	0x9096966E: 300, #"GDI riflemen",
	0xEF1252DB: 400, #"GDI missile squad",
	0x64EEDB5A: 500, #"GDI engineer",
	0x42896060: 800, #"GDI grenadier",
	0xBCB36A05: 1000, #"GDI sniper",
	0xDCB85878: 2000, #"GDI commando",
	0x5D5E5931: 1300, #"GDI zone trooper",
	0x921C06CC: 1500, #"GDI surveyer",
	0x6FF52808: 700 ,#"GDI putbull",
	0xE6EAD02C: 1000, #"GDI predator",
	0xD01CFD88: 700, #"GDI APC",
	0x0D258354: 1400, #"GDI harvester",
	0x52935296: 2500, #"GDI MCV",
	0x2144BD64: 1500, #"GDI shatterer",
	0xB54034FF: 1000, #"GDI sling shot",
	0xB48BEDD2: 2000, #"GDI rig",
	0xBC0A0849: 2500, #"GDI mammoth tank",
	0x32488E32: 2200, #"GDI juggernaught",

	0xB587039F: 1100, #"GDI orca",
	0xB3363EA3: 1500, #"GDI firehawk",
	0xA8C09808: 1500, #"GDI hammer head",
	0x30354418: 5000, #"GDI MARV",

	0xE5F7D19B: 800, #"ST power plant",
	0x349BBD51: 500, #"ST barracks",
	0x6F3D0449: 600, #"ST watch tower",
	0x4C2E2C25: 3000, #"ST ref",
	0x296BE097: 1500, #"ST command post",
	0xA0426848: 1500, #"ST crane",
	0xEEAC5E37: 1000, #"ST airfield",
	0x40A17081: 2000, #"ST factory",
	0x0F640F30: 3000, #"ST space uplink",
	0xEABA4298: 3000, #"ST rec. hub",
	0x6C309FAB: 4000, #"ST tech center",
	0x358EB5E4: 1200, #"ST guardian cannon",
	0x5C80259B: 800, #"ST AA battery",
	0x2C6EB27C: 500, #"ST silo",
	0xDF57BC42: 500, #"ST support airfield",
	0x01644BAB: 5000, #"ST ion cannon",

	0xCF35F1B4: 300, #"ST riflemen",
	0xEA23C76F: 400, #"ST missile",
	0x80DFF5D9: 500, #"ST engineer",
	0x0FC6A915: 800, #"ST grenadier",
	0x6BD7B8AB: 1100, #"ST orca",
	0x1348CA0A: 1500, #"ST firehawk",
	0xDADBFA6C: 1500, #"ST hammer head",
	0xF3F183DD: 1500, #"ST surveyer",
	0x0C6387E0: 700, #"ST pitbull",
	0x3C6842D0: 1300, #"ST titan",
	0x7CC56843: 700, #"ST MRT",
	0xF52AEEDF: 1600, #"ST harvester",
	0x3E7EE781: 2500, #"ST MCV",
	0x4AFAC6E8: 1000, #"ST slihgshot",
	0x5C43DE8F: 900, #"ST wolverine",
	0x82D6E5D8: 2000, #"ST rig",
	0xC1B5AB13: 2500, #"ST mammoth tank",
	0x53167D53: 2200, #"ST behemoth",
	0x565BE825: 5000, #"ST MARV",

	0x0A06D953: 1500, #"BH crane",
	0x29BD08C8: 500, #"BH power plant",
	0x701FB486: 500, #"BH hand of nod",
	0x98F45D06: 600, #"BH shredder turrets",
	0x05F6FA50: 3000, #"BH ref",
	0x2C62828E: 2000, #"BH factory",
	0x23052F70: 1500, #"BH operation center",
	0x0F62BDA5: 1500, #"BH secret shrine",
	0x6F950650: 4000, #"BH tech center",
	0x71F0EA3D: 3000, #"BH redeemer eng. center",
	0x3232304B: 1200, #"BH laser turrets",
	0xF5BD29E4: 800, #"BH SAM turrets",
	0xBCE723C7: 500, #"BH silo",
	0xCE205DD2: 3000, #"BH tib. chem. plant",
	0xD78A3ED5: 1000, #"BH voice of Kane",
	0xF2C0CB22: 1800, #"BH obelisk of light",
	0x8D78D973: 5000, #"BH temple of Nod",

	0x0FDEF5E7: 400, #"BH confessor cabal",
	0xC3011861: 400, #"BH mil. rocket",
	0x282A11E3: 500, #"BH saboteur",
	0x08E0F9C9: 800, #"BH fanatics",
	0x5F44F92F: 900, #"BH black hand",
	0x4E4C1963: 1500, #"BH commando",
	0x297C2132: 600, #"BH attack bike",
	0x79609108: 400, #"BH buggy",
	0xA33F11AF: 800, #"BH scorpion",
	0x21661DFB: 1400, #"BH harvester",
	0x5B6D5FE4: 2500, #"BH MCV",
	0x1E1AEEBE: 1200, #"BH flame tank",
	0x198BF501: 900, #"BH reckoner",
	0x7F5C5CDA: 1000, #"BH beam cannon",
	0xF38615BD: 1200, #"BH mantis",
	0x7A639A9A: 1200, #"BH spectre",
	0x3C7C08FB: 3000, #"BH purifier",
	0xCD5A5360: 5000, #"BH redeemer",
	0x7D560AEC: 1500, #"BH emissary",

	0x6753D4CA: 1500, #"MoK crane",
	0xBDEA92DF: 500, #"MoK power plant",
	0x84B21B76: 500, #"MoK hand of nod",
	0x8161F095: 600, #"MoK shredder turrets",
	0x8ADF6801: 1500, #"MoK secret shrine",
	0x40DCA116: 3000, #"MoK ref.",
	0xE6D4B65C: 2000, #"MoK factory",
	0xC6999B8E: 1500, #"MoK operation center",
	0x8E42292A: 1000, #"MoK air tower",
	0xF79AF4E3: 4000, #"MoK tech center",
	0xF2A73707: 3000, #"MoK Redeemer eng. fac.",
	0xD5326C9E: 3000, #"MoK tib. chem. plant",
	0x3FC7B8E4: 1200, #"MoK laser turrets",
	0x9D52F3D7: 800, #"MoK SAM turrets",
	0x17D5CAAA: 500, #"MoK silo",
	0x13517F79: 1000, #"MoK voice of Kane",
	0x7CADE3A3: 500, #"MoK disruption tower",
	0x483EAEC0: 1800, #"MoK obelisk of light",
	0xA12474B6: 5000, #"MoK temple of Nod",
	0x75F7ECE5: 500, #"MoK support air tower",

	0x23E82509: 700, #"MoK venom",
	0x393E446C: 1800, #"MoK vertigo",
	0xD5BE6F6C: 500, #"MoK awakened",
	0x020126F6: 400, #"MoK mil. rocket",
	0xA6A2C1D4: 500, #"MoK saboteur",
	0x6093B1BE: 800, #"MoK fanatics",
	0xE6E24EF7: 900, #"MoK tiberium trooper",
	0x6AEA240A: 800, #"MoK shadow team",
	0xB27DDF67: 1200, #"MoK enlightened",
	0x406C94AC: 2000, #"MoK commando",
	0x1DAE1C47: 600, #"MoK attack bike",
	0xE3C841B0: 400, #"MoK buggy",
	0x1B44D6AE: 800, #"MoK scorpion",
	0xC3785BFE: 1400, #"MoK harvester",
	0xB3847303: 2500, #"MoK MCV",
	0x3000821A: 900, #"MoK reckoner",
	0x3D143A57: 1000, #"MoK beam cannon",
	0x1025B90B: 1500, #"MoK stealth tank",
	0x9A533FC7: 1200, #"MoK spectre",
	0xD53D8ABF: 2200, #"MoK avatar",
	0x711A18DF: 5000, #"MoK redeemer",
	0xBDC39D7D: 1500, #"MoK emissary",

	0x95A33CC6: 600, #"Sc power plant",
	0x0CA58AEF: 3000, #"Sc ref.",
	0x929BD6C1: 600, #"Sc barracks",
	0xFEFD8CB5: 200, #"Sc factory",
	0xEEBC2492: 1500, #"Sc nerve center",
	0x468981C5: 1000, #"Sc gravity stabilizer",
	0xC1AFF92C: 1200, #"Sc stasis chamber",
	0x951B67BA: 4000, #"Sc tech center",
	0xE315D4B3: 3000, #"Sc signal transmitter",
	0x550E8876: 1500, #"Sc crane",
	0x23BE7BC2: 3000, #"Sc warp chasm",
	0x0416A92F: 600, #"Sc buzzer hive",
	0xF4B32C4E: 1200, #"Sc photon cannon",
	0xB6046563: 800, #"Sc plasma battery",
	0xDFCF8D47: 1500, #"Sc growth accelerator",
	0x425D00A4: 1500, #"Sc storm column",
	0x384EA3E7: 5000, #"Sc rift generator",

	0x8E2679EF: 200, #"Sc buzzer",
	0x2B9428D0: 300, #"Sc disint.",
	0xAA95429D: 500, #"Sc assimiliator",
	0x6495F509: 800, #"Sc shock trooper",
	0x32EA13B3: 1200, #"Sc ravager",
	0xF601EB6C: 2500, #"Sc master mind",
	0x01A54C1B: 700, #"Sc gunwalker",
	0xB8802763: 800, #"Sc seeker",
	0x14E34DE2: 1400, #"Sc harvester",
	0xAF991372: 1400, #"Sc devouer",
	0x77A0E8A9: 1000, #"Sc corrupter",
	0xE2D7C037: 3000, #"Sc tripod",
	0x0D396F28: 1400, #"Sc mechapede",
	0x1D137C85: 5000, #"Sc hexapod",
	0x30E33C29: 3000, #"Sc drone ship",
	0xF6E707D5: 1500, #"Sc storm rider",
	0x42E35730: 2400, #"Sc devastator warship",
	0x14EACF09: 3000, #"Sc carrier",
	0x4B93BEEC: 1500, #"Sc explorer",

	0x3CDBD279: 600, #"R17 power plant",
	0x7E291858: 3000, #"R17 ref.",
	0x38A4A9E0: 600, #"R17 barracks",
	0x9A917351: 2000, #"R17 factory",
	0xEFB4E2C0: 1500, #"R17 nerve center",
	0x3A64AE56: 1000, #"R17 gravity stabilizer",
	0xEB2D33E3: 1200, #"R17 stasis chamber",
	0xDFDD1DA9: 4000, #"R17 tech center",
	0x0C371C2A: 3000, #"R17 signal transmitter",
	0x3400D06F: 1500, #"R17 crane",
	0x589D2B2B: 3000, #"R17 warp chasm",
	0x27C3413C: 600, #"R17 buzzer hive",
	0xBA9657C9: 1200 ,#"R17 photon cannon",
	0x0FD56363: 800, #"R17 plasma battery",
	0xDBE925A9: 1500, #"R17 growth accelerator",
	0x6862DB83: 1500, #"R17 storm column",
	0xA503835E: 5000, #"R17 rift generator",

	# R17 buzzer, disint, assimiliators are shared with Scrin.
	0x40241AC3: 800, #"R17 shock trooper",
	0x7F2D0EF5: 1200, #"R17 ravager",
	0x7FCCFDE3: 700, #"R17 shard walker",
	0xDB2B7D2F: 800, #"R17 seeker",
	0xC37F7227: 1400, #"R17 harvester",
	0x416EFDFF: 1400, #"R17 devouer",
	0xB187F87A: 1000, #"R17 corrupter",
	0x4DD96105: 3000, #"R17 tripod",
	0x0F108542: 1400, #"R17 mechapede",
	0x146C2890: 5000, #"R17 hexapod",
	0xEECD3E80: 3000, #"R17 drone ship",
	0x1DF82E16: 1500, #"R17 storm rider",
	0xF3E8F14F: 1500, #"R17 explorer",

	0x1F633A81: 600, #"T59 power plant",
	0xF4E73A51: 3000, #"T59 ref.",
	0xAD3B9CCD: 600, #"T59 barracks",
	0x5743BC5C: 2000, #"T59 factory",
	0x74F0DB70: 1500, #"T59 nerve center",
	0x714AFABF: 1000, #"T59 gravity stabilizer",
	0x73D55ACC: 1200, #"T59 stasis chamber",
	0x9AF79C8D: 4000, #"T59 tech center",
	0x3E28732D: 3000, #"T59 signal transmitter",
	0xDE06E6CF: 1500, #"T59 crane",
	0xA69624CC: 3000, #"T59 warp chasm",
	0xD56430FB: 600, #"T59 buzzer hive",
	0x6AA8919A: 1200, #"T59 photon cannon",
	0x385D26A8: 800, #"T59 plasma battery",
	0x730EA95B: 1500, #"T59 growth accelerator",
	0x62697C2C: 1500, #"T59 storm column",
	0x4379775A: 5000, #"T59 rift generator",

	# buzzer is shared with scrin
	0x00240FB1: 300, #"T59 disint.",
	0xDFDE337F: 500, #"T59 assimiliators",
	0x4803957E: 800, #"T59 shock trooper",
	0xC46CECA2: 1000, #"T59 cultist",
	0x72A9F5D5: 1200, #"T59 ravager",
	0x5F8004DF: 2500, #"T59 progidy",
	0x51430053: 700, #"T59 gunwalker",
	0x7296891C: 800, #"T59 seeker",
	0x998395BF: 1400, #"T59 harvester",
	0x91B5B69D: 1000, #"T59 corrupter",
	0x748C4C22: 3000, #"T59 tripod",
	0x7F3CEB99: 1400, #"T59 mechapede",
	0xA4FD281B: 5000, #"T59 hexapod",
	0x292DB333: 3000, #"T59 drone ship",
	0xECA08561: 1500, #"T59 storm rider",
	0xB15E754C: 2400, #"T59 devastator warship",
	0x0F71843C: 3000, #"T59 carrier",
	0x8C82B86C: 1500, #"T59 explorer",

	0xDCD2D288: 1500, #"ZCM crane",
	0x34E71EC6: 800, #"ZCM power plant",
	0xBA62677D: 3000, #"ZCM ref",
	0x502F0AAA: 600, #"ZCM watch tower",
	0x50EB58F7: 500, #"ZCM barracks",
	0xD2E0D294: 1500, #"ZCM command post",
	0x8F222FF5: 2000, #"ZCM factory",
	0xF2B92697: 1000, #"ZCM airfield",
	0x7D372A88: 1000, #"ZCM armory",
	0xD2CA793C: 500, #"ZCM silo",
	0x622F00EB: 1200, #"ZCM guardian cannon",
	0xF689DAA0: 500, #"ZCM support airfield",
	0xE76FAF0F: 4000, #"ZCM tech center",
	0x1F54F6C2: 3000, #"ZCM space uplink",
	0xEBDE1709: 3000, #"ZCM rec. hub",
	0xF459C486: 800, #"ZCM AA battery",
	0x089DA349: 2000, #"ZCM sonic emitter",

	0x0AC645E3: 300, #"ZCM riflemen",
	0x17A153BA: 400, #"ZCM missile",
	0x009260E6: 500, #"ZCM engineer",
	0xC43CF79F: 800, #"ZCM grenadier",
	0xB724E036: 1000, #"ZCM sniper",
	0x2FA51492: 2000, #"ZCM commando",
	0x0D213112: 1300, #"ZCM zone raider",
	0xFAA68740: 700, #"ZCM pitbull",
	0xFA477EAA: 1000, #"ZCM predator",
	0x42D55831: 700, #"ZCM apc",
	0xAD5F0217: 1600, #"ZCM harvester",
	0xF714BBD3: 2500, #"ZCM MCV",
	0x64BCB106: 1600, #"ZCM shatterer",
	0xC23B3A15: 1000, #"ZCM sling shot",
	0x330CEC90: 2000, #"ZCM rig",
	0xAE73138F: 2500, #"ZCM mammoth tank",
	0x5A6044BC: 5000, #"ZCM MARV",
	0x6FCB2318: 1500, #"ZCM hammerhead",
	0x12E1C8C8: 1500, #"ZCM firehawk",
	0x37F0A5F5: 1500, #"ZCM orca",
	0xFD890B01: 1500, #"ZCM surveyer",
}



AFLD_UNITS = [
	0x6AA59D16, # Nod vertigo
	0x393E446C, # MoK vertigo
	0xB587039F, # GDI orca
	0xB3363EA3, # GDI firehawk
	0x6BD7B8AB, # ST orca
	0x42D55831, # ST FH
	0xFAA68740, # Zorca
	0x12E1C8C8, # ZCM FH
	0xF6E707D5, # SC storm rider
	0x1DF82E16, # R17 storm rider
	0xECA08561, # T59 storm rider
]



class KWChunk( chunks.Chunk ) :

	def is_bo_cmd( self, cmd ) :
		return cmd.cmd_id in BO_COMMANDS

	def is_known_cmd( self, cmd ) :
		return cmd.cmd_id in CMDNAMES

	def resolve_known( self, cmd ) :
		return CMDNAMES[ cmd.cmd_id ]

	def decode_cmd( self, cmd ) :
		if cmd.cmd_id == 0x31 :
			cmd.decode_placedown_cmd( UNITNAMES, UNITCOST, FREEUNITS )
		elif cmd.cmd_id == 0x26 :
			cmd.decode_skill_targetless( POWERNAMES, POWERCOST )
		elif cmd.cmd_id == 0x27 :
			cmd.decode_skill_xy( POWERNAMES, POWERCOST )
		elif cmd.cmd_id == 0x28 :
			cmd.decode_skill_target( POWERNAMES, POWERCOST )
		elif cmd.cmd_id == 0x2B :
			cmd.decode_upgrade_cmd( UPGRADENAMES, UPGRADECOST )
		elif cmd.cmd_id == 0x2D :
			cmd.decode_queue_cmd( UNITNAMES, AFLD_UNITS, UNITCOST )
		elif cmd.cmd_id == 0x2E :
			cmd.decode_hold_cmd( UNITNAMES )
		elif cmd.cmd_id == 0x8A :
			cmd.decode_skill_2xy( POWERNAMES, POWERCOST )
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



	# The "legacy" split command.
	def split_one_cmd( self, f ) :
		cmd = chunks.Command()
		# Was old split_command( self, f, ncmd ) :
		cmd.cmd_id = read_byte( f )
		player_id = read_byte( f )
		cmd.player_id = int( player_id / 8 ) - 3 # 3 for KW.  for RA3, it should be 2.
		# Probably, that offset must be that neutral factions. (initial spike owners)

		if not cmd.cmd_id in CMDLENS :
			print( "Warning: unknown command. FF creeping.", file=sys.stderr )
			chunks.Splitter.split_ff_crawl( cmd, f ) # same as 0x00, creep until FF.
			return

		cmdlen = CMDLENS[ cmd.cmd_id ]

		if cmdlen > 0 :
			chunks.Splitter.split_fixed_len(cmd, f, cmdlen )
		# more var len commands
		elif cmdlen < 0 :
			# var len cmds!
			chunks.Splitter.split_var_len( cmd, f, cmdlen )
		else :
			if cmd.cmd_id <= 0x03 or cmd.cmd_id >= 0xFA :
				# group designation command.
				assert cmd.cmd_id >= 0
				assert cmd.cmd_id <= 0xFF
				chunks.Splitter.split_ff_crawl( cmd, f )
			elif 0x04 <= cmd.cmd_id and cmd.cmd_id <= 0x0D :
				# group selection command.
				# I usually get 0x0A 0x?? 0xFF (length=3).
				# I sometimes get (rarely) 0x0A 0x00 0x00 0xFF
				chunks.Splitter.split_ff_crawl( cmd, f ) # same as 0x00, creep until FF.

			elif cmd.cmd_id == 0x0E :
				chunks.Splitter.split_ff_crawl( cmd, f ) # same as 0x00, creep until FF.
			elif cmd.cmd_id == 0x1F :
				chunks.Splitter.split_ff_crawl( cmd, f ) # same as 0x00, creep until FF.
			elif cmd.cmd_id == 0x2D :
				#print( "split_cmd.ncmd:", ncmd )
				chunks.Splitter.split_production_cmd( cmd, f )
			elif cmd.cmd_id == 0x28 :
				chunks.Splitter.split_skill_target( cmd, f )
			elif cmd.cmd_id == 0x2C :
				chunks.Splitter.split_0x2c( cmd, f )
			elif cmd.cmd_id == 0x31 :
				chunks.Splitter.split_placedown_cmd( cmd, f )
			elif cmd.cmd_id == 0x36 :
				chunks.Splitter.split_var_len2( cmd, f, 1, 4 )
			elif cmd.cmd_id == 0x7F :
				chunks.Splitter.split_ff_crawl( cmd, f ) # same as 0x00, creep until FF.
			elif cmd.cmd_id == 0x8B :
				chunks.Splitter.split_chunk1_uuid( cmd, f )
			else :
				print( "Unhandled command:" )
				print( "0x%02X" % cmd.cmd_id )
				print_bytes( f.getbuffer() )
				print()
				return None

		return cmd



	# The "old" command splitter code, essentially the method in the cpp code by R. Schneider.
	def fix_mismatch( self ) :
		f = io.BytesIO( self.payload )

		self.commands = []
		for i in range( self.ncmd ) :
			cmd = self.split_one_cmd( f )
			if not cmd :
				self.commands = [] # Let's not have anything... it is meaningless.
				break

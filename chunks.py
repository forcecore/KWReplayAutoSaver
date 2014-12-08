#!/usr/bin/python3
# coding: utf8

###
### http://www.gamereplays.org/community/index.php?showtopic=706067&st=0&p=7863248&#entry7863248
### The decoding of the replays format is credited to R Schneider.
###

import struct # bin file enc/dec
import sys
import re
import io
import codecs
import datetime
import time
from kwreplay import KWReplay, read_byte, read_uint32, read_float, \
	read_cstr, time_code2str, read_tb_str

CMDLENS = {
	0x00: 0, # unknown + var len.
	0x01: -2,
	0x02: -2,
	0x03: -2,
	0x04: -2,
	0x05: -2,
	0x06: -2,
	0x07: -2,
	0x08: -2,
	0x09: -2,
	0x0A: 0, # short + no len info... assume 0x00
	0x0B: -2,
	0x0C: -2,
	0x0D: -2,
	0x0E: 0, # really rare command... short+nolen. assume 0x00
	0x0F: -2,
	0x10: -2,
	0x11: -2,
	0x12: -2,
	0x17: -2,

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
	0x7F: 12,
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
	0xFA: -2,
	0xFB: -2,
	0xFC: -2,
	0xFD: -2,
	0xFE: -2,
	0xFF: -2
}

CMDNAMES = {
	0x2B: "Upgrade",
	0x2D: "Unit exit production building",
	0x26: "Skill (targetless)",
	0x27: "Skill",
	0x28: "Skill (with target unit)",
	0x31: "Place down building",
	0x34: "sell?",
	0x3D: "attack?",
	0x61: "30s heartbeat",
	0x8F: "'scroll'",
	0xF5: "drag selection box and/or select units/structures",
	0xF8: "left click"
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

	0xA1819100: "Decoy army",
	0x7668A300: "Radar jamming", # probably incorrect.
	0xF1630D20: "Radar jamming",
	0xC21CA400: "Laser fence",
	0x34EAD100: "Nod Stealth field",
	0x7DBB9C00: "MoK Stealth field",
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
	0xA0E6D800: "Wormhole",
}

UPGRADENAMES = {
	0x60737ED1: "GDI power plant",
	0xB44E9A3B: "ST power plant",
	0xA73AE932: "ZCM power plant",
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
	0x7DC1C5B4: "Reactive armor",
	0xCA8D43C1: "Tib resistant armor",
	0xE5C2A0EC: "Zorca sensor pod",
	0x5F9C9069: "Ceramic armor",
	0x6FB1DF0F: "Zone raider scanner pack",

	0x58B082E5: "Nod power plant",
	0xE0DD89F8: "BH power plant",
	0x6C96D5F1: "MoK power plant",
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

	0x3409F073: "Scrin power plant",
	0xA98BDFE4: "R17 power plant",
	0x9E936CEA: "T59 power plant",
	0x269AF75A: "Attenuated shield",
	0x023714AD: "Blink pack",
	0x9B19AB1B: "Plasma disc launcher",
	0xE5A3374C: "Force shield generator",
	0x230E8321: "Shard launcher",
	0x673B860F: "R17 attenuated shield",
	0x88B36F31: "R17 force shield generator",
	0x62495112: "Blue shards",
	0x70427973: "Conversion beam cap.",
	0xA921E313: "Advanced articulators",
	0x4FCCDACF: "Traveller engine",
}

UNITNAMES = {
	0xA333C6A8: "Nod power plant",
	0x72407A4F: "Nod barracks",
	0xB5D275B6: "Nod refinery",
	0x22943F1D: "Nod factory",
	0x4E57EF4B: "Nod shredder turret",
	0xA46AA481: "Nod operations center",
	0xD5C63044: "Nod air tower",
	0x989B10EB: "Nod secret shrine",
	0xE630F233: "Nod tech center",
	0x8F61720F: "Nod tib chem plant",
	0x667CDE9C: "Nod crane",
	0xA78E52C1: "Nod redeemer eng. fac.",
	0xC04FB821: "Nod laser turret",
	0x821322AD: "Nod sam turret",
	0x5593CBD2: "Nod silo",
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
	0xE1659649: "GDI command center",
	0x115E0E31: "GDI armory",
	0x9ABD65AC: "GDI factory",
	0x8314C7A0: "GDI airfield",
	0x33B40C6F: "GDI tech center",
	0x51474781: "GDI rec. hub",
	0x8136F6F6: "GDI space uplink",
	0x3EA580F4: "GDI watch tower",
	0x3554B096: "GDI guardian cannon",
	0xAD54632A: "GDI AA turret",
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
	0x2144BD64: "GDI sonic emitter tank",
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
	0x296BE097: "ST command center",
	0xA0426848: "ST crane",
	0xEEAC5E37: "ST airfield",
	0x40A17081: "ST factory",
	0x0F640F30: "ST space uplink",
	0xEABA4298: "ST rec. hub",
	0x6C309FAB: "ST tech center",
	0x358EB5E4: "ST guardian cannon",
	0x5C80259B: "ST AA turret",
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
	0xD2E0D294: "ZCM command center",
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
	0xFAA68740: "ZCM pitbull",
	0xFA477EAA: "ZCM predator",
	0x42D55831: "ZCM apc",
	0xAD5F0217: "ZCM harvester",
	0xF714BBD3: "ZCM MCV",
	0x64BCB106: "ZCM sonic emitter tank",
	0xC23B3A15: "ZCM sling shot",
	0x330CEC90: "ZCM rig",
	0xAE73138F: "ZCM mammoth tank",
	0x5A6044BC: "ZCM MARV",
	0x6FCB2318: "ZCM hammerhead",
	0x12E1C8C8: "ZCM firehawk",
	0x37F0A5F5: "ZCM orca",
	0xFD890B01: "ZCM surveyer",
}



def byte2int( byte ) :
	return struct.unpack( 'B', byte )[0]



def uint42int( bys ) :
	return struct.unpack( 'I', bys )[ 0 ]



def uint42float( bys ) :
	return struct.unpack( 'f', bys )[ 0 ]



def print_bytes( bys ) :
	i = 0
	for b in bys :
		print( "%02X " % b, end="" )
		i += 1
		if i >= 16 :
			i = 0
			print()
	print()


class Command :

	verbose = False     # manually make this True if you want to debug...

	def __init__( self ) :
		self.cmd_id = 0
		self.player_id = 0 # dunno if it really is player_id.
		self.payload = None # raw command

		# these are dynamically alloced.
		# self.substructures = []

	def split_fixed_len( self, f, cmdlen ) :
		# that cmdlen includes the terminator and cmd code+0xff Thus, -3.
		cmdlen -= 3
		self.payload = f.read( cmdlen )

		if Command.verbose :
			print( "fixed len. payload:" )
			print_bytes( self.payload )
			print()



	def split_var_len( self, f, cmdlen, ncmd ) :
		payload = f.getbuffer() # cursor unaffected buffer, w00t.
		opos = f.tell()

		#if Command.verbose :
		#	print( "Varlen input:" )
		#	print( "Len info @:", cmdlen )
		#	print( "Cheat: ", end="" )
		#	print_bytes( payload )

		pos = f.tell() - 2 + (-cmdlen)

		while payload[ pos ] != 0xFF and pos < len( payload ) :
			adv = ( payload[ pos ] >> 4 ) + 1
			pos += 4*adv + 1

		read_cnt = pos-opos
		self.payload = f.read( read_cnt )

		if Command.verbose :
			print( "cmd_id: 0x%02X" % self.cmd_id )
			print( "spit_var_len.ncmd:", ncmd )
			print( "cheat: ", end="" )
			print_bytes( payload )
			print( "opos ~ pos:", opos, pos )
			print( "read", read_cnt, "bytes" )
			print( "Read varlen command: ", end="" )
			print_bytes( self.payload )
			print()



	def split_chunk1_uuid( self, f ) :
		cheat = f.getbuffer()

		f.read( 1 )
		l = read_byte( f )
		s1 = read_cstr( f, l )

		if Command.verbose :
			print_bytes( cheat )
			print( "chunk thingy:" )
			print( "0x%02X" % self.cmd_id )
			print( "cheat:" )
			print()
			print( "s1:", s1 )

		f.read( 1 ) # skip
		l = read_byte( f )
		if l > 0 :
			s2 = read_tb_str( f, length=l )
			#buf = f.read( 2 ) # terminating two bytes of 0.
			if Command.verbose :
				print( "s2:", s2 )
			#print( "term0: %02X %02X" % ( buf[0], buf[1] ) )

		buf = f.read( 5 ) # consume til 0xFF?
		#print( "what is left:" )
		#print_bytes( buf )



	def split_var_len2( self, f, cnt_skip, skip_after ) :
		dunno = f.read( cnt_skip )
		l = read_byte( f )
		for i in range( l ) :
			f.read( 4 )
		f.read( skip_after ) # consume

	def split_0x2c( self, f ) :
		self.split_var_len2( f, 5, 4 )



	def split_0x00( self, f ) :
		# 00 42 03 6C 1A 00 00 FF (8)

		# 00 2A 33 9F 16 00 00 CC 16 00 00 A6 17 00 00 8A
		# 17 00 00 FF (20)

		# 00 32 13 63 05 00 00 69 05 00 00 FF (12)

		# 00 22 33 51 08 00 00 9A 07 00 00 85 07 00 00 5F
		# 07 00 00 FF (20)

		# From what I have observed, there seems to be no length rule.
		# It's not a null terminated string either.
		# Lots of periodic 00 00 ... hmm...

		# For now, I'll just seek FF, it seems to be the only
		# feasible way, as there is no length info.

		buf = f.getbuffer()
		pos = f.tell()
		end = pos
		while buf[ end ] != 0xFF :
			end += 1

		self.payload = f.read( end-pos )



	def split_command( self, f, ncmd ) :
		self.cmd_id = read_byte( f )
		player_id = read_byte( f )
		self.player_id = int( player_id / 8 ) - 3 # 3 for KW.  for RA3, it should be 2.
		# Probably, that offset must be that neutral factions. (initial spike owners)

		if not self.cmd_id in CMDLENS :
			print( "Unknown command:" )
			print( "0x%02X" % self.cmd_id )
			print_bytes( f.getbuffer() )
			print()
			assert 0

		cmdlen = CMDLENS[ self.cmd_id ]

		if cmdlen > 0 :
			self.split_fixed_len( f, cmdlen )
		# more var len commands
		elif cmdlen < 0 :
			# var len cmds!
			self.split_var_len( f, cmdlen, ncmd )
		else :
			if self.cmd_id == 0x00 :
				self.split_0x00( f )
			elif self.cmd_id == 0x0A :
				# I usually get 0x0A 0x?? 0xFF (length=3).
				# I sometimes get (rarely) 0x0A 0x00 0x00 0xFF
				self.split_0x00( f ) # same as 0x00, creep until FF.
			elif self.cmd_id == 0x0E :
				self.split_0x00( f ) # same as 0x00, creep until FF.
			elif self.cmd_id == 0x2D :
				#print( "split_cmd.ncmd:", ncmd )
				self.split_production_cmd( f )
			elif self.cmd_id == 0x28 :
				self.split_skill_target( f )
			elif self.cmd_id == 0x2C :
				self.split_0x2c( f )
			elif self.cmd_id == 0x31 :
				self.split_placedown_cmd( f )
			elif self.cmd_id == 0x36 :
				self.split_var_len2( f, 1, 4 )
			elif self.cmd_id == 0x8B :
				self.split_chunk1_uuid( f )
			else :
				print( "Unhandled command:" )
				print( "0x%02X" % self.cmd_id )
				print_bytes( f.getbuffer() )
				print()
				assert 0



	def split_production_cmd( self, f ) :
		# either short or long...
		# length 8 or length 26, it seems, refering to cnc3reader_impl.cpp.

		cheat = f.getbuffer()
	
		if Command.verbose :
			print( "Production splitting" )
			print( "0x%02X" % self.cmd_id )
			print( "cheat:" )
			print_bytes( cheat )
			print()

		if cheat[ f.tell() ] == 0xFF :
			self.payload = None # stub command can happen... omg
		elif cheat[ f.tell() + 5 ] == 0xFF :
			self.payload = f.read( 5 )
		else :
			self.payload = f.read( 23 )



	def decode_production_cmd( self ) :
		# either short or long...
		# length 8 or length 26, it seems, refering to cnc3reader_impl.cpp.

		if Command.verbose :
			print( "Production decoding" )
			print_bytes( self.payload )
		data = self.payload
	
		if len( data ) == 5 :
			print( "Not production. GG from this player?" )
		else :
			produced_by = uint42int( data[ 1:5 ] ) # probably.
			produced = uint42int( data[ 8:12 ] ) # This one is pretty sure
			cnt = data[ 17 ]

			if cnt > 0 :
				print( "5x ", end="" )
			if produced in UNITNAMES :
				print( "Production of %s from 0x%08X" % (UNITNAMES[produced], produced_by) )
			else :
				print( "Production of 0x%08X from 0x%08X" % (produced, produced_by) )
			print()



	# this skill targets GROUND.
	def decode_skill_xy( self ) :
		data = self.payload

		if Command.verbose :
			print( "decode_skill_xy" )
			print_bytes( data )

		x = uint42float( data[ 6:10] )
		y = uint42float( data[ 10:14] )
		power = uint42int( data[ 0:4 ] )

		if power in POWERNAMES :
			print( "Skill use %s at (%f, %f)" % (POWERNAMES[power], x, y) )
		else :
			print( "Skill use 0x%08X at (%f, %f)" % (power, x, y) )



	# this skill targets GROUND, with two positions.
	# Obviously, only wormhole does that.
	def decode_skill_2xy( self ) :
		data = self.payload

		if Command.verbose :
			print( "decode_skill_2xy" )
			print_bytes( data )

		x1 = uint42float( data[ 16:20] )
		y1 = uint42float( data[ 20:24] )
		x2 = uint42float( data[ 28:32] )
		y2 = uint42float( data[ 32:36] )
		power = uint42int( data[ 0:4 ] )

		if power in POWERNAMES :
			print( "Skill use %s at (%f, %f)-(%f, %f)" % (POWERNAMES[power], x1, y1, x2, y2) )
		else :
			print( "Skill use 0x%08X at (%f, %f)-(%f, %f)" % (power, x1, y1, x2, y2) )



	def decode_skill_targetless( self ) :
		data = self.payload

		if Command.verbose :
			print( "decode_skill_targetless" )
			print_bytes( data )

		power = uint42int( data[ 0:4 ] )
		# dunno about target, but it is certain that this is only used on walling
		# structures -_-

		if power in POWERNAMES :
			print( "Skill use %s" % POWERNAMES[power] )
		else :
			print( "Skill use 0x%08X" % power )



	# this skill targets one exact unit.
	# sonic/laser fence that is.
	def split_skill_target( self, f ) :
		buf = f.getbuffer()
		cnt = buf[ f.tell() + 15 ]
		end = f.tell() + 4*(cnt+1) + 30
		self.payload = f.read( end - f.tell() - 1 )

		if Command.verbose :
			print( "split_skill_target" )
			print( "0x%02X" % self.cmd_id )
			print( "cheat: ", end="" )
			print_bytes( buf )
			print( "end:", end )
			print( "payload:", end="" )
			print_bytes( self.payload )
			print()



	# this skill targets GROUND.
	def decode_skill_target( self ) :
		data = self.payload

		if Command.verbose :
			print( "decode_skill_target" )
			print_bytes( data )

		power = uint42int( data[ 0:4 ] )
		# dunno about target, but it is certain that this is only used on walling
		# structures -_-

		if power in POWERNAMES :
			print( "Skill use %s" % POWERNAMES[power] )
		else :
			print( "Skill use 0x%08X" % power )



	def decode_upgrade_cmd( self ) :
		data = self.payload

		if Command.verbose :
			print( "decode_upgrade_cmd" )
			print_bytes( data )

		upgrade = uint42int( data[1:5] )
		if upgrade in UPGRADENAMES :
			print( "Upgrade purchase of %s" % UPGRADENAMES[upgrade] )
		else :
			print( "Upgrade purchase of 0x%08X" % upgrade )
	


	def split_placedown_cmd( self, f ) :
		payload = io.BytesIO()
		buf = f.read( 10 ) # dunno what this is.
		payload.write( buf )
		substructure_cnt = f.read( 1 )
		payload.write( substructure_cnt )
		substructure_cnt = byte2int( substructure_cnt )
		payload.write( f.read( 18 * substructure_cnt ) )
		payload.write( f.read( 3 ) ) # more unknown stuff

		self.payload = payload.getbuffer()



	def decode_placedown_cmd( self ) :
		if Command.verbose :
			print( "PLACE DOWN" )
			print_bytes( self.payload )

		data = self.payload
		building_type = uint42int( data[6:10] )
		substructure_cnt = data[10]
		self.substructures = []

		pos = 11
		for i in range( substructure_cnt ) :
			pos += 4
			x = uint42float( data[pos:pos+4] )
			pos += 4
			y = uint42float( data[pos:pos+4] )
			pos += 6

		if building_type in UNITNAMES :
			print( "building_type: %s" % UNITNAMES[building_type] )
		else :
			print( "building_type: 0x%08X" % building_type )
		print( "\tLocation: %f, %f" % (x, y) )
		#print( "substructure_cnt:", substructure_cnt )

		# subcomponent ID, x, y, orientation
		# I don't know how 18 bytes are made of...
		# I know x and y. What about the rest of 10 bytes?
		# there should be building orientation... which shoulbe float, 4 bytes.
		# or it sould be one byte? 0~255 enough?

		# For normal buildings, we don't get var length.
		# But for Nod defenses... shredder turrets, laser turrets,
		# SAM turrets... we get multiple coordinates.
		# That's why we get var len commands.
		# The multiplier 18 must be related to coordinates.
		# 8 for 2*4bytes (=2 floats) of x-y coords.
		# or... z coord?! dunno?!

		# old code...
		#unknown = f.read( 10 )
		#l = read_byte( f )
		#more_unknown = f.read( 18*l )
		#cmdlen = 3
		#more_unknown = f.read( 3 )
	


	def print_known( self ) :
		print( "Player" + str( self.player_id ) + ":" )
		if self.cmd_id == 0x31 :
			self.decode_placedown_cmd()
		elif self.cmd_id == 0x26 :
			self.decode_skill_targetless()
		elif self.cmd_id == 0x27 :
			self.decode_skill_xy()
		elif self.cmd_id == 0x28 :
			self.decode_skill_target()
		elif self.cmd_id == 0x2B :
			self.decode_upgrade_cmd()
		elif self.cmd_id == 0x2D :
			self.decode_production_cmd()
		elif self.cmd_id == 0x8A :
			self.decode_skill_2xy()
		print()



class Chunk :
	def __init__( self ) :
		self.time_code = 0
		self.ty = 0
		self.size = 0
		self.data = None

		self.time = 0 # decoded time (str)

		# for ty == 1
		self.ncmd = 0
		self.payload = None # undecoded payload
		self.commands = []

		# for ty == 2
		# player number, index in the player list in the plain-text game info
		self.player_number = 0
		self.time_code_payload = 0 # another timecode, in the payload.
		self.ty2_payload = None
	
	def split( self ) :
		if self.ty != 1 :
			# I only care about game affecting stuff.
			return

		f = io.BytesIO( self.data )
		one = read_byte( f )
		assert one == 1
		if self.data[ -1 ] != 0xFF :
			if Command.verbose :
				print( "Some unknown command format:" )
				print( "data:" )
				print_bytes( self.data )
				print()
		else :
			self.ncmd = read_uint32( f )
			self.payload = f.read()
			self.split_commands( self.ncmd, self.payload )
			assert len( self.commands ) == self.ncmd



	# Currently, I can't decode very well.
	# I only extract what I can... T.T
	def split_commands( self, ncmd, payload ) :
		f = io.BytesIO( payload )
		#print( "COMMANDS payload:", payload )

		for i in range( ncmd ) :
			c = Command()
			self.commands.append( c )
			c.split_command( f, ncmd )

			terminator = read_byte( f )
			#terminator = 0xFF
			if terminator != 0xFF :
				print( "Decode error" )
				print( "ncmd:", ncmd )
				print( "cmd_id: 0x%02X" % c.cmd_id )
				print( "Payload:" )
				print_bytes( payload )
				print( "TERMINATOR: 0x%02X" % terminator )
				print( f.read() )
			assert terminator == 0xFF



	def print( self ) :
		self.decode()

		if self.ty == 1 :
			if cmd_id in CMDNAMES :
				print( "---" )
				print( CMDNAMES[ cmd_id ] )
				print( "---" )
			print( "player_id:", player_id )
			print( "cmd_id: 0x%X" % cmd_id )

			print( "time:", self.time )
			print( "ncmd:", self.ncmd )
			print( "payload:" )
			for i in range( len( self.payload ) ) :
				print( "0x%02X" % self.payload[i], end=" " )
				if i % 16 == 0 :
					print()
			print()
			print()
			print()
		elif self.ty == 2 :
			#print( "Camera data." )
			pass
			#print( "\tplayer#:", self.player_number )
			#print( "\ttimecode:", self.time_code_payload )
		else :
			# From eareplay.html:
			# Chunk types 3 and 4 only appear to be present in replays with a
			# commentary track, and it seems that type 3 contains the audio
			# data and type 4 the telestrator data.
			pass
			#print( "type:", self.ty )
			#print( "size:", self.size )
			#print( "data:", self.data )
	
	def has_known( self ) :
		for cmd in self.commands :
			if cmd.cmd_id in [ 0x31, 0x26, 0x27, 0x28, 0x2B, 0x2D, 0x8A ] :
				return True
		return False
	
	def print_known( self ) :
		if self.ty == 1 :
			if not self.has_known() :
				return

			time = time_code2str( self.time_code/15 )
			print( "time:", time )

			for cmd in self.commands :
				cmd.print_known()

		# I don't care about these!!
		#elif self.ty == 2 :
		#	f = io.BytesIO( self.data )
		#	# This is camera data or heart beat data.
		#	# I'll not try too hard to decode this.
		#	one = read_byte( f ) # should be ==1
		#	zero = read_byte( f ) # should be ==0
		#	self.player_number = read_uint32( f ) # uint32
		#	self.time_code_payload = read_uint32( f ) # time code...
		#	self.ty2_payload = f.read() # the payload
	
	

class ReplayBody :
	def __init__( self, f ) :
		self.chunks = []
		self.loadFromStream( f )
	
	def read_chunk( self, f ) :
		chunk = Chunk()
		chunk.time_code = read_uint32( f )
		if chunk.time_code == 0x7FFFFFFF :
			return None

		chunk.ty = read_byte( f )
		chunk.size = read_uint32( f )
		chunk.data = f.read( chunk.size )
		unknown = read_uint32( f ) # mostly 0, but not always.

		# chunk debugging stuff:
		#print( "chunk pos: 0x%08X" % f.tell() )
		#print( "read_chunk.time_code: 0x%08X" % chunk.time_code )
		#print( "read_chunk.ty: 0x%02X" % chunk.ty )
		#print( "read_chunk.size:", chunk.size )
		#print( "chunk.data:" )
		#print_bytes( chunk.data )
		#print()
	
		chunk.split()
		return chunk
	
	def loadFromStream( self, f ) :
		while True :
			chunk = self.read_chunk( f )
			if chunk == None :
				break
			self.chunks.append( chunk )
	
	def print_known( self ) :
		for chunk in self.chunks :
			chunk.print_known()



class KWReplayWithCommands( KWReplay ) :
	def __init__( self, fname=None, verbose=False ) :
		self.replay_body = None

		# self.footer_str ... useless
		self.final_time_code = 0
		self.footer_data = None # I have no idea what this is. I'll keep it as it is.
		#self.footer_length = 0

		super().__init__( fname=fname, verbose=verbose )

	def read_footer( self, f ) :
		footer_str = read_cstr( f, self.FOOTER_MAGIC_SIZE )
		self.final_time_code = read_uint32( f )
		self.footer_data = f.read()
		if self.verbose :
			print( "footer_str:", footer_str )
			print( "final_time_code:", self.final_time_code )
			print( "footer_data:", self.footer_data )
			print()
	
	def loadFromFile( self, fname ) :
		f = open( fname, 'rb' )
		self.loadFromStream( f )
		self.replay_body = ReplayBody( f )
		self.read_footer( f )

		self.replay_body.print_known()

		f.close()



###
###
###
def main() :
	fname = "1.KWReplay"
	if len( sys.argv ) >= 2 :
		fname = sys.argv[1]
	kw = KWReplayWithCommands( fname=fname, verbose=False )
	#kw.replay_body.print_known_chunks()
	#kw = KWReplay()
	#kw.modify_desc( fname, "2.KWReplay", "매치 설명 있음" )
	#kw.modify_desc_inplace( "2.KWReplay", "show me the money 오예" )

if __name__ == "__main__" :
	main()

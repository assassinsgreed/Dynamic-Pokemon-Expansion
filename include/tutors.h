#pragma once

enum MoveTutors
{
	TUTOR00_FIRE_PUNCH,
	TUTOR01_ICE_PUNCH,
	TUTOR02_THUNDER_PUNCH,
	TUTOR03_SNORE,
	TUTOR04_HEAL_BELL,
	TUTOR05_ELECTROWEB,
	TUTOR06_LOW_KICK,
	TUTOR07_UPROAR,
	TUTOR08_BIND,
	TUTOR09_HELPING_HAND,
	TUTOR10_BLOCK,
	TUTOR11_WORRY_SEED,
	TUTOR12_COVET,
	TUTOR13_BUG_BITE,
	TUTOR14_SNATCH,
	TUTOR15_SPITE,
	TUTOR16_AFTER_YOU,
	TUTOR17_SYNTHESIS,
	TUTOR18_SIGNAL_BEAM,
	TUTOR19_GRAVITY,
	TUTOR20_IRON_DEFENSE,
	TUTOR21_TELEKINESIS,
	TUTOR22_MAGNET_RISE,
	TUTOR23_BOUNCE,
	TUTOR24_LAST_RESORT,
	TUTOR25_IRON_HEAD,
	TUTOR26_AQUA_TAIL,
	TUTOR27_PAIN_SPLIT,
	TUTOR28_TAILWIND,
	TUTOR29_ENDEAVOR,
	TUTOR30_ICY_WIND,
	TUTOR31_ZEN_HEADBUTT,
	TUTOR32_SEED_BOMB,
	TUTOR33_LASER_FOCUS,
	TUTOR34_DRAGON_PULSE,
	TUTOR35_DRILL_RUN,
	TUTOR36_MAGIC_COAT,
	TUTOR37_MAGIC_ROOM,
	TUTOR38_WONDER_ROOM,
	TUTOR39_LIQUIDATION,
	TUTOR40_GASTRO_ACID,
	TUTOR41_FOUL_PLAY,
	TUTOR42_SUPER_FANG,
	TUTOR43_OUTRAGE,
	TUTOR44_SKY_ATTACK,
	TUTOR45_THROAT_CHOP,
	TUTOR46_STOMPING_TANTRUM,
	TUTOR47_EARTH_POWER,
	TUTOR48_GUNK_SHOT,
	TUTOR49_DUAL_CHOP,
	TUTOR50_HEAT_WAVE,
	TUTOR51_HYPER_VOICE,
	TUTOR52_SUPERPOWER,
	TUTOR53_GRASS_PLEDGE,
	TUTOR54_FIRE_PLEDGE,
	TUTOR55_WATER_PLEDGE,
	TUTOR56_FRENZY_PLANT,
	TUTOR57_BLAST_BURN,
	TUTOR58_HYDRO_CANNON,
	TUTOR59_NASTY_PLOT,
	TUTOR60_GRASSY_TERRAIN,
	TUTOR61_MISTY_TERRAIN,
	TUTOR62_ELECTRIC_TERRAIN,
	TUTOR63_PSYCHIC_TERRAIN,

//Special Move Tutors - Not in Table
	TUTOR_SPECIAL_DRACO_METEOR,			//64 - Dragon Pokemon
	TUTOR_SPECIAL_SECRET_SWORD,			//65 - Keldeo only
	TUTOR_SPECIAL_RELIC_SONG,			//66 - Meloetta only
	TUTOR_SPECIAL_VOLT_TACKLE,			//67 - Pikachu only
	TUTOR_SPECIAL_DRAGON_ASCENT,		//68 - Rayquaza only
	TUTOR_SPECIAL_THOUSAND_ARROWS,		//69 - Zygarde only
	TUTOR_SPECIAL_THOUSAND_WAVES,		//70 - Zygarde only
	TUTOR_SPECIAL_CORE_ENFORCER,		//71- Zygarde only
	TUTOR_SPECIAL_STEEL_BEAM,			//72 - Steel Pokemon
	TUTOR_SPECIAL_ASSIST,				//73 - Normal Pokemon
	TUTOR_SPECIAL_SECRETPOWER,			//74 - Normal Pokemon
	TUTOR_SPECIAL_PAYDAY,				//75 - Normal Pokemon
	TUTOR_SPECIAL_FIREFANG,				//76 - Fire Pokemon
	TUTOR_SPECIAL_MYSTICALFIRE,			//77 - Fire Pokemon
	TUTOR_SPECIAL_INCINERATE,			//78 - Fire Pokemon
	TUTOR_SPECIAL_AQUARING,				//79 - Water Pokemon
	TUTOR_SPECIAL_BRINE,				//80 - Water Pokemon
	TUTOR_SPECIAL_RAZORSHELL,			//81 - Water Pokemon
	TUTOR_SPECIAL_SPARK,				//82 - Electric Pokemon
	TUTOR_SPECIAL_SHOCKWAVE,			//83 - Electric Pokemon
	TUTOR_SPECIAL_PARABOLICCHARGE,		//84 - Electric Pokemon
	TUTOR_SPECIAL_COTTONSPORE,			//85 - Grass Pokemon
	TUTOR_SPECIAL_FORESTSCURSE,			//86 - Grass Pokemon
	TUTOR_SPECIAL_MEGADRAIN,			//87 - Grass Pokemon
	TUTOR_SPECIAL_ICESHARD,				//88 - Ice Pokemon
	TUTOR_SPECIAL_FREEZEDRY,			//89 - Ice Pokemon
	TUTOR_SPECIAL_AURORABEAM,			//90 - Ice Pokemon
	TUTOR_SPECIAL_KARATECHOP,			//91 - Fighting Pokemon
	TUTOR_SPECIAL_AURASPHERE,			//92 - Fighting Pokemon
	TUTOR_SPECIAL_STORMTHROW,			//93 - Fighting Pokemon
	TUTOR_SPECIAL_SLUDGE,				//94 - Poison Pokemon
	TUTOR_SPECIAL_ACIDSPRAY,			//95 - Poison Pokemon
	TUTOR_SPECIAL_COIL,					//96 - Poison Pokemon
	TUTOR_SPECIAL_MUDSHOT,				//97 - Ground Pokemon
	TUTOR_SPECIAL_SPIKES,				//98 - Ground Pokemon
	TUTOR_SPECIAL_MAGNITUDE,			//99 - Ground Pokemon
	TUTOR_SPECIAL_CHATTER,				//100 - Flying Pokemon
	TUTOR_SPECIAL_DUALWINGBEAT,			//101 - Flying Pokemon
	TUTOR_SPECIAL_SKYDROP,				//102 - Flying Pokemon
	TUTOR_SPECIAL_HEALBLOCK,			//103 - Psychic Pokemon
	TUTOR_SPECIAL_PSYWAVE,				//104 - Psychic Pokemon
	TUTOR_SPECIAL_MAGICPOWDER,			//105 - Psychic Pokemon
	TUTOR_SPECIAL_FURYCUTTER,			//106 - Bug Pokemon
	TUTOR_SPECIAL_FELLSTINGER,			//107 - Bug Pokemon
	TUTOR_SPECIAL_RAGEPOWDER,			//108 - Bug Pokemon
	TUTOR_SPECIAL_ROLLOUT,				//109 - Rock Pokemon
	TUTOR_SPECIAL_WIDEGUARD,			//110 - Rock Pokemon
	TUTOR_SPECIAL_ANCIENTPOWER,			//111 - Rock Pokemon
	TUTOR_SPECIAL_DESTINYBOND,			//112 - Ghost Pokemon
	TUTOR_SPECIAL_SHADOWSNEAK,			//113 - Ghost Pokemon
	TUTOR_SPECIAL_GRUDGE,				//114 - Ghost Pokemon
	TUTOR_SPECIAL_BREAKINGSWIPE,		//115 - Dragon Pokemon
	TUTOR_SPECIAL_SCALESHOT,			//116 - Dragon Pokemon
	TUTOR_SPECIAL_DRAGONRUSH,			//117 - Dragon Pokemon
	TUTOR_SPECIAL_FAKETEARS,			//118 - Dark Pokemon
	TUTOR_SPECIAL_SUCKERPUNCH,			//119 - Dark Pokemon
	TUTOR_SPECIAL_PURSUIT,				//120 - Dark Pokemon
	TUTOR_SPECIAL_AUTOMIZE,				//121 - Steel Pokemon
	TUTOR_SPECIAL_METALBURST,			//122 - Steel Pokemon
	TUTOR_SPECIAL_HEAVYSLAM,			//123 - Steel Pokemon
	TUTOR_SPECIAL_CRAFTYSHIELD,			//124 - Fairy Pokemon
	TUTOR_SPECIAL_DRAININGKISS,			//125 - Fairy Pokemon
	TUTOR_SPECIAL_SPIRITBREAK,			//126 - Fairy Pokemon
};

#define LAST_TOTAL_TUTOR_NUM 126

#include "defines.h"

struct Habitat
{
	const struct HabitatPage* page;
	u32 numPages;
};

struct HabitatPage
{
	const u16* mons;
	u32 numMons;
};

// Grassland
const u16 gGrasslandPage1[] =
{
	SPECIES_BIDOOF,		// 1
	SPECIES_BIBAREL,	// 2
};

const u16 gGrasslandPage2[] =
{
	SPECIES_SUNKERN,	// 6
	SPECIES_SUNFLORA,	// 7
};

const u16 gGrasslandPage3[] =
{
	SPECIES_YAMPER,			// 8
	SPECIES_BOLTUND,		// 9
};

const u16 gGrasslandPage4[] =
{
	SPECIES_BUDEW,		// 10
	SPECIES_ROSELIA,	// 11
	SPECIES_ROSERADE,	// 12
};

const u16 gGrasslandPage5[] =
{
	SPECIES_GRUBBIN,	// 13
	SPECIES_CHARJABUG,	// 14
	SPECIES_VIKAVOLT,	// 15
};

const u16 gGrasslandPage6[] =
{
	SPECIES_NICKIT,		// 18
	SPECIES_THIEVUL,	// 19
};

const u16 gGrasslandPage7[] =
{
	SPECIES_NIDORAN_M,	// 20
	SPECIES_NIDORINO,	// 21
	SPECIES_NIDOKING,	// 22
};

const u16 gGrasslandPage8[] =
{
	SPECIES_BLIPBUG,	// 23
	SPECIES_DOTTLER,	// 24
	SPECIES_ORBEETLE,	// 25
};

const u16 gGrasslandPage9[] =
{
	SPECIES_PIKIPEK,	// 26
	SPECIES_TRUMBEAK,	// 27
	SPECIES_TOUCANNON,	// 28
};

const u16 gGrasslandPage10[] =
{
	SPECIES_BUNEARY,	// 36
	SPECIES_LOPUNNY,	// 37
};

const u16 gGrasslandPage11[] =
{
	SPECIES_LILLIPUP,	// 56
	SPECIES_HERDIER,	// 57
	SPECIES_STOUTLAND,	// 58
};

const u16 gGrasslandPage12[] =
{
	SPECIES_FARFETCHD_G,	// 63
	SPECIES_SIRFETCHD,		// 64
	SPECIES_FARFETCHD,      // 63
};

const u16 gGrasslandPage13[] =
{
	SPECIES_FLETCHLING,		// 65 
	SPECIES_FLETCHINDER,	// 66
	SPECIES_TALONFLAME,		// 67
};

const u16 gGrasslandPage14[] =
{
	SPECIES_FLABEBE,	// 68
	SPECIES_FLOETTE,	// 69
	SPECIES_FLORGES,	// 70
};

const u16 gGrasslandPage15[] =
{
	SPECIES_FLABEBE_BLUE,	// 68
	SPECIES_FLOETTE_BLUE,	// 69
	SPECIES_FLORGES_BLUE,	// 70
};

const u16 gGrasslandPage16[] =
{
	SPECIES_FLABEBE_ORANGE,	// 68
	SPECIES_FLOETTE_ORANGE,	// 69
	SPECIES_FLORGES_ORANGE,	// 70
};

const u16 gGrasslandPage17[] =
{
	SPECIES_FLABEBE_YELLOW,	// 68
	SPECIES_FLOETTE_YELLOW,	// 69
	SPECIES_FLORGES_YELLOW,	// 70
};

const u16 gGrasslandPage18[] =
{
	SPECIES_FLABEBE_WHITE,	// 68
	SPECIES_FLOETTE_WHITE,	// 69
	SPECIES_FLORGES_WHITE,	// 70
};

const u16 gGrasslandPage19[] =
{
	SPECIES_CASTFORM,	// 91
};

const u16 gGrasslandPage20[] =
{
	SPECIES_MAREEP,		// 191
	SPECIES_FLAAFFY,	// 192
	SPECIES_AMPHAROS,	// 193
};

const u16 gGrasslandPage21[] =
{
	SPECIES_MUDBRAY,	// 197
	SPECIES_MUDSDALE,	// 198
};

const u16 gGrasslandPage22[] =
{
	SPECIES_SKIDDO,	// 204
	SPECIES_GOGOAT,	// 205
};

const u16 gGrasslandPage23[] =
{
	SPECIES_PACHIRISU,		// 211
	SPECIES_MORPEKO,		// 238
	// SPECIES_MORPEKO_HANGRY,	// 238
};

const u16 gGrasslandPage24[] =
{
	SPECIES_LITLEO,		// 284
	SPECIES_PYROAR,		// 285
	SPECIES_KANGASKHAN,	// 286
};

const u16 gGrasslandPage25[] =
{
	SPECIES_BULBASAUR,	// 301
	SPECIES_IVYSAUR,	// 302
	SPECIES_VENUSAUR,	// 303
};

const u16 gGrasslandPage26[] =
{
	SPECIES_CHIKORITA,	// 310
	SPECIES_BAYLEEF,	// 311
	SPECIES_MEGANIUM,	// 312
};

const u16 gGrasslandPage27[] =
{
	SPECIES_CYNDAQUIL,	// 313
	SPECIES_QUILAVA,	// 314
	SPECIES_TYPHLOSION,	// 315
};

const u16 gGrasslandPage28[] =
{
	SPECIES_TORCHIC,	// 322
	SPECIES_COMBUSKEN,	// 323
	SPECIES_BLAZIKEN,	// 324
};

const u16 gGrasslandPage29[] =
{
	SPECIES_TURTWIG,	// 328
	SPECIES_GROTLE,		// 329
	SPECIES_TORTERRA,	// 330
};

const u16 gGrasslandPage30[] =
{
	SPECIES_SNIVY,		// 337
	SPECIES_SERVINE,	// 338
	SPECIES_SERPERIOR,	// 339
};

// Forest
const u16 gForestPage1[] =
{
	SPECIES_MORELULL,	// 29
	SPECIES_SHIINOTIC,	// 30
};

const u16 gForestPage2[] =
{
	SPECIES_HOOTHOOT,	// 31
	SPECIES_NOCTOWL,	// 32
};

const u16 gForestPage3[] =
{
	SPECIES_PICHU,		// 33
	SPECIES_PIKACHU,	// 34
	SPECIES_RAICHU,		// 35
	SPECIES_RAICHU_A,   // 35
	// SPECIES_PIKACHU_CAP_ORIGINAL,	// 34
};

const u16 gForestPage4[] =
{
	SPECIES_SHROOMISH,	// 38
	SPECIES_BRELOOM,	// 39
};

const u16 gForestPage5[] =
{
	SPECIES_BONSLY,		// 40
	SPECIES_SUDOWOODO,	// 41
};

const u16 gForestPage6[] =
{
	SPECIES_VENIPEDE,	// 42
	SPECIES_WHIRLIPEDE,	// 43
	SPECIES_SCOLIPEDE,	// 44
};

const u16 gForestPage7[] =
{
	SPECIES_SLAKOTH,	// 45
	SPECIES_VIGOROTH,	// 46
	SPECIES_SLAKING,	// 47
};

const u16 gForestPage8[] =
{
	SPECIES_CUTIEFLY,	// 71
	SPECIES_RIBOMBEE,	// 72
};

const u16 gForestPage9[] =
{
	SPECIES_COMBEE,		// 79
	SPECIES_VESPIQUEN,	// 80
};

const u16 gForestPage10[] =
{
	SPECIES_NINCADA,	// 106
	SPECIES_NINJASK,	// 107
	SPECIES_SHEDINJA,	// 108
};

const u16 gForestPage11[] =
{
	SPECIES_SNEASEL,	// 133
	SPECIES_WEAVILE,	// 134
};

const u16 gForestPage12[] =
{
	SPECIES_FOONGUS,	// 152
	SPECIES_AMOONGUSS,	// 153
};

const u16 gForestPage13[] =
{
	SPECIES_HATENNA,	// 167
	SPECIES_HATTREM,	// 168
	SPECIES_HATTERENE,	// 169
};

const u16 gForestPage14[] =
{
	SPECIES_ORANGURU,	// 170
	SPECIES_PASSIMIAN,	// 171
};

const u16 gForestPage15[] =
{
	SPECIES_COTTONEE,	// 179
	SPECIES_WHIMSICOTT,	// 180
};

const u16 gForestPage16[] =
{
	SPECIES_TOGEPI,		// 194
	SPECIES_TOGETIC,	// 195
	SPECIES_TOGEKISS,	// 196
};

const u16 gForestPage17[] =
{
	SPECIES_DUSKULL,	// 226
	SPECIES_DUSCLOPS,	// 227
	SPECIES_DUSKNOIR,	// 228
};

const u16 gForestPage18[] =
{
	SPECIES_EMOLGA,		// 229
	SPECIES_HERACROSS,	// 232
};

const u16 gForestPage19[] =
{
	SPECIES_ZORUA,		// 253
	SPECIES_ZOROARK,	// 254
};

const u16 gForestPage20[] =
{
	SPECIES_PHANTUMP,	// 258
	SPECIES_TREVENANT,	// 259
	SPECIES_COMFEY,		// 278
};

const u16 gForestPage21[] =
{
	SPECIES_SHAYMIN,		// 292
	// SPECIES_SHAYMIN_SKY,	// 292
};

const u16 gForestPage22[] =
{
	SPECIES_TREECKO,	// 319
	SPECIES_GROVYLE,	// 320
	SPECIES_SCEPTILE,	// 321
};

const u16 gForestPage23[] =
{
	SPECIES_CHIMCHAR,	// 331
	SPECIES_MONFERNO,	// 332
	SPECIES_INFERNAPE,	// 333
};

const u16 gForestPage24[] =
{
	SPECIES_CHESPIN,	// 346
	SPECIES_QUILLADIN,	// 347
	SPECIES_CHESNAUGHT,	// 348
};

const u16 gForestPage25[] =
{
	SPECIES_ROWLET,		// 355
	SPECIES_DARTRIX,	// 356
	SPECIES_DECIDUEYE,	// 357
};

const u16 gForestPage26[] =
{
	SPECIES_GROOKEY,	// 364
	SPECIES_THWACKEY,	// 365
	SPECIES_RILLABOOM,	// 366
};

// Water's Edge
const u16 gWatersEdgePage1[] =
{
	SPECIES_CORPHISH,	// 100
	SPECIES_CRAWDAUNT,	// 101
};

const u16 gWatersEdgePage2[] =
{
	SPECIES_MAGIKARP,	// 102
	SPECIES_GYARADOS,	// 103
};

const u16 gWatersEdgePage3[] =
{
	SPECIES_DRATINI,	// 208
	SPECIES_DRAGONAIR,	// 209
	SPECIES_DRAGONITE,	// 210
};

const u16 gWatersEdgePage4[] =
{
	SPECIES_GOOMY,		// 220
	SPECIES_SLIGGOO,	// 221
	SPECIES_GOODRA,		// 222
};

const u16 gWatersEdgePage5[] =
{
	SPECIES_SHELLOS,		// 223
	SPECIES_GASTRODON,		// 224
	SPECIES_SHELLOS_EAST,	// 223
	SPECIES_GASTRODON_EAST,	// 224
};

const u16 gWatersEdgePage6[] =
{
	SPECIES_PINCURCHIN,	// 237
	SPECIES_STUNFISK_G,	// 239
	SPECIES_STUNFISK,	// 239
};

const u16 gWatersEdgePage7[] =
{
	SPECIES_BINACLE,	// 243
	SPECIES_BARBARACLE,	// 244
};

const u16 gWatersEdgePage8[] =
{
	SPECIES_SANDYGAST,	// 260
	SPECIES_PALOSSAND,	// 261
};

const u16 gWatersEdgePage9[] =
{
	SPECIES_SLOWPOKE,	// 262
	SPECIES_SLOWBRO,	// 263
	SPECIES_SLOWKING,	// 264
};

const u16 gWatersEdgePage10[] =
{
	SPECIES_SLOWPOKE_G,	// 262
	SPECIES_SLOWBRO_G,	// 263
	SPECIES_SLOWKING_G,	// 264
};

const u16 gWatersEdgePage11[] =
{
	SPECIES_SQUIRTLE,	// 307
	SPECIES_WARTORTLE,	// 308
	SPECIES_BLASTOISE,	// 309
};

const u16 gWatersEdgePage12[] =
{
	SPECIES_TOTODILE,	// 316
	SPECIES_CROCONAW,	// 317
	SPECIES_FERALIGATR,	// 318
};

const u16 gWatersEdgePage13[] =
{
	SPECIES_MUDKIP,		// 325
	SPECIES_MARSHTOMP,	// 326
	SPECIES_SWAMPERT,	// 327
};

const u16 gWatersEdgePage14[] =
{
	SPECIES_PIPLUP,		// 334
	SPECIES_PRINPLUP,	// 335
	SPECIES_EMPOLEON,	// 336
};

const u16 gWatersEdgePage15[] =
{
	SPECIES_OSHAWOTT,	// 343
	SPECIES_DEWOTT,		// 344
	SPECIES_SAMUROTT,	// 345
};

const u16 gWatersEdgePage16[] =
{
	SPECIES_FROAKIE,		// 352
	SPECIES_FROGADIER,		// 353
	SPECIES_GRENINJA,		// 354
	// SPECIES_ASHGRENINJA,	// 354
};

const u16 gWatersEdgePage17[] =
{
	SPECIES_POPPLIO,	// 361
	SPECIES_BRIONNE,	// 362
	SPECIES_PRIMARINA,	// 363
};

const u16 gWatersEdgePage18[] =
{
	SPECIES_SOBBLE,		// 370
	SPECIES_DRIZZILE,	// 371
	SPECIES_INTELEON,	// 372
};

// Sea
const u16 gSeaPage1[] =
{
	SPECIES_CHINCHOU,	// 59
	SPECIES_LANTURN,	// 60
};

const u16 gSeaPage2[] =
{
	SPECIES_WINGULL,	// 85
	SPECIES_PELIPPER,	// 86
};

const u16 gSeaPage3[] =
{
	SPECIES_FRILLISH,	// 150
	SPECIES_JELLICENT,	// 151
};

const u16 gSeaPage4[] =
{
	SPECIES_LILEEP,		// 173
	SPECIES_CRADILY,	// 174
};

const u16 gSeaPage5[] =
{
	SPECIES_SHELLDER,	// 175
	SPECIES_CLOYSTER,	// 176
};

const u16 gSeaPage6[] =
{
	SPECIES_HORSEA,		// 215
	SPECIES_SEADRA,		// 216
	SPECIES_KINGDRA,	// 217
};

const u16 gSeaPage7[] =
{
	SPECIES_CARVANHA,	// 230
	SPECIES_SHARPEDO,	// 231
	SPECIES_DHELMISE,	// 236
};

const u16 gSeaPage8[] =
{
	SPECIES_MAREANIE,	// 249
	SPECIES_TOXAPEX,	// 250
};

const u16 gSeaPage9[] =
{
	SPECIES_LAPRAS,		// 255
};

const u16 gSeaPage10[] =
{
	SPECIES_CORSOLA_G,	// 265
	SPECIES_CURSOLA,	// 266
	SPECIES_CORSOLA,	// 265
};

const u16 gSeaPage11[] =
{
	SPECIES_KYOGRE,		// 293
};

// Cave
const u16 gCavePage1[] =
{
	SPECIES_ZUBAT, 	// 48
	SPECIES_GOLBAT,	// 49
	SPECIES_CROBAT, // 50
};

const u16 gCavePage2[] =
{
	SPECIES_DRILBUR,	// 51
	SPECIES_EXCADRILL,	// 52
};

const u16 gCavePage3[] =
{
	SPECIES_ROGGENROLA,	// 53
	SPECIES_BOLDORE,	// 54
	SPECIES_GIGALITH,	// 55
};

const u16 gCavePage4[] =
{
	SPECIES_FERROSEED,	// 77
	SPECIES_FERROTHORN,	// 78
};

const u16 gCavePage5[] =
{
	SPECIES_WYNAUT,		// 109
	SPECIES_WOBBUFFET,	// 110
	SPECIES_CARBINK,	// 111
};

const u16 gCavePage6[] =
{
	SPECIES_KLINK,		// 112
	SPECIES_KLANG,		// 113
	SPECIES_KLINKLANG,	// 114
};

const u16 gCavePage7[] =
{
	SPECIES_SABLEYE,	// 115
	SPECIES_MAWILE,		// 116
};

const u16 gCavePage8[] =
{
	SPECIES_JANGMO_O,	// 118
	SPECIES_HAKAMO_O,	// 119
	SPECIES_KOMMO_O,	// 120
};

const u16 gCavePage9[] =
{
	SPECIES_CUBCHOO,	// 121
	SPECIES_BEARTIC,	// 122
};

const u16 gCavePage10[] =
{
	SPECIES_SWINUB,		// 123
	SPECIES_PILOSWINE,	// 124
	SPECIES_MAMOSWINE,	// 125
};

const u16 gCavePage11[] =
{
	SPECIES_SNORUNT,	// 126
	SPECIES_GLALIE,		// 127
	SPECIES_FROSLASS,	// 128
};

const u16 gCavePage12[] =
{
	SPECIES_LARVESTA,	// 141
	SPECIES_VOLCARONA,	// 142
};

const u16 gCavePage13[] =
{
	SPECIES_ROLYCOLY,	// 144
	SPECIES_CARKOL,		// 145
	SPECIES_COALOSSAL,	// 146
};

const u16 gCavePage14[] =
{
	SPECIES_SHIELDON,	// 154
	SPECIES_BASTIODON,	// 155
};

const u16 gCavePage15[] =
{
	SPECIES_MISDREAVUS,	// 240
	SPECIES_MISMAGIUS,	// 241
};

const u16 gCavePage16[] =
{
	SPECIES_GIBLE,		// 244
	SPECIES_GABITE,		// 245
	SPECIES_GARCHOMP,	// 246
};

const u16 gCavePage17[] =
{
	SPECIES_BERGMITE,	// 274
	SPECIES_AVALUGG,	// 275
};

const u16 gCavePage18[] =
{
	SPECIES_JOLTIK,		// 281
	SPECIES_GALVANTULA,	// 282
};

// Mountains
const u16 gMountainPage1[] =
{
	SPECIES_ROCKRUFF,		// 16
	SPECIES_LYCANROC,		// 17
	// SPECIES_LYCANROC_N,		// 17
	// SPECIES_LYCANROC_DUSK,	// 17
};

const u16 gMountainPage2[] =
{
	SPECIES_VULLABY,	// 89
	SPECIES_MANDIBUZZ,	// 90
};

const u16 gMountainPage3[] =
{
	SPECIES_INKAY,		// 104
	SPECIES_MALAMAR,	// 105
	SPECIES_SHUCKLE,	// 117
};

const u16 gMountainPage4[] =
{
	SPECIES_NOIBAT,		// 129
	SPECIES_NOIVERN,	// 130
};

const u16 gMountainPage5[] =
{
	SPECIES_TYRUNT,		// 131
	SPECIES_TYRANTRUM,	// 132
};

const u16 gMountainPage6[] =
{
	SPECIES_SNOM,		// 135
	SPECIES_FROSMOTH,	// 136
};

const u16 gMountainPage7[]=
{
	SPECIES_MINIOR_SHIELD,	// 143
	// SPECIES_MINIOR_RED,		// 143
	// SPECIES_MINIOR_BLUE,	// 143
	// SPECIES_MINIOR_ORANGE,	// 143
};

// const u16 gMountainPage8[]=
// {
// 	SPECIES_MINIOR_YELLOW,	// 143
// 	SPECIES_MINIOR_INDIGO,	// 143
// 	SPECIES_MINIOR_GREEN,	// 143
// };

const u16 gMountainPage9[] =
{
	SPECIES_SALANDIT,	// 148
	SPECIES_SALAZZLE,	// 149
};

const u16 gMountainPage10[] =
{
	SPECIES_TIMBURR,	// 156
	SPECIES_GURDURR,	// 157
	SPECIES_CONKELDURR,	// 158
};

const u16 gMountainPage11[] =
{
	SPECIES_AMAURA,		// 159
	SPECIES_AURORUS,	// 160
};

const u16 gMountainPage12[] =
{
	SPECIES_TURTONATOR,	// 161
	SPECIES_SLUGMA,		// 165
	SPECIES_MAGCARGO,	// 166
	SPECIES_TORKOAL,	// 172
};

const u16 gMountainPage13[] =
{
	SPECIES_MIENFOO,	// 202
	SPECIES_MIENSHAO,	// 203
};

const u16 gMountainPage14[] =
{
	SPECIES_RIOLU,		// 206
	SPECIES_LUCARIO,	// 207
	SPECIES_CROAGUNK,	// 218
	SPECIES_TOXICROAK,	// 219
};

const u16 gMountainPage15[] =
{
	SPECIES_CRABRAWLER,		// 256
	SPECIES_CRABOMINABLE,	// 257
};

const u16 gMountainPage16[] =
{
	SPECIES_MANKEY,		// 272
	SPECIES_PRIMEAPE,	// 273
};

const u16 gMountainPage17[] =
{
	SPECIES_STONJOURNER,	// 276
	SPECIES_DELIBIRD,		// 277
	SPECIES_CUFANT,			// 279
	SPECIES_COPPERAJAH,		// 280
};

const u16 gMountainPage18[] =
{
	SPECIES_CARNIVINE,	// 283
	SPECIES_DURALUDON,	// 287
};

const u16 gMountainPage19[] =
{
	SPECIES_ARTICUNO_G,	// 288
	SPECIES_ZAPDOS_G,	// 289
	SPECIES_MOLTRES_G,	// 290
};

const u16 gMountainPage20[] =
{
	SPECIES_JIRACHI,	// 291
};

const u16 gMountainPage21[] =
{
	SPECIES_CHARMANDER,	// 304
	SPECIES_CHARMELEON,	// 305
	SPECIES_CHARIZARD,	// 306
};

// Rough Terrain
const u16 gRoughTerrainPage1[] =
{
	SPECIES_ROOKIDEE,		// 3
	SPECIES_CORVISQUIRE,	// 4
	SPECIES_CORVIKNIGHT,	// 5
};

const u16 gRoughTerrainPage2[] =
{
	SPECIES_SCRAGGY,	// 81
	SPECIES_SCRAFTY,	// 82
};

const u16 gRoughTerrainPage3[] =
{
	SPECIES_CACNEA,		// 83
	SPECIES_CACTURNE,	// 84
};

const u16 gRoughTerrainPage4[] =
{
	SPECIES_HELIOPTILE,	// 87
	SPECIES_HELIOLISK,	// 88
};

const u16 gRoughTerrainPage5[] =
{
	SPECIES_TRAPINCH,	// 92
	SPECIES_VIBRAVA,	// 93
	SPECIES_FLYGON,		// 94
};

const u16 gRoughTerrainPage6[] =
{
	SPECIES_SANDILE,	// 95
	SPECIES_KROKOROK,	// 96
	SPECIES_KROOKODILE,	// 97
};

const u16 gRoughTerrainPage7[] =
{
	SPECIES_HIPPOPOTAS,	// 98
	SPECIES_HIPPOWDON,	// 99
};

const u16 gRoughTerrainPage8[] =
{
	SPECIES_DARUMAKA_G,			// 137
	SPECIES_DARMANITAN_G,		// 138
	// SPECIES_DARMANITAN_G_ZEN,	// 138
	SPECIES_DARUMAKA,			// 137
	SPECIES_DARMANITAN,	     	// 138
};

const u16 gRoughTerrainPage9[] =
{
	SPECIES_HOUNDOUR,	// 139
	SPECIES_HOUNDOOM,	// 140
};

const u16 gRoughTerrainPage10[] =
{
	SPECIES_SKARMORY,	// 147
};

const u16 gRoughTerrainPage11[] =
{
	SPECIES_SIZZLIPEDE,		// 177
	SPECIES_CENTISKORCH,	// 178
};

const u16 gRoughTerrainPage12[] =
{
	SPECIES_YAMASK,		// 233
	SPECIES_COFAGRIGUS,	// 234
	SPECIES_YAMASK_G,	// 233
	SPECIES_RUNERIGUS,	// 235
};

const u16 gRoughTerrainPage13[] =
{
	SPECIES_FALINKS,	// 267
	SPECIES_PAWNIARD,	// 268
	SPECIES_BISHARP,	// 269
};

const u16 gRoughTerrainPage14[] =
{
	SPECIES_GROUDON,	// 294
};

const u16 gRoughTerrainPage15[] =
{
	SPECIES_VOLCANION,	// 295
};

// Urban
const u16 gUrbanPage1[] =
{
	SPECIES_RATTATA_A,	// 61
	SPECIES_RATICATE_A,	// 62
	SPECIES_RATTATA,	// 61
	SPECIES_RATICATE,	// 62
};

const u16 gUrbanPage2[] =
{
	SPECIES_RALTS,		// 73
	SPECIES_KIRLIA,		// 74
	SPECIES_GARDEVOIR,	// 75
	SPECIES_GALLADE,	// 76
};

const u16 gUrbanPage3[] =
{
	SPECIES_MIME_JR_G,	// 162
	SPECIES_MR_MIME_G,	// 163
	SPECIES_MR_RIME,	// 164
};

const u16 gUrbanPage4[] =
{
	SPECIES_MIME_JR,	// 162
	SPECIES_MR_MIME,	// 163
	SPECIES_DITTO,		// 181
};

const u16 gUrbanPage5[] =
{
	SPECIES_EEVEE,		// 182
	SPECIES_VAPOREON,	// 183
	SPECIES_JOLTEON,	// 184
	SPECIES_FLAREON,	// 185
};

const u16 gUrbanPage6[] =
{
	SPECIES_ESPEON,		// 186
	SPECIES_UMBREON,	// 187
};

const u16 gUrbanPage7[] =
{
	SPECIES_LEAFEON,	// 188
	SPECIES_GLACEON,	// 189
	SPECIES_SYLVEON,	// 190
};

const u16 gUrbanPage8[] =
{
	SPECIES_HAPPINY,	// 199
	SPECIES_CHANSEY,	// 200
	SPECIES_BLISSEY,	// 201
};

const u16 gUrbanPage9[] =
{
	SPECIES_ROTOM,		// 212
	// SPECIES_ROTOM_HEAT,	// 212
	// SPECIES_ROTOM_WASH,	// 212
};

// const u16 gUrbanPage10[] =
// {
// 	SPECIES_ROTOM_FROST,	// 212
// 	SPECIES_ROTOM_FAN,		// 212
// 	SPECIES_ROTOM_MOW,		// 212
// };

const u16 gUrbanPage11[] =
{
	SPECIES_TOXEL,				// 213
	SPECIES_TOXTRICITY,			// 214
	// SPECIES_TOXTRICITY_LOW_KEY,	// 214
};

const u16 gUrbanPage12[] =
{
	SPECIES_MIMIKYU,		// 225
	// SPECIES_MIMIKYU_BUSTED,	// 225
};

const u16 gUrbanPage13[] =
{
	SPECIES_GRIMER_A,	// 242
	SPECIES_MUK_A,		// 243
	SPECIES_GRIMER,     // 242
	SPECIES_MUK,        // 243
};

const u16 gUrbanPage14[] = 
{
	SPECIES_KOFFING_G,	// 251
	SPECIES_WEEZING_G,	// 252
	SPECIES_KOFFING,	// 251
	SPECIES_WEEZING,	// 252
};

const u16 gUrbanPage15[] =
{
	SPECIES_ELGYEM,		// 270
	SPECIES_BEHEEYEM,	// 271
};

const u16 gUrbanPage16[] =
{
	SPECIES_TEPIG,		// 340
	SPECIES_PIGNITE,	// 341
	SPECIES_EMBOAR,		// 342
};

const u16 gUrbanPage17[] =
{
	SPECIES_FENNEKIN,	// 349
	SPECIES_BRAIXEN,	// 350
	SPECIES_DELPHOX,	// 351
};

const u16 gUrbanPage18[] =
{
	SPECIES_LITTEN,		// 358
	SPECIES_TORRACAT,	// 359
	SPECIES_INCINEROAR,	// 360
};

const u16 gUrbanPage19[] =
{
	SPECIES_SCORBUNNY,	// 367
	SPECIES_RABOOT,		// 368
	SPECIES_CINDERACE,	// 369
};

// Rare
const u16 gRarePage1[] =
{
	SPECIES_ZERAORA,	// 296
};

const u16 gRarePage2[] =
{
	SPECIES_GLASTRIER,	// 297
};

const u16 gRarePage3[] =
{
	SPECIES_MELTAN,		// 298
	SPECIES_MELMETAL,	// 299
};

const u16 gRarePage4[] =
{
	SPECIES_VICTINI,	// 300
};

const u16 gRarePage5[] =
{
	SPECIES_COSMOG,		// 373
	SPECIES_COSMOEM,	// 374
	SPECIES_SOLGALEO,	// 375
	SPECIES_LUNALA,		// 376
};

const u16 gRarePage6[] =
{
	SPECIES_NIHILEGO,	// 377
	SPECIES_BUZZWOLE,	// 378
	SPECIES_PHEROMOSA,	// 379
	SPECIES_XURKITREE,	// 380
};

const u16 gRarePage7[] =
{
	SPECIES_CELESTEELA,	// 381
	SPECIES_KARTANA,	// 382
	SPECIES_GUZZLORD,	// 383
};

const u16 gRarePage8[] =
{
	SPECIES_NECROZMA,				// 384
	SPECIES_NECROZMA_DUSK_MANE,		// 384
	SPECIES_NECROZMA_DAWN_WINGS,	// 384
	SPECIES_NECROZMA_ULTRA,			// 384
};

const u16 gRarePage9[] =
{
	SPECIES_POIPOLE,		// 385
	SPECIES_NAGANADEL,		// 386
	SPECIES_STAKATAKA,		// 387
	SPECIES_BLACEPHALON,	// 388
};

const u16 gRarePage10[] =
{
	SPECIES_TYPE_NULL,		// 389
	SPECIES_SILVALLY,		// 390
};

const struct HabitatPage gGrasslandPages[] =
{
	{gGrasslandPage1, ARRAY_COUNT(gGrasslandPage1)}, 
	{gGrasslandPage2, ARRAY_COUNT(gGrasslandPage2)}, 
	{gGrasslandPage3, ARRAY_COUNT(gGrasslandPage3)}, 
	{gGrasslandPage4, ARRAY_COUNT(gGrasslandPage4)}, 
	{gGrasslandPage5, ARRAY_COUNT(gGrasslandPage5)}, 
	{gGrasslandPage6, ARRAY_COUNT(gGrasslandPage6)}, 
	{gGrasslandPage7, ARRAY_COUNT(gGrasslandPage7)}, 
	{gGrasslandPage8, ARRAY_COUNT(gGrasslandPage8)}, 
	{gGrasslandPage9, ARRAY_COUNT(gGrasslandPage9)}, 
	{gGrasslandPage10, ARRAY_COUNT(gGrasslandPage10)}, 
	{gGrasslandPage11, ARRAY_COUNT(gGrasslandPage11)}, 
	{gGrasslandPage12, ARRAY_COUNT(gGrasslandPage12)}, 
	{gGrasslandPage13, ARRAY_COUNT(gGrasslandPage13)}, 
	{gGrasslandPage14, ARRAY_COUNT(gGrasslandPage14)}, 
	{gGrasslandPage15, ARRAY_COUNT(gGrasslandPage15)}, 
	{gGrasslandPage16, ARRAY_COUNT(gGrasslandPage16)}, 
	{gGrasslandPage17, ARRAY_COUNT(gGrasslandPage17)}, 
	{gGrasslandPage18, ARRAY_COUNT(gGrasslandPage18)}, 
	{gGrasslandPage19, ARRAY_COUNT(gGrasslandPage19)}, 
	{gGrasslandPage20, ARRAY_COUNT(gGrasslandPage20)}, 
	{gGrasslandPage21, ARRAY_COUNT(gGrasslandPage21)}, 
	{gGrasslandPage22, ARRAY_COUNT(gGrasslandPage22)}, 
	{gGrasslandPage23, ARRAY_COUNT(gGrasslandPage23)}, 
	{gGrasslandPage24, ARRAY_COUNT(gGrasslandPage24)}, 
	{gGrasslandPage25, ARRAY_COUNT(gGrasslandPage25)}, 
	{gGrasslandPage26, ARRAY_COUNT(gGrasslandPage26)}, 
	{gGrasslandPage27, ARRAY_COUNT(gGrasslandPage27)}, 
	{gGrasslandPage28, ARRAY_COUNT(gGrasslandPage28)}, 
	{gGrasslandPage29, ARRAY_COUNT(gGrasslandPage29)}, 
	{gGrasslandPage30, ARRAY_COUNT(gGrasslandPage30)},
};

const struct HabitatPage gForestPages[] =
{
	{gForestPage1, ARRAY_COUNT(gForestPage1)}, 
	{gForestPage2, ARRAY_COUNT(gForestPage2)}, 
	{gForestPage3, ARRAY_COUNT(gForestPage3)}, 
	{gForestPage4, ARRAY_COUNT(gForestPage4)}, 
	{gForestPage5, ARRAY_COUNT(gForestPage5)}, 
	{gForestPage6, ARRAY_COUNT(gForestPage6)}, 
	{gForestPage7, ARRAY_COUNT(gForestPage7)}, 
	{gForestPage8, ARRAY_COUNT(gForestPage8)}, 
	{gForestPage9, ARRAY_COUNT(gForestPage9)}, 
	{gForestPage10, ARRAY_COUNT(gForestPage10)}, 
	{gForestPage11, ARRAY_COUNT(gForestPage11)}, 
	{gForestPage12, ARRAY_COUNT(gForestPage12)}, 
	{gForestPage13, ARRAY_COUNT(gForestPage13)}, 
	{gForestPage14, ARRAY_COUNT(gForestPage14)}, 
	{gForestPage15, ARRAY_COUNT(gForestPage15)}, 
	{gForestPage16, ARRAY_COUNT(gForestPage16)}, 
	{gForestPage17, ARRAY_COUNT(gForestPage17)}, 
	{gForestPage18, ARRAY_COUNT(gForestPage18)}, 
	{gForestPage19, ARRAY_COUNT(gForestPage19)}, 
	{gForestPage20, ARRAY_COUNT(gForestPage20)}, 
	{gForestPage21, ARRAY_COUNT(gForestPage21)}, 
	{gForestPage22, ARRAY_COUNT(gForestPage22)}, 
	{gForestPage23, ARRAY_COUNT(gForestPage23)}, 
	{gForestPage24, ARRAY_COUNT(gForestPage24)}, 
	{gForestPage25, ARRAY_COUNT(gForestPage25)}, 
	{gForestPage26, ARRAY_COUNT(gForestPage26)},
};

const struct HabitatPage gWatersEdgePages[] =
{
	{gWatersEdgePage1, ARRAY_COUNT(gWatersEdgePage1)}, 
	{gWatersEdgePage2, ARRAY_COUNT(gWatersEdgePage2)}, 
	{gWatersEdgePage3, ARRAY_COUNT(gWatersEdgePage3)}, 
	{gWatersEdgePage4, ARRAY_COUNT(gWatersEdgePage4)}, 
	{gWatersEdgePage5, ARRAY_COUNT(gWatersEdgePage5)}, 
	{gWatersEdgePage6, ARRAY_COUNT(gWatersEdgePage6)}, 
	{gWatersEdgePage7, ARRAY_COUNT(gWatersEdgePage7)}, 
	{gWatersEdgePage8, ARRAY_COUNT(gWatersEdgePage8)}, 
	{gWatersEdgePage9, ARRAY_COUNT(gWatersEdgePage9)}, 
	{gWatersEdgePage10, ARRAY_COUNT(gWatersEdgePage10)}, 
	{gWatersEdgePage11, ARRAY_COUNT(gWatersEdgePage11)}, 
	{gWatersEdgePage12, ARRAY_COUNT(gWatersEdgePage12)}, 
	{gWatersEdgePage13, ARRAY_COUNT(gWatersEdgePage13)}, 
	{gWatersEdgePage14, ARRAY_COUNT(gWatersEdgePage14)}, 
	{gWatersEdgePage15, ARRAY_COUNT(gWatersEdgePage15)}, 
	{gWatersEdgePage16, ARRAY_COUNT(gWatersEdgePage16)}, 
	{gWatersEdgePage17, ARRAY_COUNT(gWatersEdgePage17)},
	{gWatersEdgePage18, ARRAY_COUNT(gWatersEdgePage18)}, 
};

const struct HabitatPage gSeaPages[] =
{
	{gSeaPage1, ARRAY_COUNT(gSeaPage1)}, 
	{gSeaPage2, ARRAY_COUNT(gSeaPage2)}, 
	{gSeaPage3, ARRAY_COUNT(gSeaPage3)}, 
	{gSeaPage4, ARRAY_COUNT(gSeaPage4)}, 
	{gSeaPage5, ARRAY_COUNT(gSeaPage5)}, 
	{gSeaPage6, ARRAY_COUNT(gSeaPage6)}, 
	{gSeaPage7, ARRAY_COUNT(gSeaPage7)}, 
	{gSeaPage8, ARRAY_COUNT(gSeaPage8)}, 
	{gSeaPage9, ARRAY_COUNT(gSeaPage9)}, 
	{gSeaPage10, ARRAY_COUNT(gSeaPage10)}, 
	{gSeaPage11, ARRAY_COUNT(gSeaPage11)}, 
};

const struct HabitatPage gCavePages[] =
{
	{gCavePage1, ARRAY_COUNT(gCavePage1)},
	{gCavePage2, ARRAY_COUNT(gCavePage2)},
	{gCavePage3, ARRAY_COUNT(gCavePage3)}, 
	{gCavePage4, ARRAY_COUNT(gCavePage4)}, 
	{gCavePage5, ARRAY_COUNT(gCavePage5)}, 
	{gCavePage6, ARRAY_COUNT(gCavePage6)}, 
	{gCavePage7, ARRAY_COUNT(gCavePage7)}, 
	{gCavePage8, ARRAY_COUNT(gCavePage8)}, 
	{gCavePage9, ARRAY_COUNT(gCavePage9)}, 
	{gCavePage10, ARRAY_COUNT(gCavePage10)}, 
	{gCavePage11, ARRAY_COUNT(gCavePage11)}, 
	{gCavePage12, ARRAY_COUNT(gCavePage12)}, 
	{gCavePage13, ARRAY_COUNT(gCavePage13)}, 
	{gCavePage14, ARRAY_COUNT(gCavePage14)}, 
	{gCavePage15, ARRAY_COUNT(gCavePage15)}, 
	{gCavePage16, ARRAY_COUNT(gCavePage16)}, 
	{gCavePage17, ARRAY_COUNT(gCavePage17)}, 
	{gCavePage18, ARRAY_COUNT(gCavePage18)},
};

const struct HabitatPage gMountainPages[] =
{
	{gMountainPage1, ARRAY_COUNT(gMountainPage1)}, 
	{gMountainPage2, ARRAY_COUNT(gMountainPage2)}, 
	{gMountainPage3, ARRAY_COUNT(gMountainPage3)}, 
	{gMountainPage4, ARRAY_COUNT(gMountainPage4)}, 
	{gMountainPage5, ARRAY_COUNT(gMountainPage5)}, 
	{gMountainPage6, ARRAY_COUNT(gMountainPage6)}, 
	{gMountainPage7, ARRAY_COUNT(gMountainPage7)}, 
	// {gMountainPage8, ARRAY_COUNT(gMountainPage8)}, 
	{gMountainPage9, ARRAY_COUNT(gMountainPage9)}, 
	{gMountainPage10, ARRAY_COUNT(gMountainPage10)}, 
	{gMountainPage11, ARRAY_COUNT(gMountainPage11)}, 
	{gMountainPage12, ARRAY_COUNT(gMountainPage12)}, 
	{gMountainPage13, ARRAY_COUNT(gMountainPage13)}, 
	{gMountainPage14, ARRAY_COUNT(gMountainPage14)}, 
	{gMountainPage15, ARRAY_COUNT(gMountainPage15)}, 
	{gMountainPage16, ARRAY_COUNT(gMountainPage16)}, 
	{gMountainPage17, ARRAY_COUNT(gMountainPage17)}, 
	{gMountainPage18, ARRAY_COUNT(gMountainPage18)}, 
	{gMountainPage19, ARRAY_COUNT(gMountainPage19)}, 
	{gMountainPage20, ARRAY_COUNT(gMountainPage20)}, 
	{gMountainPage21, ARRAY_COUNT(gMountainPage21)},
};

const struct HabitatPage gRoughTerrainPages[] =
{
	{gRoughTerrainPage1, ARRAY_COUNT(gRoughTerrainPage1)}, 
	{gRoughTerrainPage2, ARRAY_COUNT(gRoughTerrainPage2)}, 
	{gRoughTerrainPage3, ARRAY_COUNT(gRoughTerrainPage3)}, 
	{gRoughTerrainPage4, ARRAY_COUNT(gRoughTerrainPage4)}, 
	{gRoughTerrainPage5, ARRAY_COUNT(gRoughTerrainPage5)}, 
	{gRoughTerrainPage6, ARRAY_COUNT(gRoughTerrainPage6)}, 
	{gRoughTerrainPage7, ARRAY_COUNT(gRoughTerrainPage7)}, 
	{gRoughTerrainPage8, ARRAY_COUNT(gRoughTerrainPage8)}, 
	{gRoughTerrainPage9, ARRAY_COUNT(gRoughTerrainPage9)}, 
	{gRoughTerrainPage10, ARRAY_COUNT(gRoughTerrainPage10)}, 
	{gRoughTerrainPage11, ARRAY_COUNT(gRoughTerrainPage11)}, 
	{gRoughTerrainPage12, ARRAY_COUNT(gRoughTerrainPage12)}, 
	{gRoughTerrainPage13, ARRAY_COUNT(gRoughTerrainPage13)}, 
	{gRoughTerrainPage14, ARRAY_COUNT(gRoughTerrainPage14)}, 
	{gRoughTerrainPage15, ARRAY_COUNT(gRoughTerrainPage15)}, 
};

const struct HabitatPage gUrbanPages[] =
{
	{gUrbanPage1, ARRAY_COUNT(gUrbanPage1)}, 
	{gUrbanPage2, ARRAY_COUNT(gUrbanPage2)}, 
	{gUrbanPage3, ARRAY_COUNT(gUrbanPage3)}, 
	{gUrbanPage4, ARRAY_COUNT(gUrbanPage4)}, 
	{gUrbanPage5, ARRAY_COUNT(gUrbanPage5)}, 
	{gUrbanPage6, ARRAY_COUNT(gUrbanPage6)}, 
	{gUrbanPage7, ARRAY_COUNT(gUrbanPage7)}, 
	{gUrbanPage8, ARRAY_COUNT(gUrbanPage8)}, 
	{gUrbanPage9, ARRAY_COUNT(gUrbanPage9)}, 
	// {gUrbanPage10, ARRAY_COUNT(gUrbanPage10)}, 
	{gUrbanPage11, ARRAY_COUNT(gUrbanPage11)}, 
	{gUrbanPage12, ARRAY_COUNT(gUrbanPage12)}, 
	{gUrbanPage13, ARRAY_COUNT(gUrbanPage13)}, 
	{gUrbanPage14, ARRAY_COUNT(gUrbanPage14)}, 
	{gUrbanPage15, ARRAY_COUNT(gUrbanPage15)}, 
	{gUrbanPage16, ARRAY_COUNT(gUrbanPage16)}, 
	{gUrbanPage17, ARRAY_COUNT(gUrbanPage17)}, 
	{gUrbanPage18, ARRAY_COUNT(gUrbanPage18)},
	{gUrbanPage19, ARRAY_COUNT(gUrbanPage19)},
};

const struct HabitatPage gRarePages[] =
{
	{gRarePage1, ARRAY_COUNT(gRarePage1)}, 
	{gRarePage2, ARRAY_COUNT(gRarePage2)}, 
	{gRarePage3, ARRAY_COUNT(gRarePage3)}, 
	{gRarePage4, ARRAY_COUNT(gRarePage4)}, 
	{gRarePage5, ARRAY_COUNT(gRarePage5)}, 
	{gRarePage6, ARRAY_COUNT(gRarePage6)}, 
	{gRarePage7, ARRAY_COUNT(gRarePage7)}, 
	{gRarePage8, ARRAY_COUNT(gRarePage8)}, 
	{gRarePage9, ARRAY_COUNT(gRarePage9)},
	{gRarePage10, ARRAY_COUNT(gRarePage10)},
};

const struct Habitat gHabitatPtrsTable[9] =
{
	{gGrasslandPages, ARRAY_COUNT(gGrasslandPages)},
	{gForestPages, ARRAY_COUNT(gForestPages)},
	{gWatersEdgePages, ARRAY_COUNT(gWatersEdgePages)},
	{gSeaPages, ARRAY_COUNT(gSeaPages)},
	{gCavePages, ARRAY_COUNT(gCavePages)},
	{gMountainPages, ARRAY_COUNT(gMountainPages)},
	{gRoughTerrainPages, ARRAY_COUNT(gRoughTerrainPages)},
	{gUrbanPages, ARRAY_COUNT(gUrbanPages)},
	{gRarePages, ARRAY_COUNT(gRarePages)},
};

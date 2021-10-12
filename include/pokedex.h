#pragma once

struct PokedexEntry
{
    /*0x00*/ u8 categoryName[12];
    /*0x0C*/ u16 height; //in decimeters
    /*0x0E*/ u16 weight; //in hectograms
    /*0x10*/ const u8* description;
    /*0x14*/ const u8* unusedDescription;
    /*0x18*/ u16 unused;
    /*0x1A*/ u16 pokemonScale;
    /*0x1C*/ u16 pokemonOffset;
    /*0x1E*/ u16 trainerScale;
    /*0x20*/ u16 trainerOffset;
	/*0x22*/ u16 unused2;
};  /*size = 0x24*/

struct AlternateDexEntries
{
	u16 species;
	const u8* description;
};

struct ListMenuItem
{
    const u8* name;
    s32 id;
};

struct PokedexScreenData
{
    u8 field_00;
    u8 field_01;
    u8 field_02;
    u8 field_03;
    u8 field_04;
    u32 field_08;
    u32 field_0C;
    u16 field_10;
    u16 field_12;
    u8 field_14;
    u8 field_15;
    u8 field_16;
    u8 field_17;
    u16 field_18[0x4];
    u8 field_20[0x4];
    u8 field_24[0x4];
    u8 field_28;
    u8 field_29;
    u8 field_2A;
    u8 field_2B;
    u8 field_2C;
    u8 field_2D;
    u8 field_2E;
    u8 field_2F;
    u32 field_30;
    u16 field_34;
    u16 field_36;
    u16 field_38;
    u16 field_3A;
    u16 field_3C;
    u16 field_3E;
    u8 field_40;
    u8 field_41;
    u8 field_42;
    struct ListMenuItem* listItem;
    u16 field_48;
    u8 field_4A[0x10];
    u16 field_5A;
    u16 * field_5C;
    u8 field_60;
    u8 field_61;
    u16 field_62;
    u8 field_64;
    u16 field_66;
    u16 field_68;
    u16 field_6A;
    u16 field_6C;
};

extern struct PokedexScreenData* gPokedexScreenDataPtr;

enum
{
    FLAG_GET_SEEN,
    FLAG_GET_CAUGHT,
    FLAG_SET_SEEN,
    FLAG_SET_CAUGHT
};

// Kulure Dex
#define NATIONAL_DEX_NONE 0
#define NATIONAL_DEX_BIDOOF 1
#define NATIONAL_DEX_BIBAREL 2
#define NATIONAL_DEX_ROOKIDEE 3
#define NATIONAL_DEX_CORVISQUIRE 4
#define NATIONAL_DEX_CORVIKNIGHT 5
#define NATIONAL_DEX_SUNKERN 6
#define NATIONAL_DEX_SUNFLORA 7
#define NATIONAL_DEX_YAMPER 8
#define NATIONAL_DEX_BOLTUND 9
#define NATIONAL_DEX_BUDEW 10
#define NATIONAL_DEX_ROSELIA 11
#define NATIONAL_DEX_ROSERADE 12
#define NATIONAL_DEX_GRUBBIN 13
#define NATIONAL_DEX_CHARJABUG 14
#define NATIONAL_DEX_VIKAVOLT 15
#define NATIONAL_DEX_ROCKRUFF 16
#define NATIONAL_DEX_LYCANROC 17
#define NATIONAL_DEX_NICKIT 18
#define NATIONAL_DEX_THIEVUL 19
#define NATIONAL_DEX_NIDORAN_M 20
#define NATIONAL_DEX_NIDORINO 21
#define NATIONAL_DEX_NIDOKING 22
#define NATIONAL_DEX_BLIPBUG 23
#define NATIONAL_DEX_DOTTLER 24
#define NATIONAL_DEX_ORBEETLE 25
#define NATIONAL_DEX_PIKIPEK 26
#define NATIONAL_DEX_TRUMBEAK 27
#define NATIONAL_DEX_TOUCANNON 28
#define NATIONAL_DEX_MORELULL 29
#define NATIONAL_DEX_SHIINOTIC 30
#define NATIONAL_DEX_HOOTHOOT 31
#define NATIONAL_DEX_NOCTOWL 32
#define NATIONAL_DEX_PICHU 33
#define NATIONAL_DEX_PIKACHU 34
#define NATIONAL_DEX_RAICHU 35
#define NATIONAL_DEX_BUNEARY 36
#define NATIONAL_DEX_LOPUNNY 37
#define NATIONAL_DEX_SHROOMISH 38
#define NATIONAL_DEX_BRELOOM 39
#define NATIONAL_DEX_BONSLY 40
#define NATIONAL_DEX_SUDOWOODO 41
#define NATIONAL_DEX_VENIPEDE 42
#define NATIONAL_DEX_WHIRLIPEDE 43
#define NATIONAL_DEX_SCOLIPEDE 44
#define NATIONAL_DEX_SLAKOTH 45
#define NATIONAL_DEX_VIGOROTH 46
#define NATIONAL_DEX_SLAKING 47
#define NATIONAL_DEX_ZUBAT 48
#define NATIONAL_DEX_GOLBAT 49
#define NATIONAL_DEX_CROBAT 50
#define NATIONAL_DEX_DRILBUR 51
#define NATIONAL_DEX_EXCADRILL 52
#define NATIONAL_DEX_ROGGENROLA 53
#define NATIONAL_DEX_BOLDORE 54
#define NATIONAL_DEX_GIGALITH 55
#define NATIONAL_DEX_LILLIPUP 56
#define NATIONAL_DEX_HERDIER 57
#define NATIONAL_DEX_STOUTLAND 58
#define NATIONAL_DEX_CHINCHOU 59
#define NATIONAL_DEX_LANTURN 60
#define NATIONAL_DEX_RATTATA 61
#define NATIONAL_DEX_RATICATE 62
#define NATIONAL_DEX_FARFETCHD 63
#define NATIONAL_DEX_SIRFETCHD 64
#define NATIONAL_DEX_FLETCHLING 65
#define NATIONAL_DEX_FLETCHINDER 66
#define NATIONAL_DEX_TALONFLAME 67
#define NATIONAL_DEX_FLABEBE 68
#define NATIONAL_DEX_FLOETTE 69
#define NATIONAL_DEX_FLORGES 70
#define NATIONAL_DEX_CUTIEFLY 71
#define NATIONAL_DEX_RIBOMBEE 72
#define NATIONAL_DEX_RALTS 73
#define NATIONAL_DEX_KIRLIA 74
#define NATIONAL_DEX_GARDEVOIR 75
#define NATIONAL_DEX_GALLADE 76
#define NATIONAL_DEX_FERROSEED 77
#define NATIONAL_DEX_FERROTHORN 78
#define NATIONAL_DEX_COMBEE 79
#define NATIONAL_DEX_VESPIQUEN 80
#define NATIONAL_DEX_SCRAGGY 81
#define NATIONAL_DEX_SCRAFTY 82
#define NATIONAL_DEX_CACNEA 83
#define NATIONAL_DEX_CACTURNE 84
#define NATIONAL_DEX_WINGULL 85
#define NATIONAL_DEX_PELIPPER 86
#define NATIONAL_DEX_HELIOPTILE 87
#define NATIONAL_DEX_HELIOLISK 88
#define NATIONAL_DEX_VULLABY 89
#define NATIONAL_DEX_MANDIBUZZ 90
#define NATIONAL_DEX_CASTFORM 91
#define NATIONAL_DEX_CASTFORM 91
#define NATIONAL_DEX_CASTFORM 91
#define NATIONAL_DEX_CASTFORM 91
#define NATIONAL_DEX_TRAPINCH 92
#define NATIONAL_DEX_VIBRAVA 93
#define NATIONAL_DEX_FLYGON 94
#define NATIONAL_DEX_SANDILE 95
#define NATIONAL_DEX_KROKOROK 96
#define NATIONAL_DEX_KROOKODILE 97
#define NATIONAL_DEX_HIPPOPOTAS 98
#define NATIONAL_DEX_HIPPOWDON 99
#define NATIONAL_DEX_CORPHISH 100
#define NATIONAL_DEX_CRAWDAUNT 101
#define NATIONAL_DEX_MAGIKARP 102
#define NATIONAL_DEX_GYARADOS 103
#define NATIONAL_DEX_INKAY 104
#define NATIONAL_DEX_MALAMAR 105
#define NATIONAL_DEX_NINCADA 106
#define NATIONAL_DEX_NINJASK 107
#define NATIONAL_DEX_SHEDINJA 108
#define NATIONAL_DEX_WYNAUT 109
#define NATIONAL_DEX_WOBBUFFET 110
#define NATIONAL_DEX_CARBINK 111
#define NATIONAL_DEX_KLINK 112
#define NATIONAL_DEX_KLANG 113
#define NATIONAL_DEX_KLINKLANG 114
#define NATIONAL_DEX_SABLEYE 115
#define NATIONAL_DEX_MAWILE 116
#define NATIONAL_DEX_SHUCKLE 117
#define NATIONAL_DEX_JANGMO_O 118
#define NATIONAL_DEX_HAKAMO_O 119
#define NATIONAL_DEX_KOMMO_O 120
#define NATIONAL_DEX_CUBCHOO 121
#define NATIONAL_DEX_BEARTIC 122
#define NATIONAL_DEX_SWINUB 123
#define NATIONAL_DEX_PILOSWINE 124
#define NATIONAL_DEX_MAMOSWINE 125
#define NATIONAL_DEX_SNORUNT 126
#define NATIONAL_DEX_GLALIE 127
#define NATIONAL_DEX_FROSLASS 128
#define NATIONAL_DEX_NOIBAT 129
#define NATIONAL_DEX_NOIVERN 130
#define NATIONAL_DEX_TYRUNT 131
#define NATIONAL_DEX_TYRANTRUM 132
#define NATIONAL_DEX_SNEASEL 133
#define NATIONAL_DEX_WEAVILE 134
#define NATIONAL_DEX_SNOM 135
#define NATIONAL_DEX_FROSMOTH 136
#define NATIONAL_DEX_DARUMAKA 137
#define NATIONAL_DEX_DARMANITAN 138
#define NATIONAL_DEX_HOUNDOUR 139
#define NATIONAL_DEX_HOUNDOOM 140
#define NATIONAL_DEX_LARVESTA 141
#define NATIONAL_DEX_VOLCARONA 142
#define NATIONAL_DEX_MINIOR 143
#define NATIONAL_DEX_ROLYCOLY 144
#define NATIONAL_DEX_CARKOL 145
#define NATIONAL_DEX_COALOSSAL 146
#define NATIONAL_DEX_SKARMORY 147
#define NATIONAL_DEX_SALANDIT 148
#define NATIONAL_DEX_SALAZZLE 149
#define NATIONAL_DEX_FRILLISH 150
#define NATIONAL_DEX_JELLICENT 151
#define NATIONAL_DEX_FOONGUS 152
#define NATIONAL_DEX_AMOONGUSS 153
#define NATIONAL_DEX_SHIELDON 154
#define NATIONAL_DEX_BASTIODON 155
#define NATIONAL_DEX_TIMBURR 156
#define NATIONAL_DEX_GURDURR 157
#define NATIONAL_DEX_CONKELDURR 158
#define NATIONAL_DEX_AMAURA 159
#define NATIONAL_DEX_AURORUS 160
#define NATIONAL_DEX_TURTONATOR 161
#define NATIONAL_DEX_MIME_JR 162
#define NATIONAL_DEX_MR_MIME 163
#define NATIONAL_DEX_MR_RIME 164
#define NATIONAL_DEX_SLUGMA 165
#define NATIONAL_DEX_MAGCARGO 166
#define NATIONAL_DEX_HATENNA 167
#define NATIONAL_DEX_HATTREM 168
#define NATIONAL_DEX_HATTERENE 169
#define NATIONAL_DEX_ORANGURU 170
#define NATIONAL_DEX_PASSIMIAN 171
#define NATIONAL_DEX_TORKOAL 172
#define NATIONAL_DEX_LILEEP 173
#define NATIONAL_DEX_CRADILY 174
#define NATIONAL_DEX_SHELLDER 175
#define NATIONAL_DEX_CLOYSTER 176
#define NATIONAL_DEX_SIZZLIPEDE 177
#define NATIONAL_DEX_CENTISKORCH 178
#define NATIONAL_DEX_COTTONEE 179
#define NATIONAL_DEX_WHIMSICOTT 180
#define NATIONAL_DEX_DITTO 181
#define NATIONAL_DEX_EEVEE 182
#define NATIONAL_DEX_VAPOREON 183
#define NATIONAL_DEX_JOLTEON 184
#define NATIONAL_DEX_FLAREON 185
#define NATIONAL_DEX_ESPEON 186
#define NATIONAL_DEX_UMBREON 187
#define NATIONAL_DEX_LEAFEON 188
#define NATIONAL_DEX_GLACEON 189
#define NATIONAL_DEX_SYLVEON 190
#define NATIONAL_DEX_MAREEP 191
#define NATIONAL_DEX_FLAAFFY 192
#define NATIONAL_DEX_AMPHAROS 193
#define NATIONAL_DEX_TOGEPI 194
#define NATIONAL_DEX_TOGETIC 195
#define NATIONAL_DEX_TOGEKISS 196
#define NATIONAL_DEX_MUDBRAY 197
#define NATIONAL_DEX_MUDSDALE 198
#define NATIONAL_DEX_HAPPINY 199
#define NATIONAL_DEX_CHANSEY 200
#define NATIONAL_DEX_BLISSEY 201
#define NATIONAL_DEX_MIENFOO 202
#define NATIONAL_DEX_MIENSHAO 203
#define NATIONAL_DEX_SKIDDO 204
#define NATIONAL_DEX_GOGOAT 205
#define NATIONAL_DEX_RIOLU 206
#define NATIONAL_DEX_LUCARIO 207
#define NATIONAL_DEX_DRATINI 208
#define NATIONAL_DEX_DRAGONAIR 209
#define NATIONAL_DEX_DRAGONITE 210
#define NATIONAL_DEX_PACHIRISU 211
#define NATIONAL_DEX_ROTOM 212
#define NATIONAL_DEX_TOXEL 213
#define NATIONAL_DEX_TOXTRICITY 214
#define NATIONAL_DEX_HORSEA 215
#define NATIONAL_DEX_SEADRA 216
#define NATIONAL_DEX_KINGDRA 217
#define NATIONAL_DEX_CROAGUNK 218
#define NATIONAL_DEX_TOXICROAK 219
#define NATIONAL_DEX_GOOMY 220
#define NATIONAL_DEX_SLIGGOO 221
#define NATIONAL_DEX_GOODRA 222
#define NATIONAL_DEX_SHELLOS 223
#define NATIONAL_DEX_GASTRODON 224
#define NATIONAL_DEX_MIMIKYU 225
#define NATIONAL_DEX_DUSKULL 226
#define NATIONAL_DEX_DUSCLOPS 227
#define NATIONAL_DEX_DUSKNOIR 228
#define NATIONAL_DEX_EMOLGA 229
#define NATIONAL_DEX_CARVANHA 230
#define NATIONAL_DEX_SHARPEDO 231
#define NATIONAL_DEX_HERACROSS 232
#define NATIONAL_DEX_YAMASK 233
#define NATIONAL_DEX_COFAGRIGUS 234
#define NATIONAL_DEX_RUNERIGUS 235
#define NATIONAL_DEX_DHELMISE 236
#define NATIONAL_DEX_PINCURCHIN 237
#define NATIONAL_DEX_MORPEKO 238
#define NATIONAL_DEX_STUNFISK 239
#define NATIONAL_DEX_MISDREAVUS 240
#define NATIONAL_DEX_MISMAGIUS 241
#define NATIONAL_DEX_GRIMER 242
#define NATIONAL_DEX_MUK 243
#define NATIONAL_DEX_GIBLE 244
#define NATIONAL_DEX_GABITE 245
#define NATIONAL_DEX_GARCHOMP 246
#define NATIONAL_DEX_BINACLE 247
#define NATIONAL_DEX_BARBARACLE 248
#define NATIONAL_DEX_MAREANIE 249
#define NATIONAL_DEX_TOXAPEX 250
#define NATIONAL_DEX_KOFFING 251
#define NATIONAL_DEX_WEEZING 252
#define NATIONAL_DEX_ZORUA 253
#define NATIONAL_DEX_ZOROARK 254
#define NATIONAL_DEX_LAPRAS 255
#define NATIONAL_DEX_CRABRAWLER 256
#define NATIONAL_DEX_CRABOMINABLE 257
#define NATIONAL_DEX_PHANTUMP 258
#define NATIONAL_DEX_TREVENANT 259
#define NATIONAL_DEX_SANDYGAST 260
#define NATIONAL_DEX_PALOSSAND 261
#define NATIONAL_DEX_SLOWPOKE 262
#define NATIONAL_DEX_SLOWBRO 263
#define NATIONAL_DEX_SLOWKING 264
#define NATIONAL_DEX_CORSOLA 265
#define NATIONAL_DEX_CURSOLA 266
#define NATIONAL_DEX_FALINKS 267
#define NATIONAL_DEX_PAWNIARD 268
#define NATIONAL_DEX_BISHARP 269
#define NATIONAL_DEX_ELGYEM 270
#define NATIONAL_DEX_BEHEEYEM 271
#define NATIONAL_DEX_MANKEY 272
#define NATIONAL_DEX_PRIMEAPE 273
#define NATIONAL_DEX_BERGMITE 274
#define NATIONAL_DEX_AVALUGG 275
#define NATIONAL_DEX_STONJOURNER 276
#define NATIONAL_DEX_DELIBIRD 277
#define NATIONAL_DEX_COMFEY 278
#define NATIONAL_DEX_CUFANT 279
#define NATIONAL_DEX_COPPERAJAH 280
#define NATIONAL_DEX_JOLTIK 281
#define NATIONAL_DEX_GALVANTULA 282
#define NATIONAL_DEX_CARNIVINE 283
#define NATIONAL_DEX_LITLEO 284
#define NATIONAL_DEX_PYROAR 285
#define NATIONAL_DEX_KANGASKHAN 286
#define NATIONAL_DEX_DURALUDON 287

// Legendaries
#define NATIONAL_DEX_ARTICUNO 288
#define NATIONAL_DEX_ZAPDOS 289
#define NATIONAL_DEX_MOLTRES 290
#define NATIONAL_DEX_JIRACHI 291
#define NATIONAL_DEX_SHAYMIN 292
#define NATIONAL_DEX_KYOGRE 293
#define NATIONAL_DEX_GROUDON 294
#define NATIONAL_DEX_VOLCANION 295
#define NATIONAL_DEX_ZARUDE 296
#define NATIONAL_DEX_GLASTRIER 297
#define NATIONAL_DEX_MELTAN 298
#define NATIONAL_DEX_MELMETAL 299
#define NATIONAL_DEX_VICTINI 300

// Starters and UBs
#define NATIONAL_DEX_BULBASAUR 301
#define NATIONAL_DEX_IVYSAUR 302
#define NATIONAL_DEX_VENUSAUR 303
#define NATIONAL_DEX_CHARMANDER 304
#define NATIONAL_DEX_CHARMELEON 305
#define NATIONAL_DEX_CHARIZARD 306
#define NATIONAL_DEX_SQUIRTLE 307
#define NATIONAL_DEX_WARTORTLE 308
#define NATIONAL_DEX_BLASTOISE 309
#define NATIONAL_DEX_CHIKORITA 310
#define NATIONAL_DEX_BAYLEEF 311
#define NATIONAL_DEX_MEGANIUM 312
#define NATIONAL_DEX_CYNDAQUIL 313
#define NATIONAL_DEX_QUILAVA 314
#define NATIONAL_DEX_TYPHLOSION 315
#define NATIONAL_DEX_TOTODILE 316
#define NATIONAL_DEX_CROCONAW 317
#define NATIONAL_DEX_FERALIGATR 318
#define NATIONAL_DEX_TREECKO 319
#define NATIONAL_DEX_GROVYLE 320
#define NATIONAL_DEX_SCEPTILE 321
#define NATIONAL_DEX_TORCHIC 322
#define NATIONAL_DEX_COMBUSKEN 323
#define NATIONAL_DEX_BLAZIKEN 324
#define NATIONAL_DEX_MUDKIP 325
#define NATIONAL_DEX_MARSHTOMP 326
#define NATIONAL_DEX_SWAMPERT 327
#define NATIONAL_DEX_TURTWIG 328
#define NATIONAL_DEX_GROTLE 329
#define NATIONAL_DEX_TORTERRA 330
#define NATIONAL_DEX_CHIMCHAR 331
#define NATIONAL_DEX_MONFERNO 332
#define NATIONAL_DEX_INFERNAPE 333
#define NATIONAL_DEX_PIPLUP 334
#define NATIONAL_DEX_PRINPLUP 335
#define NATIONAL_DEX_EMPOLEON 336
#define NATIONAL_DEX_SNIVY 337
#define NATIONAL_DEX_SERVINE 338
#define NATIONAL_DEX_SERPERIOR 339
#define NATIONAL_DEX_TEPIG 340
#define NATIONAL_DEX_PIGNITE 341
#define NATIONAL_DEX_EMBOAR 342
#define NATIONAL_DEX_OSHAWOTT 343
#define NATIONAL_DEX_DEWOTT 344
#define NATIONAL_DEX_SAMUROTT 345
#define NATIONAL_DEX_CHESPIN 346
#define NATIONAL_DEX_QUILLADIN 347
#define NATIONAL_DEX_CHESNAUGHT 348
#define NATIONAL_DEX_FENNEKIN 349
#define NATIONAL_DEX_BRAIXEN 350
#define NATIONAL_DEX_DELPHOX 351
#define NATIONAL_DEX_FROAKIE 352
#define NATIONAL_DEX_FROGADIER 353
#define NATIONAL_DEX_GRENINJA 354
#define NATIONAL_DEX_ROWLET 355
#define NATIONAL_DEX_DARTRIX 356
#define NATIONAL_DEX_DECIDUEYE 357
#define NATIONAL_DEX_LITTEN 358
#define NATIONAL_DEX_TORRACAT 359
#define NATIONAL_DEX_INCINEROAR 360
#define NATIONAL_DEX_POPPLIO 361
#define NATIONAL_DEX_BRIONNE 362
#define NATIONAL_DEX_PRIMARINA 363
#define NATIONAL_DEX_GROOKEY 364
#define NATIONAL_DEX_THWACKEY 365
#define NATIONAL_DEX_RILLABOOM 366
#define NATIONAL_DEX_SCORBUNNY 367
#define NATIONAL_DEX_RABOOT 368
#define NATIONAL_DEX_CINDERACE 369
#define NATIONAL_DEX_SOBBLE 370
#define NATIONAL_DEX_DRIZZILE 371
#define NATIONAL_DEX_INTELEON 372
#define NATIONAL_DEX_COSMOG 373
#define NATIONAL_DEX_COSMOEM 374
#define NATIONAL_DEX_SOLGALEO 375
#define NATIONAL_DEX_LUNALA 376
#define NATIONAL_DEX_NIHILEGO 377
#define NATIONAL_DEX_BUZZWOLE 378
#define NATIONAL_DEX_PHEROMOSA 379
#define NATIONAL_DEX_XURKITREE 380
#define NATIONAL_DEX_CELESTEELA 381
#define NATIONAL_DEX_KARTANA 382
#define NATIONAL_DEX_GUZZLORD 383
#define NATIONAL_DEX_NECROZMA 384
#define NATIONAL_DEX_POIPOLE 385
#define NATIONAL_DEX_NAGANADEL 386
#define NATIONAL_DEX_STAKATAKA 387
#define NATIONAL_DEX_BLACEPHALON 388

#define FINAL_DEX_ENTRY NATIONAL_DEX_BLACEPHALON //Not +1 b/c used like this for some asm
#define NATIONAL_DEX_COUNT FINAL_DEX_ENTRY + 1

extern const u8 DEX_ENTRY_TURTWIG[];
extern const u8 DEX_ENTRY_GROTLE[];
extern const u8 DEX_ENTRY_TORTERRA[];
extern const u8 DEX_ENTRY_CHIMCHAR[];
extern const u8 DEX_ENTRY_MONFERNO[];
extern const u8 DEX_ENTRY_INFERNAPE[];
extern const u8 DEX_ENTRY_PIPLUP[];
extern const u8 DEX_ENTRY_PRINPLUP[];
extern const u8 DEX_ENTRY_EMPOLEON[];
extern const u8 DEX_ENTRY_BIDOOF[];
extern const u8 DEX_ENTRY_BIBAREL[];
extern const u8 DEX_ENTRY_BUDEW[];
extern const u8 DEX_ENTRY_ROSERADE[];
extern const u8 DEX_ENTRY_SHIELDON[];
extern const u8 DEX_ENTRY_BASTIODON[];
extern const u8 DEX_ENTRY_COMBEE[];
extern const u8 DEX_ENTRY_VESPIQUEN[];
extern const u8 DEX_ENTRY_PACHIRISU[];
extern const u8 DEX_ENTRY_SHELLOS[];
extern const u8 DEX_ENTRY_GASTRODON[];
extern const u8 DEX_ENTRY_BUNEARY[];
extern const u8 DEX_ENTRY_LOPUNNY[];
extern const u8 DEX_ENTRY_MISMAGIUS[];
extern const u8 DEX_ENTRY_BONSLY[];
extern const u8 DEX_ENTRY_MIME_JR[];
extern const u8 DEX_ENTRY_HAPPINY[];
extern const u8 DEX_ENTRY_GIBLE[];
extern const u8 DEX_ENTRY_GABITE[];
extern const u8 DEX_ENTRY_GARCHOMP[];
extern const u8 DEX_ENTRY_RIOLU[];
extern const u8 DEX_ENTRY_LUCARIO[];
extern const u8 DEX_ENTRY_HIPPOPOTAS[];
extern const u8 DEX_ENTRY_HIPPOWDON[];
extern const u8 DEX_ENTRY_CROAGUNK[];
extern const u8 DEX_ENTRY_TOXICROAK[];
extern const u8 DEX_ENTRY_CARNIVINE[];
extern const u8 DEX_ENTRY_WEAVILE[];
extern const u8 DEX_ENTRY_TOGEKISS[];
extern const u8 DEX_ENTRY_LEAFEON[];
extern const u8 DEX_ENTRY_GLACEON[];
extern const u8 DEX_ENTRY_MAMOSWINE[];
extern const u8 DEX_ENTRY_GALLADE[];
extern const u8 DEX_ENTRY_DUSKNOIR[];
extern const u8 DEX_ENTRY_FROSLASS[];
extern const u8 DEX_ENTRY_ROTOM[];
extern const u8 DEX_ENTRY_SHAYMIN[];
extern const u8 DEX_ENTRY_VICTINI[];
extern const u8 DEX_ENTRY_SNIVY[];
extern const u8 DEX_ENTRY_SERVINE[];
extern const u8 DEX_ENTRY_SERPERIOR[];
extern const u8 DEX_ENTRY_TEPIG[];
extern const u8 DEX_ENTRY_PIGNITE[];
extern const u8 DEX_ENTRY_EMBOAR[];
extern const u8 DEX_ENTRY_OSHAWOTT[];
extern const u8 DEX_ENTRY_DEWOTT[];
extern const u8 DEX_ENTRY_SAMUROTT[];
extern const u8 DEX_ENTRY_LILLIPUP[];
extern const u8 DEX_ENTRY_HERDIER[];
extern const u8 DEX_ENTRY_STOUTLAND[];
extern const u8 DEX_ENTRY_ROGGENROLA[];
extern const u8 DEX_ENTRY_BOLDORE[];
extern const u8 DEX_ENTRY_GIGALITH[];
extern const u8 DEX_ENTRY_DRILBUR[];
extern const u8 DEX_ENTRY_EXCADRILL[];
extern const u8 DEX_ENTRY_TIMBURR[];
extern const u8 DEX_ENTRY_GURDURR[];
extern const u8 DEX_ENTRY_CONKELDURR[];
extern const u8 DEX_ENTRY_VENIPEDE[];
extern const u8 DEX_ENTRY_WHIRLIPEDE[];
extern const u8 DEX_ENTRY_SCOLIPEDE[];
extern const u8 DEX_ENTRY_COTTONEE[];
extern const u8 DEX_ENTRY_WHIMSICOTT[];
extern const u8 DEX_ENTRY_SANDILE[];
extern const u8 DEX_ENTRY_KROKOROK[];
extern const u8 DEX_ENTRY_KROOKODILE[];
extern const u8 DEX_ENTRY_SCRAGGY[];
extern const u8 DEX_ENTRY_SCRAFTY[];
extern const u8 DEX_ENTRY_YAMASK[];
extern const u8 DEX_ENTRY_COFAGRIGUS[];
extern const u8 DEX_ENTRY_ZORUA[];
extern const u8 DEX_ENTRY_ZOROARK[];
extern const u8 DEX_ENTRY_EMOLGA[];
extern const u8 DEX_ENTRY_FOONGUS[];
extern const u8 DEX_ENTRY_AMOONGUSS[];
extern const u8 DEX_ENTRY_FRILLISH[];
extern const u8 DEX_ENTRY_JELLICENT[];
extern const u8 DEX_ENTRY_JOLTIK[];
extern const u8 DEX_ENTRY_GALVANTULA[];
extern const u8 DEX_ENTRY_FERROSEED[];
extern const u8 DEX_ENTRY_FERROTHORN[];
extern const u8 DEX_ENTRY_KLINK[];
extern const u8 DEX_ENTRY_KLANG[];
extern const u8 DEX_ENTRY_KLINKLANG[];
extern const u8 DEX_ENTRY_ELGYEM[];
extern const u8 DEX_ENTRY_BEHEEYEM[];
extern const u8 DEX_ENTRY_CUBCHOO[];
extern const u8 DEX_ENTRY_BEARTIC[];
extern const u8 DEX_ENTRY_MIENFOO[];
extern const u8 DEX_ENTRY_MIENSHAO[];
extern const u8 DEX_ENTRY_PAWNIARD[];
extern const u8 DEX_ENTRY_BISHARP[];
extern const u8 DEX_ENTRY_VULLABY[];
extern const u8 DEX_ENTRY_MANDIBUZZ[];
extern const u8 DEX_ENTRY_LARVESTA[];
extern const u8 DEX_ENTRY_VOLCARONA[];
extern const u8 DEX_ENTRY_CHESPIN[];
extern const u8 DEX_ENTRY_QUILLADIN[];
extern const u8 DEX_ENTRY_CHESNAUGHT[];
extern const u8 DEX_ENTRY_FENNEKIN[];
extern const u8 DEX_ENTRY_BRAIXEN[];
extern const u8 DEX_ENTRY_DELPHOX[];
extern const u8 DEX_ENTRY_FROAKIE[];
extern const u8 DEX_ENTRY_FROGADIER[];
extern const u8 DEX_ENTRY_GRENINJA[];
extern const u8 DEX_ENTRY_FLETCHLING[];
extern const u8 DEX_ENTRY_FLETCHINDER[];
extern const u8 DEX_ENTRY_TALONFLAME[];
extern const u8 DEX_ENTRY_LITLEO[];
extern const u8 DEX_ENTRY_PYROAR[];
extern const u8 DEX_ENTRY_FLABEBE[];
extern const u8 DEX_ENTRY_FLOETTE[];
extern const u8 DEX_ENTRY_FLORGES[];
extern const u8 DEX_ENTRY_SKIDDO[];
extern const u8 DEX_ENTRY_GOGOAT[];
extern const u8 DEX_ENTRY_INKAY[];
extern const u8 DEX_ENTRY_MALAMAR[];
extern const u8 DEX_ENTRY_BINACLE[];
extern const u8 DEX_ENTRY_BARBARACLE[];
extern const u8 DEX_ENTRY_HELIOPTILE[];
extern const u8 DEX_ENTRY_HELIOLISK[];
extern const u8 DEX_ENTRY_TYRUNT[];
extern const u8 DEX_ENTRY_TYRANTRUM[];
extern const u8 DEX_ENTRY_AMAURA[];
extern const u8 DEX_ENTRY_AURORUS[];
extern const u8 DEX_ENTRY_SYLVEON[];
extern const u8 DEX_ENTRY_CARBINK[];
extern const u8 DEX_ENTRY_GOOMY[];
extern const u8 DEX_ENTRY_SLIGGOO[];
extern const u8 DEX_ENTRY_GOODRA[];
extern const u8 DEX_ENTRY_PHANTUMP[];
extern const u8 DEX_ENTRY_TREVENANT[];
extern const u8 DEX_ENTRY_BERGMITE[];
extern const u8 DEX_ENTRY_AVALUGG[];
extern const u8 DEX_ENTRY_NOIBAT[];
extern const u8 DEX_ENTRY_NOIVERN[];
extern const u8 DEX_ENTRY_VOLCANION[];
extern const u8 DEX_ENTRY_ROWLET[];
extern const u8 DEX_ENTRY_DARTRIX[];
extern const u8 DEX_ENTRY_DECIDUEYE[];
extern const u8 DEX_ENTRY_LITTEN[];
extern const u8 DEX_ENTRY_TORRACAT[];
extern const u8 DEX_ENTRY_INCINEROAR[];
extern const u8 DEX_ENTRY_POPPLIO[];
extern const u8 DEX_ENTRY_BRIONNE[];
extern const u8 DEX_ENTRY_PRIMARINA[];
extern const u8 DEX_ENTRY_PIKIPEK[];
extern const u8 DEX_ENTRY_TRUMBEAK[];
extern const u8 DEX_ENTRY_TOUCANNON[];
extern const u8 DEX_ENTRY_GRUBBIN[];
extern const u8 DEX_ENTRY_CHARJABUG[];
extern const u8 DEX_ENTRY_VIKAVOLT[];
extern const u8 DEX_ENTRY_CRABRAWLER[];
extern const u8 DEX_ENTRY_CRABOMINABLE[];
extern const u8 DEX_ENTRY_CUTIEFLY[];
extern const u8 DEX_ENTRY_RIBOMBEE[];
extern const u8 DEX_ENTRY_ROCKRUFF[];
extern const u8 DEX_ENTRY_LYCANROC[];
extern const u8 DEX_ENTRY_MAREANIE[];
extern const u8 DEX_ENTRY_TOXAPEX[];
extern const u8 DEX_ENTRY_MUDBRAY[];
extern const u8 DEX_ENTRY_MUDSDALE[];
extern const u8 DEX_ENTRY_MORELULL[];
extern const u8 DEX_ENTRY_SHIINOTIC[];
extern const u8 DEX_ENTRY_SALANDIT[];
extern const u8 DEX_ENTRY_SALAZZLE[];
extern const u8 DEX_ENTRY_COMFEY[];
extern const u8 DEX_ENTRY_ORANGURU[];
extern const u8 DEX_ENTRY_PASSIMIAN[];
extern const u8 DEX_ENTRY_SANDYGAST[];
extern const u8 DEX_ENTRY_PALOSSAND[];
extern const u8 DEX_ENTRY_MINIOR[];
extern const u8 DEX_ENTRY_TURTONATOR[];
extern const u8 DEX_ENTRY_MIMIKYU[];
extern const u8 DEX_ENTRY_DHELMISE[];
extern const u8 DEX_ENTRY_JANGMO_O[];
extern const u8 DEX_ENTRY_HAKAMO_O[];
extern const u8 DEX_ENTRY_KOMMO_O[];
extern const u8 DEX_ENTRY_COSMOG[];
extern const u8 DEX_ENTRY_COSMOEM[];
extern const u8 DEX_ENTRY_SOLGALEO[];
extern const u8 DEX_ENTRY_LUNALA[];
extern const u8 DEX_ENTRY_NIHILEGO[];
extern const u8 DEX_ENTRY_BUZZWOLE[];
extern const u8 DEX_ENTRY_PHEROMOSA[];
extern const u8 DEX_ENTRY_XURKITREE[];
extern const u8 DEX_ENTRY_CELESTEELA[];
extern const u8 DEX_ENTRY_KARTANA[];
extern const u8 DEX_ENTRY_GUZZLORD[];
extern const u8 DEX_ENTRY_NECROZMA[];
extern const u8 DEX_ENTRY_POIPOLE[];
extern const u8 DEX_ENTRY_NAGANADEL[];
extern const u8 DEX_ENTRY_STAKATAKA[];
extern const u8 DEX_ENTRY_BLACEPHALON[];
extern const u8 DEX_ENTRY_MELTAN[];
extern const u8 DEX_ENTRY_MELMETAL[];
extern const u8 DEX_ENTRY_GROOKEY[];
extern const u8 DEX_ENTRY_THWACKEY[];
extern const u8 DEX_ENTRY_RILLABOOM[];
extern const u8 DEX_ENTRY_SCORBUNNY[];
extern const u8 DEX_ENTRY_RABOOT[];
extern const u8 DEX_ENTRY_CINDERACE[];
extern const u8 DEX_ENTRY_SOBBLE[];
extern const u8 DEX_ENTRY_DRIZZILE[];
extern const u8 DEX_ENTRY_INTELEON[];
extern const u8 DEX_ENTRY_ROOKIDEE[];
extern const u8 DEX_ENTRY_CORVISQUIRE[];
extern const u8 DEX_ENTRY_CORVIKNIGHT[];
extern const u8 DEX_ENTRY_BLIPBUG[];
extern const u8 DEX_ENTRY_DOTTLER[];
extern const u8 DEX_ENTRY_ORBEETLE[];
extern const u8 DEX_ENTRY_NICKIT[];
extern const u8 DEX_ENTRY_THIEVUL[];
extern const u8 DEX_ENTRY_YAMPER[];
extern const u8 DEX_ENTRY_BOLTUND[];
extern const u8 DEX_ENTRY_ROLYCOLY[];
extern const u8 DEX_ENTRY_CARKOL[];
extern const u8 DEX_ENTRY_COALOSSAL[];
extern const u8 DEX_ENTRY_TOXEL[];
extern const u8 DEX_ENTRY_TOXTRICITY[];
extern const u8 DEX_ENTRY_SIZZLIPEDE[];
extern const u8 DEX_ENTRY_CENTISKORCH[];
extern const u8 DEX_ENTRY_HATENNA[];
extern const u8 DEX_ENTRY_HATTREM[];
extern const u8 DEX_ENTRY_HATTERENE[];
extern const u8 DEX_ENTRY_CURSOLA[];
extern const u8 DEX_ENTRY_SIRFETCHD[];
extern const u8 DEX_ENTRY_MR_RIME[];
extern const u8 DEX_ENTRY_RUNERIGUS[];
extern const u8 DEX_ENTRY_FALINKS[];
extern const u8 DEX_ENTRY_PINCURCHIN[];
extern const u8 DEX_ENTRY_SNOM[];
extern const u8 DEX_ENTRY_FROSMOTH[];
extern const u8 DEX_ENTRY_STONJOURNER[];
extern const u8 DEX_ENTRY_MORPEKO[];
extern const u8 DEX_ENTRY_CUFANT[];
extern const u8 DEX_ENTRY_COPPERAJAH[];
extern const u8 DEX_ENTRY_DURALUDON[];
extern const u8 DEX_ENTRY_ZARUDE[];
extern const u8 DEX_ENTRY_GLASTRIER[];

extern const u8 DEX_ENTRY_RATTATA_A[];
extern const u8 DEX_ENTRY_RATICATE_A[];
extern const u8 DEX_ENTRY_FARFETCHD_G[];
extern const u8 DEX_ENTRY_GRIMER_A[];
extern const u8 DEX_ENTRY_MUK_A[];
extern const u8 DEX_ENTRY_WEEZING_G[];
extern const u8 DEX_ENTRY_MR_MIME_G[];
extern const u8 DEX_ENTRY_ARTICUNO_G[];
extern const u8 DEX_ENTRY_ZAPDOS_G[];
extern const u8 DEX_ENTRY_MOLTRES_G[];
extern const u8 DEX_ENTRY_CORSOLA_G[];
extern const u8 DEX_ENTRY_DARUMAKA_G[];
extern const u8 DEX_ENTRY_DARMANITAN_G[];
extern const u8 DEX_ENTRY_DARMANITAN_G_ZEN[];
extern const u8 DEX_ENTRY_YAMASK_G[];
extern const u8 DEX_ENTRY_STUNFISK_G[];
extern const u8 DEX_ENTRY_LYCANROC_N[];
extern const u8 DEX_ENTRY_LYCANROC_DUSK[];
extern const u8 DEX_ENTRY_NECROZMA_DUSK_MANE[];
extern const u8 DEX_ENTRY_NECROZMA_DAWN_WINGS[];
extern const u8 DEX_ENTRY_NECROZMA_ULTRA[];
extern const u8 DEX_ENTRY_TOXTRICITY_LOW_KEY[];
extern const u8 DEX_ENTRY_MORPEKO_HANGRY[];

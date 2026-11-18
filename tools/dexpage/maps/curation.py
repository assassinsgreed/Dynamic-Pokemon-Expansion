"""Collin's review of the interactive maps (2026-11-01): which markers players need, written by script label so the
choices survive map edits. maps2.classify and web.export read these tables."""

# Maps the ROM still has but that are unused (Olenic Town's three broken interiors)
BROKEN_MAPS = {(5, 3), (5, 4), (5, 5)}

# Map → place, where the PSS file or image name points at the wrong place
PLACE_OF = {
    (22, 0): "Route 12 East",   # "Route12 Rest House": the gatehouse off Route 12 East (to Route 9 / Peradon Forest)
    (20, 0): "Route 11 South",  # its file is named just "Route 11"
    (3, 29): "Route 11 South",  # its image is named just "Route 11"
}
FLOOR_NAMES = {(22, 0): "Rest House", (20, 0): "Mega Refiner House", (3, 29): "Route 11 South",
               (1, 44): "Hidden Chamber",  # Carnelidge Volcano's "Volcanion Room"
               (1, 71): "Marsh Cave"}  # Mimmett Jungle's "Zeraora Room"

CATEGORY = {"Secret Trail": "Routes", "Calicin Bay": "Routes", "Treasure Beach": "Routes",
            "Heleo Ranch": "Dungeons & landmarks", "Lake Laplaz": "Dungeons & landmarks",
            "Orichelle Garden": "Dungeons & landmarks"}

# A line under the place name
PLACE_NOTES = {"Treasure Beach": "Items here refresh at random as you walk around."}

# People who only chat, sell everyday stock or are part of a scene: sprite only, no marker.
# Every Pokémon Center nurse and every Poké Mart clerk is dropped by rule in web.export.
NO_MARKER = {
    "EventScript_UltraSpace_EclipseVillage_NPCHouses3_Boy", "EventScript_UltraSpace_EclipseVillage_BikeShop_Boy",
    "EventScript_UltraSpace_EclipseVillage_BikeShop_Man", "EventScript_UltraSpace_EclipseVillage_BikeShop_Shopkeeper",
    "EventScript_BruccieVillage_Abby", "EventScript_BruccieVillageNPCHouses_CherishBallGuy",
    "EventScript_BruccieVillageNPCHouses_TutorWife", "EventScript_BruccieVillageNPCHouses_TutorKid",
    "EventScript_DaimynCityFacilities_RestaurauntIris",  # shown with Stella
    "EventScript_DaimynCityNPCHouses_TutorsDaughter", "EventScript_DaimynCityNPCHouses_TutorsSon",
    "EventScript_DaimynCityNPCHouses_MoveDeleterReminderSon", "EventScript_DaimynCityNPCHouses_TradeBuddy",
    "EventScript_DaimynCityMall_GarageSaleMan", "EventScript_DaimynCityMall_RareCollectiblesMan",
    "EventScript_DaimynCityGym_GymExpert",
    "EventScript_EmraldinQuayNPCHouses_CamperMom", "EventScript_EmraldinQuayNPCHouses_TutorSon",
    "EventScript_EmraldinQuayNPCHouses_TutorYoungSon",
    "EventScript_FerroxNPCHouses_TutorsInTowns", "EventScript_FerroxNPCHouses_TradeGirlDad",
    "EventScript_HeleoCity_MoveTutorSon", "EventScript_HeleoCity_ForemanAssistant", "EvenScript_HeleoRanch_Mareep",  # (sic)
    "EventScript_LaplazNPCHouses_ApricornDescriber",
    "EventScript_RhodanziTrainerSchool_MainRoom_Professor", "EventScript_RhodanziFacilities_Center_UsingFacility",
    "EventScript_RhodanziFacilities_Center_Trade",
    "EventScript_TsarvosaCity_Gym_Attendant", "EventScript_TsarvosaCity_StatsDojo_Kaito",
    "EventScript_TsarvosaCity_StatsDojo_EVReducingBerryShop", "EventScript_TsarvosaCity_StatsDojo_VitaminShop",
    "EventScript_TsarvosaCity_StatsDojo_PowerItemShop", "EventScript_TsarvosaCity_NPCHouses_SlowbroGTradeMother",
    "EventScript_TsarvosaCity_NPCHouses_MoveTutorGirlfriend",
    "EventScript_PokemonCenter_BirdKeeper",
    "EventScript_Route9_Slowbro",
    "EventScript_Route11South_TeamPlutoClancy", "EventScript_Route11South_TeamPlutoEna",
    "EventScript_Route13_RestHouse_Hiker",
    "EventScript_Route18_RestWoman",
    "EventScript_Route21_VictoryRoadGuard",
    # round 2
    "EventScript_RubarrDesert_StoryEvents", "EventScript_ScaldingSpa_SpaRoom_Picknicker",
    "EventScript_UltraSpace_EclipseVillage_Shopkeeper", "EventScript_BruccieVillage_Wingull",
    "EventScript_CalicinBay_StoryEvents", "EventScript_DaimynCityMall_WaitingGirl", "EventScript_HeleoGym_Slowbro",
    "EventScript_RhodanziNPCHouses_Nidoran",
    "EventScript_BattleFrontier_PokemonCenterOldMan", "EventScript_DaimynCityGym_LeaderChance",  # gym leaders: no marker
}
NO_MARKER_MAPS = {(2, 0)}  # Tsarvosa's Type Trainer House: the Gym Trainee tutors

# Sprites that aren't there when the player walks by
NO_SPRITE = {
    "EventScript_Route3_Assistant",                                  # hands over the DexNav in a scene
    "EventScript_Route13_Hiker_Left", "EventScript_Route13_Hiker_Right",  # the hikers standing in the trees
    "EventScript_Route17_ProfessorHawthorne", "EventScript_Route17_ChampionSelene",  # only in the game's intro
    "EventScript_StarterChoice_Grass", "EventScript_StarterChoice_Fire", "EventScript_StarterChoice_Water",  # Route 17's starter Poké Balls
    "EventScript_AnthraTown_Gabby", "EventScript_AnthraTown_Ty",  # the reporters by the Route 2 entrance
}

# Where a person ends up after their scene (sprite and marker): label → (x, y)
FINAL_SPOT = {
    "EventScript_DaimynCityGym_LeaderChance": (16, 3),  # movesprite2 Chance 0x10 0x3 (daimyn_city_gym.s)
    "EventScript_DaimynFactory_Meltan": (24, 6),        # movesprite2 Meltan 0x18 0x6 (daimyn_factory.s)
}

# Legendary encounters whose script picks the Pokémon by mode: label → (text, postgame)
WILD_NOTES = {
    "EvenScript_HeleoRanch_Ampharos": ("Ampharos (Pidgeot in Divergent)", False),  # the label's typo is CFRU's
    "EventScript_MimmettJungle_Zeraora": ("Zeraora (Zarude in Divergent)", False),
    "EventScript_LaplazNPCHouses_Monty": ("Darkrai (Divergent only)", True),
    "EventScript_CarnelidgeVolcano_Volcanion": ("Volcanion (Heatran in Divergent)", True),
    "EventScript_GlastrierRoom_Glastrier": ("Glastrier (Spectrier in Divergent)", True),
    "EventScript_OrichelleGarden_Shaymin": ("Shaymin (Xerneas in Divergent)", False),
    "EventScript_DaimynFactory_Meltan": ("Meltan (Genesect in Divergent)", False),
}

# Hidden items the player can't reach (leftover data): (map, x, y)
NO_HIDDEN = {((3, 38), 3, 0), ((3, 38), 2, 0), ((3, 41), 1, 0), ((3, 40), 15, 4)}  # Route 20 (2: the Nest Ball, retired), Route 22, Secret Trail

# Ways out that only show the next map, which the player can't walk into: (place, destination)
NO_EXIT = {("Route 6", "Daimyn City")}

# What a person or event does, where their script doesn't say it plainly: label → (text, differs by mode, postgame).
# Objects, signs and step triggers alike.
NOTES = {
    "EventScript_LaplazNPCHouses_PsychicSister": ("Psychic Sister: IV Grading Unlock", False, False),
    "EventScript_HeleoFacilities_PokemonCenter_CriticalCapture":
        ("Critical Capture: gives Catch Charm after 10 critical captures", False, False),
    "EventScript_HeleoCity_SwamiResearcher":
        ("Swami Researcher: Bottlecap per unique swarming species shown.", False, False),
    "EventScript_AnthraTown_ChampionFanatic": ("Champion Fanatic: shows your game stats", False, False),
    "EventScript_BruccieVillageNPCHouses_PokeballSwapper":
        ("Poké Ball Swapper: moves a Pokémon into another Poké Ball for 2 PokéChips", False, False),
    "EventScript_DaimynCityFacilities_RestaurauntStella":
        ("Stella and Iris: give UtilUmbrella, TM42 Facade", False, False),
    "EventScript_HeleoCity_ShadyDealer": ("Shady Dealer: trades 1 PokéChip for a random item, Potion to Nugget",
                                          False, False),
    "EventScript_HeleoCity_PokemonGroomer":
        ("Pokémon Groomer: grooms one Pokémon a day for ₽1,000, raising its friendship", False, False),
    "EventScript_HeleoCity_SwarmSwami": ("Swarm Swami: tells you where today's swarm is", False, False),
    "TileScript_LakeLaplaz_GalarianBirdsCommon":
        ("Galarian Articuno, Zapdos and Moltres appear here, then roam the region at Lv 50 "
         "(Tornadus, Thundurus and Landorus in Divergent)", True, False),
    "EventScript_OlenicLab_ToolsDeveloper":
        ("Tools Developer: builds a Poké Vial, Infinite Repel or ADM for 30 PokéChips each", False, True),
    "EventScript_TsarvosaCity_NPCHouses_PokeChipCrusher":
        ("PokéChip Crusher: trades PokéChips for Max Revives, PP Max, Rare Candies, Bottle Caps, Ability Capsules, "
         "Ability Patches, Gold Bottle Caps or a Master Ball", False, False),
    "EventScript_UteyaVillage_Clancy": ("Clancy: changes a Pokémon's Nature for 10 PokéChips", False, False),
    "EventScript_BattleFrontier_PokemonCenterPokeChipBuyer": ("PokéChip exchange", False, False),
    "EventScript_BattleFrontier_PokemonCenterCosplayPikachuLady":
        ("Cosplay Pikachu Lady: gives a Cosplay Pikachu, then changes its costume", False, False),
    "EventScript_TsarvosaCity_NPCHouses_SlowbroGTrade":
        ("Trade: gives you a Galarian Slowbro for a Slowbro (Galarian Rapidash for a Rapidash in Divergent)", True, False),
    "EventScript_BattleFrontier_PokemonCenterWonderPick": ("Wonder Pick", False, False),
    "EventScript_UltraSpace_EclipseVillage_ReturnHomeResearcher":
        ("Researcher: takes you back to the Interdimensional Research Facility", False, False),
    "EventScript_DaimynRestaurant_Chef":
        ("Restaurant Proprietor: serves meals that boost your team for a few battles; donations unlock more of the menu",
         False, False),
    "EventScript_DaimynCityFacilities_PokeballTraveller":
        ("Travelling Man: sells one random Safari, Sport, Park or Dream Ball a day for ₽1,500", False, False),
    "EventScript_FerroxNPCHouses_ChinchouTrade": ("Trade: gives you a Chinchou (Eelektrik in Divergent)", True, False),
    "EventScript_FerroxVillage_UndergroundMiner": ("Digging Minigame", False, False),
    "EventScript_Route11SouthRefiner_RefinerShop": ("Mega Stone Refiner", False, False),
    # a magazine seller who only chats in Standard mode
    "EventScript_DaimynCityMall_MagazineSeller":
        ("Sweets Seller (Divergent only): sells Tart Apple, Sweet Apple, Cracked Pot and the seven Sweets", True, False),
    "SignScript_ForgottenManseStorage_ApplianceCatalog":
        ("Appliance catalog: changes Rotom into its Fan, Frost, Heat, Mow or Wash form, or back", False, False),
}
# The Gym Trainee Cafe (Tsarvosa's Type Trainer House, otherwise unmarked): each trainee stands in their own spot, but
# InitializeGymTraineesCafe (CFRU scripting.c) shows only 3-5 of the 18 each day. Beaten, they tutor a move of their
# type (one of three, rolled daily). build.TUTOR_MARKERS links each to its Tutors entry.
GYM_TRAINEES = {"Noam": "Normal", "Ashley": "Fire", "Chelsea": "Water", "Buddy": "Grass", "Gawain": "Fighting",
                "Skylar": "Flying", "Bella": "Poison", "Flash": "Electric", "Terra": "Ground", "Seifa": "Psychic",
                "Rocco": "Rock", "Janice": "Ice", "Antoinette": "Bug", "Ryu": "Dragon", "Caspar": "Ghost",
                "Darcy": "Dark", "Mason": "Steel", "Faye": "Fairy"}
NOTES.update({f"EventScript_TsarvosaCity_GymTraineeCafe_{name}":
              (f"Gym Trainee {name} ({kind} type, here on some days): move tutor", False, False)
              for name, kind in GYM_TRAINEES.items()})

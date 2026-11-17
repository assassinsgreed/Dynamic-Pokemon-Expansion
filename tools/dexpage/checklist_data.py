"""The Checklist tab's hand-kept half: the order a playthrough goes in, story beats, and corrections.

A first draft written from the dev diary, the trainer tables and the maps, for Collin to correct.
Entry ids are printed by `python -m tools.dexpage.checklist` (place/kind/floor/x-y in map tiles); ids and place
patterns here may use * wildcards where noted.
"""

# Badge number → (name, the place it's won in)
BADGES = {
    1: ("Terrain", "Rhodanzi City"), 2: ("Patch", "Ferrox Village"), 3: ("Stormcloud", "Heleo City"),
    4: ("Roundabout", "Daimyn City"), 5: ("Tactician", "Laplaz Town"), 6: ("Talent", "Bruccie Village"),
    7: ("Support", "Tsarvosa City"), 8: ("Double", "Uteya Village"),
}

# The stage in which each HM comes into the player's hands. With the badge CFRU asks for, that decides where the
# "After … (with Cut)" section goes: after whichever of the two comes later.
HM_FROM = {"Cut": "Ferrox Village", "Rock Smash": "Heleo City", "Fly": "Route 11 South", "Surf": "Pluto HQ",
           "Strength": "Tsarvosa City", "Rock Climb": "Uteyan Ruins"}

# Stops in the order a playthrough first reaches them (the dev diary's milestone order; where the game opens up,
# the order things become available). A stop is a place, or (title, place, floor-name prefixes) for the part of a
# place that opens at another time; the place's own stop keeps the floors no part claims.
ORDER = [
    "Anthra Town", "Route 17", "Route 1", "Olenic Town", "Route 2", "Varisi Forest", "Rhodanzi City",
    "Route 3", "Rubarr Desert", "Route 4", "Torma Cave", "Route 13", "Ferrox Village",
    "Route 5", "Heleo Ranch", "Route 6", "Route 7", "Heleo City",
    "Route 8", "Forgotten Manse", "Daimyn City",
    "Route 9", ("Daimyn Factory Overworld", "Daimyn Factory", ["Overworld"]), "Route 10", "Route 11 South",
    "Hesson Pass", "Route 11 North", "Laplaz Town", "Peradon Forest", "Lake Laplaz",
    "Route 12 East", "Scalding Spa", "Route 12 West", "Bruccie Village", "Calicin Bay", "Pluto HQ",
    ("Route 17 cave", "Route 17", ["Cave"]), "Route 18", "Orichelle Garden",
    "Route 14", "Route 15 North", "Route 15 South", "Route 16", "Route 19", "Emraldin Quay", "Route 20",
    "Treasure Beach", "Route 21", "Mimmett Jungle", "Route 22", "Route 23", "Tsarvosa City",
    "Secret Trail",  # Collin: it can't be explored before Strength, which comes at Tsarvosa City
    "Seppire Cove", "Daimyn Factory", ("Rubarr Desert Caves", "Rubarr Desert", ["Cave", "Caverns"]),
    ("Route 13 cave", "Route 13", ["Cave"]), "Carnelidge Volcano", ("Hesson Pass F2", "Hesson Pass", ["F2"]), "Uteya Village", "Route 24", "Uteyan Ruins",
    "Victory Road", "Ascension Tower",
]

# Places whose every entry is postgame
POSTGAME_PLACES = ["Ultra Space", "Battle Frontier"]

# Story beats per stage: (key, text[, options]). Keys are part of the saved id, so keep them when rewording.
# Options: trainer=(class, name, place in the Trainers tab) links the battle; item=name links the reward's item;
# daily=True (left off the list: never finished); at=place (Postgame only); ultra=True (Postgame: in the Ultra Episode
# section).
STORY = {
    "Anthra Town": [("starter", "Follow the story to choose your starter"),
                    ("gifts", "Receive the Town Map and Running Shoes from Mom")],
    "Route 17": [("rival", "Battle your rival for the first time", {"trainer": ("Rival", "", "Route 17")})],
    "Olenic Town": [("pokedex", "Meet Professor Hawthorne and receive the Pokédex and Poké Balls")],
    "Rhodanzi City": [("gym", "Defeat Leader Terrence for the Terrain Badge", {"trainer": ("Leader", "Terrence", "Rhodanzi City Gym")})],
    "Route 3": [("pluto", "Get past the Pluto Thugs (after the Terrain Badge)"),
                ("rival", "Battle your rival", {"trainer": ("Rival", "", "Route 3")})],
    "Rubarr Desert": [("pluto", "Follow the Team Pluto grunts to the oasis and defeat Admin Irene",
                       {"trainer": ("Pluto Admin", "Irene", "Rubarr Desert")})],
    "Torma Cave": [("landslide", "Bypass the landslide via Torma Cave"),
                   ("casey", "Battle Casey", {"trainer": ("PKMN Trainer", "Casey", "Torma Cave")})],
    "Ferrox Village": [("rival", "Meet your rival outside the gym"),
                       ("library", "Solve the Ferrox Library password puzzle and receive HM01 Cut from Alistair"),
                       ("gym", "Defeat Leader Stella for the Patch Badge", {"trainer": ("Leader", "Stella", "Ferrox Village Gym")})],
    "Heleo City": [("gym", "Defeat Leader Raine for the Stormcloud Badge", {"trainer": ("Leader", "Raine", "Heleo City Gym")}),
                   ("trainer-house", "Trainer House: win the grand prize, the Mach Bike", {"item": "Mach Bike"})],
    "Daimyn City": [("rival", "Battle your rival", {"trainer": ("Rival", "", "Daimyn City")}),
                    ("gym", "Defeat Leader Chance for the Roundabout Badge", {"trainer": ("Leader", "Chance", "Daimyn City Gym")})],
    "Route 9": [("pluto", "Stop Team Pluto at Route 11 South to move Slowbro")],
    "Route 10": [("casey", "Battle Casey", {"trainer": ("PKMN Trainer", "Casey", "Route 10")})],
    "Route 11 South": [("ronald", "Defeat Pluto Admin Ronald", {"trainer": ("Pluto Admin", "Ronald", "Route 11 South")}),
                       ("rival", "Battle your rival and receive HM02 Fly", {"trainer": ("Rival", "", "Route 11 South")})],
    "Laplaz Town": [("gym", "Defeat Leader Casey for the Tactician Badge", {"trainer": ("Leader", "Casey", "Laplaz Town Gym")}),
                    ("trainer-house", "Trainer House: win the grand prize, the Lucky Egg", {"item": "Lucky Egg"})],
    "Scalding Spa": [("yolena", "Defeat Team Pluto Yolena", {"trainer": ("Team Pluto", "Yolena", "Route 12 & Scalding Spa")})],
    "Bruccie Village": [("rival", "Battle your rival to access the gym", {"trainer": ("Rival", "", "Bruccie Village & Calicin Bay")}),
                        ("gym", "Defeat Leader Abby for the Talent Badge", {"trainer": ("Leader", "Abby", "Bruccie Village Gym")})],
    "Calicin Bay": [("pluto", "Battle Team Pluto Clancy and Ena", {"trainer": ("Team Pluto", "Clancy", "Bruccie Village & Calicin Bay")})],
    "Pluto HQ": [("irene", "Defeat Pluto Admin Irene and receive the Serpent Key", {"trainer": ("Pluto Admin", "Irene", "Pluto HQ")}),
                 ("ronald", "Defeat Pluto Admin Ronald and receive the Cerberus Key", {"trainer": ("Pluto Admin", "Ronald", "Pluto HQ")}),
                 ("kurtis", "Defeat Pluto Leader Kurtis and receive HM03 Surf", {"trainer": ("Pluto Leader", "Kurtis", "Pluto HQ")})],
    # (the rival battle here is optional: the rival's side event covers it)
    "Emraldin Quay": [("trainer-house", "Trainer House: win the grand prize, the Item Finder", {"item": "Item Finder"})],
    "Tsarvosa City": [("kaito", "Stats Dojo: defeat Sensei Kaito without items to receive HM04 Strength",
                       {"trainer": ("Sensei", "Kaito", "Tsarvosa City")}),
                      ("gym", "Defeat Leader Iris for the Support Badge", {"trainer": ("Leader", "Iris", "Tsarvosa City Gym")}),
                      ("cafe", "Gym Trainee Cafe: challenge the day's 3 to 5 gym trainees", {"daily": True})],
    "Carnelidge Volcano": [("rival", "Battle your rival", {"trainer": ("Rival", "", "Carnelidge Volcano")}),
                           ("alistair", "Battle Alistair", {"trainer": ("PKMN Trainer", "Alistair", "Carnelidge Volcano")}),
                           ("peak", "See the story through at the peak (the Empty World and Ultra Space)")],
    "Uteya Village": [("gym", "Defeat Leaders Dennis & Dee for the Double Badge", {"trainer": ("Leader", "Dennis&Dee", "Uteya Village Gym")}),
                      ("trainer-house", "Trainer House: win the grand prize, the PokéChip Charm", {"item": "PokeChip Charm"})],
    "Victory Road": [("rival", "Battle your rival", {"trainer": ("Rival", "", "Victory Road")})],
    "Ascension Tower": [("hannah", "Defeat Elite Four Hannah", {"trainer": ("Elite Four", "Hannah", "Ascension Tower & Post Credits")}),
                        ("lucas", "Defeat Elite Four Lucas", {"trainer": ("Elite Four", "Lucas", "Ascension Tower & Post Credits")}),
                        ("jenna", "Defeat Elite Four Jenna", {"trainer": ("Elite Four", "Jenna", "Ascension Tower & Post Credits")}),
                        ("thomas", "Defeat Elite Four Thomas", {"trainer": ("Elite Four", "Thomas", "Ascension Tower & Post Credits")}),
                        ("selene", "Defeat Champion Selene and enter the Hall of Fame", {"trainer": ("Champion", "Selene", "Ascension Tower & Post Credits")})],
    "Postgame": [
        ("title-defense", "Champion Title Defense: defend your title against the 14 possible challengers",
         {"at": "Ascension Tower", "trainer": ("Challenger", "Joey", "Title Defense")}),
        ("e4-hannah", "Elite Four rematch: Hannah", {"at": "Ascension Tower", "trainer": ("Elite Four", "Hannah", "Elite Four Rematches")}),
        ("e4-lucas", "Elite Four rematch: Lucas", {"at": "Ascension Tower", "trainer": ("Elite Four", "Lucas", "Elite Four Rematches")}),
        ("e4-jenna", "Elite Four rematch: Jenna", {"at": "Ascension Tower", "trainer": ("Elite Four", "Jenna", "Elite Four Rematches")}),
        ("e4-thomas", "Elite Four rematch: Thomas", {"at": "Ascension Tower", "trainer": ("Elite Four", "Thomas", "Elite Four Rematches")}),
        ("conservatory", "Professor's Conservatory: catch the starters behind Hawthorne's lab", {"at": "Olenic Town"}),
        ("shiny-charm", "Receive the Shiny Charm from Hawthorne (75% of the Pokédex caught)", {"at": "Olenic Town"}),
        ("diploma", "Receive the Diploma from Hawthorne (Pokédex complete)", {"at": "Olenic Town"}),
        ("rematch-terrence", "Gym Leader rematch: Terrence", {"at": "Rhodanzi City", "daily": True, "trainer": ("Leader", "Terrence", "Gym Leader Rematches")}),
        ("rematch-stella", "Gym Leader rematch: Stella", {"at": "Ferrox Village", "daily": True, "trainer": ("Leader", "Stella", "Gym Leader Rematches")}),
        ("rematch-raine", "Gym Leader rematch: Raine", {"at": "Heleo City", "daily": True, "trainer": ("Leader", "Raine", "Gym Leader Rematches")}),
        ("blissey", "Pokémon Fan Club: battle the Blissey Trainer", {"at": "Heleo City", "daily": True}),
        ("rematch-chance", "Gym Leader rematch: Chance", {"at": "Daimyn City", "daily": True, "trainer": ("Leader", "Chance", "Gym Leader Rematches")}),
        ("ultra-episode", "Ultra Episode: start it at the Interdimensional Research Facility", {"at": "Daimyn City", "ultra": True}),
        ("rematch-casey", "Gym Leader rematch: Casey", {"at": "Laplaz Town", "daily": True, "trainer": ("Leader", "Casey", "Gym Leader Rematches")}),
        ("rematch-abby", "Gym Leader rematch: Abby", {"at": "Bruccie Village", "daily": True, "trainer": ("Leader", "Abby", "Gym Leader Rematches")}),
        ("rematch-iris", "Gym Leader rematch: Iris", {"at": "Tsarvosa City", "daily": True, "trainer": ("Leader", "Iris", "Gym Leader Rematches")}),
        ("rematch-dennis-dee", "Gym Leader rematch: Dennis & Dee", {"at": "Uteya Village", "daily": True, "trainer": ("Leader", "Dennis&Dee", "Gym Leader Rematches")}),
        ("tower", "Battle Tower", {"at": "Battle Frontier"}), ("quarry", "Battle Quarry", {"at": "Battle Frontier"}),
        ("sands", "Battle Sands", {"at": "Battle Frontier"}), ("maze", "Battle Maze", {"at": "Battle Frontier"}),
        ("isle", "Battle Isle", {"at": "Battle Frontier"}), ("sim", "Battle Sim", {"at": "Battle Frontier"}),
        ("factory", "Battle Factory", {"at": "Battle Frontier"}), ("observatory", "Battle Observatory", {"at": "Battle Frontier"}),
    ],
}

# Reworded entries: id → text
TEXT = {
    "ferrox-village/npc/house-1/1-4": "Daily Berry: a girl gives a random Berry each day",
    "ferrox-village/npc/house-3/7-5": "Trade your Snom for a Chinchou (Vanillite for an Eelektrik in Divergent)",
    "rhodanzi-city/npc/trainer-school-basic-class/11-6":
        "Type Student: pass the type quiz to receive a Miracle Seed, Charcoal or Mystic Water (1 of the 3, based on your starter)",
    "daimyn-city/npc/trade-house/8-5": "Trade with the Trade House trader (one trade per save; your Fire starter decides which Pokémon)",
    "daimyn-city/npc/daimyn-mall/12-6": "Fish Seller: sells one Carvanha (Wishiwashi in Divergent) for ₽2,000",
    "daimyn-city/npc/gym/4-2": "Pokémon exchange: buy each Pokémon offered for coins",
    "daimyn-city/npc/gym/5-2": "Item exchange: buy items for coins",
    "tsarvosa-city/npc/npc-house-9/6-4": "Trade your Slowbro for a Galarian Slowbro (Rapidash for a Galarian Rapidash in Divergent)",
    "tsarvosa-city/npc/npc-house-7/5-4": "Dev Team Collin: battle him once a day; gives PokéChip",
    "tsarvosa-city/npc/npc-house-7/8-4": "Dev Team Crystal: battle her once a day; gives PokéChip",
    "battle-frontier/npc/pokemon-center/3-7": "Trade your Heat Rotom for a Ditto (after a 5-win streak at any facility)",
    "ultra-space/npc/ultra-space/38-49": "Poipole Researcher: gives Poipole (once you have caught 150+ Pokémon)",
    "route-19/npc/route-19/67-14": "Selene: gives Victini; switches a max-friendship Greninja to and from Battle Bond",
    "route-13/npc/cave-kurtis-room/4-4": "Battle Kurtis in his hideout",
    "daimyn-city/wild/ash-s-house/7-5": "Pikachu Gift",
    "laplaz-town/npc/laplaz-pokemon-center/10-4": "Gentleman: gives Decoder (after you talk to an NPC at Uteyan Ruins)",
}

# Entries that belong to another stage than their floor's: id → stage title, "Postgame", or "with Strength" for
# that HM's "After … (with Strength)" section
MOVE: dict[str, str] = {
    "daimyn-city/npc/restaurant/9-3": "with Strength",   # Stella and Iris: only once the 7th badge is won
    "daimyn-city/npc/lana-s-house/11-13": "Postgame",    # Lana's PortaPC
    "laplaz-town/npc/laplaz-pokemon-center/10-4": "Uteyan Ruins",  # the Decoder needs a talk at Uteyan Ruins first
    # Hesson Pass: F1 and most of BF1 are open from the start; these two wait for F2 (Strength + Carnelidge Volcano)
    "hesson-pass/item/bf1/29-18": "Hesson Pass F2",      # Charizite X
    "hesson-pass/hidden/bf1/21-13": "Hesson Pass F2",    # Light Clay
    "rubarr-desert/wild/desert/81-34": "Rubarr Desert Caves",
}

# HMs an entry needs, where the feature list says nothing or the wrong thing: id → every HM it needs ([] = none)
NEEDS: dict[str, list] = {
    "route-8/hidden/route-8/1-5": ["Rock Smash"],  # Everstone
    "route-12-west/item/route-12-west/92-36": ["Rock Smash"],  # Zinc
    "route-12-west/item/route-12-west/34-35": ["Rock Smash"],  # Revive
    "route-2/item/area-1/3-74": ["Surf"],          # Nugget
    "torma-cave/item/bf2/5-32": ["Surf"],          # Calcium
    "peradon-forest/item/area-2/42-53": ["Surf"],  # Max Elixir
    "route-19/item/route-19/30-4": ["Cut"],        # Zinc
    # the feature list's "Rare Candy, Route 8 (needs Surf)" is the one in the cave under the Forgotten Manse
    "route-8/hidden/route-8/11-88": [],
    "forgotten-manse/item/underground/2-22": ["Surf"],
}

# HMs a whole place is reached with, so its entries aren't tagged with them (Collin: Routes 14-16 need Surf to explore)
REACHED_WITH = {"Route 14": ["Surf"], "Route 15 North": ["Surf"], "Route 15 South": ["Surf"], "Route 16": ["Surf"]}

# What an HM is called at a place: Surf on Carnelidge Volcano's lava
HM_NAMES = {"Carnelidge Volcano": {"Surf": "Lava Surf"}}

# Entries that exist in one mode only, where the item data doesn't say: id → "Standard" / "Divergent"
ONLY = {
    "route-18/npc/caretaker-house/4-4": "Standard",  # the Shaymin form-change girl (Divergent has Xerneas)
}

# Postgame entries in the Ultra Episode section (ids, * allowed); every Ultra Wormhole goes there too
ULTRA_EPISODE_ENTRIES = ["ultra-space/npc/*", "ultra-space/wild/ultra-space/*", "ultra-space/wild/dias-of-light/*"]

# Floors renamed after their entries were first ticked: (place, floor) → the slug their ids keep
FLOOR_IDS = {("Mimmett Jungle", "Marsh Cave"): "zeraora-room"}

# People the maps mark who are a battle: id → (class, name, place in the Trainers tab)
LINKS: dict[str, tuple] = {
    "route-13/npc/cave-kurtis-room/4-4": ("Pluto Leader", "Kurtis", "Route 13 Cave"),
    "tsarvosa-city/npc/npc-house-7/5-4": ("Developer", "Collin", "Tsarvosa City"),
    "tsarvosa-city/npc/npc-house-7/8-4": ("Developer", "Crystal", "Tsarvosa City"),
    "daimyn-city/npc/restaurant/9-3": ("Leader", "Iris", "Daimyn City Restaurant"),
}

# Entries to leave out (ids, * allowed): HMs handed over as part of a story beat, renewing items, plain services
DROP = [
    "anthra-town/npc/player-home-1st-floor/*",  # Mom's Town Map is part of the opening story beat
    "ferrox-village/npc/library/*",   # Alistair's HM01 Cut is part of the library story beat
    "treasure-beach/hidden/*",        # renew as you walk: never finished
    "olenic-town/npc/area-5/1-7",     # "Hawthorne: trade" (not a trade in trades.csv)
    "pluto-hq/npc/ronald-s-office/*", "pluto-hq/npc/irene-s-office/*",  # their keys are part of the story beats
    # services a player uses as often as they like: nothing to finish
    "heleo-city/npc/swarm-house/8-4",          # Swarm Swami
    "forgotten-manse/npc/closet-1f/*",         # Rotom appliance catalog
    "daimyn-city/npc/restaurant/11-6",         # Restaurant Proprietor
    "daimyn-city/npc/daimyn-mall/50-26",       # Sweets Seller
    "bruccie-village/npc/npc-house-1/*",       # Poké Ball Swapper
    "tsarvosa-city/npc/npc-house-5/*",         # PokéChip Crusher
    "uteya-village/npc/npc-house-2/*",         # Clancy's Nature changes
    "olenic-town/npc/area-5/7-3",              # Tools Developer
    "anthra-town/npc/anthra-town/3-7",         # Champion Fanatic
    "battle-frontier/npc/pokemon-center/13-2",  # PokéChip exchange
    "ultra-space/npc/ultra-space/29-50",       # the researcher who takes you home
    "route-11-south/npc/mega-refiner-house/7-4",  # Mega Stone Refiner (a shop; its map text no longer says so)
]

# What in a save file says an entry is done, where save_flags.py can't tell on its own: id → conditions, done when
# any holds; [] = nothing in the save says so. A condition is a flag number, var(n, at_least), item("ITEM_X") (in the
# bag) or both(...); another entry's id instead of the list means "done when that one is". Battles with a trainer link, item balls, hidden items, one-off Pokémon and people whose script
# checks and sets one flag need no line here. Flags and their meanings are from CFRU's overworld scripts.
def var(number: int, at_least: int) -> list:
    return ["v", number, at_least]


def item(const: str) -> list:
    return ["i", const]


def both(*conditions) -> list:
    return ["&", *conditions]


ULTRA_EPISODE = 0x4073  # 2: started; 5: the Ultra Wormholes are open; 11: Ultra Necrozma beaten; 12: over
_wormhole = lambda flag: [both(flag, var(ULTRA_EPISODE, 5))]  # its flag starts set (hidden) until the wormholes open
SAVE: dict[str, list] = {
    "anthra-town/story/starter": [0x828],                   # FLAG_SYS_POKEMON_GET
    "anthra-town/story/gifts": [item("ITEM_TOWN_MAP")],
    "olenic-town/story/pokedex": [0x829],                   # FLAG_SYS_POKEDEX_GET
    # (saves from old versions lack these two flags: the Patch Badge, 0x821, can't be won without either)
    "route-3/story/pluto": [0x232, 0x821],                  # the Route 3 DexNav event with the rival and Pluto
    "torma-cave/story/landslide": [0x255, 0x821],           # battled Casey at the far end of Torma Cave
    "ferrox-village/story/rival": [item("ITEM_HM01_CUT")],  # no flag of its own: it comes before the library
    "ferrox-village/story/library": [item("ITEM_HM01_CUT")],
    "route-9/story/pluto": "route-11-south/story/ronald",   # beating Ronald is what moves Team Pluto on
    "heleo-city/story/trainer-house": [0x24F],              # got the bike
    "laplaz-town/story/trainer-house": [0x26C],             # got the Lucky Egg
    "emraldin-quay/story/trainer-house": [0x252],           # got the Item Finder
    "uteya-village/story/trainer-house": [0x277],           # got the PokéChip Charm
    "heleo-city/npc/pokemon-center/13-2": [item("ITEM_CATCHING_CHARM")],
    "laplaz-town/npc/laplaz-pokemon-center/10-4": [item("ITEM_DECODER")],
    "laplaz-town/npc/laplaz-psychics-house/9-4": [0x92B],   # IV ratings shown (she can switch them off again)
    "lake-laplaz/npc/lake-laplaz/29-31": [0x43],            # the birds have flown off to roam
    "daimyn-city/npc/lana-s-house/11-13": [0x935],          # received the PortaPC (0x834 is only "met Lana")
    "carnelidge-volcano/story/peak": [0x273],               # completed the Carnelidge Volcano events
    "ultra-space/wild/hoenn/29-8": [0x273],                 # the Jirachi of the same story
    "carnelidge-volcano/wild/peak/11-6": [both(0x270, 0x5A)],  # Jirachi awakened, then gone (0x5A alone: not yet shown)
    "carnelidge-volcano/wild/hidden-chamber/10-3": [0x73],  # Volcanion caught, defeated or fled from (0x3C is reused)
    "route-12-west/wild/glastrier-event/7-8": [0x46],       # Glastrier caught, defeated or fled from
    "laplaz-town/wild/laplaz-casey-s-house/1-4": [0x298],   # Darkrai caught
    "postgame/story/shiny-charm": [item("ITEM_SHINY_CHARM")],
    "postgame/story/ultra-episode": [var(ULTRA_EPISODE, 2)],
    "postgame/story/title-defense": [],                     # its trainer flags are cleared for the next defense
    "ultra-space/wild/ultra-space/101-19": [both(0x6E, var(ULTRA_EPISODE, 5))],  # Cosmog caught and reported
    "ultra-space/wild/dias-of-light/15-7": [both(0x6F, 0x289)],  # Ultra Necrozma defeated, then Necrozma caught
    "varisi-forest/wild/varisi-forest/45-30": _wormhole(0x68), "rubarr-desert/wild/desert/66-58": _wormhole(0x65),
    "forgotten-manse/wild/bf/19-2": _wormhole(0x6D), "daimyn-factory/wild/daimyn-factory/45-2": _wormhole(0x66),
    "pluto-hq/wild/b1f/14-1": _wormhole(0x69), "mimmett-jungle/wild/mimmett-jungle/62-49": _wormhole(0x64),
    "seppire-cove/wild/side-room/8-8": _wormhole(0x63), "carnelidge-volcano/wild/exterior/41-21": _wormhole(0x67),
    "uteyan-ruins/wild/overworld/22-17": _wormhole(0x6A),
}

# Once-a-day events the text doesn't already call daily (the diary: trap Pokémon are daily). Ids, * allowed.
# Daily things get no entry (Collin: they aren't completion).
DAILY = [
    "route-1/wild/*", "varisi-forest/wild/*", "route-8/wild/*", "peradon-forest/wild/*", "route-19/wild/*",
    "route-23/wild/*", "heleo-city/npc/heleo-city/55-26",  # Shady Dealer
]

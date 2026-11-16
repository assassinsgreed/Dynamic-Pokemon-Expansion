"""The Checklist tab's hand-kept half: the order a playthrough goes in, story beats, and corrections.

PROOF OF CONCEPT: covers the game up to the second badge. Everything here is a first draft for Collin to correct.
Entry ids are printed by `python -m tools.dexpage.checklist` (place/kind/floor/x-y in map tiles).
"""

# Places in the order a playthrough first reaches them (the dev diary's milestone order).
ORDER = [
    "Anthra Town", "Route 17", "Route 1", "Olenic Town", "Route 2", "Varisi Forest", "Rhodanzi City",
    "Route 3", "Rubarr Desert", "Route 4", "Torma Cave", "Route 13", "Ferrox Village",
]

# Where each badge is earned. An "After badge N (with Cut)" section follows that place.
BADGE_AT = {"Rhodanzi City": 1, "Ferrox Village": 2}

# The preview stops here: anything that needs a later badge goes in the closing "Later in the game" section.
LAST_BADGE = 2

# Story beats per place: (key, text). Keys are part of the saved id, so keep them when rewording.
STORY = {
    "Anthra Town": [("starter", "Choose your starter and battle your rival")],
    "Olenic Town": [("pokedex", "Meet Professor Hawthorne and receive the Pokédex and Poké Balls")],
    "Rhodanzi City": [("gym", "Defeat Leader Terrence for the Terrain Badge")],
    "Route 3": [("pluto", "Get past the Pluto Thugs (after the Terrain Badge)"), ("rival", "Battle your rival")],
    "Rubarr Desert": [("pluto", "Follow the Team Pluto grunts to the oasis and face Clancy and Ena")],
    "Torma Cave": [("foreman", "Help the foreman's crew clear the boulders")],
    "Ferrox Village": [("rival", "Meet your rival outside the gym"),
                       ("library", "Solve the Ferrox Library password puzzle"),
                       ("gym", "Defeat Leader Stella for the Patch Badge")],
}

# Parts of an early place that open much later: (place, floor-name prefix) → why. Guesses, to be corrected.
LATER_FLOORS = {
    ("Route 17", "Cave"): "Route 17 revisited",
    ("Rubarr Desert", "Caverns"): "Rubarr Desert Caves",
    ("Route 13", "Cave"): "Carnelidge Volcano climb",
}
# Single entries that open later: id → why
LATER = {
    "rubarr-desert/wild/desert/81-34": "Legendary encounter",
}

# Reworded entries: id → text
TEXT = {
    "ferrox-village/npc/house-1/1-4": "Daily Berry: a girl gives a random Berry each day",
    "ferrox-village/npc/library/16-4": "Alistair: gives HM01 Cut (after the library puzzle)",
}

# Once-a-day events the text doesn't already call "Daily" (the diary: trap Pokémon are daily)
DAILY = {
    "route-1/wild/route-1/*",
    "varisi-forest/wild/varisi-forest/*",
}

# Item names to list although marts sell them, and to leave out although they don't
INCLUDE: set[str] = set()
EXCLUDE: set[str] = set()

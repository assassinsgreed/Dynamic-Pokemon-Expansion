---
name: amethyst-companion
description: Work on the Pokemon Amethyst Companion web page (tools/dexpage) — the offline, searchable reference of Pokémon, moves, items and locations built from DPE + CFRU source and the built ROM. Use when asked to change, fix, rebuild, preview or extend the companion / dex page / reference site.
---

# Pokemon Amethyst Companion (tools/dexpage)

A Python generator that reads this repo (DPE), the sibling `../Complete-Fire-Red-Upgrade` (CFRU) and the built
ROM `../Complete-Fire-Red-Upgrade/test.gba`, and writes a single self-contained `site/index.html` (plus PWA files)
that Collin hosts on GitHub Pages. Players use it offline (downloaded file or home-screen app).

Design + history: `docs/superpowers/specs/2026-10-28-pokedex-reference-page-design.md`,
`docs/superpowers/plans/2026-10-28-pokedex-reference-page.md`. Branch: `dexpage-reference`.

## Build, test, look

```
python -m pytest tests/dexpage -q          # ~70 tests against the real repos (~30 s)
python -m tools.dexpage --out site         # writes site/; fails loudly on missing ROM / unknown names
```

No JS runtime here, so check the page in headless Chrome. Inject a click script into a copy of the page and
screenshot; open a specific view with a hash (`#rockruff`, `#move-crunch`, `#item-fire-stone`, `#place-route-2`,
`#items`, `#moves`, `#locations`). Chrome's window can't go below ~500 px, so test phone width with an iframe:

```
CH="/c/Program Files/Google/Chrome/Application/chrome.exe"
"$CH" --headless=new --disable-gpu --user-data-dir="$SCRATCH/prof" --enable-logging=stderr --hide-scrollbars \
  --window-size=1000,1000 --virtual-time-budget=6000 --screenshot="$SCRATCH/x.png" "file:///$SCRATCH/copy.html#eevee"
# phone: a wrapper page with <iframe src="copy.html#eevee" style="width:390px;height:1100px">, run with --allow-file-access-from-files
# console errors: grep "Uncaught" in the stderr log
```

Collin previews via a private claude.ai artifact (https://claude.ai/artifact/WHK7kT9oh5y4KfizQCjbaN): publish the
`<head>` contents + `<body>` contents of `site/index.html` (no doctype/html wrappers) to the same artifact URL.
He also tests `site/index.html` directly.

## Files

| File | Role |
|---|---|
| `cparse.py` | `#ifdef/#if` resolution against real defines, designated-array / struct / string-table parsing |
| `load_dpe.py` | dex lists, habitat forms, base stats, learnsets, egg moves (first entry wins), TM/tutor files (number from **filename**), evolutions, names, front sprites |
| `load_cfru.py` | moves (Z/Max dropped), ability names + per-species renames (`GetAbilityNameOverride`), ability descriptions (positional table: ROM addresses + CFRU strings), shop stock (`pokemart` lists in `assembly/overworld_scripts`) |
| `rom.py` | item names and item icons (icon table found via literal pool near `AddItemIconSprite` 0x8098758), text at ROM addresses |
| `roster.py` | which Pokémon/forms get rows, Mode labels, special tutors (parsed from `item.c`), egg-move rules (parsed from `daycare.c`), evolution text |
| `locations.py` + `encounters.csv` | wild/gift/trade encounters from Collin's Google Sheet (Encounters tab, hand-exported CSV) |
| `items.py` + `items.csv`, `machines.csv`, `tutors.csv` | item, TM and tutor locations imported from the feature-list Google Doc (`python -m tools.dexpage.items doc.docx`, needs python-docx) |
| `docs.py` + `docs.json`, `doc_images/` | Docs tab: feature-list topics (H1 group / H2 topic), imported with `python -m tools.dexpage.docs doc.docx`; overlapping topics skipped via `SKIP_GROUPS`/`SKIP_TOPICS` |
| `ability_details.json` | Abilities tab's longer explanation per ability (keyed by the name shown) + `moves`: CFRU move-table names (`gPunchingMoves`…) whose moves show as chips. Hand-written from CFRU's code, not Bulbapedia; the build fails if it's out of step with the page's abilities |
| `build.py` | page data JSON, item list merge (doc + shops + held + evolution items), sprite/icon sheets, site files |
| `template.html` | CSS + markup; `app.js` is the whole UI, inlined at build (`__APP_SCRIPT__`) |
| `sw.js` | service worker; cache name = content hash so installs update |

Data sources and links are listed in memory `amethyst-encounters-sheet`.

## Rules that came from Collin (don't regress)

- Show **in-game names**; search must also accept official/full names (12-char move names, 10-char species names).
- Never edit his data files to make the build work (`Tutour 25` header, cp1252 TM42 file, TM55/77 Psych Up header).
- Trade evolutions and `EVO_GIGANTAMAX` are dropped; `*_GIGA` forms are Megas ("Mega G").
- Level 0 learnset entries show as **Evo** (learned on evolution + relearner).
- Mode label per Pokémon (Standard / Divergent with that dex's number); mode filters sort by that mode's dex number.
- Forms get rows when meaningfully different; supported forms come from `src/Habitat_Table.c`.
- Battle-only forms (Megas) aren't listed as move learners; their entry says they know what the base knows.
- Wild held items belong in the profile, not the location rows. "Used on" is hidden for evolution items that
  already show under Evolves, but kept for form-changing items (Gracidea, Drives, Nectars).
- Look: Amethyst purple palette (game label art: #b27cfa / #320077), Trozei Jirachi header icon
  (`jirachi-trozei.png`, embedded), type-colour tints, equal-width chips, offline help for PC and phone.
- Everything must work from the single downloaded file: no network, no CDNs, no fonts.
- Performance: never put the sprite/icon data URLs in a CSS custom property (`url(var(--sheet))`) — every element
  re-parses the multi-hundred-KB string on each style recalc (Items tab went 195 ms → 13 ms when moved into a
  plain stylesheet rule in app.js). Time changes with a load-event probe that clicks tabs and logs
  `performance.now()` deltas (run without `--virtual-time-budget`, which freezes the clock).
- Views: Pokédex, Moves, Tutors, Abilities, Items, Locations, Docs; each has its own list/cards layout (remembered per browser).
  Back/Forward buttons sit right of the tabs, always visible, disabled when there's nowhere to go.
- Tutor rows like "Fire Fang, or Flame Burst (v1.4+)" resolve to the move the game teaches for that tutor kind
  (move-tutor files for Regular, CFRU special tutors for Special); doc typos fuzzy-match (Breaking Strike → Breaking Swipe).
- Content describes the **latest release** (version tag from `../PokemonShootingStars/Changelog.txt` beside the
  title): "A, or B (v1.4+)" means B; "(v1.4)" tags are dropped from place names.
- Docs text is cleaned at build time (`clean_versions` in docs.py): version history is removed, keeping only what
  is true now ("X (v1.3) or Y (v1.4+)" → Y, "Introduced in v1.4" dropped, "Removed from pool" rows dropped); type
  names become Pokédex type chips only in type-only cells or "<type> type" phrases. docs.json keeps the raw doc text.
- Shell heredocs eat regex backslashes (`` → control char): write regex-heavy edits via a file + Edit/Write.
- Gym Trainee special tutors are grouped per trainee ("one of three chosen each day" is the shared note).
- Moves, Tutors, Items and Locations open an entry in place (under its row, or full-width under its card) with a
  collapse button, like Pokédex rows; links from inside a card open the entry in its own view. The type filter is
  hidden on Items and Locations.
- Abilities tab: one entry per ability *as shown* (CFRU per-species renames make Libero/Protean separate), with
  in-game description and who has it (normal/hidden, incl. Mega forms). Ability names in Pokédex profiles and
  doc table cells that are exactly an ability name link to it.
- Ability details must describe **CFRU's** behavior, checked in its source with `#ifdef`s resolved against `src/config.h` + `include/constants/abilities.h` (e.g. Protean/Libero has no once-per-switch-in limit; `OLD_GALE_WINGS` is off so Gale Wings needs full HP; Flash Fire boosts only Sp. Atk; `FROSTBITE` replaces freezing; Pickup/Honey Gather items go to the bag). Include outside-battle lead effects from `wild_encounter.c`/`build_pokemon.c`/`daycare.c`. Pokémon profiles keep only the in-game line.
- Abilities resolve through **ids**: DPE's constant (its own spelling, e.g. ABILITY_GULPMISSLE) → DPE id → CFRU's
  name/description/rename rules at that id (`ability_ids` in load_cfru.py). Effect chances (Poison Touch 30%,
  Static 33%…) are parsed from the `case ABILITY_X:` blocks in CFRU's battle code (`ability_chances`).
- Move descriptions come from gMoveDescriptions (entry N = move N+1; ROM address or CFRU string) and cards show
  `secondaryEffectChance` as "Effect chance" when it's between 1 and 99%.
- Every TM/HM is an item ("TM02 Dragon Claw", category TMs/HMs) linking to its move; typing a type name in the
  Pokédex lists that type.

## Known gaps / ideas not done yet

- Battle-only habitat forms (Aegislash Blade, Cramorant Gulping, Eiscue Noice, Wishiwashi School, Necrozma Ultra)
  still appear as separate move learners.
- Service worker install not verified on a real phone (headless Chrome CacheStorage error).
- Items with no icon: Running Shoes, Pokedex (no bag icon in game).
- Place cards only list encounter places; item-only places (shops) are reachable through item cards.

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
| `items.py` + `items.csv`, `machines.csv` | item & TM locations imported from the feature-list Google Doc (`python -m tools.dexpage.items doc.docx`, needs python-docx) |
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

## Known gaps / ideas not done yet

- Battle-only habitat forms (Aegislash Blade, Cramorant Gulping, Eiscue Noice, Wishiwashi School, Necrozma Ultra)
  still appear as separate move learners.
- Service worker install not verified on a real phone (headless Chrome CacheStorage error).
- Items with no icon: Running Shoes, Pokedex (no bag icon in game).
- Place cards only list encounter places; item-only places (shops) are reachable through item cards.

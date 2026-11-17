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
| `load_dpe.py` | dex lists, habitat forms, base stats, learnsets, egg moves (first entry wins), TM/tutor files (number from **filename**), evolutions, names, front + back sprites, shiny palettes |
| `load_cfru.py` | moves (Z/Max dropped), ability names + per-species renames (`GetAbilityNameOverride`), ability descriptions (positional table: ROM addresses + CFRU strings), shop stock (`pokemart` lists in `assembly/overworld_scripts`) |
| `rom.py` | item names and item icons (icon table found via literal pool near `AddItemIconSprite` 0x8098758), text at ROM addresses |
| `roster.py` | which Pokémon/forms get rows, Mode labels, special tutors (parsed from `item.c`), egg-move rules (parsed from `daycare.c`), evolution text |
| `locations.py` + `encounters.csv`, `trades.csv` | wild/gift/trade encounters from Collin's Google Sheet (Encounters tab, hand-exported CSV; `trades.csv` is the Trades tab, used only for its "You give" column so trade notes say what to send); only wild methods (`WILD_METHODS`) feed profile held items; `OWN_PLACES` lists sheet rows shown as their own place (Route 9 / "Daimyn City Factory" → Daimyn Factory Overworld, map 1.30; its item balls follow via `field_items.MAP_PLACES`) |
| `items.py` + `items.csv`, `machines.csv`, `tutors.csv` | item, TM and tutor locations imported from the feature-list Google Doc (`python -m tools.dexpage.items doc.docx`, needs python-docx) |
| `docs.py` + `docs.json`, `doc_images/` | Docs tab: feature-list topics (H1 group / H2 topic), imported with `python -m tools.dexpage.docs doc.docx`; overlapping topics skipped via `SKIP_GROUPS`/`SKIP_TOPICS` |
| `ability_details.json` | Abilities tab's longer explanation per ability (keyed by the name shown) + `moves`: CFRU move-table names (`gPunchingMoves`…) whose moves show as chips. Hand-written from CFRU's code, not Bulbapedia; the build fails if it's out of step with the page's abilities |
| `ball_effects.json` | Poké Ball "Effect" text (the feature list has none), keyed by CFRU's `BALL_TYPE_*` = the ROM item table's type byte (+27), since some balls have placeholder constants (Heal Ball is `ITEM_03D`). Hand-written from CFRU's `GetBaseBallCatchOdds` / `ApplyBallSpecialEffect` (Quick Ball is 5x here, Dusk 3x); the build fails if a ball on the page has no entry |
| `town_map.py` | place cards' Town Map: FireRed's region-map section grid in the ROM (`0x3F2490`, [2 layers][15][22], 8×8 px squares from (32, 32)) + section names (`map_section_names`) → each place's squares over `../PokemonShootingStars/graphics/Maps/TownMap.png` (cropped to 208×144); places inside another's square (Pluto HQ, Scalding Spa) are hand-placed in `SPOTS`, and where the grid overstates a place Collin's corrections are in `NOT_PART_OF` / `PLACED_AT`; the italic description under the map comes from `../PokemonShootingStars/designdocs/region/region-layout.md` (`place_descriptions`; split routes use their route's entry) |
| `field_items.py` | item balls + hidden items read from the ROM's map data (gMapGroups → events; item scripts resolved via CFRU `offsets.ini`); skips FireRed's unused Sevii maps, marks Treasure Beach hidden items as renewing |
| `script_items.csv` | hand-written sources the feature list misses (Apricorn balls, Traveller balls, Memories, Drives, relics…), checked against CFRU's scripts |
| `extra_forms.csv` | forms the Habitat table leaves out but players can get (Rotom appliances, Cosplay/Cap Pikachu), with a how-to-get row; never enable them in Habitat_Table.c |
| `trainers.py` | Trainers tab: CFRU's 4 trainer tables with GetTrainerData's fallback order; teams finished like CreateNPCTrainerParty (class IVs / 31 on Extra Hard, Hard nature via GiveMonBestStatNature, Extra Hard EVs in the 2 best base stats, default moves = last 4 level-up); places from gTrainers `#region` headings; variant notes (rival = water starter gen, badge-count gym teams, rematches) from constants + `NOTES`; sprites and class names from the ROM |
| `build.py` | page data JSON, item list merge (doc + shops + held + evolution items), sprite/icon sheets, site files. Sprite sheet keys (`sprites.build_sheet`): `<key>` front, `shiny:` front in the shiny palette, `back:` / `shinyback:`; page mons carry them as `sp` / `ss` / `sb` / `ssb`. The `gBackShinySprite*.png` back PNGs are stored in **shiny** colours (their palette is `gMonShinyPaletteTable`'s), so back shiny = the PNG as is, back regular = its pixels in the front PNG's palette |
| `maps/` | interactive place maps drawn from the ROM: `rom_maps.py` (headers, tilesets, metatile renderer, offsets.ini labels; `init(paths)` before importing `places.py`), `places.py` (which PSS map files form each place, objects + sprites + what each NPC does, floor names/order, stitching edge-joined maps, Rubarr's sand-statue pits), `export.py` (per place: floor pictures as lossless WebP data URIs + markers/warps/exits/edges; `place_maps()` caches in `maps/.cache/` keyed on the ROM, CFRU scripts/offsets, PSS map list and this package — a cold build redraws for ~4 min), `curation.py` (**Collin's per-NPC review**, by script label: NO_MARKER, NO_SPRITE, NOTES, WILD_NOTES, FINAL_SPOT, NO_HIDDEN, NO_EXIT, PLACE_OF, CATEGORY, PLACE_NOTES). `python -m tools.dexpage.maps.export "Route 17"` prints a place's markers |
| `mapview.js` | the map viewer, inlined before app.js; maps live in `<script id="mapdata">` (parsed on first open); app.js links a place to its map by name or `DEX.maps.alias` (`build.MAP_OF`) |
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
- Pokédex Locations table: an encounter found only by day or only by night shows "☀️ Morning/Day" / "🌙 Evening/Night"
  in a Time column between Method and Lv (only when some row needs it; just the icon on phones), and the "… only"
  note is dropped; paired rates stay in Rate.
- Wild held items belong in the profile, not the location rows. "Used on" is hidden for evolution items that
  already show under Evolves, but kept for form-changing items (Gracidea, Drives, Nectars).
- Evolutions with special conditions (male Kirlia → Gallade, Sneasel → Weavile at night) **must** show that
  condition wherever the evolution appears. The text comes from `evolution_text` (roster.py) over
  `src/Evolution Table.c`; item cards list every evolution that is more than "Use <item>" under the Evolves chips,
  since hiding "Used on" dropped the doc's "(male)" / "(Must hold @ night)".
- Header subtitle (shown on phones too): "Where to find (just about) everything | Last updated: Nov 16, 2026" on the
  website, where the date is `document.lastModified` (GitHub Pages' built-in deploy sets Last-Modified; the companion
  repo has no workflow of its own), hidden if the header is missing. The downloaded file has no date; its Download
  button is replaced, beside the link buttons, by "You are using the offline copy" (Collin: it belongs with the
  Download button, not the subtitle; no "go online" hint, since a saved file never updates). Phones: title, then the
  subtitle (lined up under the title text) with "Last updated: …" on its own line and no pipe (the pipe is a CSS
  `::before`), then the link buttons spread out for tapping beside the Download button / offline note; on the Trainers tab
  the Difficulty toggles sit above the count. Trainer list rows keep the right-aligned Level column on phones, as on desktop.
- Look: Amethyst purple palette (game label art: #b27cfa / #320077), Trozei Jirachi header icon
  (`jirachi-trozei.png`, embedded), type-colour tints, equal-width chips, offline help for PC and phone.
- Everything must work from the single downloaded file: no network, no CDNs, no fonts.
- Performance: never put the sprite/icon data URLs in a CSS custom property (`url(var(--sheet))`) — every element
  re-parses the multi-hundred-KB string on each style recalc (Items tab went 195 ms → 13 ms when moved into a
  plain stylesheet rule in app.js). Time changes with a load-event probe that clicks tabs and logs
  `performance.now()` deltas (run without `--virtual-time-budget`, which freezes the clock).
- Views: Pokédex, Moves, Tutors, Abilities, Items, Trainers, Locations, Docs; each has its own list/cards layout (remembered per browser).
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
- List views open an entry in place under its row, with a collapse button. Card (grid) views open it in a pop-up
  over the page instead (Collin: inline expansion split the card grid), closed with ×, the backdrop, Escape or Back; links from inside a card open the entry in its own view.
- No type filter (Collin removed it): typing a type name ("Fire") in the search lists that type in the Pokédex,
  Moves and Tutors, as their search hints say.
- Abilities tab: one entry per ability *as shown* (CFRU per-species renames make Libero/Protean separate), with
  in-game description and who has it (normal/hidden, incl. Mega forms). Ability names in Pokédex profiles and
  doc table cells that are exactly an ability name link to it.
- Ability details must describe **CFRU's** behavior, checked in its source with `#ifdef`s resolved against `src/config.h` + `include/constants/abilities.h` (e.g. Protean/Libero has no once-per-switch-in limit; `OLD_GALE_WINGS` is off so Gale Wings needs full HP; Flash Fire boosts only Sp. Atk; `FROSTBITE` replaces freezing; Pickup/Honey Gather items go to the bag). Include outside-battle lead effects from `wild_encounter.c`/`build_pokemon.c`/`daycare.c`. Pokémon profiles keep only the in-game line.
- Abilities resolve through **ids**: DPE's constant (its own spelling, e.g. ABILITY_GULPMISSLE) → DPE id → CFRU's
  name/description/rename rules at that id (`ability_ids` in load_cfru.py). Effect chances (Poison Touch 30%,
  Static 33%…) are parsed from the `case ABILITY_X:` blocks in CFRU's battle code (`ability_chances`).
- Move descriptions come from gMoveDescriptions (entry N = move N+1; ROM address or CFRU string) and cards show
  `secondaryEffectChance` as "Effect chance" when it's between 1 and 99%.
- Page size: `render()` packs the two most repeated tables only in the written page (move learners as
  `{how: [mon…]}`, Pokémon abilities as indexes into `DEX.abilities`); app.js unpacks them first thing, so
  `page_data()`, the tests and the rest of app.js see the plain shapes. Docs images are embedded as lossless WebP.
  To check a data change is lossless, dump `DEX` from the page in headless Chrome (`--dump-dom` with an injected
  load-event script) and compare with the previous build; pixel-diff screenshots of each tab against it.
  `#move-…` / `#ability-…` hashes open a pop-up that screenshots blank in headless Chrome (already so before this).
- Locations search matches a place's name and what's there, in the chosen mode: Pokémon ("Bidoof"), encounter
  methods ("Grass", "Wormhole") and items ("Full Heal"). The search box waits 120 ms after typing before it runs,
  so a headless probe that types into `#q` must wait longer than that.
- Place cards: one list per method, sorted by floor (sub-area's first floor: outside/exterior, 1F/F1, 2F…, then
  B1F/BF1/Basement…, then named rooms; `floorRank`), then rate (highest first). On All each method is split into Standard,
  Divergent and Both lists with the mode tag beside the method name ("Grass [Standard]"); each encounter is listed
  once, under the tag its row has (Collin: Jirachi in both the Standard and Divergent lists was wrong; it's Both, as in
  the Pokédex). He preferred this to a tag on every chip.
  The Locations list's Found by column gets the width (Location 28%). A time-of-day encounter's chip says when
  ("☀️ 20%", "🌙 20%", "☀️ 10% 🌙 15%"; `times` on encounter rows, from locations.py `_by_time`); a bare rate means
  all day (Collin: Varisi Forest read as 120% when day/night rows looked like all-day ones). Wild chips are 4 across
  (`.chips.wild`), 3 when a list has paired rates or a non-numeric level ("Same Lv as sent").
- Chips never truncate with "…" (Collin: players couldn't tell what "Galari… H." meant): a chip grows taller and
  wraps instead, grid rows stretch so chips stay uniform. Names keep priority (never split mid-word); the right-hand
  detail wraps first; on wild chips the level/rate stays on one line and the form/sub-area drop to a second line.
- An item's Effect is the doc's text, else (`ball_effects.json` for balls, then) the game's bag description from the
  ROM item table (+20); TMs/HMs leave it empty since Teaches shows the move. The doc's Mega Stone "Standard /
  Divergent / Both" column is *where-to-find* info: it becomes "(Standard mode)" on the where lines, not the effect.
  Doc "*" footnotes the item import misses go in `ITEM_FOOTNOTES` (build.py; Ability Capsule/Patch → Battle Bond).
- Every TM/HM is an item ("TM02 Dragon Claw", category TMs/HMs) linking to its move; typing a type name in the
  Pokédex lists that type.
- Shinies live only in the details (Collin: a shiny beside every row was information overload; players open a
  Pokémon to compare near-identical shinies like Farfetch'd-G). Rows and collapsed cards show the normal front sprite.
  The details open with a **Sprites** grid: columns Regular / Shiny ✦, rows Front / Back, at 56 px (112 px was too big).
- Details top row (`.toprow`, one wrapping flex row): Sprites, Base stats, Abilities, Profile side by side on wide
  screens; on phones two rows, sprites + stats, then abilities + profile. The gender line never wraps (the profile
  is at least that wide); egg groups wrap instead, and on phones wild held items stack one per line under their label.

- Interactive maps: see the section below.

## Interactive maps (`maps/` + `mapview.js`)

Each place card has a **View Interactive Map** button that opens `#map-<slug>`: every floor and room of the place
(PSS map files grouped into places), drawn from the ROM with its sprites, with markers laid over it.

**Iterating on what's marked** (Collin's usual feedback: "remove person 4", "X should read Y", "add a marker for Z",
"hide this sprite"):
1. Find the marker's script label: `python -m tools.dexpage.maps.export "Daimyn City"` prints each place's markers
   by kind and number. Numbers count per kind (items 1–4, people 1–4) in floor order, and the label is the CFRU
   `EventScript_…` at that object (grep `assembly/overworld_scripts` for what it does; read the script before writing
   text — e.g. the "Cherish Ball Guy" only chats, the swapper stands next to him).
2. Edit `maps/curation.py` only: `NO_MARKER` (sprite stays), `NO_SPRITE` (gone entirely: intro/cutscene actors),
   `NOTES` (label → text, mode-specific, postgame; also works for signs and step triggers that have no sprite),
   `WILD_NOTES` (legendaries picked by mode: "A (B in Divergent)", postgame), `FINAL_SPOT` (where `movesprite2` leaves
   someone), `NO_HIDDEN` ((map, x, y) of unreachable hidden items), `NO_EXIT`, `PLACE_OF`/`FLOOR_NAMES`,
   `CATEGORY`, `PLACE_NOTES`, `BROKEN_MAPS`. Never special-case in places.py.
3. `python -m tools.dexpage --out site`. Any change in `maps/` (or the ROM, CFRU scripts/offsets.ini, the PSS map
   list) invalidates `maps/.cache/` and the build redraws every map (~4 min); app.js/mapview.js/template changes don't.
4. Check in headless Chrome with `#map-<slug>` (see below), run the tests, commit.

**Collin's rules:**
- Players care about warps, items (incl. hidden) and special NPCs. Never mark Pokémon Center nurses or anyone in a
  Poké Mart (rule in export.py), trainers, gym leaders, chat-only people, obstacles (rocks/boulders/trees: the sprite
  shows them), or anything that spawns in for a scene (unscripted trainer-type objects, every `*Rival*` object except
  the rival side events, flag-hidden actors with no script).
- Rival side events show what they ask and give (`RIVAL_EVENTS` in places.py, from `rival_events.s`).
- TM pickups read "TM67 Smart Strike". Mode-picked things read "A (B in Divergent)" with an S/D tag; no extra
  "differs between Standard and Divergent" sentence. Postgame things carry PG.
- Marker kinds each have an Okabe-Ito colour *and* a shape; the key lists only the kinds on that map.
- Warps: ↑/↓ for stairs between numbered floors (`floor_rank`; BF/Underground count as −1), → for any other warp.
  Clicking a warp scrolls to its other end (both ends light up; a line only if it crosses no other map). Clicking a
  way out opens that place's map. Clicking a key row jumps to its marker; clicking a marker scrolls the key to its
  row (only where the key scrolls beside the maps, never on phones). No action buttons on the card.
- Marker links (for Collin to share): `#map-<place>/<kind>-<n>` (`item-2`, `hidden-4`, `person-15`, `wild-1`,
  `statue-3`). Selecting a marker puts its link in the address bar (replaceState); opening one scrolls to the
  marker, selects it and pulses it 6 times (`.ping.long`). Numbers shift if curation adds or removes a marker of that kind.
- On-page help is exactly: "Click or tap a warp to see where it leads." / "Click or tap a marker in the map to see
  what it is." / "Click or tap a marker in the key to highlight it in the map." (+ a 2× hint on touch screens).
- The map layer sits under the console (`--console-h`), so tabs and Back/Forward stay usable; its own
  "← Back to place details" button, Escape and the header's Back return to the card. A place pop-up behind it is
  hidden (`body.map-open .sheet`). Typing a search or switching tabs closes the map.
- Fit scales floors to the frame and must never scroll inside the maps area (fractional widths at 125% display
  scaling made stray scrollbars); 2× scrolls sideways with `flex-shrink: 0` floors.
- Full-size lossless WebP pictures are fine (~4.4 MB of the ~8 MB page); they sit in `<script id="mapdata">` and are
  parsed on first open.

**How it's built:** `places.py` groups PSS map files into places (image names beat stale `.map` names, longest
whole-word match; `PLACE_OF` fixes the rest), classifies each object (items, hidden items, wild, NPC role from its
script, postgame from hide flags 0x9D/0x6C or a cleared-game load script, Standard/Divergent from `checkflag 0x945`),
draws each sprite's starting frame from CFRU's overworld tables (`gOverworldTableSwitcher` from **offsets.ini** — the
address moves every CFRU build), and stitches edge-joined maps into one picture (Battle Frontier, Mimmett Jungle).
Runtime-changeable sprites (0xFF0n) take the value the map's own load script sets; read those scripts from the
map's own file, because files reuse local labels (four dungeons each have `MapLoadScript_SetLegendarySprite`).
Rubarr's sand-statue pits come from `MapEntryScript_RubarrDesertBF2_SetSand` (`rubarr()`).

**Checking a map:** open `site/index.html#map-rubarr-desert` headless (same recipe as above); inject a load-event
script that clicks `.mapbtn`, `.warp`, `.door`, `.mk` or `.mv-list button` and writes results to `document.title`,
then `--dump-dom`. Smooth scrolling doesn't finish under `--virtual-time-budget`: add `--force-prefers-reduced-motion`
when measuring scroll positions. `--force-device-scale-factor=1.25` reproduces a 1080p monitor at 125%. The page has
no `</body>` inside `#mapdata`, so append probes before the final `</body>`.
Pillow's `getbbox()` on an RGBA difference only looks at alpha: convert to RGB before comparing map pictures.

## Checklist tab (`checklist.py` + `checklist_data.py`)

A playthrough-order list of tick boxes for 100% completion, before Docs. Design:
`docs/superpowers/specs/2026-11-16-companion-checklist-design.md` (the reachability tool in it was not built).

- Entries are the maps' markers (items, hidden items, people/events, wild) plus hand-written story beats. Iterate the
  same way as the maps: `python -m tools.dexpage.checklist` prints every entry with its id
  (`place/kind/floor/x-y` in tiles; ticks are saved under it, so never renumber), then edit **only**
  `checklist_data.py`: `ORDER` (stops; a `(title, place, floor prefixes)` stop is the part of a place that opens at
  another time), `STORY`, `TEXT`, `MOVE`, `LINKS` (marker → trainer), `DROP`, `DAILY`, `INCLUDE`/`EXCLUDE`. A wrong id
  or trainer fails the build. It reads the cached map export, so edits don't redraw maps.
- HM gating: the item data's "(need Cut)" notes and a TM's Requires column, with CFRU's
  `gFieldMoveBadgeRequirements`. An "After … (with HM)" section follows whichever comes later, the badge or the stage
  the HM is received in (`HM_FROM`; Surf's is "After Pluto HQ"). Items in places reached after that stay put, tagged.
- Collin's rules: common items (general Poké Mart stock) get no entry; shops, healers, tutors and other repeatable
  services get none; trades read "Trade your X for Y (A for B in Divergent)"; Cut, Fly and Surf arrive inside a story
  beat (no "gives HM" entry), while Rock Smash, Strength and Rock Climb are errands of their own; rival side events
  say "Until the <next> Badge is obtained"; named bosses link to their trainer entry in the mode the player has chosen;
  each place section has a Location button to its card; the progress bar, legend, controls and the Beta note stay
  stuck under the header; Pokémon named in an entry link to their Pokédex entries; the tab is tagged Beta; one
  layout only (he tried cards and dropped them: sections of uneven length looked chaotic); gift lists are written
  out in full (the maps' "A, B +1" is `tf` on the marker), and story hand-outs (Town Map and Running Shoes) are one
  story tick, not an NPC entry.
- More of Collin's rules: buttons read "See Location" / "See Interactive Map"; no coloured border on sections
  (purple reads as Divergent); Trainer Houses list their grand prize, not the trainers; an item the data says is in
  one mode only is tagged "Divergent only" (`only`; the map shows it as `mo`); what an item needs also shows on the
  interactive map (`rq`, set on the marker by checklist.py; `NEEDS` adds what the feature list lacks); `KEEP` lists a
  common item anyway; `MOVE` to "with Strength" puts an entry in that HM's section. Regional forms are named in
  encounter text ("Alolan Diglett": `wild_name` in places.py). When he says the feature list changed, re-download
  it and run `python -m tools.dexpage.items doc.docx` (skip the docs import unless Docs text changed: it only
  renumbers images).
- Daily things get no entry (Collin: they aren't completion): `daily=True` story beats, `DAILY` ids, text that says
  "daily", and any person whose script flag is in the game's daily range (0xE00-0xEFF). Postgame markers stay.
  `python -m tools.dexpage.checklist` lists what was left out as daily.
- **Load Save File** ticks the list from a `.sav` / `.srm` (the raw 128 KiB flash; save states don't work) and
  replaces the current ticks after a confirm. Each entry's `sv` lists what in the save means done (`save_flags.py`):
  item balls and one-off Pokémon by the flag that hides them, hidden items by 1000 + their id byte (both on the
  map markers as `fg`, with the script label `lb`; checklist.py pops them so the page's map data is unchanged),
  battles by trainer flag (0x500 + id), people by the flag their script checks and sets, and the rest by hand in
  `checklist_data.SAVE` (flags, `var()`, `item()` in the bag, `both()`, or another entry's id). A flag that starts
  set because the object is hidden until an event (Ultra Wormholes, Cosmog, Necrozma, Jirachi) needs a second
  condition. The reader is in app.js (`ckReadSave`) and mirrored in Python (`save_flags.read_save`);
  `python -m tools.dexpage.save_flags <save or folder>` prints what a save ticks ("?" = can't be read). Collin's
  test saves are in `../PokemonShootingStars/saves`. After changing either reader, run both over every save and
  compare (inject `window.__ck = { ckReadSave, ckFromSave }` before `function ckAct` in a copy of the page).
- Ticks: `localStorage["dex-checklist"]`; the Download link writes them into the saved copy as `#saved-checklist`
  (merged once per saved file); Export/Import is a small JSON file. Don't write `/</g` in app.js: the build turns
  every `</` into `<\/`, which breaks a regex literal.

## Known gaps / ideas not done yet

- Maps: the rival's story appearances (e.g. the HM02 hand-over on Route 11 South) are hidden, so those gifts aren't
  marked; Heleo Ranch's "Ampharos, Pidgeot" may be a mode split (unconfirmed, left as is); Rubarr's
  `FillBigHole_Level2/3` use x=0x450 (should be 0x50) — a game script bug, ask Collin before touching CFRU.

- Battle-only habitat forms (Aegislash Blade, Cramorant Gulping, Eiscue Noice, Wishiwashi School, Necrozma Ultra)
  still appear as separate move learners.
- Service worker install not verified on a real phone (headless Chrome CacheStorage error).
- Items with no icon: Running Shoes, Pokedex (no bag icon in game).
- Item-only places get a card only if they're a Town Map place (`DEX.townMap.places`) named in some item's where
  line (Treasure Beach, towns with shops); other item-only spots are reachable through item cards.

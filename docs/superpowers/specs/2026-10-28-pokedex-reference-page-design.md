# Pokédex Reference Page — Design

## Intent

Players of the game regularly ask two kinds of question:

- **"How do I evolve X?"** — they need the trigger in plain words.
- **"Can X learn move Y?" / "Is move Y in the game?"** — recent examples: "is Ceaseless Edge in the game", "does Kangaskhan not learn Power-Up Punch".

Collin wants one reference people can open on a PC or a phone and get those answers fast. He first pictured a Google Sheet; the format is flexible as long as it is intuitive and easy to search. **Where Pokémon and items are found is out of scope.**

## Decisions

| Topic | Decision | Whose |
|---|---|---|
| Medium | A single self-contained static web page (HTML + inline data + sprites), hosted by Collin on **GitHub Pages** | Collin |
| Source of truth | A generator script in this repo reads the source files (and the built ROM, below) and writes the page; Collin reruns it **manually, without Claude**, whenever data changes, then pushes to Pages. Nothing is hand-maintained. | Collin (manual regen); Claude's call (script in repo) |
| Display names | Must be the **in-game names**. Item names (and anything else not in source, e.g. species/move names if missing) are read from `../Complete-Fire-Red-Upgrade/test.gba` — the final built game in the pipeline | Collin |
| Mode label | Every row shows **Standard**, **Divergent**, or **Standard & Divergent** | Collin |
| Trade evolutions | Omit `EVO_TRADE` / `EVO_TRADE_ITEM` entries — trading isn't possible in game. (Verified: every trade entry also has a non-trade route, e.g. Kadabra → Alakazam via Link Stone.) | Collin |
| Alternate forms | Included. A form gets **its own row** when it differs meaningfully from its base (sprite, typing, stats, abilities, or moveset). | Collin |
| Which forms are supported | Uncommented entries in `src/Habitat_Table.c`, plus Mega/Gigantamax/Primal forms reached via `EVO_MEGA` from any in-dex species | Collin (habitat table); Claude's call (Megas from evo table, since the habitat table doesn't list them) |
| Gigantamax | `*_GIGA` forms reached via `EVO_MEGA` with `*_G` stones are **functionally Megas and presented as Megas** — trigger reads "Mega Evolve holding Venusaurite-G" (in-game stone name), never "Gigantamax". The separate `EVO_GIGANTAMAX` entries are unreachable (Dynamax compiled out) and are dropped. | Collin (presentation); builder check (drop `EVO_GIGANTAMAX`) |
| Special tutors | Follow only the `#ifdef`s actually active in CFRU — e.g. Secret Sword / Dragon Ascent / Thousand Arrows compile out because `NATIONAL_DEX_KELDEO/_RAYQUAZA/_ZYGARDE` aren't defined | Claude's call |
| Truth when sources disagree | Code + built ROM, not `PokemonShootingStars/designdocs/` (out of date) | Claude's call |
| Offline use | Players want the info **without internet access**. Two ways, both required: (1) a **"Download for offline use"** link that saves the single self-contained `.html`, which works fully (search, filters, sprites) when opened from disk; (2) the Pages site is an **installable PWA** — web app manifest + service worker that caches the page and assets after one visit, so "Add to Home Screen" gives an icon that works offline. The service worker must pick up a regenerated page (versioned cache, e.g. by content hash) so players don't get stuck on stale data. | Collin |
| PDF export | Not now — loses search/filters; revisit only if asked | Collin |
| Iteration | Ship a first version, iterate from feedback | Collin |
| Name | Page title/app name: **Pokemon Amethyst Pokedex** | Collin (round 2) |
| Locations | **Now in scope** (reverses the original non-goal). Source: the Encounters tab of Collin's "Pokémon Amethyst: Where to Find Every Pokémon" sheet, stored as static `tools/dexpage/encounters.csv`; Collin re-exports it by hand when it changes. Rows match roster entries by name + "(Form)"; unmatched rows are reported by the build. | Collin (round 2) |
| Detail tabs | The expanded entry has tabs: **Level up, Egg moves, TM/HM, Tutor, Locations**, each with its own filter box. Special tutors live under Tutor. | Collin (round 2) |
| Evolutions | Every Pokémon in the evolution chain is clickable and opens that entry | Collin (round 2) |

## Which Pokémon appear

1. **Dex species:** union of `gPokedexOrder_Regional` (Standard, 390) and `gPokedexOrder_Divergent_Regional` (Divergent, 390) in `src/Pokedex_Orders.c`. 94 overlap → ~686 species. Mode comes from list membership.
2. **Habitat forms:** every uncommented `SPECIES_*` in `src/Habitat_Table.c` not already covered (e.g. `RAICHU_A`, `TYPHLOSION_H`, `LYCANROC_N`, `LYCANROC_DUSK`, `ORICORIO_*`, `FLABEBE_BLUE`, `SNEASLER`, `KLEAVOR`, `OVERQWIL`, `GENESECT_*`). Commented-out entries (Rotom appliances, Shaymin Sky, Mimikyu Busted, Minior colours, Darmanitan Zen, …) are **excluded**. Mode: Standard if it sits on a standard habitat page, Divergent if on a `*DivergentPage*`, both if both — or inherit from the base species if that's broader.
3. **Mega / Gigantamax / Primal:** targets of `EVO_MEGA` entries in `src/Evolution Table.c` whose source species is included. Mode inherits from the source species.
4. **Collapse rule:** if a form is identical to its base in sprite, types, stats, abilities and all learnsets, fold it into the base row instead of giving it its own. (In practice nearly every listed form has a distinct sprite, so most get rows.)

Dex number shown: Standard and/or Divergent regional position (both if in both).

## What each row shows

**Collapsed row (scan view):** front sprite · name (+ form label) · type icon(s) · Mode label · BST · dex number(s).

**Expanded row (tap/click):**
- Base stats as compact bars (HP/Atk/Def/SpA/SpD/Spe), abilities incl. hidden — from `src/Base_Stats.c`. Other useful Base_Stats fields (gender ratio, egg groups, catch rate, EV yield, growth rate) in a terse secondary line.
- **Evolution:** the whole family chain with sprites, each arrow labelled in plain English ("Lv. 36", "Use Fire Stone", "Level up at night, high friendship", "Level up holding Razor Claw at night", "Mega: hold Venusaurite"). From `src/Evolution Table.c`; trade entries dropped.
- **Moves**, grouped by how they're learned, each move with type icon + category icon (physical/special/status) + power/accuracy:
  - Level-up (with level) — `src/Learnsets.c`. Level **0** means "learned on evolution, and still offered by the move relearner" — show as **Evo**, not "Lv 0" (Collin).
  - Egg — `src/Egg_Moves.c`
  - TM/HM (with number) — `src/tm_compatibility/*.txt`
  - Tutor — `src/tutor_compatibility/*.txt`
  - Special tutor — rules from CFRU (below), shown with a short note ("Fire types", "Max friendship Dragon types")

## Move search

Typing a move name matches moves as well as Pokémon. A move result shows its type, category, power, accuracy, and **every included Pokémon that learns it, with how** (Lv/Egg/TM##/Tutor/Special). A move that exists but no included Pokémon learns says so; a move not in the game says "not found". This directly answers "is Ceaseless Edge in the game".

## Search & filters

- One search box: matches Pokémon names (and form names) and move names; tolerant of case, spaces, hyphens, apostrophes ("power up punch", "farfetchd").
- Filters: Mode (All / Standard / Divergent), type (one or two).
- No server; everything runs client-side. Offline: see "Offline use" above. Because the downloaded copy must work standalone, all data and sprites must be inside the one `.html` (data URIs / inline JSON), with no external fonts, scripts or CDNs.
- Usable at phone width: one-column rows, tap to expand, no horizontal scroll. Light and dark themes.

## Data sources & gotchas

- **Special tutors** live as code, not a table: `../Complete-Fire-Red-Upgrade/src/item.c` (`CanMonLearnTutorMove` special section + `GetExpandedTutorMove`). Rules: species blocklist (Egg, Blipbug, Combee, Cosmog, Cosmoem, Ditto, Magikarp, Wobbuffet, Wynaut, all Silvally, all Rotom, Shaymin Sky) can't learn any; Draco Meteor = Dragon type at max friendship; Secret Sword = Keldeo; Relic Song = Meloetta; Volt Tackle = Pichu/Pikachu/Raichu line (+ Shinx/Blitzle lines only `#ifdef UNBOUND` — check whether it's defined); Dragon Ascent = Rayquaza; Thousand Arrows/Waves/Core Enforcer = Zygarde; Steel Beam = Steel type or Silvally/Zacian/Zamazenta; and three moves per type for that type. Mirror these rules in the generator (hand-ported is fine — note the source location so it can be re-checked). Check which `#ifdef`s are active.
- **Move data** (type, split, power, accuracy, PP) from `../Complete-Fire-Red-Upgrade/src/Tables/battle_moves.c`; names from `../Complete-Fire-Red-Upgrade/strings/attack_name_table.string`.
- **Join moves by `MOVE_*` constant name, never by numeric ID** — CFRU and DPE disagree on ~156 move IDs (PLA renumbering).
- **TM/tutor files**: first line is the header (`TM01: Work Up`), then species names without the `SPECIES_` prefix.
- **Sprites**: `graphics/frontspr/gFrontSprite###Name.png`; map species → file via `src/Front_Pic_Table.c` rather than guessing names. Some PNGs are indexed and may be sprite sheets (2 frames) — crop to the first frame, and make the palette's transparent colour transparent.
- **Item names** for evolution text: **not in any source file** — read them from the ROM's item table in `../Complete-Fire-Red-Upgrade/test.gba` (e.g. `ITEM_LINK_STONE` displays as "Linking Cord"). Map `ITEM_*` constant → item ID via CFRU's item constants header, then ID → name via the ROM table (locate the table pointer from CFRU/offsets; text uses the game charmap — `charmap.tbl` in this repo). The ROM must be freshly built before regenerating; the script should say so if the file looks stale or a lookup fails rather than silently guessing.
- **TM numbers**: `gTMHMMoves` exists only in the ROM; the `tm_compatibility` file headers (`TM01: Work Up`) are the source copy. Use the headers; optionally cross-check against the ROM and warn on mismatch.
- **Display names**: species and move names as the game shows them ("Farfetch'd", "Mr. Mime", "Type: Null") — from the repos' name strings where present, otherwise from the ROM.
- Don't modify any source data files — read-only. (Collin hand-edits learnsets, tutor files and base stats.)

## Non-goals

- ~~Locations / encounter data~~ (moved into scope in round 2; item locations remain out of scope).
- Trainer data, damage calc, team builder.
- Pokémon outside both dexes (and their forms).

## Anti-goals (would be a failure even if it "works")

- Showing a move as learnable when the game wouldn't allow it, or missing one it would (wrong answers to "can X learn Y" are the whole failure mode).
- Showing trade evolutions.
- A page that's painful on a phone (tiny text, horizontal scrolling, huge download).
- A hand-edited output that drifts from the source files.

## Left to the builder

- Exact visual design, icon style for types/categories (CSS badges or game graphics are both fine), layout details.
- Script language (Python 3.14 is available) and location (suggest `scripts/` or `tools/`), output path.
- Page architecture, as long as it deploys as static files to GitHub Pages and stays small enough to load comfortably on a phone (sprites must be embedded — e.g. one inline sprite-sheet data URI — so the downloaded file works alone).
- Output location (e.g. a `docs/`-style folder Pages can serve, or a separate branch) and a one-line regenerate command documented in the repo.
- Optionally also publish a preview as a claude.ai Artifact during development.
- Sort order (default: by dex number, Standard first, then Divergent-only).

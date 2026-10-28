# Pokédex reference site

Builds a single-page, searchable reference of every Pokémon in the Standard and Divergent dexes (plus supported
forms and Megas): stats, abilities, evolutions, locations, and every way to learn each move. Players can install it to their
home screen or download one `.html` file, and both work offline.

## Regenerate

1. Build the game first. Item names (e.g. "Linking Cord") are read from `../Complete-Fire-Red-Upgrade/test.gba`,
   so that ROM must be up to date.
2. Once: `pip install -r tools/dexpage/requirements.txt`
3. From the repo root:

   ```
   python -m tools.dexpage --out site
   ```

   Options: `--cfru PATH` (CFRU checkout, default `../Complete-Fire-Red-Upgrade`), `--rom PATH` (default
   `<cfru>/test.gba`). The command exits with an error, and writes nothing, if a name can't be found or a source
   file has a shape it doesn't understand.

`site/` then contains `index.html`, `dex.html` (the same page, used by the download link), `sw.js`,
`manifest.webmanifest` and two icons. `site/` is git-ignored.

## Publish on GitHub Pages

Copy the contents of `site/` to whatever your Pages source serves (a `gh-pages` branch or a separate repo) and push.
Upload all six files: the service worker and manifest are what make "Add to Home Screen" work offline. Each
rebuild changes the service worker's cache name, so installed copies pick up the new data the next time the
player opens it with a connection.

## Where the data comes from

| Data | Source |
|---|---|
| Which Pokémon, and their Mode | `src/Pokedex_Orders.c` (both regional dexes), forms from `src/Habitat_Table.c`, Megas from `EVO_MEGA` |
| Stats, abilities, egg groups | `src/Base_Stats.c` |
| Level-up / egg moves | `src/Learnsets.c` (level 0 shows as "Evo"), `src/Egg_Moves.c` |
| TM/HM and tutors | `src/tm_compatibility/`, `src/tutor_compatibility/` |
| Special tutors | parsed from `CanMonLearnTutorMove` in CFRU `src/item.c` |
| Evolutions | `src/Evolution Table.c`; trade and Gigantamax entries are left out |
| Move data and names | CFRU `src/Tables/battle_moves.c`, `strings/attack_name_table.string` |
| Item names | the built ROM |
| Locations | `tools/dexpage/encounters.csv`, a copy of the Encounters tab of the "Where to Find Every Pokémon" sheet |

## Updating locations

Open the sheet, select the **Encounters** tab, choose File → Download → Comma-separated values, save it over
`tools/dexpage/encounters.csv`, and rebuild. Rows are matched by Pokémon name, plus the form in parentheses
(e.g. `Lycanroc (Midnight)`). The build lists any rows it couldn't match, so check its output after an update.

Tests: `python -m pytest tests/dexpage`

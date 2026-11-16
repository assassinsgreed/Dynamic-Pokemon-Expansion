# Companion Checklist tab — design

Date: 2026-11-16. Branch: `dexpage-reference`. Read `.claude/skills/amethyst-companion/SKILL.md` first.

## Intent

Players want to know what there is to do for 100% completion and to tick it off as they play. The Checklist tab is
a playthrough companion: it walks the game in story order, place by place, and tells the player when an earlier
place has something new for them ("After badge 2 (with Cut)": Olenic Town, Route 3…).

Collin's example: Ferrox Village lists the daily berry event, the Chinchou/Eelektrik trade and its story events.

## Goals

- A **Checklist** tab, placed before Docs.
- Sections in rough progress order, following the dev diary's milestone order (each milestone ends at a gym).
- Return-visit sections between places, titled by what unlocked them, listing only what is newly reachable.
- Every **meaningful** thing has a tick box; common pickups do not appear at all.
- Ticks survive closing the browser, with no server: browser storage, baked into the downloaded file, and
  movable between devices by export/import.
- Works from the single downloaded file like everything else on the page.

## Non-goals

- Pokédex completion tracking (seen/caught per species).
- Ticking off ordinary trainers. Gym leaders and bosses appear as story beats.
- Reading a save file.
- A written walkthrough. Entries are one line each.

## Anti-goals

- A list so long that the Chinchou trade is buried under Potions.
- Ticks lost when the page is rebuilt or the game data changes. IDs must be stable across builds.
- A reachability guess shown to players as fact. Computed gating is only ever a draft for the hand file.
- Any network use.

## What counts as meaningful

Always listed:
- NPC markers the maps already show: gifts, trades, daily events, rival side events, special tutors and the like
  (everything `places.py` classifies as `npc` and `curation.NO_MARKER` has not removed).
- Static and scripted wild encounters (`wild` markers).
- Story beats (hand-written, see below).
- Item balls and hidden items whose item is a TM/HM, key item, Mega Stone, evolution item, form-changing item, or
  anything not sold in ordinary marts.

Dropped: an item ball or hidden item whose item is **general Poké Mart stock** — its `where` list in the page's
item data has a "Poké Marts" / "Poké Marts (after N badges)" line (`build.py` already recognises these). That drops
Potion, Repel, Burn Heal, Poké Ball; it keeps Reaper Cloth (one specific shop). Renewing Treasure Beach hidden items
are dropped (they never finish).

Overrides live in the hand file (`INCLUDE` / `EXCLUDE`, by item name or entry ID). The build prints the list of
dropped item names so Collin can review it once.

Builder's call: where exactly the item-category test reads from (page item categories are the obvious source).

## Approaches considered

1. **Hand-kept progress file, drafted by Claude.** Expresses badge and story gates; costs upkeep.
2. **Compute reachability from the ROM.** No upkeep for HM gates, but ledges, scripted blockers and elevation make
   it wrong in hard-to-see ways, and badge/story gates still need a hand file.
3. **Both: the hand file is the truth, a reachability tool drafts it.** — **Collin picked this** ("most reliable").

## Parts

### 1. Entry IDs and extraction (`tools/dexpage/checklist.py`)

Build the entry list from the same classified objects the maps use (`places.py` `classify`), before `export.py`
numbers the markers, so each entry carries:

- `id`: the CFRU script label when the object has one and it is unique within the place; otherwise
  `<group>.<num>.<x>.<y>` (item balls and hidden items share scripts). IDs are what ticks are stored under, so they
  must not depend on marker numbering.
- `place`, `kind` (`item`, `hidden`, `npc`, `wild`, `story`), `text` (the marker text), `pg`, `sd`, and the marker's
  map link (`#map-<slug>/<kind>-<n>`) so a row can open the map at that spot.
- `daily: true` where the text/role marks a daily event (builder: derive from the script or curation text; a small
  `DAILY` set in the hand file is acceptable).

Hooking in without redrawing maps: checklist extraction must not sit inside the cached picture export, or every
checklist edit costs a 4-minute redraw. Keep `checklist_data.py` outside `maps/` or exclude it from the cache key.

### 2. The hand file (`tools/dexpage/checklist_data.py`)

Same spirit as `maps/curation.py`: plain Python data, edited from Collin's numbered notes.

- `STAGES`: the ordered sections. A stage is either a first visit to a place
  (`("Ferrox Village",)`), or a milestone with return visits
  (`("After badge 2 (with Cut)", {"Olenic Town": [ids…], "Route 3": [ids…]})`).
- `STORY`: hand-written story beats per place (`id`, `text`), e.g. gym battles, Team Pluto events.
- `INCLUDE` / `EXCLUDE`, `DAILY`.

Rules:
- An entry not named in any milestone belongs to its place's first-visit section.
- Postgame entries (`pg`) go to a final "Postgame" stage unless the file places them.
- A place with entries but no stage goes to a trailing "Elsewhere" section and the build prints its name.
- An ID in the file that no longer exists **fails the build** with the ID and file line.

First draft of `STAGES` order: from the dev diary (below). First draft of milestone contents: from the reach tool.

### 3. Reachability drafting tool (`python -m tools.dexpage.maps.reach "Route 3"`)

Developer tool only; its output never reaches the page.

- Per place, flood-fill walkable tiles from each way in (warps, exits, map edges) using the map block collision
  bits, treating Cut trees, Rock Smash rocks and Strength boulders (the `hm` objects) as walls and water tiles as
  needing Surf.
- For each entry, report the smallest set of HMs that reaches it from any way in: none, Cut, Surf, Cut+Surf…
- Print in a form that pastes into `STAGES`.
- Known blind spots, stated in its output header: ledges, elevation, scripted blockers (Pluto Thugs), badge gates,
  Waterfall/Rock Climb unless trivial to add. Collin corrects these by hand.

### 4. Page data and tab (`build.py`, `template.html`, `app.js`)

`DEX.checklist`: `[{title, milestone: bool, groups: [{place, entries: [...]}]}]`.

Tab, between Locations and Docs. Text sketch:

```
Checklist                                   132 / 480 done  [▓▓▓░░░░░░░]
[ ] Hide finished    [Export] [Import] [Reset]

▾ Ferrox Village                                               2 / 6
  [x] ◆ Daily  A girl gives a random Berry each day            → map
  [ ] ● Trade  Chinchou for Eelektrik                          → map
  [ ] ★ Story  Beat the Ferrox Gym
▾ After badge 2 (with Cut)                                     0 / 5
    Olenic Town
  [ ] ■ Item   TM45 Attract                                    → map
    Route 3
  [ ] ■ Hidden Rare Candy                                      → map
```

- Kind badges reuse the map key's colour + shape per kind.
- Sections collapse; collapsed state and "Hide finished" are remembered per browser.
- The existing Standard/Divergent mode toggle applies: mode-tagged entries show per the chosen mode, both when none.
- Search box filters entries by text and place.
- A daily entry carries a "Daily" tag; its tick means "done at least once".
- Item names link to the item card, place names to the place card.
- Reset asks for confirmation.

### 5. Saving

- Browser storage key `dex-checklist`: `{v: 1, done: {id: 1}, t: <ms>}`; all access in try/catch like the existing
  settings.
- **Download with ticks baked in:** on the website the Download link's click fetches `dex.html`, inserts
  `<script id="saved-checklist" type="application/json">…</script>`, and saves the result as a Blob. If the fetch
  fails, fall back to today's plain link. On load, a baked block is merged into browser storage once (remember its
  `t` so later un-ticks are not undone).
- **Export / Import:** a small `.json` file (`amethyst-checklist.json`); import merges (union) after confirming.
  This is how ticks move from the downloaded file or phone app to another device.
- Ticks for IDs that no longer exist are kept in storage and ignored.

Builder's call: whether the service worker needs a change for the `dex.html` fetch.

## Dev diary order

"Pokemon Amethyst Dev Diary", ten milestones, each a run of per-place headings ending at a gym. Order from its
table of contents (bodies of milestones 2–10 not yet read; read them when drafting `STORY`):

Anthra Town, Route 17, Route 1, Olenic Town, Route 2, Varisi Forest, Rhodanzi City (badge 1) · Route 3, Rubarr
Desert, Route 4, Torma Cave, Route 13, Ferrox Village (badge 2) · Route 5, Heleo Ranch, Route 6, Route 7, Heleo
City (badge 3) · Route 8, Forgotten Manse, Daimyn City (badge 4) · Route 9, Route 10, Route 11 South, Hesson Pass,
Route 11 North, Laplaz Town (badge 5) · Peradon Forest, Lake Laplaz, Route 12, Scalding Spa, Bruccie Village
(badge 6) · Calicin Bay, Team Pluto HQ, Route 17 revisited, Route 18, Orichelle Garden, Routes 14–16, Route 19,
Emraldin Quay, Route 20, Treasure Beach, Route 21, Mimmett Jungle, Route 22, Secret Trail, Route 23, Tsarvosa City
(badge 7) · Seppire Cove, Rubarr Desert Caves, Carnelidge Volcano, Uteya Village (badge 8) · Route 24, Uteyan
Ruins, Ascension Tower, Victory Road. Battle Frontier and other v1.2–1.4 additions: place by reading those sections.

Badge numbers past the first are inferred from "one gym per milestone"; which HM arrives when is unconfirmed —
Collin confirms the milestone titles.

## Tests (`tests/dexpage`)

- IDs are unique and stable in shape; every hand-file ID resolves.
- Ferrox Village's stage contains the daily berry event and the Chinchou trade.
- A Potion item ball is absent; Reaper Cloth is present.
- Every non-dropped entry lands in exactly one stage.
- The tab sits before Docs.
- Headless-Chrome probe: tick, reload, tick persists; baked block imports once.

## Order of work

1. Extraction + IDs + meaningful filter + tests; print the dropped list for Collin.
2. Tab + saving with a bare `STAGES` (diary order, no milestones yet) — usable already.
3. Reach tool; draft the milestones; draft `STORY` from the diary.
4. Collin's review rounds on gating and story text.

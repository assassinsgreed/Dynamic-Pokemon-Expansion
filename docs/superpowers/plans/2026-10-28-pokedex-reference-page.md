# Pokédex Reference Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Python generator that reads DPE + CFRU source and the built ROM and writes a single self-contained, searchable, offline-capable HTML reference of every Standard/Divergent Pokémon (with forms), their moves, and evolutions.

**Architecture:** `tools/dexpage/` is a small Python package. Loaders parse the C/text sources into plain dicts; `roster.py` decides which species/forms appear and with what Mode; `build.py` serialises everything to one JSON blob, embeds it plus a sprite sheet into `template.html`, and writes `index.html`, `manifest.webmanifest`, `sw.js` and icons to an output folder Collin pushes to GitHub Pages. All UI logic (search, filters, expand, move view) is vanilla JS inside the template.

**Tech Stack:** Python 3.14, pytest, Pillow (sprites). No JS build step, no CDN, no runtime dependencies in the page.

**Spec:** `docs/superpowers/specs/2026-10-28-pokedex-reference-page-design.md`

## Global Constraints

- Source files are **read-only** — never write to `src/`, `strings/`, `graphics/`, or anything in `../Complete-Fire-Red-Upgrade`.
- Paths: DPE root = repo root; CFRU root = `../Complete-Fire-Red-Upgrade` (overridable via `--cfru`); ROM = `<cfru>/test.gba` (overridable via `--rom`).
- Join moves/items/abilities across repos **by constant name** (`MOVE_*`, `ITEM_*`, `ABILITY_*`), never by DPE numeric ID. Index CFRU name tables with **CFRU's** constant values.
- `#ifdef`/`#if` blocks must be resolved against the real active defines (CFRU `src/config.h`, DPE `src/config.h` / `include/` as relevant). Unknown conditional → raise, never guess.
- Display **in-game** names. Item names come from the ROM. Where an in-game name was truncated (12-char move names, 10-char species names), also index the official name for search (e.g. "Endless Edge" must be findable as "Ceaseless Edge").
- Drop `EVO_TRADE`, `EVO_TRADE_ITEM`, and `EVO_GIGANTAMAX`. `*_GIGA` forms via `EVO_MEGA` are presented as **Mega** ("Mega Evolve holding Venusaurite-G"), never "Gigantamax".
- Output page: one `index.html` that works opened from disk with no network — no external URLs of any kind.
- Mobile: no horizontal scroll at 360 px width; light + dark theme via `prefers-color-scheme`.
- Generator fails loudly (non-zero exit, clear message) on a stale/missing ROM or a failed lookup; it never silently falls back to a guessed name.
- Regenerate command (documented in `tools/dexpage/README.md`): `python -m tools.dexpage --out site`.

## Review Focus

1. **Truncated names in search** — searching "ceaseless edge", "Ceaseless-Edge", or "endless edge" must all land on the same move; same for 10-char species names (e.g. Crabominable). Test in Task 2 (`test_move_aliases`) and Task 6 (`test_search_keys`).
2. **Level-0 moves and moves nobody learns** — `LEVEL_UP_MOVE( 0, …)` (262 entries) means "learned on evolution, also in the move relearner"; it must show as **"Evo"**, never "Lv 0", and count as a learner (Ceaseless Edge → Hisuian Samurott). A move in the move table that truly no included Pokémon learns must still appear, saying "No Pokémon learn this move." rather than "not found". Tests in Task 6 (`test_level_zero_is_evo`, `test_move_with_no_learners_is_listed`).
3. **Species blocked from special tutors** — Ditto, Magikarp, every Rotom/Silvally form, Shaymin Sky get *no* special-tutor moves even when their type matches (e.g. Rotom is Electric). Test in Task 4 (`test_special_tutor_blocklist`).
4. **Stale offline copy** — after a regenerate, an installed PWA must fetch the new page on its next online visit. Test in Task 7 (`test_sw_cache_name_tracks_content`).
5. **Forms sharing a base learnset/sprite** — a form identical to its base must not produce a duplicate row, and a form with a different sprite but same moves *must* get a row. Test in Task 4 (`test_collapse_rule`).

---

## File Structure

```
tools/dexpage/
  __init__.py
  __main__.py        # CLI: argparse → build.build(...)
  paths.py           # Paths dataclass (dpe, cfru, rom)
  cparse.py          # define collection, #if resolution, struct/array/string-table parsing
  load_dpe.py        # dex lists, habitat forms, base stats, learnsets, egg moves, tm/tutor files, evolutions, species names, front-pic map
  load_cfru.py       # move table, move/ability names, item constants, special tutor rules
  rom.py             # charmap decode + item-name table lookup in test.gba
  roster.py          # included entries, Mode, collapse rule, special-tutor application, evolution text
  sprites.py         # PNG → cropped, transparent, sprite-sheet + offsets
  build.py           # assemble JSON, render template, write site/
  template.html      # page shell, CSS, JS (search, filters, rows, move view)
  sw.js              # service worker template ({{CACHE}} placeholder)
  README.md          # how to regenerate + deploy
tests/dexpage/
  conftest.py        # session-scoped fixtures loading real repo data once
  test_cparse.py
  test_load_dpe.py
  test_load_cfru.py
  test_rom.py
  test_roster.py
  test_sprites.py
  test_build.py
```

Tests run against the **real** repos (they are the fixtures); `conftest.py` skips ROM-dependent tests with a clear reason if `test.gba` is absent.

---

### Task 1: C-source parsing primitives

**Files:**
- Create: `tools/dexpage/__init__.py`, `tools/dexpage/paths.py`, `tools/dexpage/cparse.py`
- Test: `tests/dexpage/test_cparse.py`, `tests/dexpage/conftest.py`

**Interfaces:**
- Produces:
  - `Paths(dpe: Path, cfru: Path, rom: Path)`; `Paths.default() -> Paths`
  - `collect_defines(*files: Path) -> dict[str, str]` — every uncommented `#define NAME [value]` (value `""` if bare). Follows `#include "..."` only if passed explicitly; don't recurse.
  - `resolve_conditionals(text: str, defines: dict[str, str]) -> str` — drops inactive `#ifdef/#ifndef/#if/#elif/#else/#endif` branches; supports `defined(X)`, `!`, `&&`, `||`, integer comparisons, macro substitution of numeric defines. Raises `UnresolvedConditional(line_no, expr)` on anything else.
  - `strip_comments(text: str) -> str` (`//` and `/* */`)
  - `parse_designated_array(text: str, array_name: str) -> dict[str, str]` — for `T array_name[...] = { [KEY] = <body>, ... };` returns `{KEY: body_text}`.
  - `parse_struct_fields(body: str) -> dict[str, str]` — `.field = value` pairs, values stripped.
  - `parse_string_table(path: Path) -> list[tuple[str, str]]` — `(label, text)` from `#org @NAME_X` blocks in order, skipping the first `#org @gXxx` table label.
  - `parse_int_defines(path: Path, prefix: str) -> dict[str, int]` — `#define PREFIX_FOO 0x5B` → `{"PREFIX_FOO": 91}` (hex/dec).

- [ ] **Step 1: Write failing tests**

```python
def test_resolve_ifdef_else():
    src = "#ifdef A\nx\n#else\ny\n#endif\n"
    assert resolve_conditionals(src, {"A": ""}).split() == ["x"]
    assert resolve_conditionals(src, {}).split() == ["y"]

def test_resolve_if_expression():
    src = "#if (N > 64) && defined(B)\nhit\n#endif\n"
    assert "hit" in resolve_conditionals(src, {"N": "96", "B": ""})
    assert "hit" not in resolve_conditionals(src, {"N": "32", "B": ""})

def test_unresolvable_raises():
    with pytest.raises(UnresolvedConditional):
        resolve_conditionals("#if FOO(1)\nx\n#endif\n", {})

def test_designated_array_and_fields():
    src = "const T gX[] = {\n [SPECIES_A] = { .hp = 1, .type1 = TYPE_FIRE, },\n [SPECIES_B] = { .hp = 2 },\n};"
    arr = parse_designated_array(src, "gX")
    assert list(arr) == ["SPECIES_A", "SPECIES_B"]
    assert parse_struct_fields(arr["SPECIES_A"]) == {"hp": "1", "type1": "TYPE_FIRE"}

def test_real_string_table(paths):
    rows = parse_string_table(paths.cfru / "strings/attack_name_table.string")
    assert rows[0] == ("NAME_MOVE_NONE", "-")
    assert ("NAME_CEASELESS_EDGE", "Endless Edge") in rows

def test_real_item_constants(paths):
    assert parse_int_defines(paths.cfru / "include/constants/items.h", "ITEM_")["ITEM_LINK_STONE"] == 0x5B
```

`conftest.py`: session fixture `paths = Paths.default()`.

- [ ] **Step 2:** `pytest tests/dexpage/test_cparse.py -v` → FAIL (import errors)
- [ ] **Step 3:** Implement. `#if` evaluation: tokenise, replace `defined(X)`/`defined X` with `1/0`, substitute numeric defines, then evaluate with a whitelist (digits, `()!&|<>=` and spaces) converted to Python (`&&`→`and`, `||`→`or`, `!`→`not `); anything else → `UnresolvedConditional`. Brace-matching (not regex) for array/struct bodies.
- [ ] **Step 4:** `pytest tests/dexpage/test_cparse.py -v` → PASS
- [ ] **Step 5:** Commit `feat(dexpage): C-source parsing primitives`

---

### Task 2: DPE + CFRU loaders

**Files:**
- Create: `tools/dexpage/load_dpe.py`, `tools/dexpage/load_cfru.py`
- Test: `tests/dexpage/test_load_dpe.py`, `tests/dexpage/test_load_cfru.py`

**Interfaces:**
- Consumes: Task 1.
- Produces (`load_dpe.py`, all keyed by `SPECIES_*` constant name):
  - `species_ids(p) -> dict[str, int]` (from `include/species.h`)
  - `dex_lists(p) -> tuple[list[str], list[str]]` — (standard, divergent) from `gPokedexOrder_Regional` / `gPokedexOrder_Divergent_Regional`
  - `habitat_forms(p) -> dict[str, set[str]]` — species → `{"standard"}`/`{"divergent"}`/both, from uncommented entries; a page whose array name contains `Divergent` → divergent.
  - `base_stats(p) -> dict[str, dict]` — keys: `hp, atk, def, spa, spd, spe, types[list], abilities[list incl hidden, NONE removed, dupes removed], hidden_ability, catch_rate, gender (float % female | None genderless), egg_groups[list], growth, ev_yield{stat:int}`
  - `levelup(p) -> dict[str, list[tuple[int, str]]]`, `egg_moves(p) -> dict[str, list[str]]`
  - `machine_compat(p) -> list[dict]` — one per file: `{"kind": "TM"|"HM"|"Tutor", "num": int, "move": "MOVE_*", "species": set[str]}`. Header gives kind/num/display; resolve to `MOVE_*` by normalised in-game name match against `load_cfru.moves()` (strip non-alphanumerics, lowercase) — raise on no match.
  - `evolutions(p) -> dict[str, list[tuple[str, str, str, str]]]` — `(method, param, target, extra)` raw strings, after `resolve_conditionals` + `strip_comments`.
  - `species_names(p) -> dict[str, str]` — `strings/Pokemon_Name_Table.string` entry *N* = species id *N*.
  - `front_pic(p) -> dict[str, Path]` — from `src/Front_Pic_Table.c` symbol `gFrontSpriteXXXTiles` → `graphics/frontspr/gFrontSpriteXXX.png`.
- Produces (`load_cfru.py`):
  - `moves(p) -> dict[str, dict]` keyed `MOVE_*`: `{name (in-game), official (title-cased from the NAME_ label, e.g. "Ceaseless Edge"), type ("FIRE"), split ("physical"|"special"|"status"), power, accuracy, pp}`. Names indexed by CFRU move id.
  - `ability_names(p) -> dict[str, str]`
  - `item_ids(p) -> dict[str, int]`

- [ ] **Step 1: Write failing tests**

```python
def test_dex_lists(paths):
    std, div = dex_lists(paths)
    assert len(std) == 390 and len(div) == 390
    assert std[0] == "SPECIES_BIDOOF" and div[0] == "SPECIES_ZIGZAGOON_G"
    assert len(set(std) & set(div)) == 94

def test_habitat_forms(paths):
    hf = habitat_forms(paths)
    assert hf["SPECIES_LYCANROC_DUSK"] == {"standard"}
    assert hf["SPECIES_VULPIX_A"] == {"divergent"}
    assert "SPECIES_ROTOM_HEAT" not in hf          # commented out

def test_bulbasaur(paths):
    b = base_stats(paths)["SPECIES_BULBASAUR"]
    assert (b["hp"], b["atk"], b["spe"]) == (45, 49, 45)
    assert b["types"] == ["GRASS", "POISON"]
    assert b["hidden_ability"] == "ABILITY_CHLOROPHYLL"
    assert b["gender"] == 12.5
    assert levelup(paths)["SPECIES_BULBASAUR"][2] == (3, "MOVE_VINEWHIP")
    assert "MOVE_SKULLBASH" in egg_moves(paths)["SPECIES_BULBASAUR"]

def test_machines(paths):
    mc = {(m["kind"], m["num"]): m for m in machine_compat(paths)}
    assert mc[("HM", 1)]["move"] == "MOVE_CUT"
    assert "SPECIES_BULBASAUR" in mc[("TM", 1)]["species"]
    assert mc[("Tutor", 1)]["move"] == "MOVE_FIREPUNCH"

def test_evolutions_raw(paths):
    evo = evolutions(paths)
    assert ("EVO_ITEM", "ITEM_LINK_STONE", "SPECIES_ALAKAZAM", "0") in evo["SPECIES_KADABRA"]

def test_front_pic(paths):
    assert front_pic(paths)["SPECIES_LYCANROC_N"].name == "gFrontSprite1046LycanrocN.png"

def test_move_aliases(paths):
    m = moves(paths)["MOVE_CEASELESSEDGE"]
    assert m["name"] == "Endless Edge" and m["official"] == "Ceaseless Edge"
    assert (m["type"], m["split"], m["accuracy"]) == ("DARK", "physical", 90)
    # power depends on ACTUAL_PLA_MOVE_POWERS: assert it equals the value in whichever branch config.h activates
```

- [ ] **Step 2:** run → FAIL
- [ ] **Step 3:** Implement. Move `split` field is `.split = SPLIT_PHYSICAL` etc. in `battle_moves.c`; resolve conditionals with CFRU defines first. Move/ability name tables are positional — index by CFRU constant value; assert the table is at least as long as the max id used.
- [ ] **Step 4:** run → PASS
- [ ] **Step 5:** Commit `feat(dexpage): source loaders`

---

### Task 3: ROM item names

**Files:**
- Create: `tools/dexpage/rom.py`
- Test: `tests/dexpage/test_rom.py`

**Interfaces:**
- Produces: `load_charmap(path: Path) -> dict[int, str]` (from DPE `charmap.tbl`; `0xFF` terminator), `item_names(rom: Path, item_ids: dict[str, int]) -> dict[str, str]`, `class RomError(Exception)`.

- [ ] **Step 1: Write failing tests**

```python
def test_link_stone_is_linking_cord(paths, item_ids):
    names = item_names(paths.rom, item_ids)
    assert names["ITEM_LINK_STONE"] == "Linking Cord"
    assert names["ITEM_FIRE_STONE"] == "Fire Stone"
    assert names["ITEM_VENUSAURITE_G"]  # non-empty; replace with the exact ROM spelling once seen

def test_missing_rom_raises(tmp_path, item_ids):
    with pytest.raises(RomError):
        item_names(tmp_path / "nope.gba", item_ids)
```

- [ ] **Step 2:** run → FAIL
- [ ] **Step 3:** Implement. Locate the item table by signature, not a hard-coded offset: scan for the charmap-encoded name of item 1 (`ITEM_MASTER_BALL`) such that the bytes 44 bytes later decode to item 2's name (FR item struct = 44 bytes, name = first 14 bytes, `0xFF`-terminated). Decode each requested id at `base + 44*id`. Raise `RomError` if the signature isn't found exactly once. Confirm the real `Venusaurite-G` spelling once and tighten that assertion.
- [ ] **Step 4:** run → PASS
- [ ] **Step 5:** Commit `feat(dexpage): read in-game item names from ROM`

---

### Task 4: Roster, Mode, special tutors, evolution text

**Files:**
- Create: `tools/dexpage/roster.py`
- Test: `tests/dexpage/test_roster.py`

**Interfaces:**
- Consumes: Tasks 2–3.
- Produces:
  - `Entry` dataclass: `key: str (SPECIES_*)`, `name: str`, `form: str | None` (e.g. "Alolan", "Midnight", "Mega", "Mega X"), `modes: list[str]` (`["Standard"]`, `["Divergent"]`, both), `dex: dict[str,int]` (`{"std": 17}` …), `base: str` (base species key), `stats`, `moves: dict[str, list]` with keys `level` `[(lvl, MOVE)]`, `egg`, `tm` `[(label "TM01", MOVE)]`, `tutor`, `special` `[(MOVE, note)]`, `family: str` (family root key).
  - `build_roster(data) -> list[Entry]` where `data` is a `SourceData` bundle (all loader outputs + item names).
  - `special_tutor_moves(species: str, types: list[str], dex_species: str) -> list[tuple[str, str]]` — `(MOVE_*, note)`.
  - `evolution_links(data, included: set[str]) -> dict[str, list[dict]]` — per species, outgoing `{"to": key, "text": str}`.
  - `FORM_LABELS: dict[str, str]` — suffix → label (`_A` Alolan, `_G` Galarian, `_H` Hisuian, `_MEGA` Mega, `_MEGA_X/Y` Mega X/Y, `_GIGA` Mega, `_N` Midnight, `_DUSK` Dusk, `_PRIMAL` Primal, …; extend as roster needs — unknown suffix → title-cased remainder).

**Rules (from spec):**
- Included = standard ∪ divergent dex lists ∪ `habitat_forms` ∪ `EVO_MEGA` targets of included species.
- Modes: dex membership; else habitat page kind; Mega targets inherit from source; union with base species' modes for habitat forms.
- Collapse: a non-dex form is folded into its base if sprite file bytes, types, stats, abilities, and all move lists are identical.
- Special tutors: port `CanMonLearnTutorMove` special section of `<cfru>/src/item.c` honoring active `#ifdef`s (compute which `NATIONAL_DEX_*`/`UNBOUND` are defined via `collect_defines`); blocklist as in that file. Notes: `"Max friendship, Dragon type"`, `"Fire type"`, `"Pikachu line"`, etc. Add a comment pointing at the source function.
- Evolution text: method → English template, derived from `<cfru>/src/evolution.c`. Items via ROM names, moves via in-game move names, types title-cased, `MAPSEC_*` title-cased ("Daimyn Factory"), `TIME_RANGE(17, 20)` → "5–8 PM". `EVO_MEGA` → `"Mega Evolve holding {item}"`. Every method present in the table must have a template — unknown method raises.

- [ ] **Step 1: Write failing tests**

```python
def test_modes(roster):
    by = {e.key: e for e in roster}
    assert by["SPECIES_BIDOOF"].modes == ["Standard"]
    assert by["SPECIES_ZIGZAGOON_G"].modes == ["Divergent"]
    std, div = dex_lists(paths)
    both = next(s for s in std if s in div)
    assert by[both].modes == ["Standard", "Divergent"]
    assert by["SPECIES_VENUSAUR_MEGA"].modes == by["SPECIES_VENUSAUR"].modes
    assert "SPECIES_LYCANROC_DUSK" in by and "SPECIES_ROTOM_HEAT" not in by

def test_no_trade_or_gigantamax(evo_links):
    texts = [l["text"] for ls in evo_links.values() for l in ls]
    assert not any("trade" in t.lower() or "gigantamax" in t.lower() for t in texts)

def test_evolution_text(evo_links):
    assert {"to": "SPECIES_ALAKAZAM", "text": "Use Linking Cord"} in evo_links["SPECIES_KADABRA"]
    assert any(l["to"] == "SPECIES_VENUSAUR_GIGA" and l["text"].startswith("Mega Evolve holding") for l in evo_links["SPECIES_VENUSAUR"])
    assert any("5" in l["text"] and "PM" in l["text"] for l in evo_links["SPECIES_ROCKRUFF"] if l["to"] == "SPECIES_LYCANROC_DUSK")

def test_special_tutor_blocklist():
    assert special_tutor_moves("SPECIES_ROTOM", ["ELECTRIC", "GHOST"], "SPECIES_ROTOM") == []
    assert special_tutor_moves("SPECIES_DITTO", ["NORMAL"], "SPECIES_DITTO") == []

def test_special_tutor_rules():
    fire = [m for m, _ in special_tutor_moves("SPECIES_CHARMANDER", ["FIRE"], "SPECIES_CHARMANDER")]
    assert set(fire) == {"MOVE_FLAMEBURST", "MOVE_MYSTICALFIRE", "MOVE_INCINERATE"}
    assert "MOVE_SECRETSWORD" not in str(special_tutor_moves("SPECIES_KELDEO", ["WATER","FIGHTING"], "SPECIES_KELDEO"))  # compiled out

def test_collapse_rule(roster):
    keys = {e.key for e in roster}
    assert {"SPECIES_LYCANROC", "SPECIES_LYCANROC_N", "SPECIES_LYCANROC_DUSK"} <= keys
    assert len(keys) == len(roster)  # no duplicate rows

def test_kangaskhan_power_up_punch_matches_source(roster, paths):
    k = next(e for e in roster if e.key == "SPECIES_KANGASKHAN")
    src = {m for _, m in levelup(paths)["SPECIES_KANGASKHAN"]} | set(egg_moves(paths).get("SPECIES_KANGASKHAN", []))
    # Power-Up Punch is not a TM/tutor in this game, so only level-up/egg can grant it
    assert ("MOVE_POWERUPPUNCH" in all_moves(k)) == ("MOVE_POWERUPPUNCH" in src)
```

Add `all_moves(entry: Entry) -> set[str]` to `roster.py` (every `MOVE_*` across all methods).

- [ ] **Step 2:** run → FAIL
- [ ] **Step 3:** Implement per rules above.
- [ ] **Step 4:** run → PASS
- [ ] **Step 5:** Commit `feat(dexpage): roster, modes, special tutors, evolution text`

---

### Task 5: Sprites

**Files:**
- Create: `tools/dexpage/sprites.py`
- Test: `tests/dexpage/test_sprites.py`

**Interfaces:**
- Produces: `build_sheet(pngs: dict[str, Path]) -> tuple[bytes, dict[str, tuple[int,int]]]` — WebP (lossless) or PNG sheet bytes of 64×64 cells, and key → (x, y) cell origin. Identical sprites share a cell.

- [ ] **Step 1: Failing tests** — every roster key has a cell; cell (0,0) pixel of Bulbasaur is transparent (palette index 0 → alpha 0); a 64×128 source is cropped to its top 64×64; sheet bytes < 3 MB.
- [ ] **Step 2:** run → FAIL
- [ ] **Step 3:** Implement with Pillow (`P` mode → RGBA, index 0 transparent). Add `Pillow` to `tools/dexpage/requirements.txt`.
- [ ] **Step 4:** run → PASS
- [ ] **Step 5:** Commit `feat(dexpage): sprite sheet`

---

### Task 6: Page — data, template, UI

**Files:**
- Create: `tools/dexpage/build.py`, `tools/dexpage/template.html`
- Test: `tests/dexpage/test_build.py`

**Interfaces:**
- Consumes: Tasks 2–5.
- Produces: `page_data(roster, moves, evo_links) -> dict` (JSON-serialisable: `{"mons": [...], "moves": {MOVE_*: {...,"learners": [[monIndex, how], ...]}}, "types": [...]}`), `search_keys(name: str, official: str | None) -> list[str]` (lowercased, non-alphanumerics stripped), `render(data: dict, sheet: bytes, offsets) -> str`.

**UI (template.html, vanilla JS, inline CSS):**
- Sticky header: search box, Mode chips (All/Standard/Divergent), type filter.
- Results: matching moves first (move card: type badge, category icon, power/acc/PP, then learner list grouped by method, each with mini sprite + name + "Lv 12"/"Evo" (level 0, tooltip/footnote: "Learned on evolution; also in the move relearner")/"Egg"/"TM45"/"Tutor 3"/"Special: Fire type"; empty → "No Pokémon learn this move."), then Pokémon rows.
- Pokémon row: sprite (CSS background-position into sheet), name + form, type badges, Mode badge, BST, dex #. Tap → expand: stat bars, abilities (hidden marked), secondary line (gender, egg groups, catch rate, EVs, growth), evolution family chain with sprites and arrow text, move tables per method with type/category icons.
- Type badges: CSS pills with the canonical type colours; category icons: small inline SVGs (physical burst, special rings, status circle).
- Render lazily (only visible rows / expanded details) to keep phones fast with ~800 entries.
- "Download for offline use" link: `href` = blob of `document.documentElement.outerHTML`, `download="dex.html"`.

- [ ] **Step 1: Failing tests**

```python
def test_search_keys():
    assert "ceaselessedge" in search_keys("Endless Edge", "Ceaseless Edge")
    assert "endlessedge" in search_keys("Endless Edge", "Ceaseless Edge")

def test_level_zero_is_evo(data):
    learners = data["moves"]["MOVE_CEASELESSEDGE"]["learners"]
    samurott_h = next(i for i, m in enumerate(data["mons"]) if m["key"] == "SPECIES_SAMUROTT_H")
    assert [samurott_h, "Evo"] in learners

def test_move_with_no_learners_is_listed(data):
    unlearned = [k for k, m in data["moves"].items() if m["learners"] == [] and k != "MOVE_NONE"]
    assert unlearned                    # such moves are kept in the data, not dropped

def test_page_is_self_contained(html):
    assert not re.search(r'(src|href)=["\']https?://', html)
    assert "@import" not in html and "fonts.googleapis" not in html

def test_page_size(html):
    assert len(html.encode()) < 8_000_000
```

- [ ] **Step 2:** run → FAIL
- [ ] **Step 3:** Implement `build.py` + template.
- [ ] **Step 4:** run → PASS
- [ ] **Step 5: Manual check** — open `site/index.html` from disk in a browser (desktop + devtools 360 px width, light & dark): search "ceaseless edge", "power up punch", "kangaskhan", "lycanroc"; expand Rockruff and Kadabra; no horizontal scroll. Publish a preview as a claude.ai Artifact for Collin.
- [ ] **Step 6:** Commit `feat(dexpage): searchable reference page`

---

### Task 7: PWA, CLI, docs

**Files:**
- Create: `tools/dexpage/__main__.py`, `tools/dexpage/sw.js`, `tools/dexpage/README.md`
- Modify: `tools/dexpage/build.py` (write site folder), `.gitignore` (`site/`)
- Test: `tests/dexpage/test_build.py`

**Interfaces:**
- Produces: `build(paths: Paths, out: Path) -> None` writing `index.html`, `dex.html` (same bytes, download target), `manifest.webmanifest`, `sw.js`, `icon-192.png`, `icon-512.png` (from a roster sprite upscaled nearest-neighbour). CLI `python -m tools.dexpage [--out site] [--cfru PATH] [--rom PATH]`.

- [ ] **Step 1: Failing tests**

```python
def test_sw_cache_name_tracks_content(tmp_path, paths):
    build(paths, tmp_path)
    sw = (tmp_path / "sw.js").read_text()
    h = hashlib.sha256((tmp_path / "index.html").read_bytes()).hexdigest()[:12]
    assert f"dex-{h}" in sw

def test_site_files(tmp_path, paths):
    build(paths, tmp_path)
    for f in ["index.html", "dex.html", "manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png"]:
        assert (tmp_path / f).exists()
```

- [ ] **Step 2:** run → FAIL
- [ ] **Step 3:** Implement. `sw.js`: precache the site files under `dex-{hash}`, delete other `dex-*` caches on activate, network-first for `index.html` (fallback cache), cache-first otherwise. `index.html` registers the SW only when `location.protocol` is `http(s):` (so the downloaded file opened via `file://` doesn't error). The "Download" link points to `dex.html` with `download` attr when served, blob fallback otherwise. README: install (`pip install -r tools/dexpage/requirements.txt`), rebuild ROM first, run command, push `site/` to the Pages branch.
- [ ] **Step 4:** `pytest tests/dexpage -v` → all PASS; `python -m tools.dexpage --out site` exits 0.
- [ ] **Step 5:** Commit `feat(dexpage): offline PWA + CLI`

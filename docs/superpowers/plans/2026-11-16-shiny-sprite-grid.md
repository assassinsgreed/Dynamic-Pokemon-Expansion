# Shiny Sprite Grid Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pokédex rows show only the normal front sprite; the details open with a "Sprites" section, a 2×2 grid (Regular / Shiny ✦ × Front / Back).

**Architecture:** The build adds back sprites to the existing sprite sheet (back shiny = the `gBackShinySprite*.png` as is; back regular = its pixels drawn with the front PNG's palette) and writes their offsets on each mon as `sb` / `ssb`. app.js drops the row's shiny and renders the grid at the top of `detail()`.

**Tech Stack:** Python 3 + Pillow (build), vanilla JS/CSS in `tools/dexpage/app.js` + `template.html`, pytest, headless Chrome.

**Spec:** `docs/superpowers/specs/2026-11-16-shiny-sprite-pair-design.md`

## Global Constraints

- Load `.claude/skills/amethyst-companion/SKILL.md` first; its rules apply (single offline file, no sprite data URLs in CSS custom properties, chips/tags rules).
- Labels exactly: column headers "Regular" and "Shiny ✦" (✦ in the existing gold `#f2c14e`), row headers "Front" and "Back"; section heading "Sprites".
- Sprites in the grid render at 112 px with `image-rendering: pixelated`.
- Commit on `dexpage-reference` as tasks finish; no pushing. Leave the unrelated uncommitted `template.html` header edits (`.brand`, `.brand .meta`, phone `.brand h1`) in the working tree and out of these commits (`git add -p`).

## Review Focus

- Castform: its sprites live in `graphics/castform`; `_graphic`'s rglob fallback must find the back too → back offsets exist for `SPECIES_CASTFORM` (test in Task 1).
- A roster entry with no back pic entry → no `sb`/`ssb`, grid shows only the Front row; with no shiny → only the Regular column (test in Task 1, check in Task 2).
- Back regular must use the *normal* palette, not the shiny one: Farfetch'd-G's back regular and back shiny cells differ (test in Task 1).
- Grid view (cards): the pop-up reuses `detail()` and must show the grid; collapsed cards show one sprite (check in Task 2).
- Phone width (390 px): the four sections stack and the grid fits without horizontal scroll (check in Task 2).

---

### Task 1: Back sprites in the sheet and page data

**Files:**
- Modify: `tools/dexpage/load_dpe.py` (add `back_pic` after `front_pic`)
- Modify: `tools/dexpage/sprites.py` (`load_shiny` → `load_with_palette`; `build_sheet` gains `backs`)
- Modify: `tools/dexpage/roster.py` (`SourceData.backs`, filled in `load_source_data`)
- Modify: `tools/dexpage/build.py:608-609` (pass backs) and `render()` at ~686 (`sb`, `ssb`)
- Test: `tests/dexpage/test_load_dpe.py`, `tests/dexpage/test_sprites.py`

**Interfaces:**
- Produces: `load_dpe.back_pic(p: Paths) -> dict[str, Path]` (species → `graphics/backspr/gBackShinySprite….png`, parsed from `gMonBackPicTable` in `src/Back_Pic_Table.c`, regex `(gBackShinySprite\w+?)Tiles\b`, cached like `front_pic`).
- Produces: `sprites.load_with_palette(path: Path, palette: Path) -> Image.Image` (the old `load_shiny`, renamed; same body).
- Produces: `build_sheet(pngs, shiny={}, backs: dict[str, tuple[Path, Path]] = {})` — `backs[key] = (back_png, front_png)` adds `"back:<key>"` = `load_with_palette(back_png, front_png)` and `"shinyback:<key>"` = `load_sprite(back_png)`.
- Produces: page mons carry `sb = offsets.get("back:<key>")`, `ssb = offsets.get("shinyback:<key>")` (null when missing), alongside `sp` / `ss`.

- [ ] **Step 1: Write the failing tests**

```python
# test_load_dpe.py
def test_back_pic(paths):
    backs = back_pic(paths)
    assert backs["SPECIES_FARFETCHD_G"].name == "gBackShinySprite1217FarfetchdG.png"
    assert backs["SPECIES_CASTFORM"].exists()

# test_sprites.py
def test_back_sprites_regular_and_shiny(source_data):
    key = "SPECIES_FARFETCHD_G"
    sheet, offsets = build_sheet({}, backs={key: (source_data.backs[key], source_data.sprites[key])})
    img = Image.open(io.BytesIO(sheet)).convert("RGBA")
    crop = lambda o: img.crop((*o, o[0] + CELL, o[1] + CELL)).tobytes()
    assert crop(offsets[f"back:{key}"]) != crop(offsets[f"shinyback:{key}"])

def test_every_row_has_a_cell(roster, source_data):  # extend the existing test
    sheet, offsets = build_sheet({e.key: source_data.sprites[e.key] for e in roster},
                                 {e.key: (source_data.sprites[e.key], source_data.shiny[e.key]) for e in roster if e.key in source_data.shiny},
                                 {e.key: (source_data.backs[e.key], source_data.sprites[e.key]) for e in roster if e.key in source_data.backs})
    assert {e.key for e in roster} <= set(offsets)
    assert f"back:SPECIES_CASTFORM" in offsets
    assert len(sheet) < 3_000_000
```

- [ ] **Step 2: Run them to make sure they fail**

Run: `python -m pytest tests/dexpage/test_load_dpe.py::test_back_pic tests/dexpage/test_sprites.py -q`
Expected: FAIL (`back_pic` not importable / `build_sheet` has no `backs` / `SourceData` has no `backs`).

- [ ] **Step 3: Implement** `back_pic`, `load_with_palette`, `build_sheet(..., backs)`, `SourceData.backs = load_dpe.back_pic(p)`, the backs dict in `build()` (same shape as the test), and `sb` / `ssb` in `render()`.

- [ ] **Step 4: Run the whole suite**

Run: `python -m pytest tests/dexpage -q`
Expected: all pass. If the sheet-size assert trips, report the size rather than raising the limit silently.

- [ ] **Step 5: Commit**

```bash
git add tools/dexpage/load_dpe.py tools/dexpage/sprites.py tools/dexpage/roster.py tools/dexpage/build.py tests/dexpage/test_load_dpe.py tests/dexpage/test_sprites.py
git commit -m "feat(dexpage): back sprites (regular + shiny) in the sprite sheet"
```

### Task 2: Rows show one sprite; details open with the Sprites grid

**Files:**
- Modify: `tools/dexpage/app.js:146-147` (remove `pics`), `:208` (`row()` uses `sprite(m)`), `detail()` at ~337 (new first section)
- Modify: `tools/dexpage/template.html:161-163` (remove `.pics`, `.shiny`), `:548` (`.pics` → `.sp`), the details top-grid column rule (three → four columns on wide screens), new `.sprites` grid rules

**Interfaces:**
- Consumes: mon fields `sp`, `ss`, `sb`, `ssb` (each `[x, y]` or null) from Task 1.

- [ ] **Step 1: Implement** a `spriteAt(xy)` helper (or generalise `sprite`) that takes an offset; in `detail()` add `<section class="sprites"><h3>Sprites</h3>…</section>` before Base stats: a CSS grid with an empty corner, "Regular" / "Shiny ✦" headers, "Front" / "Back" row headers, cells at 112 px (`.sp` box 112 px, `i` scaled 1.75). Leave out the Shiny column when `ss` and `ssb` are both null, the Back row when `sb` is null; skip the section when only `sp` exists. Style cells like `.evcard` (panel background, rounded). Phones: sections stack; shrink the cells (e.g. 96 px) so two cells + row header fit 390 px.

- [ ] **Step 2: Build**

Run: `python -m tools.dexpage --out site`
Expected: finishes without errors (maps come from cache; no `maps/` change).

- [ ] **Step 3: Check in headless Chrome** (recipe in the skill) and look at each screenshot:
  - `#pokedex` at 1000 px: one sprite per row, no ✦.
  - `#farfetchd-g` (or whatever hash the row uses; search "Farfetch") at 1000 px: four labelled sprites, back regular brown-toned vs. back shiny differing.
  - `#castform` details: Back row present.
  - Cards layout (`localStorage["dex-layouts"] = '{"dex":"grid"}'` via injected script) + open a Pokémon: grid in the pop-up.
  - Phone 390 px iframe of `#eevee`: no horizontal scroll, grid fits.
  - stderr log has no "Uncaught".

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/dexpage -q`
Expected: all pass.

- [ ] **Step 5: Commit** (stage hunks so the header edits stay out)

```bash
git add tools/dexpage/app.js
git add -p tools/dexpage/template.html
git commit -m "feat(dexpage): shiny and back sprites move to a Sprites grid in the details"
```

- [ ] **Step 6: Publish the preview** to Collin's artifact (https://claude.ai/artifact/WHK7kT9oh5y4KfizQCjbaN) as the skill describes.

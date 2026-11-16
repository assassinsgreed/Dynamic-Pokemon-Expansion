# Shiny sprites: details only, as a labelled Sprites grid

## Why
Every Pokédex row shows the normal and shiny sprite side by side (`pics()` in app.js, gold ✦ on the shiny).
Across 880 rows that is information overload. Players look at a shiny when they open a Pokémon, usually to tell
apart near-identical colours (e.g. Farfetch'd-G), so the comparison belongs in the details and should be easy to read.
Collin also wants the back sprites there, to fill out the visual part of the details.

## Goals / non-goals
- Goal: rows (list and cards, collapsed) show only the normal front sprite.
- Goal: the details open with a "Sprites" section: a 2×2 grid, columns Regular / Shiny ✦, rows Front / Back.
- Non-goal: tap-to-swap (possible follow-up), shiny odds/mechanics text, back or shiny sprites anywhere else.
- Anti-goal: the details header still carries the small pair (that is the clutter being removed).

## Approaches
- **A. Labelled sprites in the details, enlarged (chosen),** extended to front + back.
- B. Tap the sprite to swap normal/shiny. Never shows both at once; less discoverable.
- C. CSS-only: show today's small pair only on the open row. Doesn't make close calls easier to see.
- Layout: 2×2 grid with row/column headers (chosen) over a 1×4 strip with "Front, Regular"-style captions — regular
  and shiny of each view sit side by side.

## Design
- Data: `Back_Pic_Table.c` → `graphics/backspr/gBackShinySprite*.png`. That PNG's own palette is the shiny palette,
  so **back shiny = the PNG as is**; **back regular = its pixels drawn with the normal palette** (the front PNG's
  palette, the same swap `sprites.load_shiny` does the other way). New loader `load_dpe.back_pic` beside `front_pic`;
  sheet keys `back:<key>` / `shinyback:<key>`; page fields alongside `sp`/`ss` (e.g. `sb`, `ssb`).
- `row()` renders just `sprite(m)`; `pics()` and the `.pics` / `.shiny::after` rules go.
- `detail()` adds a first section "Sprites" before Base stats; sprites at 112 px (`image-rendering: pixelated`).
  Wide screens: the top grid becomes four columns; phones: sections stack and the grid shrinks to fit.
- Missing sprites: a cell is left out / the section shrinks to what exists; no section if only the front exists.
- Page size: the sprite sheet roughly doubles (~1.4 MB → ~2.8 MB; page ~8 → ~9.4 MB). Accepted.
- Card pop-up reuses `detail()`, so it gets the grid too.

## Left to the builder
Exact spacing/background (match `.evcard`), header styling, the column breakpoints for the four-column top grid.

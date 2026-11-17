// Pokemon Amethyst Companion. Inlined into template.html by build.py; DEX and SHEET are defined just before it.
(() => {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const root = document.documentElement;
  // The sheets go in one stylesheet rule each: a data URL in a CSS variable is re-parsed for every sprite on the page
  const sheets = document.createElement("style");
  sheets.textContent = `.sp i { background-image: url("${SHEET}"); } .ii:not(.none) { background-image: url("${DEX.itemSheet}"); } .tp i { background-image: url("${DEX.trainerSheet}"); }`;
  document.head.appendChild(sheets);
  const consoleEl = $("header.console");
  const syncConsoleHeight = () => root.style.setProperty("--console-h", `${consoleEl.offsetHeight}px`);
  window.addEventListener("resize", syncConsoleHeight);
  // Strips and tables that scroll sideways fade out on the side with more to see (phones hide scrollbars)
  const SCROLLERS = ".views, .tablist, .moves, .movelist, .listtable, .doctable";
  const cue = (el) => {
    const max = el.scrollWidth - el.clientWidth;
    el.classList.toggle("more-l", max > 1 && el.scrollLeft > 1);
    el.classList.toggle("more-r", max > 1 && el.scrollLeft < max - 1);
  };
  const cueAll = () => document.querySelectorAll(SCROLLERS).forEach(cue);
  document.addEventListener("scroll", (e) => { if (e.target.matches?.(SCROLLERS)) cue(e.target); }, { capture: true, passive: true });
  window.addEventListener("resize", cueAll);
  let cueFrame = 0;  // views, opened entries and their tabs all change #out; re-check once per frame
  const cueSoon = () => { if (!cueFrame) cueFrame = requestAnimationFrame(() => { cueFrame = 0; cueAll(); }); };

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const norm = (s) => s.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]/g, "");
  // Prose (descriptions, notes, docs) is searched word by word: "terra" finds "terrain" but not "encounter rate"
  const words = (s) => (s || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  const slug = (s) => s.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const TYPES = ["NORMAL", "FIRE", "WATER", "GRASS", "ELECTRIC", "ICE", "FIGHTING", "POISON", "GROUND", "FLYING", "PSYCHIC", "BUG", "ROCK", "GHOST", "DRAGON", "DARK", "STEEL", "FAIRY"];
  const STAT_LABELS = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"];
  // The games' own Physical / Special / Status labels (cat_icons/, embedded by build.py)
  const CAT = Object.fromEntries(Object.entries(CAT_ICONS).map(([k, src]) => [k, `<img src="${src}" alt="" draggable="false">`]));
  const CAT_NAME = { physical: "Physical", special: "Special", status: "Status" };
  const TYPE_COLOR = { NORMAL: "#9a9d9a", FIRE: "#e2562a", WATER: "#2f7fe6", GRASS: "#3c9a2d", ELECTRIC: "#f2bd16", ICE: "#3fc4e8",
    FIGHTING: "#e07510", POISON: "#8f45c6", GROUND: "#946033", FLYING: "#6f9fdc", PSYCHIC: "#e8487d", BUG: "#8b9b1c", ROCK: "#a49a6c",
    GHOST: "#6c4a74", DRAGON: "#5463d8", DARK: "#5b4b4c", STEEL: "#5f99ad", FAIRY: "#e06fe0", MYSTERY: "#5e8f86" };
  const CHEVRON = '<span class="chev" aria-hidden="true"><svg viewBox="0 0 16 16" width="14" height="14"><path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span>';

  // ---------------------------------------------------------------- data
  // build.py writes each move's learners as {how: [mon, ...]}; back to [[mon, how], ...] in Pokémon order
  for (const mv of Object.values(DEX.moves)) {
    mv.learners = Object.entries(mv.learners).flatMap(([how, ids]) => ids.map((i) => [i, how])).sort((a, b) => a[0] - b[0]);
  }
  // …and a Pokémon's abilities as indexes into DEX.abilities where the text is the same
  const unpackAbility = (a) => (typeof a === "number" ? [DEX.abilities[a].name, DEX.abilities[a].desc, DEX.abilities[a].chance] : a);
  for (const m of DEX.mons) { m.abilities = m.abilities.map(unpackAbility); m.hidden = unpackAbility(m.hidden); }
  const mons = DEX.mons, moves = DEX.moves, items = DEX.items;
  const moveKeys = Object.keys(moves).sort((a, b) => moves[a].name.localeCompare(moves[b].name));
  const monMoves = mons.map(() => []);  // per-Pokémon move lists, rebuilt from the move → learners table
  for (const k of moveKeys) for (const [i, how] of moves[k].learners) monMoves[i].push([k, how]);
  const parent = new Map();
  mons.forEach((m, i) => m.evo.forEach(([to]) => { if (!parent.has(to)) parent.set(to, i); }));
  const itemKeys = items.map((it) => norm(it.name));

  const escapeRe = (text) => text.replace(/[.*+?^$()|[\]\\{}]/g, "\\$&");
  // "Route 2" must match "Route 2" and "Route 2 (hidden)" but not "Route 20"
  const placeRe = (name) => new RegExp("(^|[^a-z0-9])" + escapeRe(name.toLowerCase()) + "($|[^a-z0-9])");
  // Places: every location in the encounter data, with the Pokémon found there
  const places = new Map();
  mons.forEach((m, i) => m.loc.forEach((l) => {
    const k = norm(l.location);
    if (!places.has(k)) places.set(k, { name: l.location, rows: [] });
    places.get(k).rows.push([i, l]);
  }));
  // Town Map places with items but no wild Pokémon (Treasure Beach, towns with shops) get cards too
  for (const name of Object.keys(DEX.townMap.places)) {
    const re = placeRe(name);
    if (!places.has(norm(name)) && items.some((it) => it.where.some((w) => re.test(w.toLowerCase())))) places.set(norm(name), { name, rows: [] });
  }
  // Interactive maps (mapview.js): a place's map is found by name, or through DEX.maps.alias where the companion's
  // place is filed under another map (the Route 12 rest house is part of Route 12 East's map)
  const mapByName = new Map(DEX.maps.places.map((m) => [norm(m.name), m]));
  const mapFor = (name) => mapByName.get(norm(DEX.maps.alias[name] || name));
  for (const m of DEX.maps.places) if (![...places.values()].some((p) => mapFor(p.name) === m)) places.set(norm(m.name), { name: m.name, rows: [] });
  const placeList = [...places.values()].sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
  const placeOfMap = (slug) => (placeList.find((p) => mapFor(p.name)?.slug === slug) || {}).name;

  // Sort keys per mode: that mode's dex number; unnumbered forms sit just after the entry before them (their base)
  const order = { Standard: new Float64Array(mons.length), Divergent: new Float64Array(mons.length) };
  for (const [mode, field] of [["Standard", "std"], ["Divergent", "div"]]) {
    let last = 0, step = 0;
    mons.forEach((m, i) => {
      // an unnumbered entry with nothing numbered before it in this mode (a gift form of a Standard-only species) goes last
      if (m.dex[field]) { last = m.dex[field]; step = 0; order[mode][i] = last; } else order[mode][i] = last ? last + ++step / 1000 : 1e6 + i;
    });
  }
  const monSlug = (i) => slug(mons[i].key.replace(/^SPECIES_/, ""));

  // ---------------------------------------------------------------- state & navigation
  // state.view: dex | moves | items | places; move/item/place name the open card; open is the expanded Pokémon
  const state = { view: "dex", q: "", move: null, item: null, place: null, map: null, mark: null, open: null, mode: "", tab: "level", tabFilter: "",
    doc: null, ability: null, trainer: null, diff: "std",
    layouts: { dex: "list", moves: "list", tutors: "list", abilities: "list", items: "grid", trainers: "list", places: "grid", check: "list", docs: "list" } };  // list or cards, per view
  try {
    state.mode = localStorage.getItem("dex-mode") || "";
    state.diff = localStorage.getItem("dex-diff") || "std";
    Object.assign(state.layouts, JSON.parse(localStorage.getItem("dex-layouts") || "{}"));
  } catch (e) {}
  let depth = 0, top = 0;  // position in this page's history, and how far Forward can go

  const snapshot = () => ({ view: state.view, q: state.q, move: state.move, item: state.item, place: state.place, map: state.map, mark: state.mark, doc: state.doc, ability: state.ability, trainer: state.trainer, open: state.open });
  function hashFor(st) {
    if (st.view === "dex" && st.open !== null) return monSlug(st.open);
    if (st.move) return "move-" + slug(moves[st.move].name);
    if (st.item !== null) return "item-" + slug(items[st.item].name);
    if (st.map) return "map-" + st.map + (st.mark ? "/" + st.mark : "");
    if (st.place) return "place-" + slug(st.place);
    if (st.doc) return "doc-" + slug(st.doc);
    if (st.ability) return "ability-" + slug(st.ability);
    if (st.trainer !== null) return "trainer-" + trainerSlug(st.trainer);
    return { dex: "", moves: "moves", tutors: "tutors", abilities: "abilities", items: "items", trainers: "trainers", places: "locations", check: "checklist", docs: "docs" }[st.view];
  }
  const queries = {};  // each tab keeps its own search text

  function navigate(change) {
    const next = Object.assign({ view: state.view, q: "", move: null, item: null, place: null, map: null, mark: null, doc: null, ability: null, trainer: null, open: null }, change);
    Object.assign(state, next, { tabFilter: "" });
    queries[state.view] = state.q;
    depth++;
    top = depth;  // a new step discards anything Forward could have returned to
    try { history.pushState({ dex: snapshot(), depth }, "", "#" + hashFor(state)); } catch (e) {}
    render(true);
  }
  function remember() {  // typing and expanding update the current entry instead of adding one
    try { history.replaceState({ dex: snapshot(), depth }, "", "#" + hashFor(state)); } catch (e) {}
  }
  window.addEventListener("popstate", (e) => {
    if (e.state && e.state.dex) { Object.assign(state, e.state.dex, { tabFilter: "" }); depth = e.state.depth || 0; top = Math.max(top, depth); render(true); }
    else fromHash();
  });

  const openMon = (i) => navigate({ view: "dex", open: i, q: mons[i].name });
  const openMove = (k) => navigate({ view: "moves", move: k });
  const openItem = (k) => navigate({ view: "items", item: k });
  const openPlace = (name) => navigate({ view: "places", place: name });
  // Back from a map returns to its place's details; a way out on the map opens the next place's map
  const closeMap = () => navigate({ view: "places", q: state.q, place: state.place });
  MapView.init({ onClose: closeMap, onLink: (slug) => navigate({ view: "places", place: placeOfMap(slug) || null, map: slug }),
    onMark: (mark) => { if (state.map) { state.mark = mark; remember(); } } });  // #map-<place>/<marker> links to one marker

  // ---------------------------------------------------------------- small pieces
  const typeBadge = (t) => `<span class="type t-${t}">${t === "MYSTERY" ? "???" : t[0] + t.slice(1).toLowerCase()}</span>`;
  const pic = (xy, cls = "") => `<span class="sp${cls}" aria-hidden="true"><i style="background-position:-${xy[0]}px -${xy[1]}px"></i></span>`;
  const sprite = (m, small) => pic(m.sp, small ? " sm" : "");
  // Details only: front/back × regular/shiny, labelled, large enough to tell near-identical shinies apart
  // (Farfetch'd-G). A missing back drops the Back row, a missing shiny the Shiny column.
  function spriteGrid(m) {
    const rows = [["Front", m.sp, m.ss], ["Back", m.sb, m.ssb]].filter(([, r]) => r);
    const shiny = rows.some(([, , s]) => s);
    if (rows.length < 2 && !shiny) return "";
    const cell = (xy, label) => (xy ? `<figure title="${label}">${pic(xy, " lg")}</figure>` : "<span></span>");
    return `<section class="sprites"><h3>Sprites</h3><div class="spgrid${shiny ? "" : " one"}"><span></span><b>Regular</b>${shiny ? '<b>Shiny <span class="star">✦</span></b>' : ""}${
      rows.map(([name, r, s]) => `<b class="rowh">${name}</b>${cell(r, `${name}, regular`)}${shiny ? cell(s, `${name}, shiny`) : ""}`).join("")}</div></section>`;
  }
  const formLabel = (m) => (m.form ? ` <small>${esc(m.form)}</small>` : "");
  const pad = (n) => String(n).padStart(3, "0");
  // One tag for the dex it's in ("Both" for the two), and its number on its own: a Pokémon in both dexes has the same
  // number in each.
  // "Standard" / "Divergent" / "Both" tag, coloured like the mode filter's dots (modeClass below)
  const modeTag = (mode) => `<span class="mode${modeClass(mode === "Both" ? ["Standard", "Divergent"] : [mode])}">${esc(mode)}</span>`;
  const modeBadge = (m) => modeTag(m.modes.length > 1 ? "Both" : m.modes[0]);
  const dexNo = (m) => {  // own number "#384"; a form shares its base's ("#384"), with "(Swarm)" for swarm Pokémon
    const fields = state.mode ? [state.mode === "Standard" ? "std" : "div"] : ["std", "div"];
    const own = fields.map((f) => m.dex[f]).find(Boolean);
    if (own) return `<span class="dexno">#${pad(own)}</span>`;
    const f = fields.find((x) => m.sharedDex[x]);
    if (!f) return m.swarm.length ? '<span class="dexno">Swarm</span>' : "";
    const swarm = m.swarm.includes(f === "std" ? "Standard" : "Divergent");
    return `<span class="dexno">#${pad(m.sharedDex[f])}${swarm ? " (Swarm)" : ""}</span>`;
  };
  const bst = (m) => m.stats.reduce((a, b) => a + b, 0);
  const inMode = (m) => !state.mode || m.modes.includes(state.mode);
  const rowInMode = (l) => !state.mode || l.mode === "Both" || l.mode === state.mode;
  const tint = (m) => {  // a faint wash of the Pokémon's type colours behind its row
    const a = TYPE_COLOR[m.types[0]], b = TYPE_COLOR[m.types[1] || m.types[0]];
    return `--tint: linear-gradient(100deg, ${a}26 0%, ${a}0d 38%, ${b}0d 70%, ${b}24 100%)`;
  };
  const itemIcon = (k) => {
    const it = k === null || k === undefined ? null : items[k];
    return it && it.icon ? `<span class="ii" style="background-position:-${it.icon[0]}px -${it.icon[1]}px" aria-hidden="true"></span>` : '<span class="ii none" aria-hidden="true"></span>';
  };
  const itemButton = (k, label) => `<button class="itembtn" data-item="${k}">${itemIcon(k)}<span class="in">${esc(label || items[k].name)}</span></button>`;
  const monLink = (i, current) => `<button class="link${i === current ? " current" : ""}" data-open="${i}">${sprite(mons[i], true)}<span class="ln">${esc(mons[i].name)}${formLabel(mons[i])}</span></button>`;
  // A chip's or Pokédex row's left edge shows the modes a Pokémon (or encounter) is found in
  const modeClass = (modes) => (modes.length > 1 ? " m-both" : modes[0] === "Divergent" ? " m-div" : " m-std");
  const modeEdge = (modes) => `${modeClass(modes)}" title="${modes.length > 1 ? "Standard and Divergent" : `${modes[0]} only`}`;
  const monChip = (i, note, sub, bare, modes = mons[i].modes) => `<button class="chip${modeEdge(modes)}" data-open="${i}">${sprite(mons[i], true)}<span class="ln">${esc(mons[i].name)}${bare ? "" : formLabel(mons[i])}${
    sub ? ` <span class="sub">${esc(sub)}</span>` : ""}</span>${note ? `<span class="hw">${esc(note)}</span>` : ""}</button>`;
  // Escaped text whose place names ("Secret Trail (need Strength)") open that place's card; longest name first
  let anyPlace = null;
  const placeLinks = (text) => {
    anyPlace ??= new RegExp(`(?<![a-z0-9])(${placeList.map((p) => p.name).sort((a, b) => b.length - a.length).map(escapeRe).join("|")})(?![a-z0-9])`, "gi");
    let out = "", at = 0;
    for (const m of text.matchAll(anyPlace)) {
      const p = placeList.find((pl) => pl.name.toLowerCase() === m[0].toLowerCase());
      out += `${esc(text.slice(at, m.index))}<button class="mvname" data-place="${esc(p.name)}">${esc(m[0])}</button>`;
      at = m.index + m[0].length;
    }
    return out + esc(text.slice(at));
  };
  const statColor = (v) => (v < 50 ? "#e2562a" : v < 80 ? "#f2a516" : v < 100 ? "#c9c21b" : v < 120 ? "#5fb83a" : "#2aa198");
  // Drawn rather than the ♂/♀ characters, whose crossbar and arrow most fonts squeeze to nothing at this size
  const FEMALE_ICON = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><circle cx="8" cy="5.5" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 9.5V15M5 12.5h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
  const MALE_ICON = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><circle cx="6.5" cy="9.5" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M9.5 6.5L14 2M10 2h4v4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const MALE = `<span class="tsex m" title="Male" aria-label="Male">${MALE_ICON}</span>`;
  const FEMALE = `<span class="tsex f" title="Female" aria-label="Female">${FEMALE_ICON}</span>`;
  const genderText = (g) => (g === null ? "Genderless" : g === 0 ? `${MALE} only` : g === 100 ? `${FEMALE} only`
    : `${MALE} ${+(100 - g).toFixed(1)}% · ${FEMALE} ${+g.toFixed(1)}%`);

  // ---------------------------------------------------------------- Pokémon detail
  function row(m, i, inSheet = false) {
    const cards = state.layouts.dex === "grid" && !inSheet, open = state.open === i && !cards;
    return `<details class="mon${modeClass(m.modes)}${cards && state.open === i ? " on" : ""}" data-i="${i}" style="${tint(m)}"${open ? " open" : ""}>
      <summary title="Show details"><span class="dexline">${dexNo(m)}${modeBadge(m)}</span>${sprite(m)}
        <span class="who"><span class="nm">${esc(m.name)}${formLabel(m)}</span>
          <span class="tags">${m.types.map(typeBadge).join("")}</span></span>
        ${CHEVRON}
      </summary>${state.open === i ? detail(i) : ""}</details>`;
  }

  // Method text with its item made clickable ("Use Fire Stone" → Fire Stone links to the item)
  function howText(how, k, written) {
    if (k === null || k === undefined) return esc(how);
    const name = written && how.includes(written) ? written : items[k].name, at = how.indexOf(name);
    if (at < 0) return `${esc(how)} ${itemButton(k)}`;
    return `<span>${esc(how.slice(0, at))}</span>${itemButton(k, name)}<span>${esc(how.slice(at + name.length))}</span>`;
  }

  function evoTree(i) {
    let first = i;
    const seen = new Set();
    while (parent.has(first) && !seen.has(first)) { seen.add(first); first = parent.get(first); }
    if (first === i && !mons[i].evo.length) return '<p class="note">Does not evolve.</p>';
    // The whole card opens its Pokémon (an item named in the method still opens the item: data-item is handled first)
    const card = ([n, how, k, written]) => `<div class="evcard${n === i ? " current" : ""}" data-open="${n}">${monLink(n, i)}${how ? `<span class="how">${howText(how, k, written)}</span>` : ""}</div>`;
    // A tree, so each branch keeps its own line: two or three evolutions fan out from one point (only one can be taken);
    // more (Eevee) sit in a grid behind a single arrow
    const placed = new Set([first]);
    const node = (e, depth) => {
      const kids = depth < 8 ? mons[e[0]].evo.filter(([to]) => !placed.has(to) && placed.add(to)) : [];
      if (!kids.length) return `<div class="evnode">${card(e)}</div>`;
      const n = kids.length, fork = n > 1 && n <= 3;
      const arrow = fork
        ? `<svg class="evarrows" viewBox="0 0 32 100" preserveAspectRatio="none" aria-hidden="true">${kids.map((_, j) => `<path d="M0 50L32 ${(j + 0.5) * 100 / n}"/>`).join("")}</svg>`
        : '<span class="sep" aria-hidden="true">›</span>';
      // The grid's own evolutions (Alcremie's shared Mega G) follow the whole grid, not the one card that lists them
      const next = n > 3 ? kids.flatMap(([k]) => mons[k].evo.filter(([to]) => !placed.has(to) && placed.add(to))) : [];
      const after = next.length ? `<div class="evkids"><span class="sep" aria-hidden="true">›</span><div class="evlist">${next.map((x) => node(x, depth + 2)).join("")}</div></div>` : "";
      return `<div class="evnode">${card(e)}<div class="evkids${fork ? " fork" : n > 3 ? " many" : ""}">${arrow}<div class="evlist${n > 3 ? " many" : ""}">${kids.map((x) => node(x, depth + 1)).join("")}</div>${after}</div></div>`;
    };
    return `<div class="evo">${node([first, "", null], 1)}</div>`;
  }

  function moveRow(k, how, showHow) {
    const mv = moves[k];
    return `<tr>${showHow ? `<td class="h">${esc(how)}</td>` : ""}
      <td><button class="mvname" data-move="${k}" title="${esc(mv.desc)}">${esc(mv.name)}</button></td>
      <td>${typeBadge(mv.type)}</td>
      <td><span class="cat" title="${CAT_NAME[mv.split]}">${CAT[mv.split]}</span></td>
      <td class="n">${mv.power || "—"}</td><td class="n hide-sm">${mv.acc || "—"}</td><td class="n hide-sm">${mv.pp}</td></tr>`;
  }

  function moveTable(title, list, howHeader, note) {
    if (!list.length) return "";
    return `<section>${title ? `<h3>${title}</h3>` : ""}${note ? `<p class="note">${note}</p>` : ""}<div class="moves"><table class="mv"><thead><tr>${
      howHeader !== null ? `<th class="c-how">${howHeader}</th>` : ""}<th>Move</th><th class="c-type">Type</th><th class="c-cat">Cat</th><th class="c-num">Pow</th><th class="c-num hide-sm">Acc</th><th class="c-num hide-sm">PP</th></tr></thead><tbody>${
      list.map(([k, how]) => moveRow(k, how, howHeader !== null)).join("")}</tbody></table></div></section>`;
  }

  function moveLists(i) {  // per tab, in game order
    const all = monMoves[i];
    const lvlKey = (h) => (h === "Evo" ? 0 : +h.slice(3));
    const level = all.filter(([, h]) => h === "Evo" || h.startsWith("Lv ")).map((x, n) => [x, n])
      .sort((a, b) => lvlKey(a[0][1]) - lvlKey(b[0][1]) || a[1] - b[1]).map(([x]) => x);
    const tm = all.filter(([, h]) => /^(TM|HM)\d/.test(h)).sort((a, b) => (a[1][0] === "H") - (b[1][0] === "H") || parseInt(a[1].slice(2), 10) - parseInt(b[1].slice(2), 10));
    const tutor = all.filter(([, h]) => h.startsWith("Tutor")).sort((a, b) => parseInt(a[1].slice(6), 10) - parseInt(b[1].slice(6), 10));
    const special = all.filter(([, h]) => h.startsWith("Special:")).map(([k, h]) => [k, h.slice(9)]);
    const egg = all.filter(([, h]) => h === "Egg").sort((a, b) => moves[a[0]].name.localeCompare(moves[b[0]].name));
    return { level, egg, tm, tutor, special };
  }

  const TABS = [["level", "Level up"], ["egg", "Egg moves"], ["tm", "TM / HM"], ["tutor", "Tutor"]];
  const locRows = (i) => mons[i].loc.filter(rowInMode);
  const tabCount = (i, tab, lists) => (tab === "tutor" ? lists.tutor.length + lists.special.length : lists[tab].length);
  const moveMatches = (f) => ([k, how]) => !f || [moves[k].name, moves[k].official || "", moves[k].type, CAT_NAME[moves[k].split], how].some((s) => norm(s).includes(f));

  // An encounter found only by day or only by night says so in a Time column (shown only when some row needs it),
  // not in its notes; paired rates ("☀️ 10% 🌙 15%") are all day and stay in Rate
  // (phones show only the icon, to leave the place name room)
  const ONLY_TIME = { day: ["☀️", "Morning/Day"], night: ["🌙", "Evening/Night"] };
  const onlyTime = (l) => (l.times && Object.keys(l.times).length === 1 ? ONLY_TIME[Object.keys(l.times)[0]] : null);
  const timeCell = (l) => { const t = onlyTime(l); return t ? `<span title="${t[1]} only">${t[0]}</span><span class="hide-sm"> ${t[1]}</span>` : ""; };
  function locTable(rows) {
    const timed = rows.some(onlyTime);
    return `<div class="moves"><table class="mv loc"><thead><tr><th>Location</th><th>Method</th>${timed ? "<th>Time</th>" : ""}<th class="c-num">Lv</th><th class="c-num">Rate</th><th class="hide-sm">Mode</th></tr></thead><tbody>${
      rows.map((l) => {
        // The first detail line (sub-area, else variant, else notes) sits beside the name; the rest stay below
        const notes = onlyTime(l) ? (l.notes || "").replace(/(☀️|🌙) (Morning\/Day|Evening\/Night) only\.?\s*/, "").trim() : l.notes;
        const [first, ...rest] = [l.sub, l.variant, notes].filter(Boolean);
        return `<tr><td><button class="mvname" data-place="${esc(l.location)}">${esc(l.location)}</button>${first ? `<span class="note locsub">${esc(first)}</span>` : ""}${
        rest.map((s) => `<div class="note">${esc(s)}</div>`).join("")}</td>
        <td class="meth">${esc(l.method)}</td>${timed ? `<td class="meth">${timeCell(l)}</td>` : ""}<td class="n">${esc(l.levels || "—")}</td><td class="n">${esc(l.rate || "—")}</td>
        <td class="hide-sm">${modeTag(l.mode)}</td></tr>`;
      }).join("")}</tbody></table></div>`;
  }

  // Where to find it: its own section of the profile, apart from the move tabs
  function locations(i) {
    const m = mons[i], rows = locRows(i);
    if (rows.length) return locTable(rows);
    if (m.movesOf !== null) return `<p class="note">Appears in battle from ${monLink(m.movesOf, i)}.</p>`;
    const from = parent.has(i) ? parent.get(i) : null;
    return `<p class="note">Not found in the wild${state.mode ? ` in ${state.mode} mode` : ""}.${from !== null ? ` Evolve it from ${monLink(from, i)}` : ""}</p>`;
  }

  function panel(i) {
    const m = mons[i];
    const f = norm(state.tabFilter);
    const battleNote = m.movesOf !== null ? `<p class="note">Exists only in battle, so it knows whatever ${monLink(m.movesOf, i)} knows.</p>` : "";
    const lists = moveLists(m.movesOf ?? i);
    const keep = moveMatches(f);
    const empty = (what) => `${battleNote}<p class="note">${f ? `No ${what} match “${esc(state.tabFilter)}”.` : `No ${what}.`}</p>`;
    if (state.tab === "tutor") {
      const tutor = lists.tutor.filter(keep), special = lists.special.filter(keep);
      if (!tutor.length && !special.length) return empty("tutor moves");
      // Tutor numbers mean nothing to players; show the town that teaches the move instead
      const where = (k) => ((moves[k].tutor || []).find((t) => t.kind === "Regular") || {}).where || "";
      const townOrder = (k) => { const n = DEX.tutors.findIndex((t) => t.move === k && t.kind === "Regular"); return n < 0 ? 1e9 : n; };
      const byTown = tutor.slice().sort((a, b) => townOrder(a[0]) - townOrder(b[0]));  // in the order players meet the tutors
      return `${battleNote}<div class="groups">${moveTable("Move tutor", byTown.map(([k]) => [k, where(k)]), "Where")}${moveTable("Special tutor", special, "Who")}</div>`;
    }
    const rows = lists[state.tab].filter(keep);
    if (!rows.length) return empty({ level: "level-up moves", egg: "egg moves", tm: "TMs or HMs" }[state.tab]);
    if (state.tab === "level") return battleNote + moveTable("", rows, "Lv", rows.some(([, h]) => h === "Evo") ? "<b>Evo</b> = learned on evolution, and also offered by the move relearner." : "");
    if (state.tab === "egg") return battleNote + moveTable("", rows, null, "Egg moves come from the first Pokémon in its evolution line.");
    return battleNote + moveTable("", rows, "No.");
  }

  function tabsBlock(i) {
    const lists = moveLists(mons[i].movesOf ?? i);
    const placeholder = "Filter moves, e.g. Fire, Physical, TM2";
    return `<div class="tabs" data-tabs="${i}">
      <div class="tablist" role="tablist">${TABS.map(([id, label]) =>
        `<button role="tab" data-tab="${id}" aria-selected="${state.tab === id}">${label} <span class="c">${tabCount(i, id, lists)}</span></button>`).join("")}</div>
      <input class="tabfilter" id="tabfilter-${i}" type="search" placeholder="${placeholder}" value="${esc(state.tabFilter)}" aria-label="Filter this tab" autocomplete="off">
      <div class="panel" role="tabpanel">${panel(i)}</div>
    </div>`;
  }

  function detail(i) {
    const m = mons[i];
    const ab = ([name, desc, chance], hidden) => `<div class="ab"><button class="mvname" data-ability="${esc(name)}">${esc(name)}</button>${hidden ? '<span class="hid">Hidden</span>' : ""}${desc ? `<span class="desc">${esc(desc)}${chance ? ` (${chance}% chance)` : ""}</span>` : ""}</div>`;
    const evs = m.evs.map((v, n) => (v ? `${v} ${STAT_LABELS[n]}` : "")).filter(Boolean).join(", ") || "—";
    return `<div class="detail">
      <div class="toprow">${spriteGrid(m)}
        <section class="sec-stats"><h3>Base stats · ${bst(m)}</h3><div class="stats">${m.stats.map((v, n) =>
          `<span class="lab">${STAT_LABELS[n]}</span><span class="val">${v}</span><span class="bar"><span style="width:${Math.min(100, v / 2)}%;background:${statColor(v)}"></span></span>`).join("")}</div></section>
        <section class="sec-abil"><h3>Abilities</h3><div class="abilities">${m.abilities.map((a) => ab(a, false)).join("")}${m.hidden ? ab(m.hidden, true) : ""}</div></section>
        <section class="sec-prof"><h3>Profile</h3><dl class="facts">
          <dt>Gender</dt><dd class="gender">${genderText(m.gender)}</dd>
          <dt>Egg groups</dt><dd>${m.eggGroups.join(", ") || "—"}</dd>
          <dt>Catch rate</dt><dd>${m.catchRate}</dd>
          <dt>Growth</dt><dd>${esc(m.growth)}</dd>
          <dt>EV yield</dt><dd>${evs}</dd>
          ${m.held.length ? `<dt class="held-dt">Wild held items</dt><dd class="held">${m.held.map(([h, k]) => (k === null ? `<span>${esc(h)}</span>` : itemButton(k, h))).join("")}</dd>` : ""}
        </dl></section>
      </div>
      <section><h3>Evolution</h3>${evoTree(i)}</section>
      <section><h3>Locations · ${locRows(i).length}</h3>${locations(i)}</section>
      <section><h3>Moves</h3>${tabsBlock(i)}</section>
    </div>`;
  }

  // ---------------------------------------------------------------- cards
  const GROUPS = [["Level up", (h) => h === "Evo" || h.startsWith("Lv ")], ["TM / HM", (h) => /^(TM|HM)\d/.test(h)],
    ["Move tutor", (h) => h.startsWith("Tutor")], ["Special tutor", (h) => h.startsWith("Special:")], ["Egg move", (h) => h === "Egg"]];

  const COLLAPSE = '<button class="collapse" data-collapse aria-label="Collapse" title="Collapse"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M4 10l4-4 4 4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>';

  function moveCard(k, collapsible) {
    const mv = moves[k];
    const learners = mv.learners.filter(([i]) => inMode(mons[i]));
    const groups = GROUPS.map(([title, test]) => [title, learners.filter(([, h]) => test(h))]).filter(([, l]) => l.length);
    const body = groups.length
      ? groups.map(([title, l]) => `<div><h4>${title} · ${l.length}</h4><div class="chips">${l.map(([i, h]) => monChip(i, h.startsWith("Tutor") ? "" : h.replace(/^Special: /, ""))).join("")}</div></div>`).join("")
      : `<p class="empty">${mv.learners.length ? "No Pokémon match the current filters." : "No Pokémon learn this move."}</p>`;
    return `<article class="movecard">${collapsible ? COLLAPSE : ""}
      <div class="top">${typeBadge(mv.type)}<span class="cat" title="${CAT_NAME[mv.split]}">${CAT[mv.split]}</span>
        <h2>${esc(mv.name)}${mv.official ? `<small>${esc(mv.official)}</small>` : ""}</h2></div>
      ${mv.desc ? `<div class="gamedesc">${esc(mv.desc)}</div>` : ""}
      <div class="specs"><span>${CAT_NAME[mv.split]}</span><span>Pow <b>${mv.power || "—"}</b></span><span>Acc <b>${mv.acc || "—"}</b></span><span>PP <b>${mv.pp}</b></span>${mv.chance ? `<span>Effect chance <b>${mv.chance}%</b></span>` : ""}</div>
      ${mv.tm ? `<div class="tmloc"><b>${mv.tm.label}</b> · ${mv.tm.where.map(placeLinks).join(" · ")}${mv.tm.requires ? ` · needs ${esc(mv.tm.requires)}` : ""}</div>` : ""}
      ${(mv.tutor || []).map((t) => `<div class="tmloc"><b>Tutor</b> · ${placeLinks(t.where)} · ${esc(t.note)}</div>`).join("")}
      <div class="learners">${body}</div></article>`;
  }

  function itemCard(k, collapsible) {
    const it = items[k];
    const holders = [];
    mons.forEach((m, i) => m.held.forEach(([h, hk]) => { if (hk === k && inMode(m)) holders.push([i, (h.match(/\(([^)]*)\)/) || [])[1] || ""]); }));
    const evolves = [];
    // The name match catches a second item in the text (Hisui Rock, Shedinja's Poké Ball), but not one that's only
    // part of the evolution's own item's name (Gengarite inside "Gengarite-G")
    const named = (how, ik) => norm(how).includes(itemKeys[k]) && !(ik != null && itemKeys[ik].includes(itemKeys[k]));
    mons.forEach((m, i) => m.evo.forEach(([to, how, ik, written]) => { if ((ik === k || named(how, ik)) && inMode(mons[to])) evolves.push([i, to, how, written || it.name]); }));
    // Conditions beyond using the item (male Kirlia, holding Razor Claw at night) are spelled out under the chips
    const conditions = evolves.filter(([, , how, name]) => how !== `Use ${name}` && how !== `Mega Evolve holding ${name}`);
    // "Used on" repeats Evolves for evolution items; form-changing items (Gracidea, Drives, Nectars) still need it
    const showUse = it.use && !(evolves.length && it.category === "Evolution");
    const useTitle = /Forme|Primal|Evolution/.test(it.category) ? "Used on" : "Effect";
    return `<article class="itemcard">${collapsible ? COLLAPSE : ""}
      <div class="top">${itemIcon(k)}<h2>${esc(it.name)}<small>${esc(it.category)}</small></h2></div>
      ${it.move ? `<div><h4>Teaches</h4><div class="chips"><button class="chip" data-move="${it.move}">${typeBadge(moves[it.move].type)}<span class="ln">${esc(moves[it.move].name)}</span><span class="hw">${moves[it.move].learners.filter(([, h]) => /^(TM|HM)\d/.test(h)).length} Pokémon</span></button></div></div>` : ""}
      ${showUse ? `<div><h4>${it.move ? "Note" : useTitle}</h4><div class="use">${esc(it.use)}</div></div>` : ""}
      ${evolves.length ? `<div><h4>${it.category === "Mega Stones" ? "Mega Evolves" : "Evolves"} · ${evolves.length}</h4><div class="chips">${evolves.map(([i, to]) => monChip(to, "", "", it.category === "Mega Stones")).join("")}</div>${
        conditions.length ? `<ul class="evocond">${conditions.map(([i, to, how]) => `<li><b>${esc(mons[i].name)}${formLabel(mons[i])}</b> → <b>${esc(mons[to].name)}${formLabel(mons[to])}</b>: ${esc(how)}</li>`).join("")}</ul>` : ""}</div>` : ""}
      ${it.where.length ? `<div><h4>Where to find</h4><ul class="where">${it.where.map((w) => `<li>${placeLinks(w)}</li>`).join("")}</ul></div>` : '<p class="note">No known location.</p>'}
      ${holders.length ? `<div><h4>Held by wild Pokémon · ${holders.length}</h4><div class="chips">${holders.map(([i, pct]) => monChip(i, pct)).join("")}</div></div>` : ""}
    </article>`;
  }

  // The Town Map with everything but the place's 8×8 squares (town_map.py) dimmed, and the squares outlined as one shape
  const townSpots = new Map(Object.entries(DEX.townMap.places).map(([name, sq]) => [norm(name), sq]));
  // The design doc's description (region-layout.md); a split route ("Route 11 North") uses its route's entry
  const placeAbout = new Map(Object.entries(DEX.townMap.about).map(([name, text]) => [norm(name), text]));
  const aboutPlace = (name) => {
    const text = placeAbout.get(norm(name)) ?? placeAbout.get(norm(name.replace(/ (North|South|East|West)$/, "")));
    return text ? `<p class="placeabout">${esc(text)}</p>` : "";
  };
  function townMap(name) {
    const sq = townSpots.get(norm(name));
    if (!sq) return "";
    const has = new Set(sq.map(([x, y]) => `${x},${y}`));
    const edges = sq.flatMap(([x, y]) => [!has.has(`${x},${y - 8}`) && `M${x} ${y}h8`, !has.has(`${x},${y + 8}`) && `M${x} ${y + 8}h8`,
      !has.has(`${x - 8},${y}`) && `M${x} ${y}v8`, !has.has(`${x + 8},${y}`) && `M${x + 8} ${y}v8`]).filter(Boolean).join("");
    const holes = sq.map(([x, y]) => `M${x} ${y}h8v8h-8z`).join("");  // even-odd: the squares cut through the dimming
    return `<figure class="townmap"><img src="${DEX.townMap.img}" alt="" width="208" height="144" draggable="false"><svg viewBox="0 0 208 144" aria-hidden="true">
      <path class="dim" fill-rule="evenodd" d="M0 0h208v144H0z${holes}"/><path class="edge-o" d="${edges}"/><path class="edge" d="${edges}"/></svg></figure>`;
  }

  function placeCard(p, collapsible) {
    const rows = p.rows.filter(([, l]) => rowInMode(l));
    const methods = [];
    rows.forEach((r) => { const g = methods.find(([mt]) => mt === r[1].method); g ? g[1].push(r) : methods.push([r[1].method, [r]]); });
    // An encounter that depends on the time of day says when on its chip ("☀️ 20%" Pikipek by day, "🌙 20%" Hoothoot
    // by night, "☀️ 10% 🌙 15%"); a bare rate is all day. Each list runs from the likeliest encounter down.
    const TIME_ICON = { day: "☀️", night: "🌙" };
    const pct = (rate) => Math.max(-1, ...(String(rate).match(/\d+(\.\d+)?(?=%)/g) || []).map(Number));
    // Trades come at the level sent: "Same Lv as sent" rather than "Lv Same as sent"
    const lvNote = (lv) => (!lv ? "" : /^\d/.test(lv) ? `Lv ${lv}` : lv === "Same as sent" ? "Same Lv as sent" : lv);
    // Places with floors list them in floor order (the outside, 1F, 2F…, then B1F, B2F…), likeliest first on each;
    // a chip found on several floors goes with the first it names. Named rooms ("Side Room", "Peak") come after.
    const floorRank = (sub) => {
      const s = (sub || "").split(",")[0].trim().replace(/^Cave\s+/i, "");
      if (!s || /^(outside|overworld|exterior)$/i.test(s)) return 0;
      let m;
      if ((m = s.match(/^(?:(\d+)F|F(\d+))$/i))) return +(m[1] || m[2]);
      if ((m = s.match(/^(?:B(\d+)F|BF(\d+))$/i))) return 100 + +(m[1] || m[2]);
      if (/^basement$/i.test(s)) return 101;
      return 1000;
    };
    // On All, each method is split by mode ("Grass [Standard]", "Grass [Divergent]", "Grass [Both]"), each encounter
    // listed once under the tag the Pokédex gives it
    const byMode = methods.flatMap(([mt, l]) => (state.mode ? [[mt, null, l]]
      : ["Standard", "Divergent", "Both"].map((md) => [mt, md, l.filter(([, e]) => e.mode === md)]).filter(([, , g]) => g.length)));
    const groups = byMode.map(([mt, md, l]) => [mt, md, l.map(([i, e]) => {
      const rate = e.times ? Object.entries(e.times).map(([t, r]) => `${TIME_ICON[t]} ${r}`).join(" ") : e.rate;
      return [i, e, rate, [lvNote(e.levels), rate].filter(Boolean).join(" · ")];
    }).sort((a, b) => floorRank(a[1].sub) - floorRank(b[1].sub) || pct(b[2]) - pct(a[2]))]);
    const re = placeRe(p.name);
    const found = [];
    // Chip hint is just the spot within the place ("Shady relic seller"); prices and notes are on the item's card
    const spot = (line) => line.replace(/\s*\([^)]*\)/g, "").replace(p.name, "").replace(/^[\s·-]+/, "");
    items.forEach((it, k) => { const line = it.where.find((w) => re.test(w.toLowerCase())); if (line) found.push([k, spot(line)]); });
    // Three parts, each set apart: the map and description, the encounters by method, the items found here
    const encounters = groups.length
      ? groups.map(([mt, md, l]) => `<div><h4>${esc(mt)}${md ? ` ${modeTag(md)}` : ""} · ${l.length}</h4><div class="chips wild${
        l.some(([, e, , note]) => (e.times && Object.keys(e.times).length > 1) || (e.levels && !/^\d/.test(e.levels))) ? " two" : ""}">${l.map(([i, e, , note]) => monChip(i, note, e.sub, false, e.mode === "Both" ? ["Standard", "Divergent"] : [e.mode])).join("")}</div></div>`).join("")
      : `<p class="empty">No Pokémon match the current filters here.</p>`;
    const itemChips = found.map(([k, line]) =>
      `<button class="chip" data-item="${k}">${itemIcon(k)}<span class="ln">${esc(items[k].name)}</span>${line ? `<span class="hw">${esc(line)}</span>` : ""}</button>`).join("");
    return `<article class="loccard">${collapsible ? COLLAPSE : ""}<h2>${esc(p.name)}<small>${p.rows.length ? `${rows.length} encounter${rows.length === 1 ? "" : "s"}` : "No wild Pokémon"}</small></h2>
      <div class="placehead">${townMap(p.name)}${aboutPlace(p.name)}${mapFor(p.name) ? `<button class="mapbtn" data-map="${mapFor(p.name).slug}" data-of="${esc(p.name)}"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M1 3.5l4.5-2 5 2 4.5-2v11l-4.5 2-5-2-4.5 2zM5.5 1.5v11M10.5 3.5v11" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>View Interactive Map</button>` : ""}</div>
      ${p.rows.length ? `<section class="placesec"><h3>Encounters · ${rows.length}</h3><div class="learners">${encounters}</div></section>` : ""}
      ${found.length ? `<section class="placesec"><h3>Items · ${found.length}</h3><div class="chips">${itemChips}</div></section>` : ""}</article>`;
  }

  // ---------------------------------------------------------------- views
  // A type name ("fire") also lists every move of that type, as in the Pokédex
  const typeOf = (q) => TYPES.find((t) => norm(t) === q);
  const moveHit = (k, q, typeQ) => moves[k].s.some((x) => x.includes(q)) || moves[k].type === typeQ;
  const matchMoves = (q) => { const typeQ = typeOf(q); return q ? moveKeys.filter((k) => moveHit(k, q, typeQ)) : moveKeys; };
  // An item also matches its category from the start of any word, singular or plural: "mega" / "megastone" →
  // Mega Stones, "berry" → Berries, "ball" → Poké Balls
  const catKeys = new Map();
  const catHit = (c, q) => {
    if (!catKeys.has(c)) {
      const ws = words(c).split(" ");
      catKeys.set(c, ws.flatMap((_, i) => {
        const tail = ws.slice(i).join("");
        return [tail, tail.replace(/ies$/, "y").replace(/s$/, "")];
      }));
    }
    return catKeys.get(c).some((t) => t.startsWith(q));
  };
  const matchItems = (q) => items.map((_, k) => k).filter((k) => !q || itemKeys[k].includes(q)
    || catHit(items[k].category, q) || (items[k].move && moves[items[k].move].s.includes(q)));
  // A place also matches what's found there (in the chosen mode): a Pokémon ("bidoof"), an encounter method ("grass",
  // "wormhole") or an item ("full heal"); the item lists are worked out once, on the first search
  let placeItems = null;
  const itemsAt = (p) => {
    placeItems ??= new Map(placeList.map((pl) => {
      const re = placeRe(pl.name);
      return [pl, items.flatMap((it, k) => (it.where.some((w) => re.test(w.toLowerCase())) ? [k] : []))];
    }));
    return placeItems.get(p);
  };
  const matchPlaces = (q) => placeList.filter((p) => !q || norm(p.name).includes(q)
    || p.rows.some(([i, l]) => rowInMode(l) && (mons[i].s.some((s) => s.includes(q)) || norm(l.method).includes(q)))
    || itemsAt(p).some((k) => itemKeys[k].includes(q)));
  const exactFirst = (list, isExact) => list.filter(isExact).concat(list.filter((x) => !isExact(x)));

  function matchMons(q) {
    const list = [];
    const typeQ = typeOf(q);  // "fire" lists every Fire type, as well as names containing it
    // "16" or "#016" is a dex number in the chosen mode (either on All), with the unnumbered forms listed after it
    const num = /^\d+$/.test(q) ? +q : 0;
    const hasNum = (m, i) => (state.mode ? [state.mode] : m.modes).some((mode) => m.modes.includes(mode) && Math.floor(order[mode][i]) === num);
    mons.forEach((m, i) => { if (inMode(m) && (num ? hasNum(m, i) : !q || m.s.some((s) => s.includes(q)) || (typeQ && m.types.includes(typeQ)))) list.push(i); });
    return list;
  }
  const matchTutors = (q) => { const typeQ = typeOf(q); return DEX.tutors.filter((t) => !q || moveHit(t.move, q, typeQ) || norm(t.where).includes(q) || words(t.note).includes(words(state.q))); };
  const matchAbilities = (q) => abilities.filter((a, n) => (!q || abilityKeys[n].includes(q))
    && a.mons.some(([i]) => inMode(mons[i])));
  const matchDocs = (q) => docTopics.filter((t) => !q || norm(t.title).includes(q) || t.s.includes(words(state.q)));

  // Above every view: how many results the same search has in the other tabs, each a chip that goes there
  const ALSO = [["dex", (q) => matchMons(q).length, "Pokémon", "Pokémon"], ["moves", (q) => matchMoves(q).length, "move", "moves"],
    ["tutors", (q) => matchTutors(q).length, "tutor move", "tutor moves"], ["abilities", (q) => matchAbilities(q).length, "ability", "abilities"],
    ["items", (q) => matchItems(q).length, "item", "items"], ["trainers", (q) => matchTrainers(q).length, "trainer", "trainers"], ["places", (q) => matchPlaces(q).length, "location", "locations"], ["check", (q) => matchCheck(q).length, "checklist entry", "checklist entries"], ["docs", (q) => matchDocs(q).length, "doc topic", "doc topics"]];
  function alsoLine(q, here) {
    if (q.length < 3) return "";
    const counts = ALSO.filter(([v]) => v !== here).map(([v, count, one, many]) => [v, count(q), one, many]).filter(([, n]) => n);
    return counts.length ? `<div class="also">Also matching: ${counts.map(([v, n, one, many]) => `<button data-goto="${v}">${n} ${n === 1 ? one : many}</button>`).join("")}</div>` : "";
  }

  function dexView(q) {
    const list = matchMons(q);
    if (state.mode) list.sort((a, b) => order[state.mode][a] - order[state.mode][b]);
    if (q) list.sort((a, b) => mons[b].s.some((s) => s.startsWith(q)) - mons[a].s.some((s) => s.startsWith(q)));
    const html = (list.length
      ? `<div class="list${state.layouts.dex === "grid" ? " grid" : ""}">${list.map((i) => row(mons[i], i)).join("")}</div>`
        + (state.layouts.dex === "grid" && state.open !== null ? sheet(`<div class="list">${row(mons[state.open], state.open, true)}</div>`) : "")
      : `<div class="nores">No Pokémon match “${esc(state.q)}”${state.mode ? ` in ${state.mode} mode` : ""}.</div>`);
    return [html, `${list.length} Pokémon`];
  }

  // In list views the open entry expands in place under its table row. In card views it opens in a pop-up over
  // the page instead, so the cards around it stay where they were.
  const expandRow = (cols, html) => `<tr class="expanded"><td colspan="${cols}">${html}</td></tr>`;
  const sheet = (html) => `<div class="sheet" role="dialog" aria-modal="true"><div class="sheet-backdrop" data-sheet-close></div>
    <div class="sheet-panel expanded"><button class="sheet-close" data-sheet-close aria-label="Close" title="Close">×</button><div class="sheet-body">${html}</div><div class="sheet-bar"><i></i></div></div></div>`;
  const chipsWithOpen = (keys, chip, isOpen, card) => {
    const open = keys.find(isOpen);
    return `<div class="chips">${keys.map(chip).join("")}</div>${open !== undefined ? sheet(card(open)) : ""}`;
  };

  // A move card's corner says how to teach it: its TM/HM number, or "Tutor" (tutor numbers mean nothing to players)
  const howTaught = (k) => (moves[k].tm ? moves[k].tm.label : moves[k].tutor ? "Tutor" : "");

  function movesView(q) {
    const list = exactFirst(matchMoves(q), (k) => moves[k].s.includes(q));
    if (!list.length) return [`<div class="nores">No moves match “${esc(state.q)}”.</div>`, "0 moves"];
    const open = state.move;  // only a click opens an entry; a typed name just sorts first
    let html;
    if (state.layouts.moves === "grid") {
      html = chipsWithOpen(list, (k) => `<button class="chip${k === open ? " on" : ""}" data-move="${k}">${typeBadge(moves[k].type)}<span class="ln">${esc(moves[k].name)}</span><span class="hw">${howTaught(k)}</span></button>`,
        (k) => k === open, (k) => moveCard(k, true));
    } else {
      const rows = list.map((k) => {
        const mv = moves[k];
        return `<tr data-move="${k}"${k === open ? ' class="on"' : ""}><td><span class="mvname">${esc(mv.name)}</span>${mv.official ? ` <span class="note">${esc(mv.official)}</span>` : ""}<span class="mvdesc">${esc(mv.desc)}</span></td><td>${typeBadge(mv.type)}</td>
          <td><span class="cat" title="${CAT_NAME[mv.split]}">${CAT[mv.split]}</span></td><td class="n">${mv.power || "—"}</td>
          <td class="n hide-sm">${mv.acc || "—"}</td><td class="n hide-sm">${mv.pp}</td><td class="n hide-sm">${mv.tm ? mv.tm.label : ""}</td></tr>${k === open ? expandRow(7, moveCard(k, true)) : ""}`;
      }).join("");
      html = `<div class="movelist"><table class="mv"><thead><tr><th>Move</th><th class="c-type">Type</th><th class="c-cat">Cat</th><th class="c-num">Pow</th><th class="c-num hide-sm">Acc</th><th class="c-num hide-sm">PP</th><th class="c-tm hide-sm">TM</th></tr></thead><tbody>${rows}</tbody></table></div>`;
    }
    return [html, `${list.length} moves`];
  }

  function itemsView(q) {
    const list = exactFirst(matchItems(q), (k) => itemKeys[k] === q);
    if (!list.length) return [`<div class="nores">No items match “${esc(state.q)}”.</div>`, "0 items"];
    const open = state.item;
    const cats = [];
    list.forEach((k) => { const c = items[k].category; const g = cats.find(([n]) => n === c); g ? g[1].push(k) : cats.push([c, [k]]); });
    const html = cats.map(([c, ks]) => `<div class="cat-head">${esc(c)} · ${ks.length}</div>${state.layouts.items === "grid"
      ? chipsWithOpen(ks, (k) => `<button class="chip${k === open ? " on" : ""}" data-item="${k}">${itemIcon(k)}<span class="ln">${esc(items[k].name)}</span></button>`, (k) => k === open, (k) => itemCard(k, true))
      : `<div class="listtable"><table class="mv"><thead><tr><th>Item</th><th>Where to find</th></tr></thead><tbody>${ks.map((k) =>
          `<tr data-item="${k}"${k === open ? ' class="on"' : ""}><td>${itemIcon(k)}<span class="mvname">${esc(items[k].name)}</span></td><td class="note">${esc(items[k].where.slice(0, 2).join("; ") || "—")}${
            items[k].where.length > 2 ? ` +${items[k].where.length - 2} more` : ""}</td></tr>${k === open ? expandRow(2, itemCard(k, true)) : ""}`).join("")}</tbody></table></div>`}`).join("");
    return [html, `${list.length} items`];
  }

  function placesView(q) {
    const list = exactFirst(matchPlaces(q), (p) => norm(p.name) === q);
    if (!list.length) return [`<div class="nores">No locations match “${esc(state.q)}”.</div>`, "0 locations"];
    const open = state.place ? norm(state.place) : null;
    const isOpen = (p) => norm(p.name) === open;
    const encounters = (p) => p.rows.filter(([, l]) => rowInMode(l)).length;
    const methods = (p) => (p.rows.length ? [...new Set(p.rows.filter(([, l]) => rowInMode(l)).map(([, l]) => l.method))].join(" · ") : "Items only");
    const html = state.layouts.places === "grid"
      ? chipsWithOpen(list, (p) => `<button class="chip${isOpen(p) ? " on" : ""}" data-place="${esc(p.name)}"><span class="ln" style="padding-left:10px">${esc(p.name)}</span><span class="hw">${p.rows.length ? encounters(p) : ""}</span></button>`, isOpen, (p) => placeCard(p, true))
      : `<div class="listtable"><table class="mv"><thead><tr><th class="c-place">Location</th><th class="hide-sm">Found by</th><th class="c-mons">Pokémon</th></tr></thead><tbody>${list.map((p) =>
          `<tr data-place="${esc(p.name)}"${isOpen(p) ? ' class="on"' : ""}><td><span class="mvname">${esc(p.name)}</span></td><td class="note hide-sm">${esc(methods(p))}</td><td class="n">${encounters(p)}</td></tr>${
            isOpen(p) ? expandRow(3, placeCard(p, true)) : ""}`).join("")}</tbody></table></div>`;
    return [html, `${list.length} locations`];
  }

  function tutorsView(q) {
    const rows = matchTutors(q);
    if (!rows.length) return [`<div class="nores">No tutors match “${esc(state.q)}”.</div>`, "0 tutor moves"];
    const open = state.move || (q && rows.find((t) => moves[t.move].s.includes(q)) || {}).move || null;
    let opened = false;  // a move taught in two places opens under the first
    const isOpen = (t) => { if (t.move !== open || opened) return false; opened = true; return true; };
    const groups = [];
    rows.forEach((t) => { const key = t.kind + "|" + t.where; const g = groups.find(([k]) => k === key); g ? g[1].push(t) : groups.push([key, [t]]); });
    const learners = (t) => moves[t.move].learners.filter(([i, h]) => inMode(mons[i]) && h.startsWith(t.kind === "Special" ? "Special:" : "Tutor")).length;
    const asCards = state.layouts.tutors === "grid";
    const html = groups.map(([key, ts]) => {
      const [kind, where] = key.split("|");
      const sameNote = ts.every((t) => t.note === ts[0].note) ? ts[0].note : "";
      const head = `<div class="cat-head tutorhead">${esc(where)}${kind === "Special" ? " · special tutor" : ""}${sameNote ? `<small>${esc(sameNote)}</small>` : ""}</div>`;
      if (asCards) {
        const flags = ts.map(isOpen);
        return head + chipsWithOpen(ts.map((_, n) => n), (n) => {
          const t = ts[n];
          return `<button class="chip${flags[n] ? " on" : ""}" data-move="${t.move}">${typeBadge(moves[t.move].type)}<span class="ln">${esc(moves[t.move].name)}</span><span class="hw" title="${sameNote ? "Pokémon that can learn it" : esc(t.note)}">${learners(t)}</span></button>`;
        }, (n) => flags[n], (n) => moveCard(ts[n].move, true));
      }
      const cols = sameNote ? 5 : 6;
      return head + `<div class="listtable"><table class="mv"><thead><tr><th>Move</th><th class="c-type">Type</th><th class="c-cat">Cat</th><th class="c-num hide-sm">Pow</th>${sameNote ? "" : "<th>Requirement</th>"}<th class="c-num">Learn</th></tr></thead><tbody>${ts.map((t) => {
        const mv = moves[t.move], on = isOpen(t);
        return `<tr data-move="${t.move}"${on ? ' class="on"' : ""}><td><span class="mvname">${esc(mv.name)}</span></td><td>${typeBadge(mv.type)}</td><td><span class="cat" title="${CAT_NAME[mv.split]}">${CAT[mv.split]}</span></td><td class="n hide-sm">${mv.power || "—"}</td>${
          sameNote ? "" : `<td class="note">${esc(t.note)}</td>`}<td class="n">${learners(t)}</td></tr>${on ? expandRow(cols, moveCard(t.move, true)) : ""}`;
      }).join("")}</tbody></table></div>`;
    }).join("");
    return [html, `${rows.length} tutor moves`];
  }

  // Abilities: each ability as players see it, with its description and who can have it
  const abilities = DEX.abilities;
  const abilityIndex = new Map(abilities.map((a, n) => [a.name, n]));
  const abilityKeys = abilities.map((a) => norm(a.name) + " " + norm(a.official || ""));  // in-game or official name

  function abilityCard(a) {
    const holders = a.mons.filter(([i]) => inMode(mons[i]));
    const group = (hidden, title) => {
      const l = holders.filter(([, h]) => h === hidden);
      return l.length ? `<div><h4>${title} · ${l.length}</h4><div class="chips">${l.map(([i]) => monChip(i, "")).join("")}</div></div>` : "";
    };
    // The game's one-line description, then how it actually works in this game (written from CFRU's code)
    const affects = a.moves.length ? `<div><h4>Affected moves · ${a.moves.length}</h4><div class="chips">${a.moves.map((k) =>
      `<button class="chip" data-move="${k}">${typeBadge(moves[k].type)}<span class="ln">${esc(moves[k].name)}</span></button>`).join("")}</div></div>` : "";
    return `<article class="abilcard">${COLLAPSE}<h2>${esc(a.name)}${a.official ? `<small>${esc(a.official)}</small>` : ""}</h2>${a.desc ? `<div class="gamedesc">${esc(a.desc)}</div>` : ""}
      <div class="abildetail">${a.detail.split(/ (?=Outside battle)/).map((p) => `<p>${esc(p)}</p>`).join("")}</div>${a.chance ? `<div class="specs"><span>Effect chance <b>${a.chance}%</b></span></div>` : ""}
      <div class="learners">${group(0, "Ability") + group(1, "Hidden ability") || '<p class="empty">No Pokémon match the current filters.</p>'}${affects}</div></article>`;
  }

  function abilitiesView(q) {
    const list = exactFirst(matchAbilities(q), (a) => norm(a.name) === q || (a.official && norm(a.official) === q));
    if (!list.length) return [`<div class="nores">No abilities match “${esc(state.q)}”.</div>`, "0 abilities"];
    const open = state.ability;
    const isOpen = (a) => a.name === open;
    const count = (a) => a.mons.filter(([i]) => inMode(mons[i])).length;
    const html = state.layouts.abilities === "grid"
      ? chipsWithOpen(list, (a) => `<button class="chip${isOpen(a) ? " on" : ""}" data-ability="${esc(a.name)}"><span class="ln" style="padding-left:10px">${esc(a.name)}</span><span class="hw">${count(a)}</span></button>`, isOpen, abilityCard)
      : `<div class="listtable"><table class="mv"><thead><tr><th>Ability</th><th class="c-num">Pokémon</th></tr></thead><tbody>${list.map((a) =>
          `<tr data-ability="${esc(a.name)}"${isOpen(a) ? ' class="on"' : ""}><td><span class="mvname">${esc(a.name)}</span>${a.official ? ` <span class="note">${esc(a.official)}</span>` : ""}<span class="mvdesc">${esc(a.desc)}</span></td><td class="n">${count(a)}</td></tr>${
            isOpen(a) ? expandRow(2, abilityCard(a)) : ""}`).join("")}</tbody></table></div>`;
    return [html, `${list.length} abilities`];
  }

  // Docs: the feature list's topics, grouped by its top-level headings
  const docTopics = DEX.docs.flatMap((g) => g.topics.map((t) => Object.assign({ group: g.title }, t)));

  function docCard(t) {
    return `<article class="doccard">${COLLAPSE}<h2>${esc(t.title)}</h2><div class="doc">${t.html}</div></article>`;
  }

  function docsView(q) {
    const list = matchDocs(q);
    if (!list.length) return [`<div class="nores">No topics mention “${esc(state.q)}”.</div>`, "0 topics"];
    const open = state.doc;
    const isOpen = (t) => t.title === open;
    const groups = [];
    list.forEach((t) => { const g = groups.find(([n]) => n === t.group); g ? g[1].push(t) : groups.push([t.group, [t]]); });
    const html = groups.map(([g, ts]) => `<div class="cat-head">${esc(g)} · ${ts.length}</div>${state.layouts.docs === "grid"
      ? '<div class="dchips">' + chipsWithOpen(ts, (t) => `<button class="chip${isOpen(t) ? " on" : ""}" data-doc="${esc(t.title)}"><span class="ln" style="padding-left:10px">${esc(t.title)}</span></button>`, isOpen, docCard) + "</div>"
      : `<div class="listtable"><table class="mv"><tbody>${ts.map((t) => `<tr data-doc="${esc(t.title)}"${isOpen(t) ? ' class="on"' : ""}><td><span class="mvname">${esc(t.title)}</span></td></tr>${
          isOpen(t) ? expandRow(1, docCard(t)) : ""}`).join("")}</tbody></table></div>`}`).join("");
    return [html, `${list.length} topics`];
  }

  // Checklist: what there is to do, in playthrough order (checklist.py). Ticks live in this
  // browser's storage; the Download link writes them into the saved file, and Export / Import moves them elsewhere.
  const CK = DEX.checklist;
  // Kinds keep the interactive maps' colours and shapes; story beats are a ring
  const CK_KIND = { story: ["Story", "#6b35c4", ""], npc: ["Person or event", "#009e73", "6,2 16,2 21,11 16,20 6,20 1,11"],
    wild: ["Pokémon encounter", "#cc79a7", "11,1 13.9,7.6 21,8.3 15.7,13.1 17.2,20.1 11,16.5 4.8,20.1 6.3,13.1 1,8.3 8.1,7.6"],
    item: ["Item ball", "#d55e00", "3,3 19,3 19,19 3,19"], hidden: ["Hidden item", "#f0e442", "11,1 21,11 11,21 1,11"] };
  const ckShape = (k) => `<span class="ck-kind" title="${CK_KIND[k][0]}"><svg viewBox="0 0 22 22" aria-hidden="true">${k === "story"
    ? `<circle cx="11" cy="11" r="8" fill="${CK_KIND[k][1]}" stroke="#111" stroke-width="1.6"/><circle cx="11" cy="11" r="3" fill="#fff" stroke="#111" stroke-width="1.2"/>`
    : `<polygon points="${CK_KIND[k][2]}" fill="${CK_KIND[k][1]}" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/>`}</svg></span>`;
  const ckAll = [];
  CK.stages.forEach((st) => st.groups.forEach((g) => g.entries.forEach((e) => {
    e.s = words(`${e.t} ${g.place} ${st.title} ${e.fl || ""} ${CK_KIND[e.k][0]} ${e.need || ""}`);
    ckAll.push(e);
  })));
  const ck = { done: {}, hide: false, closed: {} };
  const ckMerge = (done) => { for (const [id, t] of Object.entries(done || {})) if (!ck.done[id]) ck.done[id] = t || 1; };
  const ckSave = () => {
    try {
      localStorage.setItem("dex-checklist", JSON.stringify({ v: 1, done: ck.done }));
      localStorage.setItem("dex-check-ui", JSON.stringify({ hide: ck.hide, closed: ck.closed }));
    } catch (e) {}
  };
  try { ckMerge(JSON.parse(localStorage.getItem("dex-checklist") || "{}").done); } catch (e) {}
  try { const ui = JSON.parse(localStorage.getItem("dex-check-ui") || "{}"); ck.hide = !!ui.hide; ck.closed = ui.closed || {}; } catch (e) {}
  // A downloaded copy carries the ticks it was saved with; they join this browser's once per saved file
  const ckBaked = document.getElementById("saved-checklist");
  if (ckBaked) {
    try {
      const b = JSON.parse(ckBaked.textContent);
      let seen = null;
      try { seen = localStorage.getItem("dex-checklist-baked"); } catch (e) {}
      if (String(b.t) !== seen) {
        ckMerge(b.done);
        try { localStorage.setItem("dex-checklist-baked", String(b.t)); } catch (e) {}
        ckSave();
      }
    } catch (e) {}
  }
  const ckDone = (list) => list.filter((e) => ck.done[e.id]).length;
  const ckStageEntries = (st) => st.groups.flatMap((g) => g.entries);
  const matchCheck = (q) => { const fw = words(state.q); return ckAll.filter((e) => !q || e.s.includes(fw)); };
  const ckTag = (text) => `<span class="mode">${esc(text)}</span>`;

  // Pokémon named in an entry link to their Pokédex entries (e.p: [start, end, Pokémon] from checklist.py)
  const ckText = (e) => {
    if (!e.p) return esc(e.t);
    let html = "", at = 0;
    for (const [a, b, i] of e.p) { html += esc(e.t.slice(at, a)) + `<button class="mvname" data-open="${i}">${esc(e.t.slice(a, b))}</button>`; at = b; }
    return html + esc(e.t.slice(at));
  };
  function ckRow(e, g) {
    const name = e.tr ? `<button class="mvname" data-cktr="${e.tr.join(",")}" title="See this trainer's team">${esc(e.t)}</button>`
      : e.item != null ? `<button class="mvname" data-item="${e.item}">${esc(e.t)}</button>` : ckText(e);
    const tags = [e.sd && "Differs by mode", e.only && `${e.only} only`, e.need && `Needs ${e.need}`, e.until, e.fl].filter(Boolean).map(ckTag).join("");
    return `<div class="ck${ck.done[e.id] ? " done" : ""}"><label><input type="checkbox" data-ck="${esc(e.id)}"${ck.done[e.id] ? " checked" : ""}>${ckShape(e.k)}
      <span class="ck-body">${name}${tags ? `<span class="ck-tags">${tags}</span>` : ""}</span></label>${
      e.mark ? `<button class="ck-map" data-ckmap="${g.slug}" data-mark="${e.mark}" >See Interactive Map</button>` : ""}</div>`;
  }

  function ckCounts() {
    const done = ckDone(ckAll), el = $("#ck-total");
    if (!el) return;
    el.textContent = `${done} / ${ckAll.length} done`;
    $("#ck-fill").style.width = `${ckAll.length ? 100 * done / ckAll.length : 0}%`;
    document.querySelectorAll("[data-ckn]").forEach((n) => {
      const es = ckStageEntries(CK.stages[+n.dataset.ckn]), d = ckDone(es);
      n.textContent = `${d} / ${es.length}`;
      n.classList.toggle("all", d === es.length);
    });
    $("#count").textContent = `${done} / ${ckAll.length} done`;
  }

  function checkView(q) {
    if (!ckAll.length) return ['<div class="nores">The checklist isn’t in this build.</div>', ""];
    const fw = words(state.q), hit = (e) => !q || e.s.includes(fw);
    const kinds = new Set(ckAll.map((e) => e.k));
    const stages = CK.stages.map((st, n) => {
      const groups = st.groups.map((g) => [g, g.entries.filter(hit)]).filter(([, es]) => es.length);
      if (!groups.length) return "";
      const open = q || (st.title in ck.closed ? !ck.closed[st.title] : st.kind === "place" || st.kind === "unlock");
      const named = st.kind !== "place";  // a place's own section needs no place heading, just a way to its card
      const card = named ? "" : places.has(norm(st.title)) ? st.title : st.groups[0].place;
      return `<details class="ck-stage k-${st.kind}" data-ckstage="${esc(st.title)}"${open ? " open" : ""}><summary>${CHEVRON}<span class="ck-title">${esc(st.title)}</span>${
        card ? `<button class="ck-loc" data-place="${esc(card)}" title="Pokémon, items and map for ${esc(card)}">See Location</button>` : ""}<span class="ck-n" data-ckn="${n}"></span></summary>
        <div class="ck-rows">${groups.map(([g, es]) => `${named || g.place !== st.place ? `<div class="ck-place"><button data-place="${esc(g.place)}">${esc(g.place)}</button></div>` : ""}${es.map((e) => ckRow(e, g)).join("")}`).join("")}</div></details>`;
    }).join("");
    if (!stages) return [`<div class="nores">Nothing on the checklist matches “${esc(state.q)}”.</div>`, "0 entries"];
    const html = `<div class="cklist${ck.hide ? " hide-done" : ""}">
      <div class="ck-head"><div class="ck-prog"><span id="ck-total"></span><span class="ck-bar"><i id="ck-fill"></i></span></div>
        <div class="ck-key">${Object.keys(CK_KIND).filter((k) => kinds.has(k)).map((k) => `<span>${ckShape(k)}${CK_KIND[k][0]}</span>`).join("")}</div>
        <div class="ck-acts"><label><input type="checkbox" data-ckact="hide"${ck.hide ? " checked" : ""}>Hide finished</label>
          <button data-ckact="open-all">Expand All</button><button data-ckact="close-all">Collapse All</button><button data-ckact="open-done" title="Expand the sections you have finished">Expand Completed</button><button data-ckact="close-done" title="Collapse the sections you have finished">Collapse Completed</button>
          <button data-ckact="save" title="Tick what your save file says you've done (.sav or .srm); replaces your current ticks">Load Save File</button><button data-ckact="export" title="Save your ticks to a file">Export</button><button data-ckact="import" title="Load ticks from an exported file">Import</button><button data-ckact="reset">Reset</button></div>
        <p class="note ck-help">Track your progress in Pokemon Amethyst. Progress is tracked in your browser; Export and Import allow you to move data to/from local copies. Entries are ordered by what you can reach as you play: things that need an HM (Surf, for example) are only listed after the point where you get it.</p></div>
      <div class="ck-stages">${stages}</div></div>`;
    return [html, ""];
  }

  const ckFile = (name, type, text) => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type }));
    a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  };
  const ckPayload = () => JSON.stringify({ app: "pokemon-amethyst-companion", v: 1, t: Date.now(), done: ck.done });
  function ckImport() {
    const input = document.createElement("input");
    input.type = "file"; input.accept = ".json,application/json";
    input.addEventListener("change", () => {
      const f = input.files[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const data = JSON.parse(reader.result);
          if (!data || typeof data.done !== "object") throw new Error();
          ckMerge(data.done); ckSave(); render();
        } catch (e) { alert("That file isn’t a checklist export."); }
      };
      reader.readAsText(f);
    });
    input.click();
  }
  // A save file ticks the list: each entry's e.sv lists what in the game's save means it's done (save_flags.py).
  // The layout is CFRU's (save.c): 2 slots of 14 sectors of 0x1000 bytes, each ending in its id, checksum, signature
  // and save counter; the newer complete slot is the game's save. SaveBlock1 is sectors 1-4 (0xFF0 bytes each) with
  // flags 0-0x8FF at 0xEE0 and variables 0x4000 on at 0x1000. CFRU's own block (flags 0x900 on, then much later the
  // bag) fills the unused tails of sectors 0, 4 and 13, then sectors 30 and 31.
  function ckReadSave(bytes) {
    if (bytes.length < 0x20000) return null;  // .sav and .srm are both the raw 128 KiB flash (some add a clock footer)
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const TAIL = { 0: 0xF24, 4: 0xD98, 13: 0x450 };  // where the vanilla game's part of a sector ends
    let best = null;
    for (let slot = 0; slot < 2; slot++) {
      const at = {};
      let counter = 0;
      for (let i = 0; i < 14; i++) {
        const o = (slot * 14 + i) * 0x1000;
        if (view.getUint32(o + 0xFF8, true) !== 0x08012025) continue;
        const id = view.getUint16(o + 0xFF4, true), size = TAIL[id] || 0xFF0;
        let sum = 0;  // the game's checksum, over the vanilla part: a half-written sector fails it
        for (let w = 0; w < size; w += 4) sum = (sum + view.getUint32(o + w, true)) >>> 0;
        if ((((sum >>> 16) + sum) & 0xFFFF) !== view.getUint16(o + 0xFF6, true)) continue;
        at[id] = o;
        counter = view.getUint32(o + 0xFFC, true);
      }
      if (Object.keys(at).length === 14 && (!best || counter > best.counter)) best = { at, counter };
    }
    if (!best) return null;
    const join = (parts) => {
      const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
      let n = 0;
      parts.forEach((p) => { out.set(p, n); n += p.length; });
      return out;
    };
    const part = (id, from) => bytes.subarray(best.at[id] + from, best.at[id] + 0xFF0);
    const block1 = join([1, 2, 3, 4].map((id) => part(id, 0)));
    const block = join([part(0, TAIL[0]), part(4, TAIL[4]), part(13, TAIL[13]), bytes.subarray(0x1E000, 0x1EFF0), bytes.subarray(0x1F000, 0x1FFF0)]);
    const u16 = (b, o) => b[o] | (b[o + 1] << 8);
    const items = new Set();
    for (let o = 0x9AC; o < 0x15D4; o += 4) items.add(u16(block, o));  // the bag: RAM 0x203BB20-0x203C748 in the block at 0x203B174
    return { flags: join([block1.subarray(0xEE0, 0x1000), block.subarray(0, 0x200)]), items, v: (n) => u16(block1, 0x1000 + 2 * (n - 0x4000)) };
  }
  // A condition is a flag number, ["v", variable, at least], ["i", item in the bag] or ["&", all of these...]
  const ckHolds = (c, save) => typeof c === "number" ? !!((save.flags[c >> 3] >> (c & 7)) & 1)
    : c[0] === "v" ? save.v(c[1]) >= c[2] : c[0] === "i" ? save.items.has(c[1]) : c.slice(1).every((x) => ckHolds(x, save));
  const ckFromSave = (save) => {
    const done = {};
    ckAll.forEach((e) => { if (e.sv && e.sv.some((c) => ckHolds(c, save))) done[e.id] = 1; });
    return done;
  };
  function ckLoadSave() {
    const input = document.createElement("input");
    input.type = "file";  // no accept filter: phones hide .sav / .srm files behind one
    input.addEventListener("change", () => {
      const f = input.files[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = () => {
        const save = ckReadSave(new Uint8Array(reader.result));
        if (!save) { alert("That isn’t a Pokémon Amethyst save file. Choose the .sav or .srm file your emulator saves (not a save state)."); return; }
        const done = ckFromSave(save), n = Object.keys(done).length, blind = ckAll.filter((e) => !e.sv).length;
        if (!confirm(`This save has ${n} of ${ckAll.length} entries done.${blind ? ` ${blind} entries can’t be read from a save file and will be left unticked.` : ""}

Replace your ${ckDone(ckAll)} current ticks with it?`)) return;
        ck.done = done; ckSave(); render();
      };
      reader.readAsArrayBuffer(f);
    });
    input.click();
  }
  function ckAct(el) {
    const act = el.dataset.ckact;
    if (act === "hide") { ck.hide = el.checked; ckSave(); el.closest(".cklist").classList.toggle("hide-done", ck.hide); }
    else if (/^(open|close)-(all|done)$/.test(act)) {  // fold or unfold every section, or only the finished ones
      const open = act.startsWith("open"), onlyDone = act.endsWith("done");
      document.querySelectorAll("details.ck-stage").forEach((d) => {
        if (onlyDone && !d.querySelector(".ck-n.all")) return;
        d.open = open;
        if (!state.q) ck.closed[d.dataset.ckstage] = !open;  // a search opens everything without saving that
      });
      ckSave();
    }
    else if (act === "export") ckFile("amethyst-checklist.json", "application/json", ckPayload());
    else if (act === "import") ckImport();
    else if (act === "save") ckLoadSave();
    else if (act === "reset" && confirm("Clear every tick on the checklist?")) { ck.done = {}; ckSave(); render(); }
  }

  // Trainers: four teams each, from the Standard, Hard, Divergent and Hard Divergent tables (in that order).
  // A trainer is one entry tagged Both when Divergent mode fights the same teams, else one entry per mode.
  const trainers = DEX.trainers, TEAMS = DEX.teams;
  const DIFF_NAME = { std: "Standard", hard: "Hard", xhard: "Extra Hard" };
  const NATURE_STATS = ["Atk", "Def", "Spe", "SpA", "SpD"];  // the order natures raise and lower stats in
  const entries = [];
  trainers.forEach((t, n) => {
    if (t.teams[0] === t.teams[2] && t.teams[1] === t.teams[3]) entries.push({ n, mode: "Both" });
    else entries.push({ n, mode: "Standard" }, { n, mode: "Divergent" });
  });
  const trainerTitle = (t) => (t.rival ? t.cls : `${t.cls} ${t.name}`.trim());
  const trainerSlug = (e) => `${e}-${slug(trainerTitle(trainers[entries[e].n]))}`;
  const slots = (e) => (entries[e].mode === "Divergent" ? [2, 3] : [0, 1]);  // [this mode's team, its Hard team]
  const teamOf = (e) => TEAMS.list[trainers[entries[e].n].teams[slots(e)[state.diff === "std" ? 0 : 1]]];
  const entryInMode = (e) => !state.mode || entries[e].mode === "Both" || entries[e].mode === state.mode;
  const entryMode = (e) => modeTag(entries[e].mode);
  // Searched from the start of any word: "raine" finds Leader Raine but not every "Trainer"
  const wordStarts = (s) => { const w = words(s).split(" "); return w.map((_, k) => w.slice(k).join("")); };
  const trainerKeys = trainers.map((t) => [...wordStarts(`${t.cls} ${t.name}`), ...wordStarts(t.place), t.rival ? "rival" : ""].filter(Boolean));
  const natureText = (n) => {
    const up = Math.floor(n / 5), down = n % 5;
    return TEAMS.natures[n] + (up === down ? "" : ` (+${NATURE_STATS[up]} −${NATURE_STATS[down]})`);
  };
  const trainerPic = (t, size) => `<span class="tp${size ? " " + size : ""}" aria-hidden="true">${t.pic ? `<i style="background-position:-${t.pic[0]}px -${t.pic[1]}px"></i>` : ""}</span>`;
  const trainerItem = (it) => (typeof it === "number" ? itemButton(it) : `<span>${esc(it)}</span>`);

  function matchTrainers(q) {
    const fw = words(state.q);
    return entries.map((_, e) => e).filter((e) => {
      if (!entryInMode(e)) return false;
      const n = entries[e].n, t = trainers[n];
      // its Pokémon count in every difficulty
      return !q || trainerKeys[n].some((k) => k.startsWith(q)) || words(t.note).includes(fw)
        || slots(e).some((s) => TEAMS.list[t.teams[s]].some(([i]) => mons[i].s.some((x) => x.includes(q))));
    });
  }

  function teamMon([i, lv, it, ab, mvs, nat, evs, custom, gender], t) {
    const m = mons[i], hard = state.diff !== "std", xhard = state.diff === "xhard";
    const ability = TEAMS.abilities[ab].split(" or ").map((a) => (abilityIndex.has(a) ? `<button class="mvname" data-ability="${esc(a)}">${esc(a)}</button>` : esc(a))).join(" or ");
    const rows = [
      ["Type", `<span class="tags">${m.types.map(typeBadge).join("")}</span>`],
      it !== null && ["Item", trainerItem(it)],
      ab !== null && TEAMS.abilities[ab] && ["Ability", ability],
      hard && ["Nature", esc(natureText(nat))],
      ["IVs", `${xhard ? 31 : t.iv} in every stat`],
      xhard && ["EVs", evs.slice().sort().map((s) => `252 ${STAT_LABELS[s]}`).join(", ")],
    ].filter(Boolean);
    const moveBtn = (n) => {
      const k = TEAMS.moves[n], mv = moves[k];
      return `<button class="tmv" data-move="${k}" style="--c:${TYPE_COLOR[mv.type]}" title="${esc(mv.desc)}"><span class="cat" title="${CAT_NAME[mv.split]}">${CAT[mv.split]}</span><span class="tmvname">${esc(mv.name)}</span>${typeBadge(mv.type)}</button>`;
    };
    // Gender the game gives it (trainers.py _gender: the trainer's, unless the species can't be or is 75%+ female)
    const sex = gender === "F" ? FEMALE : gender === "M" ? MALE : "";
    return `<div class="tmon" style="${tint(m)}"><div class="head">${monLink(i)}${sex}<span class="lv">${t.scaled ? `Scaling, minimum ${lv}` : `Lv ${lv}`}</span></div>
      <dl>${rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl>
      ${t.scaled && !custom  // the game picks these moves at the scaled level, so the listed level's moves would be wrong
        ? `<p class="note tmnote">Knows the last four moves it learns by level up, at the level it scales to.</p>`
        : `<div class="tmoves">${mvs.map(moveBtn).join("")}</div>`}</div>`;
  }

  function trainerCard(e) {
    const t = trainers[entries[e].n], team = teamOf(e);
    const flags = [t.double && "Double battle", t.rival && "Named whatever you named your rival"].filter(Boolean);
    return `<article class="trainercard">${COLLAPSE}
      <div class="top">${trainerPic(t, "lg")}
        <div class="thead"><h2>${esc(trainerTitle(t))} ${entryMode(e)}<small>${esc(t.place)}</small></h2>
          ${t.note ? `<div class="tnote">${esc(t.note)}</div>` : ""}
          ${flags.length ? `<div class="tflags">${flags.map((f) => `<span class="mode">${f}</span>`).join("")}</div>` : ""}</div>
        <div class="tside"><div><h4>Poké Ball</h4><div class="tflags">${trainerItem(t.ball)}</div></div>
          ${t.items.length ? `<div><h4>Items the trainer uses</h4><div class="tflags">${t.items.map(trainerItem).join("")}</div></div>` : ""}</div>
      </div>
      <div><h4>Team · ${DIFF_NAME[state.diff]} difficulty · ${team.length} Pokémon</h4><div class="team">${team.map((mon) => teamMon(mon, t)).join("")}</div></div>
    </article>`;
  }

  function trainersView(q) {
    const list = matchTrainers(q);
    if (!list.length) return [`<div class="nores">No trainers match “${esc(state.q)}”${state.mode ? ` in ${state.mode} mode` : ""}.</div>`, "0 trainers"];
    const open = state.trainer;
    const groups = [];
    list.forEach((e) => { const p = trainers[entries[e].n].place || "Other"; const g = groups.find(([x]) => x === p); g ? g[1].push(e) : groups.push([p, [e]]); });
    const maxLv = (e) => Math.max(...teamOf(e).map(([, lv]) => lv));
    // Scaled battles (Trainer Houses, Gym Trainees…) come out at your party's highest level
    const SCALE_TIP = "Levels scale to your party's highest";
    const minLv = (e) => Math.min(...teamOf(e).map(([, lv]) => lv));
    const lvRange = (e) => (minLv(e) === maxLv(e) ? `${minLv(e)}` : `${minLv(e)}–${maxLv(e)}`);
    const lvText = (e) => (trainers[entries[e].n].scaled ? `Scaling, min ${minLv(e)}` : `Lv ${lvRange(e)}`);
    const html = groups.map(([p, es]) => `<div class="cat-head">${esc(p)} · ${es.length}</div>${state.layouts.trainers === "grid"
      ? '<div class="tchips">' + chipsWithOpen(es, (e) => `<button class="chip${e === open ? " on" : ""}" data-trainer="${e}">${trainerPic(trainers[entries[e].n], "sm")}<span class="ln">${esc(trainerTitle(trainers[entries[e].n]))}</span>${
          state.mode ? "" : entryMode(e)}<span class="hw" title="${trainers[entries[e].n].scaled ? SCALE_TIP : "Levels on the team"}">${lvText(e)}</span></button>`, (e) => e === open, trainerCard) + '</div>'
      : `<div class="listtable"><table class="mv"><thead><tr><th>Trainer</th><th class="tteam">Team</th><th class="c-lv tlvcol">Level</th></tr></thead><tbody>${es.map((e) => {
          const t = trainers[entries[e].n], sprites = teamOf(e).map(([i]) => sprite(mons[i], true)).join("");
          return `<tr data-trainer="${e}"${e === open ? ' class="on"' : ""}><td><div class="trow">${trainerPic(t)}<span class="tn"><span class="tname"><span class="mvname">${esc(trainerTitle(t))}</span>${entryMode(e)}</span>${
            t.note ? `<span class="note">${esc(t.note)}</span>` : ""}<span class="teamline tt-inline">${sprites}</span></span></div></td><td class="tteam"><span class="teamline">${sprites}</span></td>
            <td class="n lvcell tlvcol" title="${t.scaled ? SCALE_TIP : "Levels on the team"}">${t.scaled ? `<span class="note">Scaling, min</span> ${minLv(e)}` : lvRange(e)}</td></tr>${e === open ? expandRow(3, trainerCard(e)) : ""}`;
        }).join("")}</tbody></table></div>`}`).join("");
    return [html, `${list.length} trainers`];
  }

  const PLACEHOLDER = {
    dex: "Search Pokémon or dex # — e.g. Rockruff, 16, Mega, Galarian, Fire",
    moves: "Search moves, TMs or types — e.g. Ceaseless Edge, TM02, Fire",
    tutors: "Search tutor moves, towns or types — e.g. Draco Meteor, Ferrox Village, Fire",
    abilities: "Search abilities or what they do — e.g. Triage, Libero, weather",
    items: "Search items or kinds — e.g. Fire Stone, Berries, Mega",
    trainers: "Search trainers, places or their Pokémon — e.g. Raine, Hiker, Route 8, Rockruff",
    places: "Search places, or what's there — e.g. Route 2, Bidoof, Full Heal, Grass",
    check: "Search the checklist — e.g. Ferrox Village, trade, TM12",
    docs: "Search the docs — e.g. Frostbite, Battle Frontier, shiny",
  };

  let shownView = null;
  function render(scroll) {
    const hadSheet = shownView === state.view && !!$("#out .sheet");
    shownView = state.view;
    const q = norm(state.q);
    const [html, count] = { dex: dexView, moves: movesView, tutors: tutorsView, abilities: abilitiesView, items: itemsView, trainers: trainersView, places: placesView, check: checkView, docs: docsView }[state.view](q);
    $("#out").innerHTML = alsoLine(q, state.view) + html;
    $("#count").textContent = count;
    if (state.view === "check") ckCounts();
    $("#q").value = state.q;
    $("#q").placeholder = PLACEHOLDER[state.view];
    $("#clear").hidden = !$("#q").value;
    $("#back").disabled = depth <= 0;
    $("#fwd").disabled = depth >= top;
    $("#mode-seg").hidden = state.view === "docs" || state.view === "check";
    $("#layout-seg").hidden = state.view === "check";  // one layout: cards of uneven length read as chaos (Collin)
    $("#diff-pick").hidden = state.view !== "trainers";
    document.querySelectorAll(".seg button[data-diff]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.diff === state.diff)));
    document.querySelectorAll("[data-viewtab]").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.viewtab === state.view)));
    document.querySelectorAll(".seg button[data-mode]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === state.mode)));
    document.querySelectorAll(".seg button[data-view]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === state.layouts[state.view])));
    syncConsoleHeight();
    document.body.classList.toggle("sheet-open", !!$("#out .sheet"));
    if (state.map && MapView.open(state.map, state.mark)) return;
    MapView.close();
    // Closing a pop-up (×, backdrop, Escape, Back) leaves the cards behind it where they were
    if (hadSheet && !$("#out .sheet")) return;
    if (scroll && $("#out .sheet")) {
      const on = document.querySelector(".mon.on, .chip.on");
      if (on) on.scrollIntoView({ block: "nearest" });
    } else if (scroll) {
      const el = (state.open !== null && document.querySelector(`.mon[data-i="${state.open}"]`)) || ((state.move || state.item !== null || state.place || state.doc || state.ability || state.trainer !== null) && document.querySelector("tr.on, .chip.on"));
      if (el) el.scrollIntoView({ block: "start" }); else window.scrollTo({ top: 0 });
    }
  }

  // ---------------------------------------------------------------- wiring
  let timer;
  $("#q").addEventListener("input", (e) => {
    clearTimeout(timer);
    timer = setTimeout(() => { Object.assign(state, { q: e.target.value, open: null, move: null, item: null, place: null, map: null, doc: null, ability: null, trainer: null }); queries[state.view] = state.q; remember(); render(); }, 120);
  });
  $("#clear").addEventListener("click", () => { Object.assign(state, { q: "", open: null, move: null, item: null, place: null, map: null, doc: null, ability: null, trainer: null }); queries[state.view] = ""; remember(); render(); $("#q").focus(); });
  $("#back").addEventListener("click", () => history.back());
  $("#fwd").addEventListener("click", () => history.forward());
  // Switching tabs restores that tab's own search; clicking the current tab again clears it
  document.querySelectorAll("[data-viewtab]").forEach((b) => b.addEventListener("click", () => {
    const view = b.dataset.viewtab;
    navigate({ view, q: view === state.view ? "" : queries[view] || "" });
  }));
  document.querySelectorAll(".seg button[data-view]").forEach((b) => b.addEventListener("click", () => {
    state.layouts[state.view] = b.dataset.view;
    try { localStorage.setItem("dex-layouts", JSON.stringify(state.layouts)); } catch (e) {}
    render();
  }));
  document.querySelectorAll(".seg button[data-mode]").forEach((b) => b.addEventListener("click", () => {
    state.mode = b.dataset.mode;
    try { localStorage.setItem("dex-mode", state.mode); } catch (e) {}
    // An open trainer with separate Standard and Divergent teams switches to the same trainer in the new mode
    const t = state.trainer;
    if (t !== null && !entryInMode(t)) {
      const other = entries.findIndex((x) => x.n === entries[t].n && x.mode === state.mode);
      if (other >= 0) { state.trainer = other; remember(); render(true); return; }
    }
    render();
  }));
  document.querySelectorAll(".seg button[data-diff]").forEach((b) => b.addEventListener("click", () => {
    state.diff = b.dataset.diff;
    try { localStorage.setItem("dex-diff", state.diff); } catch (e) {}
    render();
  }));

  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (MapView.isOpen()) { if (!MapView.escape()) closeMap(); return; }
    if ($("#out .sheet")) navigate({ view: state.view, q: state.q });
  });

  $("#out").addEventListener("click", (e) => {
    const t = e.target;
    const act = t.closest("button[data-ckact]");
    if (act) { ckAct(act); return; }
    const onMap = t.closest("[data-ckmap]");
    if (onMap) { navigate({ view: "places", place: placeOfMap(onMap.dataset.ckmap), map: onMap.dataset.ckmap, mark: onMap.dataset.mark }); return; }
    const boss = t.closest("[data-cktr]");
    if (boss) {  // the trainer's entry for the mode the player has chosen (difficulty is the Trainers tab's own setting)
      const ns = boss.dataset.cktr.split(",").map(Number);
      const hit = entries.findIndex((x, n) => ns.includes(x.n) && entryInMode(n));
      if (hit >= 0) navigate({ view: "trainers", trainer: hit });
      return;
    }
    const stage = t.closest(".ck-stage > summary");
    if (stage && t.closest("[data-place]")) e.preventDefault();  // the Location button opens the place, not the section
    else if (stage && !state.q) {  // remember which sections are folded (a search opens them all without saving that)
      const d = stage.parentElement;
      setTimeout(() => { ck.closed[d.dataset.ckstage] = !d.open; ckSave(); });
      return;
    }
    const go = t.closest("[data-goto]");
    if (go) { navigate({ view: go.dataset.goto, q: state.q }); return; }
    const secret = t.closest(".reveal");
    if (secret) { secret.classList.toggle("shown"); secret.title = secret.classList.contains("shown") ? "Click to hide" : "Click to reveal"; return; }
    if (t.closest("[data-collapse], [data-sheet-close]") || t.closest(".sheet .mon > summary")) {
      e.preventDefault(); navigate({ view: state.view, q: state.q }); return;
    }
    const card = t.closest(".list.grid .mon > summary");
    if (card) { e.preventDefault(); navigate({ view: "dex", q: state.q, open: +card.parentElement.dataset.i }); return; }
    // In its own list, an entry toggles open in place; from inside a card it opens in its own view
    const inList = !t.closest(".expanded");
    const itm = t.closest("[data-item]");
    if (itm) {
      e.preventDefault();
      const k = +itm.dataset.item;
      if (state.view === "items" && inList) navigate({ view: "items", q: state.q, item: state.item === k ? null : k });
      else openItem(k);
      return;
    }
    const mv = t.closest("[data-move]");
    if (mv) {
      e.preventDefault();
      const k = mv.dataset.move;
      if ((state.view === "moves" || state.view === "tutors") && inList) navigate({ view: state.view, q: state.q, move: state.move === k ? null : k });
      else openMove(k);
      return;
    }
    const ab = t.closest("[data-ability]");
    if (ab) {
      e.preventDefault();
      const name = ab.dataset.ability;
      if (state.view === "abilities" && inList) navigate({ view: "abilities", q: state.q, ability: state.ability === name ? null : name });
      else navigate({ view: "abilities", ability: name });
      return;
    }
    const tr = t.closest("[data-trainer]");
    if (tr && inList) {
      e.preventDefault();
      const n = +tr.dataset.trainer;
      navigate({ view: "trainers", q: state.q, trainer: state.trainer === n ? null : n });
      return;
    }
    const dc = t.closest("[data-doc]");
    if (dc && inList) {
      e.preventDefault();
      navigate({ view: "docs", q: state.q, doc: state.doc === dc.dataset.doc ? null : dc.dataset.doc });
      return;
    }
    const mb = t.closest("[data-map]");
    if (mb) { e.preventDefault(); navigate({ view: "places", q: state.q, place: mb.dataset.of, map: mb.dataset.map }); return; }
    const pl = t.closest("[data-place]");
    if (pl) {
      e.preventDefault();
      const name = pl.dataset.place;
      if (state.view === "places" && inList) navigate({ view: "places", q: state.q, place: state.place === name ? null : name });
      else openPlace(name);
      return;
    }
    const op = t.closest("[data-open]");
    if (op) { e.preventDefault(); if (+op.dataset.open !== state.open) openMon(+op.dataset.open); return; }
    const tab = t.closest("[data-tab]");
    if (tab) {
      const box = tab.closest("[data-tabs]");
      state.tab = tab.dataset.tab; state.tabFilter = "";
      box.outerHTML = tabsBlock(+box.dataset.tabs);
    }
  });
  $("#out").addEventListener("change", (e) => {
    const box = e.target;
    if (box.dataset.ckact) { ckAct(box); return; }
    if (!box.dataset.ck) return;
    if (box.checked) ck.done[box.dataset.ck] = Date.now(); else delete ck.done[box.dataset.ck];
    ckSave();
    box.closest(".ck").classList.toggle("done", box.checked);
    ckCounts();
  });
  $("#out").addEventListener("input", (e) => {
    if (!e.target.classList.contains("tabfilter")) return;
    const box = e.target.closest("[data-tabs]");
    state.tabFilter = e.target.value;
    box.querySelector(".panel").innerHTML = panel(+box.dataset.tabs);
  });
  new MutationObserver(cueSoon).observe($("#out"), { childList: true, subtree: true });
  cueSoon();

  $("#out").addEventListener("toggle", (e) => {
    const d = e.target;
    if (!d.classList || !d.classList.contains("mon")) return;
    const i = +d.dataset.i;
    if (d.open) {
      if (state.open !== null && state.open !== i) {
        const prev = document.querySelector(`.mon[data-i="${state.open}"]`);
        if (prev) { prev.open = false; const det = prev.querySelector(".detail"); if (det) det.remove(); }
      }
      state.open = i; state.tabFilter = "";
      if (!d.querySelector(".detail")) d.insertAdjacentHTML("beforeend", detail(i));
    } else if (state.open === i) {
      state.open = null;
    }
    remember();
  }, true);

  // Offline: on the website, offer the download and register the installable app; the saved file already works offline
  $("#offline-btn").addEventListener("click", () => {
    const help = $("#offline-help");
    help.hidden = !help.hidden;
    $("#offline-btn").setAttribute("aria-expanded", String(!help.hidden));
    syncConsoleHeight();
  });
  // The downloaded file takes the checklist ticks with it: they're written into the copy as #saved-checklist, ahead of
  // the scripts that read them. Anything going wrong falls back to the plain download.
  $("#dl").addEventListener("click", (ev) => {
    const a = ev.currentTarget;
    if (a.dataset.plain || !Object.keys(ck.done).length || !/^https?:$/.test(location.protocol)) return;
    ev.preventDefault();
    const plain = () => { a.dataset.plain = "1"; a.click(); delete a.dataset.plain; };
    fetch(a.getAttribute("href")).then((r) => (r.ok ? r.text() : Promise.reject())).then((html) => {
      const at = html.indexOf('<script type="application/json" id="map' + 'data">');
      if (at < 0) return plain();
      const saved = '<script type="application/json" id="saved-checklist">' + ckPayload().split("<").join("\\u003c") + "</" + "script>\n";
      ckFile(a.getAttribute("download"), "text/html", html.slice(0, at) + saved + html.slice(at));
    }).catch(plain);
  });
  if (/^https?:$/.test(location.protocol)) {
    document.head.insertAdjacentHTML("beforeend", '<link rel="manifest" href="manifest.webmanifest">');
    if ("serviceWorker" in navigator) { try { navigator.serviceWorker.register("sw.js").catch(() => {}); } catch (e) {} }
    // GitHub Pages' deploy sets Last-Modified, which the browser exposes as document.lastModified (the service worker's
    // cached copy keeps the header). With no header it reads as "now": show nothing rather than a made-up date.
    const mod = new Date(document.lastModified);
    if (!isNaN(mod) && Date.now() - mod > 60000)
      $("#updated").textContent = "Last updated: " + mod.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  } else {
    $("#offline-btn").hidden = true; $("#offline-note").hidden = false;  // the note takes the Download button's place
  }

  // Links: #rockruff, #move-crunch, #item-fire-stone, #place-route-2, #map-daimyn-city/item-2, #items … (older #ceaseless-edge style still works)
  function fromHash() {
    const h = decodeURIComponent(location.hash.slice(1));
    const views = { "": "dex", pokedex: "dex", moves: "moves", tutors: "tutors", abilities: "abilities", items: "items", trainers: "trainers", locations: "places", checklist: "check", docs: "docs" };
    Object.assign(state, { view: "dex", q: "", move: null, item: null, place: null, map: null, mark: null, doc: null, ability: null, trainer: null, open: null });
    if (h in views) state.view = views[h];
    else if (h.startsWith("trainer-")) { const n = parseInt(h.slice(8), 10); Object.assign(state, { view: "trainers", trainer: n >= 0 && n < entries.length ? n : null }); }
    else if (h.startsWith("move-")) { const k = moveKeys.find((x) => slug(moves[x].name) === h.slice(5)); Object.assign(state, k ? { view: "moves", move: k } : { view: "moves", q: h.slice(5).replace(/-/g, " ") }); }
    else if (h.startsWith("item-")) { const k = items.findIndex((it) => slug(it.name) === h.slice(5)); Object.assign(state, k >= 0 ? { view: "items", item: k } : { view: "items", q: h.slice(5).replace(/-/g, " ") }); }
    else if (h.startsWith("ability-")) { const a = abilities.find((x) => slug(x.name) === h.slice(8)); Object.assign(state, { view: "abilities", ability: a ? a.name : null }); }
    else if (h.startsWith("doc-")) { const t = docTopics.find((x) => slug(x.title) === h.slice(4)); Object.assign(state, { view: "docs", doc: t ? t.title : null }); }
    else if (h.startsWith("map-") && placeOfMap(h.slice(4).split("/")[0])) {  // #map-daimyn-city/item-2: one marker on that map
      const [m, mark] = h.slice(4).split("/");
      Object.assign(state, { view: "places", place: placeOfMap(m), map: m, mark: mark || null });
    }
    else if (h.startsWith("place-")) { const p = placeList.find((x) => slug(x.name) === h.slice(6)); Object.assign(state, { view: "places", place: p ? p.name : h.slice(6).replace(/-/g, " ") }); }
    else {
      const bySlug = mons.findIndex((_, i) => monSlug(i) === h);
      const text = norm(h);
      const byName = bySlug >= 0 ? bySlug : mons.findIndex((m) => m.s.includes(text));
      const mv = moveKeys.find((k) => moves[k].s.includes(text));
      if (byName >= 0 && !mv) Object.assign(state, { open: byName, q: mons[byName].name });
      else if (mv) Object.assign(state, { view: "moves", move: mv });
      else state.q = h.replace(/-/g, " ");
    }
    remember();
    render(true);
  }
  // The pop-up hides its native scrollbar and draws a thumb that floats over the content, so the pinned header runs edge to edge
  const syncSheetBar = (body) => {
    const bar = body.nextElementSibling, thumb = bar && bar.firstChild;
    if (!thumb) return;
    const { scrollHeight: sh, clientHeight: ch, scrollTop: st } = body, room = bar.clientHeight;
    bar.hidden = sh <= ch + 1;
    const h = Math.max(36, room * ch / sh);
    thumb.style.height = `${h}px`;
    thumb.style.transform = `translateY(${(room - h) * st / (sh - ch || 1)}px)`;
    bar.classList.add("live");
    clearTimeout(bar.fade);
    bar.fade = setTimeout(() => bar.classList.remove("live"), 900);
  };
  document.addEventListener("scroll", (e) => { if (e.target.classList && e.target.classList.contains("sheet-body")) syncSheetBar(e.target); }, true);
  new MutationObserver(() => { const b = $(".sheet-body"); if (b) requestAnimationFrame(() => syncSheetBar(b)); }).observe(document.body, { childList: true, subtree: true });
  fromHash();
})();

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
  const placeList = [...places.values()].sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));

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
  const state = { view: "dex", q: "", move: null, item: null, place: null, open: null, mode: "", type: "", tab: "level", tabFilter: "",
    doc: null, ability: null, trainer: null, diff: "std",
    layouts: { dex: "list", moves: "list", tutors: "list", abilities: "list", items: "grid", trainers: "list", places: "grid", docs: "list" } };  // list or cards, per view
  try {
    state.mode = localStorage.getItem("dex-mode") || "";
    state.diff = localStorage.getItem("dex-diff") || "std";
    Object.assign(state.layouts, JSON.parse(localStorage.getItem("dex-layouts") || "{}"));
  } catch (e) {}
  let depth = 0, top = 0;  // position in this page's history, and how far Forward can go

  const snapshot = () => ({ view: state.view, q: state.q, move: state.move, item: state.item, place: state.place, doc: state.doc, ability: state.ability, trainer: state.trainer, open: state.open });
  function hashFor(st) {
    if (st.view === "dex" && st.open !== null) return monSlug(st.open);
    if (st.move) return "move-" + slug(moves[st.move].name);
    if (st.item !== null) return "item-" + slug(items[st.item].name);
    if (st.place) return "place-" + slug(st.place);
    if (st.doc) return "doc-" + slug(st.doc);
    if (st.ability) return "ability-" + slug(st.ability);
    if (st.trainer !== null) return "trainer-" + trainerSlug(st.trainer);
    return { dex: "", moves: "moves", tutors: "tutors", abilities: "abilities", items: "items", trainers: "trainers", places: "locations", docs: "docs" }[st.view];
  }
  const queries = {};  // each tab keeps its own search text

  function navigate(change) {
    const next = Object.assign({ view: state.view, q: "", move: null, item: null, place: null, doc: null, ability: null, trainer: null, open: null }, change);
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

  // ---------------------------------------------------------------- small pieces
  const typeBadge = (t) => `<span class="type t-${t}">${t === "MYSTERY" ? "???" : t[0] + t.slice(1).toLowerCase()}</span>`;
  const sprite = (m, small) => `<span class="sp${small ? " sm" : ""}" aria-hidden="true"><i style="background-position:-${m.sp[0]}px -${m.sp[1]}px"></i></span>`;
  // Pokédex rows only: the shiny colours beside the normal sprite, so the two can be told apart
  const pics = (m) => `<span class="pics">${sprite(m)}${m.ss ? `<span class="shiny" title="Shiny"><span class="sp" aria-hidden="true"><i style="background-position:-${m.ss[0]}px -${m.ss[1]}px"></i></span></span>` : ""}</span>`;
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
  const inType = (m) => !state.type || m.types.includes(state.type);
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
      <summary title="Show details"><span class="dexline">${dexNo(m)}${modeBadge(m)}</span>${pics(m)}
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

  function locTable(rows) {
    return `<div class="moves"><table class="mv loc"><thead><tr><th>Location</th><th>Method</th><th class="c-num">Lv</th><th class="c-num">Rate</th><th class="hide-sm">Mode</th></tr></thead><tbody>${
      rows.map((l) => `<tr><td><button class="mvname" data-place="${esc(l.location)}">${esc(l.location)}</button>${l.sub ? `<div class="note">${esc(l.sub)}</div>` : ""}${
        l.variant ? `<div class="note">${esc(l.variant)}</div>` : ""}${l.notes ? `<div class="note">${esc(l.notes)}</div>` : ""}</td>
        <td class="meth">${esc(l.method)}</td><td class="n">${esc(l.levels || "—")}</td><td class="n">${esc(l.rate || "—")}</td>
        <td class="hide-sm">${modeTag(l.mode)}</td></tr>`).join("")}</tbody></table></div>`;
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
      <div class="cols">
        <section><h3>Base stats · ${bst(m)}</h3><div class="stats">${m.stats.map((v, n) =>
          `<span class="lab">${STAT_LABELS[n]}</span><span class="val">${v}</span><span class="bar"><span style="width:${Math.min(100, v / 2)}%;background:${statColor(v)}"></span></span>`).join("")}</div></section>
        <section><h3>Abilities</h3><div class="abilities">${m.abilities.map((a) => ab(a, false)).join("")}${m.hidden ? ab(m.hidden, true) : ""}</div></section>
        <section><h3>Profile</h3><dl class="facts">
          <dt>Gender</dt><dd>${genderText(m.gender)}</dd>
          <dt>Egg groups</dt><dd>${m.eggGroups.join(", ") || "—"}</dd>
          <dt>Catch rate</dt><dd>${m.catchRate}</dd>
          <dt>Growth</dt><dd>${esc(m.growth)}</dd>
          <dt>EV yield</dt><dd>${evs}</dd>
          ${m.held.length ? `<dt>Wild held items</dt><dd class="held">${m.held.map(([h, k]) => (k === null ? `<span>${esc(h)}</span>` : itemButton(k, h))).join("")}</dd>` : ""}
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
    const learners = mv.learners.filter(([i]) => inMode(mons[i]) && inType(mons[i]));
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
    mons.forEach((m, i) => m.evo.forEach(([to, how, ik, written]) => { if ((ik === k || norm(how).includes(itemKeys[k])) && inMode(mons[to])) evolves.push([i, to, how, written || it.name]); }));
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
    const groups = methods.map(([mt, l]) => [mt, l.map(([i, e]) =>
      [i, e, e.times ? Object.entries(e.times).map(([t, r]) => `${TIME_ICON[t]} ${r}`).join(" ") : e.rate])
      .sort((a, b) => pct(b[2]) - pct(a[2]))]);
    const re = placeRe(p.name);
    const found = [];
    // Chip hint is just the spot within the place ("Shady relic seller"); prices and notes are on the item's card
    const spot = (line) => line.replace(/\s*\([^)]*\)/g, "").replace(p.name, "").replace(/^[\s·-]+/, "");
    items.forEach((it, k) => { const line = it.where.find((w) => re.test(w.toLowerCase())); if (line) found.push([k, spot(line)]); });
    // Three parts, each set apart: the map and description, the encounters by method, the items found here
    const encounters = groups.length
      ? groups.map(([mt, l]) => `<div><h4>${esc(mt)} · ${l.length}</h4><div class="chips wild${
        l.some(([, e]) => e.times && Object.keys(e.times).length > 1) ? " two" : ""}">${l.map(([i, e, rate]) => monChip(i, [e.levels && `Lv ${e.levels}`, rate].filter(Boolean).join(" · "), e.sub, false, e.mode === "Both" ? ["Standard", "Divergent"] : [e.mode])).join("")}</div></div>`).join("")
      : `<p class="empty">No Pokémon match the current filters here.</p>`;
    const itemChips = found.map(([k, line]) =>
      `<button class="chip" data-item="${k}">${itemIcon(k)}<span class="ln">${esc(items[k].name)}</span>${line ? `<span class="hw">${esc(line)}</span>` : ""}</button>`).join("");
    return `<article class="loccard">${collapsible ? COLLAPSE : ""}<h2>${esc(p.name)}<small>${p.rows.length ? `${rows.length} encounter${rows.length === 1 ? "" : "s"}` : "No wild Pokémon"}</small></h2>
      <div class="placehead">${townMap(p.name)}${aboutPlace(p.name)}</div>
      ${p.rows.length ? `<section class="placesec"><h3>Encounters · ${rows.length}</h3><div class="learners">${encounters}</div></section>` : ""}
      ${found.length ? `<section class="placesec"><h3>Items · ${found.length}</h3><div class="chips">${itemChips}</div></section>` : ""}</article>`;
  }

  // ---------------------------------------------------------------- views
  const matchMoves = (q) => (q ? moveKeys.filter((k) => moves[k].s.some((x) => x.includes(q))) : moveKeys);
  const matchItems = (q) => items.map((_, k) => k).filter((k) => !q || itemKeys[k].includes(q)
    || (items[k].move && moves[items[k].move].s.includes(q)));
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
    const typeQ = TYPES.find((t) => norm(t) === q);  // "fire" lists every Fire type, as well as names containing it
    // "16" or "#016" is a dex number in the chosen mode (either on All), with the unnumbered forms listed after it
    const num = /^\d+$/.test(q) ? +q : 0;
    const hasNum = (m, i) => (state.mode ? [state.mode] : m.modes).some((mode) => m.modes.includes(mode) && Math.floor(order[mode][i]) === num);
    mons.forEach((m, i) => { if (inMode(m) && inType(m) && (num ? hasNum(m, i) : !q || m.s.some((s) => s.includes(q)) || (typeQ && m.types.includes(typeQ)))) list.push(i); });
    return list;
  }
  const matchTutors = (q) => DEX.tutors.filter((t) => (!q || moves[t.move].s.some((x) => x.includes(q)) || norm(t.where).includes(q) || words(t.note).includes(words(state.q)))
    && (!state.type || moves[t.move].type === state.type));
  const matchAbilities = (q) => abilities.filter((a, n) => (!q || abilityKeys[n].includes(q))
    && a.mons.some(([i]) => inMode(mons[i]) && inType(mons[i])));
  const matchDocs = (q) => docTopics.filter((t) => !q || norm(t.title).includes(q) || t.s.includes(words(state.q)));

  // Above every view: how many results the same search has in the other tabs, each a chip that goes there
  const ALSO = [["dex", (q) => matchMons(q).length, "Pokémon", "Pokémon"], ["moves", (q) => matchMoves(q).filter((k) => !state.type || moves[k].type === state.type).length, "move", "moves"],
    ["tutors", (q) => matchTutors(q).length, "tutor move", "tutor moves"], ["abilities", (q) => matchAbilities(q).length, "ability", "abilities"],
    ["items", (q) => matchItems(q).length, "item", "items"], ["trainers", (q) => matchTrainers(q).length, "trainer", "trainers"], ["places", (q) => matchPlaces(q).length, "location", "locations"], ["docs", (q) => matchDocs(q).length, "doc topic", "doc topics"]];
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
    const list = exactFirst(matchMoves(q), (k) => moves[k].s.includes(q)).filter((k) => !state.type || moves[k].type === state.type);
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
      : `<div class="listtable"><table class="mv"><thead><tr><th>Location</th><th class="hide-sm">Found by</th><th class="c-num">Pokémon</th></tr></thead><tbody>${list.map((p) =>
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
    const count = (a) => a.mons.filter(([i]) => inMode(mons[i]) && inType(mons[i])).length;
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
      ? chipsWithOpen(ts, (t) => `<button class="chip${isOpen(t) ? " on" : ""}" data-doc="${esc(t.title)}"><span class="ln" style="padding-left:10px">${esc(t.title)}</span></button>`, isOpen, docCard)
      : `<div class="listtable"><table class="mv"><tbody>${ts.map((t) => `<tr data-doc="${esc(t.title)}"${isOpen(t) ? ' class="on"' : ""}><td><span class="mvname">${esc(t.title)}</span></td></tr>${
          isOpen(t) ? expandRow(1, docCard(t)) : ""}`).join("")}</tbody></table></div>`}`).join("");
    return [html, `${list.length} topics`];
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
      it !== null && ["Item", trainerItem(it)],
      ab !== null && TEAMS.abilities[ab] && ["Ability", ability],
      hard && ["Nature", esc(natureText(nat))],
      ["IVs", `${xhard ? 31 : t.iv} in every stat`],
      xhard && ["EVs", evs.slice().sort().map((s) => `252 ${STAT_LABELS[s]}`).join(", ")],
    ].filter(Boolean);
    const moveBtn = (n) => {
      const k = TEAMS.moves[n], mv = moves[k];
      return `<button class="tmv" data-move="${k}" style="--c:${TYPE_COLOR[mv.type]}" title="${esc(mv.desc)}"><span class="cat" title="${CAT_NAME[mv.split]}">${CAT[mv.split]}</span><span>${esc(mv.name)}</span></button>`;
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
          const t = trainers[entries[e].n], sprites = teamOf(e).map(([i]) => sprite(mons[i], true)).join(""), lvLabel = lvText(e);
          return `<tr data-trainer="${e}"${e === open ? ' class="on"' : ""}><td><div class="trow">${trainerPic(t)}<span class="tn"><span class="tname"><span class="mvname">${esc(trainerTitle(t))}</span>${entryMode(e)}<span class="note tlv-inline">${lvLabel}</span></span>${
            t.note ? `<span class="note">${esc(t.note)}</span>` : ""}<span class="teamline tt-inline">${sprites}</span></span></div></td><td class="tteam"><span class="teamline">${sprites}</span></td>
            <td class="n lvcell tlvcol" title="${t.scaled ? SCALE_TIP : "Levels on the team"}">${t.scaled ? `<span class="note">Scaling, min</span> ${minLv(e)}` : lvRange(e)}</td></tr>${e === open ? expandRow(3, trainerCard(e)) : ""}`;
        }).join("")}</tbody></table></div>`}`).join("");
    return [html, `${list.length} trainers`];
  }

  const PLACEHOLDER = {
    dex: "Search Pokémon or dex # — e.g. Rockruff, 16, Mega, Galarian, Fire",
    moves: "Search moves or TMs — e.g. Ceaseless Edge, TM02",
    tutors: "Search tutor moves or towns — e.g. Draco Meteor, Ferrox Village",
    abilities: "Search abilities or what they do — e.g. Triage, Libero, weather",
    items: "Search items — e.g. Fire Stone, Berries",
    trainers: "Search trainers, places or their Pokémon — e.g. Raine, Hiker, Route 8, Rockruff",
    places: "Search places, or what's there — e.g. Route 2, Bidoof, Full Heal, Grass",
    docs: "Search the docs — e.g. Frostbite, Battle Frontier, shiny",
  };

  let shownView = null;
  function render(scroll) {
    const hadSheet = shownView === state.view && !!$("#out .sheet");
    shownView = state.view;
    const q = norm(state.q);
    const [html, count] = { dex: dexView, moves: movesView, tutors: tutorsView, abilities: abilitiesView, items: itemsView, trainers: trainersView, places: placesView, docs: docsView }[state.view](q);
    $("#out").innerHTML = alsoLine(q, state.view) + html;
    $("#count").textContent = count;
    $("#q").value = state.q;
    $("#q").placeholder = PLACEHOLDER[state.view];
    $("#clear").hidden = !$("#q").value;
    $("#back").disabled = depth <= 0;
    $("#fwd").disabled = depth >= top;
    $("#typepick").hidden = ["abilities", "items", "trainers", "places", "docs"].includes(state.view);  // these have no type
    $("#mode-seg").hidden = state.view === "docs";
    $("#diff-pick").hidden = state.view !== "trainers";
    document.querySelectorAll(".seg button[data-diff]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.diff === state.diff)));
    document.querySelectorAll("[data-viewtab]").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.viewtab === state.view)));
    document.querySelectorAll(".seg button[data-mode]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === state.mode)));
    document.querySelectorAll(".seg button[data-view]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === state.layouts[state.view])));
    $("#type-label").innerHTML = state.type ? typeBadge(state.type) : "All types";
    syncConsoleHeight();
    document.body.classList.toggle("sheet-open", !!$("#out .sheet"));
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
    timer = setTimeout(() => { Object.assign(state, { q: e.target.value, open: null, move: null, item: null, place: null, doc: null, ability: null, trainer: null }); queries[state.view] = state.q; remember(); render(); }, 120);
  });
  $("#clear").addEventListener("click", () => { Object.assign(state, { q: "", open: null, move: null, item: null, place: null, doc: null, ability: null, trainer: null }); queries[state.view] = ""; remember(); render(); $("#q").focus(); });
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

  // Type picker: a popover of type badges
  const menu = $("#type-menu");
  const drawTypeMenu = () => {
    menu.innerHTML = `<button class="all" data-type="" aria-pressed="${!state.type}">All types</button>` +
      TYPES.map((t) => `<button data-type="${t}" aria-pressed="${state.type === t}">${typeBadge(t)}</button>`).join("");
  };
  const closeMenu = () => { menu.hidden = true; $("#type-btn").setAttribute("aria-expanded", "false"); };
  $("#type-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    if (menu.hidden) { drawTypeMenu(); menu.hidden = false; $("#type-btn").setAttribute("aria-expanded", "true"); } else closeMenu();
  });
  menu.addEventListener("click", (e) => {
    const b = e.target.closest("[data-type]");
    if (!b) return;
    state.type = b.dataset.type;
    closeMenu();
    render();
  });
  document.addEventListener("click", (e) => { if (!menu.hidden && !e.target.closest("#typepick")) closeMenu(); });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if ($("#out .sheet")) navigate({ view: state.view, q: state.q }); else closeMenu();
  });

  $("#out").addEventListener("click", (e) => {
    const t = e.target;
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
  if (/^https?:$/.test(location.protocol)) {
    document.head.insertAdjacentHTML("beforeend", '<link rel="manifest" href="manifest.webmanifest">');
    if ("serviceWorker" in navigator) { try { navigator.serviceWorker.register("sw.js").catch(() => {}); } catch (e) {} }
  } else {
    $("#offline-web").hidden = true; $("#offline-web2").hidden = true; $("#offline-file").hidden = false;
  }

  // Links: #rockruff, #move-crunch, #item-fire-stone, #place-route-2, #items … (older #ceaseless-edge style still works)
  function fromHash() {
    const h = decodeURIComponent(location.hash.slice(1));
    const views = { "": "dex", pokedex: "dex", moves: "moves", tutors: "tutors", abilities: "abilities", items: "items", trainers: "trainers", locations: "places", docs: "docs" };
    Object.assign(state, { view: "dex", q: "", move: null, item: null, place: null, doc: null, ability: null, trainer: null, open: null });
    if (h in views) state.view = views[h];
    else if (h.startsWith("trainer-")) { const n = parseInt(h.slice(8), 10); Object.assign(state, { view: "trainers", trainer: n >= 0 && n < entries.length ? n : null }); }
    else if (h.startsWith("move-")) { const k = moveKeys.find((x) => slug(moves[x].name) === h.slice(5)); Object.assign(state, k ? { view: "moves", move: k } : { view: "moves", q: h.slice(5).replace(/-/g, " ") }); }
    else if (h.startsWith("item-")) { const k = items.findIndex((it) => slug(it.name) === h.slice(5)); Object.assign(state, k >= 0 ? { view: "items", item: k } : { view: "items", q: h.slice(5).replace(/-/g, " ") }); }
    else if (h.startsWith("ability-")) { const a = abilities.find((x) => slug(x.name) === h.slice(8)); Object.assign(state, { view: "abilities", ability: a ? a.name : null }); }
    else if (h.startsWith("doc-")) { const t = docTopics.find((x) => slug(x.title) === h.slice(4)); Object.assign(state, { view: "docs", doc: t ? t.title : null }); }
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

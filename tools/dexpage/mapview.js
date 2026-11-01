// Interactive place maps (maps/export.py): a full-screen layer over the companion, opened from a place card's
// "View Interactive Map" button. Warps, markers and ways out are buttons laid over each floor's picture; pointing at
// one (or tapping it) fills the card at the bottom. The pictures are parsed from #mapdata the first time a map opens.
const MapView = (() => {
  const KINDS = {
    item:   { label: "Item ball",          shape: "square" },
    hidden: { label: "Hidden item",        shape: "diamond" },
    npc:    { label: "Person or event",    shape: "hex" },
    wild:   { label: "Pokémon encounter",  shape: "star" },
    statue: { label: "Sand statue",        shape: "pent" },
  };
  const POLY = {
    square: "2,2 20,2 20,20 2,20",
    diamond: "11,0 22,11 11,22 0,11",
    hex: "11,0 21,5.5 21,16.5 11,22 1,16.5 1,5.5",
    star: "11,0 14,7.5 22,8 16,13.5 18,22 11,17.5 4,22 6,13.5 0,8 8,7.5",
    pent: "11,0 22,8 18,22 4,22 0,8",
  };
  const shape = (k) => `<svg viewBox="0 0 22 22" aria-hidden="true"><polygon points="${POLY[KINDS[k].shape]}" fill="var(--k-${k})" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>`;
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const touch = matchMedia("(hover: none)").matches;
  const smooth = () => (matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth");
  const HELP = ["Click or tap a warp to see where it leads.", "Click or tap a marker in the map to see what it is.",
                "Click or tap a marker in the key to highlight it in the map."];

  let data = null, bySlug = null;  // parsed on first open
  let root, place = null, sel = null, zoom = 1, opts = {};
  const $ = (id) => document.getElementById("mv-" + id);

  function build() {
    root = document.createElement("div");
    root.id = "mapview";
    root.hidden = true;
    root.setAttribute("role", "region");
    root.setAttribute("aria-labelledby", "mv-title");
    root.innerHTML = `<div class="mv-bar">
        <button class="mv-close" id="mv-close" type="button"><span aria-hidden="true">←</span> Back to place details</button>
        <div class="seg" role="group" aria-label="Map size"><button id="mv-z1" type="button" aria-pressed="true">Fit</button><button id="mv-z2" type="button" aria-pressed="false">2×</button></div>
      </div>
      <div class="mv-page">
        <div class="mv-main"><h2 id="mv-title"></h2><p class="mv-note" id="mv-note" hidden></p>
          <p class="mv-help">${HELP.join("<br>")}${touch ? "<br>Use <b>2×</b> to enlarge the maps, then scroll sideways." : ""}</p>
          <div class="mv-maps" id="mv-maps"></div></div>
        <aside class="mv-side" id="mv-side"></aside>
      </div>
      <div class="mv-card" id="mv-card" hidden role="status" aria-live="polite">
        <p class="what" id="mv-cwhat"></p><p class="text" id="mv-ctext"></p><div class="acts" id="mv-cacts"></div>
        <button class="x" id="mv-cx" type="button" aria-label="Close">×</button>
      </div>`;
    document.body.append(root);
    try { zoom = +localStorage.getItem("mapzoom") || 1; } catch (e) {}
    $("z1").onclick = () => setZoom(1);
    $("z2").onclick = () => setZoom(2);
    $("close").onclick = () => opts.onClose();
    $("cx").onclick = unpin;
    const target = (e) => e.target.closest(".warp, .mk, .door, .edge, .mv-list button");
    root.addEventListener("click", (e) => {
      const t = target(e);
      if (t && t.closest(".mv-list")) { jump(`.mv-maps [data-m="${t.dataset.m}"]`); return; }  // a key row goes straight to its marker
      if (t && t.matches(".warp")) { goWarp(t); return; }
      if (t && t.matches(".door, .edge")) {  // a way out opens that place's map
        const x = t.dataset.x !== undefined ? place.exits[t.dataset.x] : place.edges[t.dataset.e];
        if (x.slug && bySlug[x.slug]) { opts.onLink(x.slug); return; }
      }
      if (t && !t.closest(".mv-key")) { show(t, true); return; }
      if (!e.target.closest(".mv-card, .mv-bar")) unpin();
    });
    if (!touch) {
      root.addEventListener("mouseover", (e) => { const t = target(e); if (t && !t.closest(".mv-key")) show(t, false); });
      root.addEventListener("mouseout", (e) => {
        const t = target(e);
        if (!t || t.contains(e.relatedTarget)) return;
        if (sel && root.contains(sel)) show(sel, true); else unpin();
      });
    }
    addEventListener("resize", () => !root.hidden && requestAnimationFrame(drawWire));
    $("maps").addEventListener("scroll", () => requestAnimationFrame(drawWire));
  }

  function setZoom(z) {
    zoom = z;
    $("z1").setAttribute("aria-pressed", z === 1); $("z2").setAttribute("aria-pressed", z === 2);
    $("maps").classList.toggle("zoom2", z === 2);
    root.querySelectorAll(".mv-floor").forEach((f) => (f.style.width = f.dataset.w * z + "px"));
    try { localStorage.setItem("mapzoom", z); } catch (e) {}
    requestAnimationFrame(drawWire);
  }

  function render(p) {
    place = p;
    sel = null;
    $("card").hidden = true;
    $("title").textContent = p.name;
    $("note").textContent = p.note || "";
    $("note").hidden = !p.note;
    const maps = $("maps");
    maps.innerHTML = '<svg class="mv-wire" id="mv-wire"></svg>';
    p.floors.forEach((f, i) => {
      const fig = document.createElement("figure");
      fig.className = "mv-floor";
      fig.dataset.w = f.w;
      fig.style.width = f.w * zoom + "px";
      const cap = p.floors.length > 1 || f.name !== p.name ? `<figcaption>${esc(f.name)}</figcaption>` : "";
      fig.innerHTML = `${cap}<div class="mv-map" data-f="${i}"><img src="${f.img}" width="${f.w}" height="${f.h}" alt="${esc(f.name)} map"></div>`;
      maps.append(fig);
    });
    const mapEl = (i) => maps.querySelector(`.mv-map[data-f="${i}"]`);
    const at = (el, f, x, y) => { const F = p.floors[f]; el.style.left = (x / F.w * 100) + "%"; el.style.top = (y / F.h * 100) + "%"; mapEl(f).append(el); };

    p.warps.forEach((ends, w) => ends.forEach((e, j) => {
      const b = document.createElement("button");
      b.className = "warp"; b.type = "button";
      b.dataset.w = w; b.dataset.j = j;
      b.textContent = e.dir === "up" ? "↑" : e.dir === "down" ? "↓" : "→";
      b.setAttribute("aria-label", warpText(e).text);
      at(b, e.f, e.x, e.y);
    }));
    p.exits.forEach((e, i) => {
      const b = document.createElement("button");
      b.className = "door"; b.type = "button"; b.dataset.x = i;
      b.textContent = e.to;
      at(b, e.f, e.x, e.y);
      const r = e.x / p.floors[e.f].w;  // near a side, the label hangs inward so it isn't cut off
      if (r < .2) b.style.transform = "translate(-14px, -50%)";
      if (r > .8) b.style.transform = "translate(calc(-100% + 14px), -50%)";
    });
    p.edges.forEach((e, i) => {
      const b = document.createElement("button");
      b.className = "edge " + e.dir; b.type = "button"; b.dataset.e = i;
      b.textContent = { up: "↑ ", down: "↓ ", left: "← ", right: "→ " }[e.dir] + e.to;
      const [x0, y0, x1, y1] = e.rect;
      const pos = { up: [(x0 + x1) / 2, y0], down: [(x0 + x1) / 2, y1], left: [x0, (y0 + y1) / 2], right: [x1, (y0 + y1) / 2] }[e.dir];
      at(b, e.f, ...pos);
    });
    p.markers.forEach((m, i) => {
      const b = document.createElement("button");
      b.className = "mk k-" + m.k; b.type = "button"; b.dataset.m = i;
      b.setAttribute("aria-label", `${m.n}: ${m.t}`);
      const tags = (m.pg ? '<span class="tag">PG</span>' : "") + (m.sd ? '<span class="tag">S/D</span>' : "");
      b.innerHTML = shape(m.k) + `<span class="n">${m.n}</span>` + (tags ? `<span class="tags">${tags}</span>` : "");
      at(b, m.f, m.x, m.y);
    });
    side(p);
    setZoom(zoom);
  }

  function side(p) {
    const kinds = new Set(p.markers.map((m) => m.k));
    let h = "<h3>Key</h3><ul class='mv-key'>";
    if (p.warps.length) h += `<li><span class="sw"><span class="warp" style="width:16px;height:16px">↑</span></span>Warp: ↑ ↓ stairs, → another room</li>`;
    if (p.exits.length) h += `<li><span class="sw"><span class="door" style="padding:2px 3px 2px 4px;font-size:0">&nbsp;</span></span>Way out to another place</li>`;
    for (const k of Object.keys(KINDS)) if (kinds.has(k)) h += `<li><span class="sw">${shape(k)}</span>${KINDS[k].label}</li>`;
    if (p.markers.some((m) => m.pg)) h += `<li><span class="sw"><span class="tag">PG</span></span>Only there after beating the Champion</li>`;
    if (p.markers.some((m) => m.sd)) h += `<li><span class="sw"><span class="tag">S/D</span></span>Different in Standard and Divergent mode</li>`;
    h += "</ul>";
    if (p.markers.length) {
      h += "<h3>On this map</h3>";
      const order = Object.keys(KINDS);
      p.floors.forEach((f, fi) => {
        const ms = p.markers.map((m, i) => [m, i]).filter(([m]) => m.f === fi)
          .sort(([a], [b]) => order.indexOf(a.k) - order.indexOf(b.k) || a.n - b.n);
        if (!ms.length) return;
        if (p.floors.length > 1) h += `<div class="mv-floorhead">${esc(f.name)}</div>`;
        h += "<ul class='mv-list'>" + ms.map(([m, i]) => `<li><button type="button" data-m="${i}">${shape(m.k)}<span class="num">${m.n}</span><span>${
          m.pg ? '<span class="pg">Postgame:</span> ' : ""}${esc(m.t)}${m.sd ? '<span class="tag">S/D</span>' : ""}</span></button></li>`).join("") + "</ul>";
      });
    } else h += `<h3>On this map</h3><p class="mv-none">No items or special people here.</p>`;
    $("side").innerHTML = h;
  }

  function warpText(e) {
    if (!e.to) return { what: "Warp", text: "Where you arrive from a scripted warp" };
    const kind = e.dir === "up" ? "Up to " : e.dir === "down" ? "Down to " : "Leads to ";
    return { what: "Warp", text: kind + e.to + (e.same ? ", landing on the same spot" : "") };
  }

  // selection: hover previews, click/tap pins
  function describe(t) {
    const p = place, d = t.dataset;
    if (d.w !== undefined) {
      const ends = p.warps[d.w], e = ends[d.j];
      const mates = ends.filter((_, j) => j != d.j);
      return { ...warpText(e), mates: mates.map((_, k) => `.warp[data-w="${d.w}"][data-j="${ends.indexOf(mates[k])}"]`) };
    }
    if (d.x !== undefined || d.e !== undefined) {
      const e = d.x !== undefined ? p.exits[d.x] : p.edges[d.e];
      return { what: "Way out", text: "To " + e.to };
    }
    const m = p.markers[d.m];
    return { what: `${m.n} · ${KINDS[m.k].label}${p.floors.length > 1 ? " · " + p.floors[m.f].name : ""}`,
      text: (m.pg ? "Postgame: " : "") + m.t, mark: d.m };
  }

  function show(t, pinned) {
    clearMarks();
    const info = describe(t);
    sel = pinned ? t : sel;
    t.classList.add("on");
    (info.mates || []).forEach((s) => root.querySelectorAll(s).forEach((el) => el.classList.add("mate")));
    if (info.mark !== undefined) root.querySelectorAll(`[data-m="${info.mark}"]`).forEach((el) => el.classList.add("on"));
    $("cwhat").textContent = info.what;
    $("ctext").textContent = info.text;
    $("cacts").innerHTML = "";
    $("card").hidden = false;
    drawWire();
  }

  function clearMarks() {
    root.querySelectorAll(".on, .mate").forEach((el) => el.classList.remove("on", "mate"));
  }

  function unpin() { sel = null; clearMarks(); $("card").hidden = true; drawWire(); }

  function ping(el) {
    el.scrollIntoView({ block: "center", inline: "center", behavior: smooth() });
    el.classList.remove("ping"); void el.offsetWidth; el.classList.add("ping");
  }

  function jump(selector) {
    const el = root.querySelector(selector);
    if (!el) return;
    ping(el);
    show(el, true);
  }

  // a warp takes you to where it lands: scroll there, keep the warp you used selected so both ends stay lit
  function goWarp(t) {
    const ends = place.warps[t.dataset.w];
    const j = ends.findIndex((_, k) => k != t.dataset.j);
    show(t, true);
    if (j >= 0) ping(root.querySelector(`.warp[data-w="${t.dataset.w}"][data-j="${j}"]`));
  }

  function drawWire() {
    const svg = $("wire");
    if (!svg) return;
    const maps = $("maps"), box = maps.getBoundingClientRect();
    svg.setAttribute("width", maps.scrollWidth); svg.setAttribute("height", maps.scrollHeight);
    const on = maps.querySelector(".warp.on");
    if (!on) { svg.innerHTML = ""; return; }
    const c = (el) => { const r = el.getBoundingClientRect(); return [r.left + r.width / 2 - box.left + maps.scrollLeft, r.top + r.height / 2 - box.top + maps.scrollTop]; };
    const [ax, ay] = c(on);
    // a line that would cross a third map reads as leading there: those ends just light up instead
    const others = (m) => [...maps.querySelectorAll(".mv-map")].filter((el) => !el.contains(on) && !el.contains(m)).map((el) => {
      const r = el.getBoundingClientRect();
      return [r.left - box.left + maps.scrollLeft, r.top - box.top + maps.scrollTop, r.width, r.height];
    });
    const crosses = (bx, by, rects) => rects.some(([x, y, w, h]) => {
      for (let t = 0; t <= 1; t += 0.01) {
        const px = ax + (bx - ax) * t, py = ay + (by - ay) * t;
        if (px > x && px < x + w && py > y && py < y + h) return true;
      }
      return false;
    });
    svg.innerHTML = [...maps.querySelectorAll(".warp.mate")].map((m) => {
      const [bx, by] = c(m);
      if (crosses(bx, by, others(m))) return "";
      return `<line x1="${ax}" y1="${ay}" x2="${bx}" y2="${by}" stroke="#fff" stroke-width="7" stroke-linecap="round"/>` +
             `<line x1="${ax}" y1="${ay}" x2="${bx}" y2="${by}" stroke="#111" stroke-width="3" stroke-linecap="round" stroke-dasharray="10 6"/>`;
    }).join("");
  }

  function load() {
    if (!data) {
      data = JSON.parse(document.getElementById("mapdata").textContent);
      bySlug = Object.fromEntries(data.map((p) => [p.slug, p]));
    }
  }

  return {
    // onLink(slug): a way out was clicked; onClose(): the Back button. The companion turns both into history steps.
    init(o) { opts = o; },
    open(slug) {
      load();
      const p = bySlug[slug];
      if (!p) return false;
      if (!root) build();
      if (p !== place) { render(p); root.scrollTop = 0; }
      root.hidden = false;
      document.body.classList.add("map-open");
      requestAnimationFrame(drawWire);
      return true;
    },
    close() {
      if (!root || root.hidden) return;
      root.hidden = true;
      unpin();
      document.body.classList.remove("map-open");
    },
    isOpen: () => !!root && !root.hidden,
    // Escape: first drop the selected marker, then close the map
    escape() { if ($("card") && !$("card").hidden) { unpin(); return true; } return false; },
  };
})();

"""Every PSS place as interactive-map data: each floor's picture (tiles and sprites, as a lossless WebP data URI)
and the markers, warps and ways out drawn over it in the page (app.js mapView).

Rendering every map takes a few minutes, so place_maps() keeps the result in .cache/ and only redraws when the
ROM, CFRU's scripts, the PSS map list or this package changes.

    python -m tools.dexpage.maps.export [place ...]    # print what each place gets (no cache)"""

import base64
import hashlib
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

from ..paths import Paths
from . import curation as C
from . import rom_maps

CACHE = Path(__file__).with_name(".cache")
GROUPS = ["Dungeons & landmarks", "Towns & cities", "Routes"]


def slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()


def category(M, place):
    if place in C.CATEGORY:
        return C.CATEGORY[place]
    if place in M.DUNGEONS or place in ("Daimyn Factory", "Ultra Space", "Secret Trail", "Ascension Tower",
                                        "Battle Frontier", "Seppire Cove", "Scalding Spa"):
        return "Dungeons & landmarks"
    return "Routes" if place.startswith("Route") else "Towns & cities"


def warp_labels(M, order, keyset):
    """A warp and the warp it lands on share a pair id (doorways two tiles wide share one)."""
    label, n = {}, 0
    for k in order:
        for i, w in enumerate(M.warps_of(k)):
            if (k, i) in label or w["to"] not in keyset:
                continue
            dest = (w["to"], w["warp"])
            pid = label.get(dest) or next((label[(k, j)] for j, v in enumerate(M.warps_of(k)) if (k, j) in label
                                           and v["to"] == w["to"] and abs(v["x"] - w["x"]) + abs(v["y"] - w["y"]) == 1), None)
            if pid is None:
                pid = n
                n += 1
                label[dest] = pid
            label[(k, i)] = pid
    return label


def webp_uri(img):
    buf = io.BytesIO()
    img.save(buf, "WEBP", lossless=True, quality=100, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def export(M, place, keys, maps, base, objs, groups):
    order = M.floor_order(keys)
    keyset = set(order)
    fnames = M.floor_names(place, order, maps)
    order = M.sort_floors(order, fnames)
    place_of = lambda k: base.get(k, maps.get(k, ("?",))[0])
    label = warp_labels(M, order, keyset)

    markers, exits, edges = [], [], []
    spots = defaultdict(list)
    imgs = {}
    for k in order:
        img, w, h, _ = M.render(*k)
        img = img.convert("RGBA")
        if place == "Rubarr Desert" and k == (1, 3):  # the pits the statues fill, drawn onto B2F
            over = Image.new("RGBA", img.size)
            M.draw_rubarr_pits(ImageDraw.Draw(over))
            img.alpha_composite(over)
        obs = objs.classify(k)
        for ob in sorted(obs, key=lambda o: o["y"]):  # sprites lower on the map draw over the ones above
            sp = M.sprite(ob["gfx"], ob["move"]) if "gfx" in ob else None
            if sp:
                sx, sy = ob["x"] * 16 + 8 - sp.width // 2, ob["y"] * 16 + 16 - sp.height
                img.alpha_composite(sp, (max(sx, 0), max(sy, 0)))
        for ob in obs:
            if ob["kind"] in ("statue", "scenery", "hm"):
                continue
            if ob["kind"] == "npc" and (ob.get("label") in ("EventScript_PokemonCenter_Main", "EventScript_Pokemart")
                                        or "mart" in fnames[k].lower()):
                continue  # Collin: Pokémon Centers and Poké Marts don't need marking
            markers.append({"f": k, "x": ob.get("mx", ob["x"]) * 16 + 8, "y": ob.get("my", ob["y"]) * 16 + 8,
                            "k": ob["kind"], "t": ob["text"], "pg": bool(ob.get("postgame")), "sd": bool(ob.get("modes")), **({"tf": ob["full"]} if ob.get("full") else {})})
        if place == "Rubarr Desert" and k == (1, 123):
            for s in M.rubarr()["statues"]:
                what = ("adds one level to the big pit on Caverns B2F (3 needed)" if s["addsLevel"]
                        else f"fills pit {s['n']} on Caverns B2F with sand")
                markers.append({"f": k, "x": s["x"] * 16 + 8, "y": s["y"] * 16 + 8, "k": "statue", "n": s["n"],
                                "t": f"Sand statue {s['n']}: moving it {what}", "pg": False, "sd": False})
        doors = []  # (kind, value, [tiles]); neighbouring tiles that do the same thing become one doorway
        for i, wp in enumerate(M.warps_of(k)):
            if (k, i) in label:
                kind, value = "warp", label[(k, i)]
            elif wp["to"] not in maps:
                continue  # into a FireRed leftover map (scripted or "previous map" warps)
            else:
                kind, value = "exit", place_of(wp["to"])
                if (place, value) in C.NO_EXIT:
                    continue
            near = next((b for b in doors if b[:2] == (kind, value)
                         and any(abs(x - wp["x"]) + abs(y - wp["y"]) == 1 for x, y in b[2])), None)
            if near:
                near[2].append((wp["x"], wp["y"]))
            else:
                doors.append((kind, value, [(wp["x"], wp["y"])]))
        for kind, value, tiles in doors:
            x = sum(t[0] for t in tiles) / len(tiles) * 16 + 8
            y = sum(t[1] for t in tiles) / len(tiles) * 16 + 8
            if kind == "warp":
                spots[value].append((k, x, y))
            else:
                exits.append({"f": k, "x": x, "y": y, "to": value})
        for cn in M.connections(k):
            if cn["dir"] not in M.DIRS or cn["to"] not in maps or cn["to"] in keyset:
                continue  # an edge into a map of this place is stitched instead
            edges.append({"f": k, "dir": M.DIRS[cn["dir"]], "to": place_of(cn["to"]), "rect": (0, 0, w * 16, h * 16)})
        imgs[k] = img

    order, fnames, imgs, _, spots, shift = M.stitch(place, order, fnames, imgs, [], spots)
    for item in markers + exits + edges:  # follow each map into the stitched picture it became part of
        if item["f"] in shift:
            head, dx, dy = shift[item["f"]]
            item["f"] = head
            if "rect" in item:
                x0, y0, x1, y1 = item["rect"]
                item["rect"] = (x0 + dx, y0 + dy, x1 + dx, y1 + dy)
            else:
                item["x"] += dx
                item["y"] += dy
    index = {k: i for i, k in enumerate(order)}
    known = {p: slug(p) for p in groups}
    floors = [{"name": fnames[k], "img": webp_uri(imgs[k]), "w": imgs[k].width, "h": imgs[k].height} for k in order]

    warps = []
    for ends in spots.values():
        out = []
        for k, x, y in ends:
            dest = next((e[0] for e in ends if e[0] != k), None)
            here, there = (M.floor_rank(fnames[k]), M.floor_rank(fnames[dest])) if dest else (None, None)
            same = dest is not None and len(ends) == 2 and \
                abs((x - next(e for e in ends if e[0] == dest)[1])) <= 24 and \
                abs((y - next(e for e in ends if e[0] == dest)[2])) <= 24
            out.append({"f": index[k], "x": x, "y": y, "to": fnames[dest] if dest else None,
                        "dir": "" if None in (here, there) or here == there else ("up" if there > here else "down"),
                        "same": same})
        warps.append(out)

    count = defaultdict(int)  # each kind of marker counts on its own (items 1-4, people 1-4), floor by floor
    markers.sort(key=lambda m: index[m["f"]])
    for m in markers:
        count[m["k"]] += 1
        m.setdefault("n", count[m["k"]])
        m["f"] = index[m["f"]]
    for e in exits + edges:
        e["f"] = index[e["f"]]
        e["slug"] = known.get(e["to"])
    return {"name": place, "slug": slug(place), "group": category(M, place), "note": C.PLACE_NOTES.get(place, ""),
            "floors": floors, "markers": markers, "warps": warps, "exits": exits, "edges": edges}


def export_all(paths, only=()):
    rom_maps.init(paths)
    from . import places as M  # reads the ROM rom_maps just loaded
    maps, _ = M.valid_maps()
    M.VALID.update(maps)
    groups, base = M.place_groups(maps)
    objs = M.Objects()
    return [export(M, place, groups[place], maps, base, objs, groups) for place in only or groups]


def _cache_key(paths):
    """Everything the maps are drawn from: the ROM, CFRU's symbols and scripts, the PSS map list, DPE's TM names
    and this package's code."""
    h = hashlib.sha256()
    pss = paths.dpe.parent / "PokemonShootingStars/maps"
    files = [paths.rom, paths.cfru / "offsets.ini", *sorted((paths.cfru / "assembly/overworld_scripts").rglob("*.s")),
             *sorted(Path(__file__).parent.glob("*.py"))]
    for f in files:
        h.update(f.read_bytes())
    for f in sorted(pss.rglob("*")) + sorted((paths.dpe / "src/tm_compatibility").iterdir()):
        h.update(f.name.encode())
    return h.hexdigest()[:16]


def place_maps(paths):
    """export_all(), from .cache/ when nothing it reads has changed."""
    key = _cache_key(paths)
    hit = CACHE / f"maps-{key}.json"
    if hit.exists():
        return json.loads(hit.read_text(encoding="utf-8"))
    print("Drawing the interactive maps (a few minutes; cached after this)", file=sys.stderr)
    places = export_all(paths)
    CACHE.mkdir(exist_ok=True)
    for old in CACHE.glob("maps-*.json"):
        old.unlink()
    hit.write_text(json.dumps(places, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return places


if __name__ == "__main__":
    for p in export_all(Paths.default(), sys.argv[1:]):
        print(f"{p['name']} ({p['group']}): {len(p['floors'])} floors, {len(p['markers'])} markers, {len(p['warps'])} warps")
        for m in p["markers"]:
            print(f"   {m['k']} {m['n']} {p['floors'][m['f']]['name']}: {m['t']}")

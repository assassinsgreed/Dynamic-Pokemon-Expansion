"""Checklist tab (proof of concept): what a player can do for 100% completion, in playthrough order.

Entries come from the interactive maps' markers (items, hidden items, people and events, Pokémon encounters) plus
hand-written story beats; checklist_data.py says the order and corrects the rest. What needs an HM comes from the
page's own item data ("Route 9 (Requires Cut)", a TM's Requires column), and the badge each HM needs outside battle
from CFRU's gFieldMoveBadgeRequirements.

    python -m tools.dexpage.checklist      # prints every entry with its id, and the common items left out
"""

import fnmatch
import re
import unicodedata

from . import checklist_data as H
from .paths import Paths

FIELD_MOVES = {"CUT": "Cut", "ROCK_SMASH": "Rock Smash", "FLY": "Fly", "SURF": "Surf", "STRENGTH": "Strength",
               "ROCK_CLIMB": "Rock Climb"}
MART_STOCK = re.compile(r"Poké Marts( \(after \d+ badges?\))?")
# People the maps mark who are a service, not something to finish
SERVICE = re.compile(r"(: shop|heals your team|: move tutor)$")


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def hm_badges(paths: Paths) -> dict[str, int]:
    """{"Cut": 2, "Rock Smash": 3, ...}: the badge each field move needs, from CFRU (the non-Unbound table)."""
    text = (paths.cfru / "src" / "party_menu.c").read_text(encoding="utf-8", errors="replace")
    block = re.search(r"gFieldMoveBadgeRequirements\[FIELD_MOVE_COUNT\]\s*=\s*\{(.*?)\};", text, re.S).group(1)
    out = {FIELD_MOVES[m]: int(n) for m, n in re.findall(r"\[FIELD_MOVE_(\w+)\]\s*=\s*(\d+)", block)
           if m in FIELD_MOVES and int(n)}
    if "Cut" not in out:
        raise ValueError("gFieldMoveBadgeRequirements: no badge found for Cut")
    return out


def _place_re(place: str) -> re.Pattern:
    return re.compile(r"(^|[^a-z0-9])" + re.escape(place.lower()) + r"($|[^a-z0-9])")


def _hms_in(text: str, badges: dict[str, int]) -> set[str]:
    return {hm for hm in badges if re.search(r"\b" + hm.lower() + r"\b", text.lower())}


class Needs:
    """Which HMs an item pickup at a place needs, as the page's item data records it."""

    def __init__(self, page: dict, badges: dict[str, int]):
        self.badges = badges
        self.items = {it["name"]: it for it in page["items"]}
        self.tms = {m["tm"]["label"]: m["tm"] for m in page["moves"].values() if m.get("tm")}

    def names(self, text: str) -> list[str]:
        """'Garchompite (Aerodactite in Divergent)' → both names; 'TM12 Taunt' → itself."""
        m = re.fullmatch(r"(.+?) \((.+?) in Divergent\)", text)
        return [m.group(1), m.group(2)] if m else [text]

    def of(self, text: str, place: str) -> set[str]:
        here, out = _place_re(place), set()
        for name in self.names(text):
            tm = self.tms.get(name.split(" ")[0])
            if tm and any(here.search(w.lower()) for w in tm["where"]):
                out |= _hms_in(tm.get("requires") or "", self.badges)
            for line in self.items.get(name, {}).get("where", []):
                if here.search(line.lower()):
                    for note in re.findall(r"\(([^)]*)\)", line):
                        if re.search(r"\b(need|needs|requires?)\b", note, re.I):
                            out |= _hms_in(note, self.badges)
        return out

    def common(self, text: str) -> bool:
        """Sold in ordinary Poké Marts, so a ball of it on the ground isn't worth a tick box."""
        names = self.names(text)
        if any(n in H.INCLUDE for n in names):
            return False
        if any(n in H.EXCLUDE for n in names):
            return True
        return all(any(MART_STOCK.fullmatch(w) for w in self.items.get(n, {}).get("where", [])) for n in names)


def _matches(ident: str, patterns) -> bool:
    return any(fnmatch.fnmatchcase(ident, p) for p in patterns)


def checklist(page: dict, maps: list[dict], paths: Paths, dropped: list | None = None) -> dict:
    badges = hm_badges(paths)
    needs = Needs(page, badges)
    by_name = {m["name"]: m for m in maps}
    item_index = {it["name"]: n for n, it in enumerate(page["items"])}
    seen: set[str] = set()

    # stage list: each place, and after a badge's place the "After badge N (with …)" sections that badge opens
    stages, place_stage, unlock_stage = [], {}, {}
    for place in H.ORDER:
        if place not in by_name:
            raise ValueError(f"checklist_data.ORDER: {place!r} has no interactive map")
        place_stage[place] = len(stages)
        stages.append({"title": place, "kind": "place", "groups": {}})
        n = H.BADGE_AT.get(place)
        if n:
            hms = sorted(hm for hm, b in badges.items() if b == n)
            if hms:
                unlock_stage[n] = len(stages)
                stages.append({"title": f"After badge {n} (with {' and '.join(hms)})", "kind": "unlock", "groups": {}})
    later = {"title": "Later in the game", "kind": "later", "groups": {}}
    postgame = {"title": "Postgame", "kind": "postgame", "groups": {}}

    def put(stage, place, entry):
        stage["groups"].setdefault(place, []).append(entry)

    for place in H.ORDER:
        mp = by_name[place]
        for key, text in H.STORY.get(place, []):
            put(stages[place_stage[place]], place, {"id": f"{mp['slug']}/story/{key}", "k": "story", "t": text})
        for mk in mp["markers"]:
            if mk["k"] not in ("item", "hidden", "npc", "wild"):
                continue
            floor = mp["floors"][mk["f"]]["name"]
            ident = f"{mp['slug']}/{mk['k']}/{slug(floor)}/{int(mk['x']) // 16}-{int(mk['y']) // 16}"
            if ident in seen:
                raise ValueError(f"checklist: two entries share the id {ident}")
            seen.add(ident)
            text = H.TEXT.get(ident, mk["t"])
            if mk["k"] == "npc" and SERVICE.search(text):
                continue
            if mk["k"] in ("item", "hidden") and needs.common(mk["t"]):
                if dropped is not None:
                    dropped.append((place, mk["t"]))
                continue
            entry = {"id": ident, "k": mk["k"], "t": text, "mark": f"{'person' if mk['k'] == 'npc' else mk['k']}-{mk['n']}"}
            if floor != place and not re.fullmatch(r"Area \d+", floor):  # "Area 2" tells a player nothing
                entry["fl"] = floor
            if mk["sd"]:
                entry["sd"] = 1
            if text.startswith("Daily") or (not mk["pg"] and _matches(ident, H.DAILY)):
                entry["daily"] = 1
            if mk["k"] in ("item", "hidden"):
                idx = item_index.get(needs.names(mk["t"])[0])
                if idx is not None:
                    entry["item"] = idx

            hms = needs.of(mk["t"], place) if mk["k"] in ("item", "hidden") else set()
            badge = max((badges[h] for h in hms), default=0)
            why = H.LATER.get(ident) or next((w for (p, fl), w in H.LATER_FLOORS.items() if p == place and floor.startswith(fl)), None)
            if hms:
                entry["need"] = ", ".join(sorted(hms, key=lambda h: badges[h]))
            if mk["pg"]:
                put(postgame, place, entry)
            elif why or badge > H.LAST_BADGE:
                if why:
                    entry["why"] = why
                put(later, place, entry)
            elif badge and unlock_stage.get(badge, -1) > place_stage[place]:
                put(stages[unlock_stage[badge]], place, entry)
            else:
                put(stages[place_stage[place]], place, entry)

    for table, name in ((H.TEXT, "TEXT"), (H.LATER, "LATER")):
        for ident in table:
            if ident not in seen:
                raise ValueError(f"checklist_data.{name}: no entry has the id {ident!r}")

    out = []
    for st in stages + [later, postgame]:
        groups = [{"place": p, "slug": by_name[p]["slug"], "entries": es} for p, es in st["groups"].items()]
        if groups:
            out.append({"title": st["title"], "kind": st["kind"], "groups": groups})
    return {"stages": out, "upTo": f"badge {H.LAST_BADGE}"}


def main() -> None:
    import sys

    from .build import build_roster, evolution_links, load_source_data, page_data, place_maps
    sys.stdout.reconfigure(encoding="utf-8")
    paths = Paths.default()
    data = load_source_data(paths)
    roster = build_roster(data)
    page = page_data(data, roster, evolution_links(data, {e.key for e in roster}))
    dropped: list = []
    for st in checklist(page, place_maps(paths), paths, dropped)["stages"]:
        print(f"== {st['title']}")
        for g in st["groups"]:
            for e in g["entries"]:
                notes = [e.get("need") and f"needs {e['need']}", e.get("why"), e.get("daily") and "daily"]
                print(f"   {e['id']:<48} {e['k']:<6} {e['t']}" + "".join(f"  [{n}]" for n in notes if n))
    print("\nLeft out as common (sold in Poké Marts):")
    for name in sorted({t for _, t in dropped}):
        print(f"   {name}: {', '.join(sorted({p for p, t in dropped if t == name}))}")


if __name__ == "__main__":
    main()

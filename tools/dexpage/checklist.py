"""Checklist tab: what a player can do for 100% completion, in playthrough order.

Entries come from the interactive maps' markers (items, hidden items, people and events, Pokémon encounters) plus
hand-written story beats; checklist_data.py says the order and corrects the rest. What needs an HM comes from the
page's own item data ("Route 9 (Requires Cut)", a TM's Requires column), and the badge each HM needs outside battle
from CFRU's gFieldMoveBadgeRequirements.

    python -m tools.dexpage.checklist      # prints every entry with its id, and the common items left out
"""

import difflib
import fnmatch
import re
import unicodedata

from . import checklist_data as H
from .paths import Paths

FIELD_MOVES = {"CUT": "Cut", "ROCK_SMASH": "Rock Smash", "FLY": "Fly", "SURF": "Surf", "STRENGTH": "Strength",
               "ROCK_CLIMB": "Rock Climb"}
MART_STOCK = re.compile(r"Poké Marts( \(after \d+ badges?\))?")
# What the maps say a person does that is a service, not something to finish
SERVICES = {"shop", "heals your team", "move tutor", "move reminder", "move deleter"}
DAILY_TEXT = re.compile(r"^Daily|\b(a|each|per|every) day\b|\bdaily\b")


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower())


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


class Items:
    """The page's item for a map marker's text, and which HMs picking it up at a place needs."""

    def __init__(self, page: dict, badges: dict[str, int], game_names: dict[str, str]):
        self.badges = badges
        self.list = page["items"]
        self.index = {it["name"]: n for n, it in enumerate(self.list)}
        self.by_norm = {_norm(it["name"]): n for n, it in enumerate(self.list)}
        self.game_names = game_names  # the in-game (often shortened) name → the page's full name
        self.tms = {m["tm"]["label"]: m["tm"] for m in page["moves"].values() if m.get("tm")}
        self.unmatched: set[str] = set()
        self.found: dict[str, int | None] = {}

    def names(self, text: str) -> list[str]:
        """'Garchompite (Aerodactite in Divergent)' → both names; 'TM12 Taunt' → itself."""
        m = re.fullmatch(r"(.+?) \((.+?) in Divergent\)", text)
        return [m.group(1), m.group(2)] if m else [text]

    def find(self, name: str) -> int | None:
        """Index of the page item a marker names: 'HvyDutyBoots' is the game's spelling of Heavy Duty Boots."""
        if name not in self.found:
            self.found[name] = self._find(name)
        return self.found[name]

    def _find(self, name: str) -> int | None:
        for key in (name, self.game_names.get(name, "")):
            if key in self.index:
                return self.index[key]
            if key and _norm(key) in self.by_norm:
                return self.by_norm[_norm(key)]
        if m := re.match(r"(TM|HM)\d+ ", name):  # "TM22 Solarbeam": the number is enough
            return next((n for n, it in enumerate(self.list) if it["name"].startswith(m.group(0))), None)
        close = difflib.get_close_matches(_norm(self.game_names.get(name, name)), list(self.by_norm), n=1, cutoff=0.8)
        if close:
            return self.by_norm[close[0]]
        self.unmatched.add(name)
        return None

    def needs(self, text: str, place: str) -> set[str]:
        here, out = _place_re(place), set()
        for name in self.names(text):
            tm = self.tms.get(name.split(" ")[0])
            if tm and any(here.search(w.lower()) for w in tm["where"]):
                out |= _hms_in(tm.get("requires") or "", self.badges)
            k = self.find(name)
            for line in (self.list[k]["where"] if k is not None else []):
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
        found = [self.find(n) for n in names]
        return all(k is not None and any(MART_STOCK.fullmatch(w) for w in self.list[k]["where"]) for k in found)


def _matches(ident: str, patterns) -> bool:
    return any(fnmatch.fnmatchcase(ident, p) for p in patterns)


def _service(text: str) -> bool:
    who, sep, does = text.partition(": ")
    return bool(sep) and all(part in SERVICES for part in does.split(", "))


def _trainers(page: dict, spec: tuple, where: str) -> list[int]:
    cls, name, place = spec
    found = [n for n, t in enumerate(page["trainers"]) if (t["cls"], t["name"], t["place"]) == (cls, name, place)]
    if not found:
        raise ValueError(f"checklist_data ({where}): no trainer {cls} {name!r} at {place!r}")
    return found


def checklist(page: dict, maps: list[dict], paths: Paths, game_names: dict[str, str], dropped: list | None = None) -> dict:
    badges = hm_badges(paths)
    items = Items(page, badges, game_names)
    by_name = {m["name"]: m for m in maps}

    # ---- stages: each stop in H.ORDER, with an "After … (with HM)" section once an HM can be used in the field
    stages, stage_of, parts = [], {}, {}  # stage_of: title → index; parts: place → [(floor prefixes, title)]
    for stop in H.ORDER:
        title, place, floors = (stop, stop, None) if isinstance(stop, str) else stop
        if place not in by_name:
            raise ValueError(f"checklist_data.ORDER: {place!r} has no interactive map")
        if title in stage_of:
            raise ValueError(f"checklist_data.ORDER: {title!r} is listed twice")
        stage_of[title] = len(stages)
        stages.append({"title": title, "kind": "place", "place": place, "groups": {}})
        if floors:
            parts.setdefault(place, []).append((tuple(floors), title))
    missing = sorted(set(by_name) - {st["place"] for st in stages} - set(H.POSTGAME_PLACES))
    if missing:
        raise ValueError(f"checklist_data.ORDER: no stage for {', '.join(missing)}")
    badge_stage = {n: stage_of[place] for n, (_, place) in H.BADGES.items()}

    # an HM opens things up once its badge is won and the HM itself is in hand, whichever comes later
    unlock_after = {}  # HM → index of the stage it follows
    for hm, b in badges.items():
        if H.HM_FROM[hm] not in stage_of:
            raise ValueError(f"checklist_data.HM_FROM: {H.HM_FROM[hm]!r} is not a stage in ORDER")
        unlock_after[hm] = max(badge_stage[b], stage_of[H.HM_FROM[hm]])
    unlocks = {}
    for hm, at in unlock_after.items():
        b = badges[hm]
        where = f"badge {b}" if at == badge_stage[b] else stages[at]["title"]
        unlocks[hm] = {"title": f"After {where} (with {hm})", "kind": "unlock", "groups": {}}
    postgame = {"title": "Postgame", "kind": "postgame", "groups": {}}

    def next_badge(index: int) -> str | None:
        """The badge a player is working toward at this stage (rival side events last until it's won)."""
        ahead = [n for n, at in badge_stage.items() if at >= index]
        return H.BADGES[min(ahead)][0] if ahead else None

    def put(stage, place, entry):
        stage["groups"].setdefault(place, []).append(entry)

    seen: set[str] = set()

    def new_id(ident: str) -> str:
        if ident in seen:
            raise ValueError(f"checklist: two entries share the id {ident}")
        seen.add(ident)
        return ident

    # ---- story beats
    for title, beats in H.STORY.items():
        for beat in beats:
            key, text = beat[0], beat[1]
            opts = beat[2] if len(beat) > 2 else {}
            if title == "Postgame":
                stage, place = postgame, opts["at"]
                if place not in by_name:
                    raise ValueError(f"checklist_data.STORY Postgame/{key}: {place!r} has no interactive map")
            elif title in stage_of:
                stage, place = stages[stage_of[title]], stages[stage_of[title]]["place"]
            else:
                raise ValueError(f"checklist_data.STORY: {title!r} is not a stage in ORDER")
            entry = {"id": new_id(f"{slug(title)}/story/{key}"), "k": "story", "t": text}
            if "trainer" in opts:
                entry["tr"] = _trainers(page, opts["trainer"], f"STORY {title}/{key}")
            if opts.get("daily"):
                entry["daily"] = 1
            put(stage, place, entry)

    # ---- everything the maps mark
    for place, mp in by_name.items():
        for mk in mp["markers"]:
            if mk["k"] not in ("item", "hidden", "npc", "wild"):
                continue
            floor = mp["floors"][mk["f"]]["name"]
            ident = new_id(f"{mp['slug']}/{mk['k']}/{slug(floor)}/{int(mk['x']) // 16}-{int(mk['y']) // 16}")
            text = H.TEXT.get(ident, mk["t"])
            if _matches(ident, H.DROP) or (mk["k"] == "npc" and _service(text)):
                continue
            if mk["k"] in ("item", "hidden") and items.common(mk["t"]):
                if dropped is not None:
                    dropped.append((place, mk["t"]))
                continue
            entry = {"id": ident, "k": mk["k"], "t": text, "mark": f"{'person' if mk['k'] == 'npc' else mk['k']}-{mk['n']}"}
            if floor != place and not re.fullmatch(r"Area \d+", floor):  # "Area 2" tells a player nothing
                entry["fl"] = floor
            if mk["sd"]:
                entry["sd"] = 1
            if mk["k"] in ("item", "hidden"):
                idx = items.find(items.names(mk["t"])[0])
                if idx is not None:
                    entry["item"] = idx
            if ident in H.LINKS:
                entry["tr"] = _trainers(page, H.LINKS[ident], f"LINKS {ident}")

            # where it goes: postgame, a hand-placed stage, the part of the place its floor belongs to, or the place
            moved = H.MOVE.get(ident)
            if moved is not None and moved not in stage_of and moved != "Postgame":
                raise ValueError(f"checklist_data.MOVE: {moved!r} is not a stage in ORDER")
            if moved == "Postgame" or (moved is None and (place in H.POSTGAME_PLACES or mk["pg"])):
                home = None
            elif moved:
                home = stage_of[moved]
            else:
                title = next((t for prefixes, t in parts.get(place, []) if floor.startswith(prefixes)), place)
                if title not in stage_of:
                    raise ValueError(f"checklist_data.ORDER: {place!r} is split into parts, but none takes {floor!r}")
                home = stage_of[title]
            if home is not None and (DAILY_TEXT.search(text) or _matches(ident, H.DAILY)):
                entry["daily"] = 1
            if mk["k"] == "npc" and text.startswith("Rival:") and home is not None and next_badge(home):
                entry["until"] = f"Until the {next_badge(home)} Badge is obtained"

            hms = items.needs(mk["t"], place) if mk["k"] in ("item", "hidden") else set()
            if hms:
                entry["need"] = ", ".join(sorted(hms, key=lambda h: badges[h]))
            if home is None:
                put(postgame, place, entry)
                continue
            last = max(hms, key=lambda h: unlock_after[h], default=None)  # the HM that arrives last
            if last and unlock_after[last] >= home:
                put(unlocks[last], place, entry)
            else:
                put(stages[home], place, entry)

    for table, name in ((H.TEXT, "TEXT"), (H.MOVE, "MOVE"), (H.LINKS, "LINKS")):
        for ident in table:
            if ident not in seen:
                raise ValueError(f"checklist_data.{name}: no entry has the id {ident!r}")

    place_rank = {}
    for n, st in enumerate(stages):
        place_rank.setdefault(st["place"], n)
    order = []
    for n, st in enumerate(stages):
        order.append(st)
        order += [unlocks[hm] for hm, at in unlock_after.items() if at == n]
    out = []
    for st in order + [postgame]:
        groups = [{"place": p, "slug": by_name[p]["slug"], "entries": es} for p, es in st["groups"].items()]
        if st["kind"] != "place":  # places in the order the playthrough reaches them
            groups.sort(key=lambda g: place_rank.get(g["place"], len(stages)))
        if groups:
            out.append({"title": st["title"], "kind": st["kind"], "groups": groups})
    return {"stages": out, "unmatchedItems": sorted(items.unmatched)}


def main() -> None:
    import sys

    from .build import build_roster, evolution_links, game_item_names, load_source_data, page_data, place_maps
    sys.stdout.reconfigure(encoding="utf-8")
    paths = Paths.default()
    data = load_source_data(paths)
    roster = build_roster(data)
    page = page_data(data, roster, evolution_links(data, {e.key for e in roster}))
    dropped: list = []
    result = checklist(page, place_maps(paths), paths, game_item_names(data), dropped)
    total = 0
    for st in result["stages"]:
        print(f"== {st['title']}")
        for g in st["groups"]:
            for e in g["entries"]:
                total += 1
                notes = [e.get("need") and f"needs {e['need']}", e.get("daily") and "daily", e.get("until"),
                         e.get("tr") and "trainer link", e["k"] in ("item", "hidden") and "item" not in e and "NO ITEM LINK"]
                print(f"   {e['id']:<52} {e['k']:<6} {g['place']}: {e['t']}" + "".join(f"  [{n}]" for n in notes if n))
    print(f"\n{total} entries")
    print("\nLeft out as common (sold in Poké Marts):")
    for name in sorted({t for _, t in dropped}):
        print(f"   {name}: {', '.join(sorted({p for p, t in dropped if t == name}))}")
    print("\nItems with no page entry:", ", ".join(result["unmatchedItems"]))


if __name__ == "__main__":
    main()

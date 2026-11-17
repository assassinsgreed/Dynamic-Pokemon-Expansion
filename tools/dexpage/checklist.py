"""Checklist tab: what a player can do for 100% completion, in playthrough order.

Entries come from the interactive maps' markers (items, hidden items, people and events, Pokémon encounters) plus
hand-written story beats; checklist_data.py says the order and corrects the rest. What needs an HM comes from the
page's own item data ("Route 9 (Requires Cut)", a TM's Requires column), and the badge each HM needs outside battle
from CFRU's gFieldMoveBadgeRequirements.

    python -m tools.dexpage.checklist      # prints every entry with its id, and the daily things left out
"""

import difflib
import fnmatch
import re
import unicodedata

from . import checklist_data as H
from . import save_flags
from .paths import Paths

FIELD_MOVES = {"CUT": "Cut", "ROCK_SMASH": "Rock Smash", "FLY": "Fly", "SURF": "Surf", "STRENGTH": "Strength",
               "ROCK_CLIMB": "Rock Climb"}
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
    """HMs a note names; "Requires Lava Surfing" is Surf (on lava: Carnelidge Volcano shows it as Lava Surf)."""
    return {hm for hm in badges if re.search(r"\b" + hm.lower() + r"(ing)?\b", text.lower())}


def _hm_label(hms, place: str, badges: dict[str, int]) -> str:
    """'Cut, Surf' in badge order, with the place's own names for them (Surf in Carnelidge Volcano is Lava Surf)."""
    names = H.HM_NAMES.get(place, {})
    return ", ".join(names.get(h, h) for h in sorted(hms, key=lambda h: badges[h]))


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
        """'Garchompite (Aerodactite in Divergent)' → both names; 'Rusted Data (Burn Drive, Shock Drive in Divergent)'
        → all three; 'TM12 Taunt' → itself."""
        m = re.fullmatch(r"(.+?) \((.+?) in Divergent\)", text)
        return [m.group(1), *m.group(2).split(", ")] if m else [text]

    def spans(self, text: str) -> list[list[int]]:
        """[start, end, page item] for each item the text names, so each links to its own card."""
        out, at = [], 0
        for name in self.names(text):
            start, k = text.find(name, at), self.find(name)
            if start >= 0 and k is not None:
                out.append([start, start + len(name), k])
                at = start + len(name)
        return out

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

    def only(self, text: str, place: str) -> str | None:
        """'Divergent' or 'Standard' when the item data says this pickup exists in one mode only."""
        names = self.names(text)
        k = self.find(names[0]) if len(names) == 1 else None  # "A (B in Divergent)" is there in both modes
        here = _place_re(place)
        for line in (self.list[k]["where"] if k is not None else []):
            if here.search(line.lower()) and (m := re.search(r"\b(Standard|Divergent) mode\b", line)):
                return m.group(1)
        return None


class Mons:
    """Pokémon named in an entry's text, as [start, end, index in the page's Pokémon] so the page can link them."""

    def __init__(self, page: dict):
        self.by_name: dict[str, list] = {}
        for i, m in enumerate(page["mons"]):
            self.by_name.setdefault(m["name"], []).append((m["form"] or "", i))
        names = sorted(self.by_name, key=len, reverse=True)
        self.re = re.compile(r"(?<![A-Za-z])(" + "|".join(map(re.escape, names)) + r")(?![A-Za-z])")

    def spans(self, text: str) -> list[list[int]]:
        out = []
        for m in self.re.finditer(text):
            forms, start = self.by_name[m.group(1)], m.start()
            # "Galarian Slowbro", "Heat Rotom": the form named just before it, else the plain one
            named = next(((f, i) for f, i in forms if f and text[:start].endswith(f + " ")), None)
            if named:
                start -= len(named[0]) + 1
            pick = named[1] if named else next((i for f, i in forms if not f), forms[0][1])
            out.append([start, m.end(), pick])
        return out


def _matches(ident: str, patterns) -> bool:
    return any(fnmatch.fnmatchcase(ident, p) for p in patterns)


def _service(text: str, roles: str) -> bool:
    """Only a service: what the script does (roles, which still says "shop" where the map's text no longer does)."""
    does = roles or text.partition(": ")[2]
    return bool(does) and all(part in SERVICES for part in does.split(", "))


def _trainers(page: dict, spec: tuple, where: str) -> list[int]:
    cls, name, place = spec
    found = [n for n, t in enumerate(page["trainers"]) if (t["cls"], t["name"], t["place"]) == (cls, name, place)]
    if not found:
        raise ValueError(f"checklist_data ({where}): no trainer {cls} {name!r} at {place!r}")
    return found


def checklist(page: dict, maps: list[dict], paths: Paths, game_names: dict[str, str], daily: list | None = None) -> dict:
    badges = hm_badges(paths)
    items = Items(page, badges, game_names)
    mons = Mons(page)
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
    ultra = {"title": "Ultra Episode", "kind": "postgame", "groups": {}}  # Collin: its own section after Postgame

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
                stage, place = ultra if opts.get("ultra") else postgame, opts["at"]
                if place not in by_name:
                    raise ValueError(f"checklist_data.STORY Postgame/{key}: {place!r} has no interactive map")
            elif title in stage_of:
                stage, place = stages[stage_of[title]], stages[stage_of[title]]["place"]
            else:
                raise ValueError(f"checklist_data.STORY: {title!r} is not a stage in ORDER")
            entry = {"id": new_id(f"{slug(title)}/story/{key}"), "k": "story", "t": text}
            if opts.get("daily"):  # Collin: once-a-day things are never finished, so they aren't completion
                if daily is not None:
                    daily.append((place, text))
                continue
            if "item" in opts:
                entry["item"] = items.find(opts["item"])
                if entry["item"] is None:
                    raise ValueError(f"checklist_data.STORY {title}/{key}: no item {opts['item']!r} on the page")
            if "trainer" in opts:
                entry["tr"] = _trainers(page, opts["trainer"], f"STORY {title}/{key}")
            elif mons.spans(text):
                entry["p"] = mons.spans(text)
            sv = save_flags.resolve(paths, H.SAVE[entry["id"]]) if entry["id"] in H.SAVE else \
                save_flags.trainer_flags(page, entry.get("tr", []))
            if sv:
                entry["sv"] = sv
            put(stage, place, entry)

    # ---- everything the maps mark
    for place, mp in by_name.items():
        for mk in mp["markers"]:
            # only the save reader (fg, lb) and the service check (rl) want these, not the map viewer
            hide_flag, label, roles = mk.pop("fg", 0), mk.pop("lb", ""), mk.pop("rl", "")
            if mk["k"] not in ("item", "hidden", "npc", "wild"):
                continue
            floor = mp["floors"][mk["f"]]["name"]
            floor_id = H.FLOOR_IDS.get((place, floor), slug(floor))  # a renamed floor keeps the ids ticks are saved under
            ident = new_id(f"{mp['slug']}/{mk['k']}/{floor_id}/{int(mk['x']) // 16}-{int(mk['y']) // 16}")
            text = H.TEXT.get(ident, mk.get("tf", mk["t"]))  # tf: the gift list in full, where the map shortens it
            # HMs it takes to reach: the item data's notes plus Collin's own; the map viewer shows them too (rq)
            # HMs it takes to reach: the item data's notes, or Collin's own (NEEDS); the map viewer shows them too (rq).
            # The HM a whole place is reached with (Surf for Routes 14-16) goes without saying.
            if ident in H.NEEDS:
                hms = set(H.NEEDS[ident])
            else:
                hms = items.needs(mk["t"], place) if mk["k"] in ("item", "hidden") else set()
            hms -= set(H.REACHED_WITH.get(place, ()))
            if hms:
                mk["rq"] = _hm_label(hms, place, badges)
            if _matches(ident, H.DROP) or (mk["k"] == "npc" and _service(text, roles)):
                continue
            only = H.ONLY.get(ident) or (items.only(mk["t"], place) if mk["k"] in ("item", "hidden") else None)
            if only:
                mk["mo"] = only
            # what in a save file says it's done (save_flags.py)
            if ident in H.SAVE:
                sv = save_flags.resolve(paths, H.SAVE[ident])
            elif ident in H.LINKS:
                sv = save_flags.trainer_flags(page, _trainers(page, H.LINKS[ident], f"LINKS {ident}"))
            elif mk["k"] == "npc":
                sv = save_flags.script_flags(paths, label)[:1]
            else:
                sv = [hide_flag] if hide_flag else []
            late = H.MOVE.get(ident) == "Postgame" or (ident not in H.MOVE and (place in H.POSTGAME_PLACES or mk["pg"]))
            # daily: the text says so, Collin says so, or (a person) the flag their script sets is one the game clears each day
            if (not late and (DAILY_TEXT.search(text) or _matches(ident, H.DAILY))) or \
                    (mk["k"] == "npc" and ident not in H.SAVE and sv and save_flags.is_daily(sv[0])):
                if daily is not None:
                    daily.append((place, text))
                continue
            entry = {"id": ident, "k": mk["k"], "t": text, "mark": f"{'person' if mk['k'] == 'npc' else mk['k']}-{mk['n']}"}
            if floor != place and not re.fullmatch(r"Area \d+", floor):  # "Area 2" tells a player nothing
                entry["fl"] = floor
            if mk["sd"]:
                entry["sd"] = 1
            if only:
                entry["only"] = only
            if mk["k"] in ("item", "hidden"):
                idx, spans = items.find(items.names(mk["t"])[0]), items.spans(text)
                if len(spans) > 1:  # "A (B in Divergent)": each name links to its own item
                    entry["ip"] = spans
                elif idx is not None:
                    entry["item"] = idx
            if ident in H.LINKS:
                entry["tr"] = _trainers(page, H.LINKS[ident], f"LINKS {ident}")
            elif mk["k"] in ("npc", "wild") and mons.spans(text):
                entry["p"] = mons.spans(text)
            if sv:
                entry["sv"] = sv

            # where it goes: postgame, a hand-placed stage, the part of the place its floor belongs to, or the place
            moved = H.MOVE.get(ident)
            if moved is not None and moved not in stage_of and moved != "Postgame" and moved.removeprefix("with ") not in unlocks:
                raise ValueError(f"checklist_data.MOVE: {moved!r} is not a stage in ORDER")
            if moved and moved.startswith("with "):  # "with Strength": that HM's "After … (with Strength)" section
                put(unlocks[moved[5:]], place, entry)
                continue
            if moved == "Postgame" or (moved is None and (place in H.POSTGAME_PLACES or mk["pg"])):
                home = None
            elif moved:
                home = stage_of[moved]
            else:
                title = next((t for prefixes, t in parts.get(place, []) if floor.startswith(prefixes)), place)
                if title not in stage_of:
                    raise ValueError(f"checklist_data.ORDER: {place!r} is split into parts, but none takes {floor!r}")
                home = stage_of[title]
            if mk["k"] == "npc" and text.startswith("Rival:") and home is not None and next_badge(home):
                entry["until"] = f"Until the {next_badge(home)} Badge is obtained"

            if hms:
                entry["need"] = _hm_label(hms, place, badges)
            if home is None:
                if text.startswith("Ultra Wormhole"):  # one list of them all, each saying where it is
                    entry["at"], entry["ms"] = place, mp["slug"]
                    put(ultra, H.ULTRA_WORMHOLES, entry)
                else:
                    put(ultra if _matches(ident, H.ULTRA_EPISODE_ENTRIES) else postgame, place, entry)
                continue
            last = max(hms, key=lambda h: unlock_after[h], default=None)  # the HM that arrives last
            if last and unlock_after[last] >= home:
                put(unlocks[last], place, entry)
            else:
                put(stages[home], place, entry)

    for table, name in ((H.TEXT, "TEXT"), (H.MOVE, "MOVE"), (H.LINKS, "LINKS"), (H.NEEDS, "NEEDS"), (H.SAVE, "SAVE"),
                        (H.ONLY, "ONLY")):
        for ident in table:
            if ident not in seen:
                raise ValueError(f"checklist_data.{name}: no entry has the id {ident!r}")

    by_id = {e["id"]: e for st in [*stages, *unlocks.values(), postgame, ultra] for es in st["groups"].values() for e in es}
    for e in by_id.values():  # SAVE: "done when that other entry is"
        if isinstance(e.get("sv"), str):
            if not isinstance(by_id.get(e["sv"], {}).get("sv"), list):
                raise ValueError(f"checklist_data.SAVE {e['id']}: {e['sv']!r} is not an entry a save can tick")
            e["sv"] = by_id[e["sv"]]["sv"]

    place_rank = {}
    for n, st in enumerate(stages):
        place_rank.setdefault(st["place"], n)
    order = []
    for n, st in enumerate(stages):
        order.append(st)
        order += [unlocks[hm] for hm, at in unlock_after.items() if at == n]
    out = []
    for st in order + [postgame, ultra]:
        groups = [{"place": p, "slug": by_name[p]["slug"] if p in by_name else None, "entries": es}
                  for p, es in st["groups"].items()]
        for g in groups:
            if g["slug"] is None:  # a list, not a place (the Ultra Wormhole Search): its entries in playthrough order
                del g["slug"]
                g["entries"].sort(key=lambda e: place_rank.get(e.get("at"), len(stages)))
        if st is ultra:
            unknown = [g["place"] for g in groups if g["place"] not in H.ULTRA_ORDER]
            if unknown:
                raise ValueError(f"checklist_data.ULTRA_ORDER: no place for {', '.join(unknown)}")
            groups.sort(key=lambda g: H.ULTRA_ORDER.index(g["place"]))
        elif st["kind"] != "place":  # places in the order the playthrough reaches them
            groups.sort(key=lambda g: place_rank.get(g["place"], len(stages)))
        if groups:
            out.append({"title": st["title"], "kind": st["kind"], "place": st.get("place"), "groups": groups})
    return {"stages": out, "unmatchedItems": sorted(items.unmatched)}


def main() -> None:
    import sys

    from .build import build_roster, evolution_links, game_item_names, load_source_data, page_data, place_maps
    sys.stdout.reconfigure(encoding="utf-8")
    paths = Paths.default()
    data = load_source_data(paths)
    roster = build_roster(data)
    page = page_data(data, roster, evolution_links(data, {e.key for e in roster}))
    daily: list = []
    result = checklist(page, place_maps(paths), paths, game_item_names(data), daily)
    total = 0
    for st in result["stages"]:
        print(f"== {st['title']}")
        for g in st["groups"]:
            for e in g["entries"]:
                total += 1
                notes = [e.get("need") and f"needs {e['need']}", e.get("until"), "sv" not in e and "NOT IN SAVE",
                         e.get("sv") and "save " + save_flags.describe(e["sv"]),
                         e.get("tr") and "trainer link", e["k"] in ("item", "hidden") and "item" not in e and "ip" not in e and "NO ITEM LINK"]
                print(f"   {e['id']:<52} {e['k']:<6} {e.get('at', g['place'])}: {e['t']}" + "".join(f"  [{n}]" for n in notes if n))
    print(f"\n{total} entries")
    print("\nLeft out as daily:")
    for place, text in daily:
        print(f"   {place}: {text}")
    print("\nItems with no page entry:", ", ".join(result["unmatchedItems"]))


if __name__ == "__main__":
    main()

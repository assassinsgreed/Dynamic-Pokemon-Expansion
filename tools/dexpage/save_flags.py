"""What in a save file says a Checklist entry is done, so the page can tick entries from a player's .sav / .srm.

Each entry gets `sv`: a list of conditions, done when any holds. A condition is a flag number (set), ["v", var,
n] (the game variable is at least n), ["i", item id] (the item is in the bag) or ["&", condition, ...] (all of them).
  item balls / one-off Pokémon   the flag that hides the object once it's taken or dealt with (ROM map data)
  hidden items                   FLAG_HIDDEN_ITEMS_START + the item's id byte (ROM map data)
  battles (story beats, LINKS)   the trainer flag of any of the linked trainers (0x500 + trainer id)
  people and events              the flag their script both checks and sets (CFRU's overworld scripts), unless
                                 checklist_data.SAVE names it
  other story beats              checklist_data.SAVE

The page's reader (app.js ckReadSave) mirrors CFRU's save.c: two slots of 14 sectors, 0xFF0 data bytes each; flags
0-0x8FF sit in SaveBlock1 at 0xEE0 with variables 0x4000-0x40FF after them. CFRU's own block (RAM 0x203B174 on) is
saved in the unused tails of sectors 0, 4 and 13 and then in sectors 30 and 31: it opens with flags 0x900-0x18FF,
and holds the bag (every pocket, back to back, from RAM 0x203BB20).
"""

import re
from functools import cache

from .cparse import collect_defines
from .paths import Paths

TRAINER_FLAGS = 0x500
MODE_FLAG = 0x945          # Divergent mode: never what marks an entry done
DAILY_FLAGS = range(0xE00, 0xF00)  # FLAG_DAILY_EVENTS_START: cleared each new day


def is_daily(condition) -> bool:
    return isinstance(condition, int) and condition in DAILY_FLAGS


@cache
def _item_ids(p: Paths) -> dict[str, int]:
    out = {}
    for k, v in collect_defines(p.cfru / "include/constants/items.h").items():
        if k.startswith("ITEM_") and re.fullmatch(r"0x[0-9A-Fa-f]+|\d+", (v or "").split()[0] if v else ""):
            out[k] = int(v.split()[0], 0)
    text = (p.cfru / "include/constants/items.h").read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"^\s*(ITEM_\w+)\s*=\s*(0x[0-9A-Fa-f]+|\d+)\s*,", text, re.M):  # the TM/HM enum
        out.setdefault(m.group(1), int(m.group(2), 0))
    return out


def resolve(p: Paths, conditions: list) -> list:
    """checklist_data.SAVE as the page reads it: item constants become their numbers. (A string instead of a list
    is another entry's id, "done when that one is": checklist() swaps it for that entry's conditions.)"""
    if isinstance(conditions, str):
        return conditions
    def one(c):
        if isinstance(c, int):
            return c
        if c[0] == "i":
            if c[1] not in _item_ids(p):
                raise ValueError(f"checklist_data.SAVE: no item {c[1]!r} in CFRU's items.h")
            return ["i", _item_ids(p)[c[1]]]
        return ["&", *map(one, c[1:])] if c[0] == "&" else list(c)
    return [one(c) for c in conditions]


def describe(conditions: list) -> str:
    def one(c):
        if isinstance(c, int):
            return f"{c:#x}"
        if c[0] == "&":
            return "(" + " & ".join(map(one, c[1:])) + ")"
        return f"var {c[1]:#x}>={c[2]}" if c[0] == "v" else f"item {c[1]}"
    return "/".join(map(one, conditions[:4])) + ("…" if len(conditions) > 4 else "")
_FLAG = r"(0x[0-9A-Fa-f]+|\d+|FLAG_\w+)"


@cache
def _flag_names(p: Paths) -> dict[str, int]:
    """Every flag constant with a number: plain ones, and "(SYS_FLAGS + 0x20)" sums of ones already known."""
    out, number = {}, r"0x[0-9A-Fa-f]+|\d+"
    for header in ("include/constants/flags.h", "src/config.h"):
        for k, v in collect_defines(p.cfru / header).items():
            v = (v or "").strip()
            if re.fullmatch(number, v.split()[0] if v else ""):
                out.setdefault(k, int(v.split()[0], 0))
            elif (m := re.fullmatch(rf"\(?\s*(\w+)\s*\+\s*({number})\s*\)?", v)) and m.group(1) in out:
                out.setdefault(k, out[m.group(1)] + int(m.group(2), 0))
    return out


def flag_number(p: Paths, text: str) -> int | None:
    if text.startswith("FLAG_"):
        return _flag_names(p).get(text)
    return int(text, 0)


@cache
def _scripts(p: Paths) -> tuple[dict, dict]:
    """(blocks per file, the file each label is in). Files reuse local labels, so a jump looks in its own file first."""
    files, home = {}, {}
    for path in sorted((p.cfru / "assembly/overworld_scripts").rglob("*.s")):
        text = path.read_text(encoding="utf-8", errors="replace")
        blocks = {}
        for m in re.finditer(r"^(\w+):[^\n]*\n(.*?)(?=^\w+:|\Z)", text, flags=re.M | re.S):
            lines = [l.split("@")[0].strip() for l in m.group(2).splitlines()]
            blocks[m.group(1)] = [l for l in lines if l and not l.startswith(".")]
            home.setdefault(m.group(1), path)
        files[path] = blocks
    return files, home


def script_flags(p: Paths, label: str, depth: int = 4) -> list[int]:
    """Flags a script (and what it jumps to) both checks and sets, in the order it checks them: "have I given this
    already?" flags. The mode flag and flags it also clears (toggles) don't count."""
    files, home = _scripts(p)
    if label not in home:
        return []
    checked, set_, cleared = [], set(), set()
    todo, seen = [(home[label], label, 0)], set()
    while todo:
        path, lab, d = todo.pop(0)
        if (path, lab) in seen:
            continue
        seen.add((path, lab))
        for line in files[path].get(lab, ()):
            if m := re.match(r"(checkflag|setflag|clearflag)\s+" + _FLAG, line, re.I):
                n = flag_number(p, m.group(2))
                if n is None:
                    continue
                if m.group(1).lower() == "checkflag":
                    checked.append(n)
                elif m.group(1).lower() == "setflag":
                    set_.add(n)
                else:
                    cleared.add(n)
            elif d < depth and (m := re.search(r"(?:goto|call)\s+(\w+)\s*$", line)):
                target = m.group(1)
                at = path if target in files[path] else home.get(target)
                if at:
                    todo.append((at, target, d + 1))
    return [n for n in dict.fromkeys(checked) if n in set_ and n not in cleared and n != MODE_FLAG and n >= 0x20]


def trainer_flags(page: dict, indexes: list[int]) -> list[int]:
    return sorted({TRAINER_FLAGS + page["trainers"][n]["id"] for n in indexes})


# ---------- reading a save here, to check the page's reader against (python -m tools.dexpage.save_flags file.sav)

SIGNATURE = 0x08012025
CHUNK = {0: 0xF24, 4: 0xD98, 13: 0x450}  # the vanilla part of a sector (what its checksum covers); the rest are full
SECTOR_DATA = 0xFF0


BLOCK = 0x203B174           # CFRU's block in RAM
BAG = (0x203BB20, 0x203C748)  # every bag pocket: 4-byte slots, item id then (scrambled) quantity
VARS = 0x4000


def read_save(data: bytes) -> dict | None:
    """{"flags": bytes for flags 0-0x18FF, "vars": [0x4000-0x40FF], "items": ids in the bag} from the newer complete
    save slot, or None when the file isn't a save of this game."""
    import struct
    if len(data) < 0x20000:
        return None
    best = None
    for slot in range(2):
        at, counter = {}, 0
        for i in range(14):
            o = (slot * 14 + i) * 0x1000
            ident, checksum, signature, count = struct.unpack_from("<HHII", data, o + 0xFF4)
            size = CHUNK.get(ident, SECTOR_DATA)
            total = sum(struct.unpack_from(f"<{size // 4}I", data, o)) & 0xFFFFFFFF
            if signature == SIGNATURE and ((total >> 16) + total) & 0xFFFF == checksum:
                at[ident], counter = o, count
        if len(at) == 14 and (best is None or counter > best[1]):
            best = (at, counter)
    if best is None:
        return None
    part = lambda ident, a, b: data[best[0][ident] + a:best[0][ident] + b]
    block = b"".join(part(i, CHUNK[i], SECTOR_DATA) for i in (0, 4, 13)) + \
        data[30 * 0x1000:30 * 0x1000 + SECTOR_DATA] + data[31 * 0x1000:31 * 0x1000 + SECTOR_DATA]
    block1 = b"".join(part(i, 0, SECTOR_DATA) for i in (1, 2, 3, 4))
    bag = block[BAG[0] - BLOCK:BAG[1] - BLOCK]
    return {"flags": block1[0xEE0:0x1000] + block[:0x200],
            "vars": list(struct.unpack_from("<256H", block1, 0x1000)),
            "items": {n for n in struct.unpack_from(f"<{len(bag) // 2}H", bag)[::2] if n}}


def holds(condition, save: dict) -> bool:
    if isinstance(condition, int):
        return bool(save["flags"][condition >> 3] >> (condition & 7) & 1)
    kind = condition[0]
    if kind == "v":
        return save["vars"][condition[1] - VARS] >= condition[2]
    if kind == "i":
        return condition[1] in save["items"]
    return all(holds(c, save) for c in condition[1:])


def ticked(result: dict, save: dict) -> set[str]:
    """Ids of the checklist entries a save says are done."""
    return {e["id"] for st in result["stages"] for g in st["groups"] for e in g["entries"]
            if any(holds(c, save) for c in e.get("sv", ()))}


def main() -> None:
    import sys
    from pathlib import Path

    from .build import build_roster, evolution_links, game_item_names, load_source_data, page_data, place_maps
    from .checklist import checklist
    sys.stdout.reconfigure(encoding="utf-8")
    paths = Paths.default()
    data = load_source_data(paths)
    roster = build_roster(data)
    page = page_data(data, roster, evolution_links(data, {e.key for e in roster}))
    result = checklist(page, place_maps(paths), paths, game_item_names(data))
    every = [(st, g, e) for st in result["stages"] for g in st["groups"] for e in g["entries"]]
    for arg in sys.argv[1:]:
        files = sorted(Path(arg).glob("*.s[ar][vm]")) if Path(arg).is_dir() else [Path(arg)]
        for f in files:
            save = read_save(f.read_bytes())
            if save is None:
                print(f"{f.name}: not a save of this game")
                continue
            done = ticked(result, save)
            print(f"{f.name}: {len(done)} of {len(every)} done")
            if len(files) == 1:
                for st, g, e in every:
                    print(f"   [{'x' if e['id'] in done else ' ' if 'sv' in e else '?'}] {st['title']} / {g['place']}: {e['t']}")


if __name__ == "__main__":
    main()

"""What in a save file says a Checklist entry is done, so the page can tick entries from a player's .sav / .srm.

Each entry gets `sv`: a list of flag numbers, done when any is set.
  item balls / one-off Pokémon   the flag that hides the object once it's taken or dealt with (ROM map data)
  hidden items                   FLAG_HIDDEN_ITEMS_START + the item's id byte (ROM map data)
  battles (story beats, LINKS)   the trainer flag of any of the linked trainers (0x500 + trainer id)
  people and events              the flag their script both checks and sets (CFRU's overworld scripts), unless
                                 checklist_data.SAVE names it
  other story beats              checklist_data.SAVE

The page's reader (app.js ckSave*) mirrors CFRU's save.c: two slots of 14 sectors, 0xFF0 data bytes each; flags
0-0x8FF sit in SaveBlock1 at 0xEE0 and CFRU's flags 0x900-0x18FF open its "parasite" block, which starts in the
unused tail of sector 0 (0xF24 on).
"""

import re
from functools import cache

from .cparse import collect_defines
from .paths import Paths

TRAINER_FLAGS = 0x500
MODE_FLAG = 0x945          # Divergent mode: never what marks an entry done
FLAG_COUNT = 0x1900
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
    """Flags a script (and what it jumps to) both checks and sets, in the order it sets them: "have I given this
    already?" flags. The mode flag and flags it also clears (toggles, daily resets) don't count."""
    files, home = _scripts(p)
    if label not in home:
        return []
    checked, set_, cleared = set(), [], set()
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
                    checked.add(n)
                elif m.group(1).lower() == "setflag":
                    set_.append(n)
                else:
                    cleared.add(n)
            elif d < depth and (m := re.search(r"(?:goto|call)\s+(\w+)\s*$", line)):
                target = m.group(1)
                at = path if target in files[path] else home.get(target)
                if at:
                    todo.append((at, target, d + 1))
    return [n for n in dict.fromkeys(set_) if n in checked and n not in cleared and n != MODE_FLAG and n >= 0x20]


def trainer_flags(page: dict, indexes: list[int]) -> list[int]:
    return sorted({TRAINER_FLAGS + page["trainers"][n]["id"] for n in indexes})


# ---------- reading a save here, to check the page's reader against (python -m tools.dexpage.save_flags file.sav)

SIGNATURE = 0x08012025
CHUNK = {0: 0xF24, 4: 0xD98, 13: 0x450}  # the vanilla part of a sector (what its checksum covers); the rest are full
SECTOR_DATA = 0xFF0


def read_flags(data: bytes) -> bytes | None:
    """Flags 0-0x18FF of the newer complete save slot, or None when the file isn't a save of this game."""
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
    extra = part(0, CHUNK[0], SECTOR_DATA) + part(4, CHUNK[4], SECTOR_DATA)  # CFRU's block starts with flags 0x900+
    return part(1, 0xEE0, SECTOR_DATA) + part(2, 0, 0x10) + extra[:0x200]


def ticked(result: dict, flags: bytes) -> set[str]:
    """Ids of the checklist entries a save's flags say are done."""
    has = lambda n: flags[n >> 3] >> (n & 7) & 1
    return {e["id"] for st in result["stages"] for g in st["groups"] for e in g["entries"] if any(map(has, e.get("sv", ())))}


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
            flags = read_flags(f.read_bytes())
            if flags is None:
                print(f"{f.name}: not a save of this game")
                continue
            done = ticked(result, flags)
            print(f"{f.name}: {len(done)} of {len(every)} done")
            if len(files) == 1:
                for st, g, e in every:
                    print(f"   [{'x' if e['id'] in done else ' ' if 'sv' in e else '?'}] {st['title']} / {g['place']}: {e['t']}")


if __name__ == "__main__":
    main()

"""Reads in-game text that only exists in the built ROM (item names were edited there with HexManiac)."""

from pathlib import Path

from .paths import DPE_ROOT

ITEM_STRUCT_SIZE = 44  # FireRed struct Item
ITEM_NAME_LENGTH = 14
TERMINATOR = 0xFF


class RomError(Exception):
    pass


def load_charmap(path: Path = DPE_ROOT / "charmap.tbl") -> dict[int, str]:
    charmap: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if "=" not in line:
            continue
        code, char = line.split("=", 1)
        if len(code) != 2 or not char:
            continue
        byte = int(code, 16)
        # Some bytes have several spellings; prefer the plain-ASCII one (' over ’).
        if byte not in charmap or (not charmap[byte].isascii() and char.isascii()):
            charmap[byte] = char
    return charmap


def decode(data: bytes, charmap: dict[int, str]) -> str:
    out = []
    for b in data:
        if b == TERMINATOR:
            break
        out.append(charmap.get(b, "?"))
    return "".join(out)


def encode(text: str, charmap: dict[int, str]) -> bytes:
    reverse = {}
    for byte, char in charmap.items():
        reverse.setdefault(char, byte)
    return bytes(reverse[c] for c in text) + bytes([TERMINATOR])


def _find_item_table(rom: bytes, charmap: dict[int, str]) -> int:
    """Locate the item table by its first two entries' names rather than a hard-coded offset."""
    candidates = []
    for first, second in (("Master Ball", "Ultra Ball"), ("MASTER BALL", "ULTRA BALL")):
        needle, follow = encode(first, charmap), encode(second, charmap)
        start = rom.find(needle)
        while start != -1:
            if rom[start + ITEM_STRUCT_SIZE:start + ITEM_STRUCT_SIZE + len(follow)] == follow:
                candidates.append(start - ITEM_STRUCT_SIZE)  # item 0 precedes Master Ball
            start = rom.find(needle, start + 1)
    if len(candidates) != 1:
        raise RomError(f"expected exactly one item table in the ROM, found {len(candidates)}")
    return candidates[0]


def item_names(rom_path: Path, item_ids: dict[str, int]) -> dict[str, str]:
    if not rom_path.exists():
        raise RomError(f"built ROM not found: {rom_path} (build Complete-Fire-Red-Upgrade first)")
    rom = rom_path.read_bytes()
    charmap = load_charmap()
    base = _find_item_table(rom, charmap)
    names = {}
    for const, idx in item_ids.items():
        offset = base + idx * ITEM_STRUCT_SIZE
        if offset + ITEM_NAME_LENGTH <= len(rom):
            names[const] = decode(rom[offset:offset + ITEM_NAME_LENGTH], charmap)
    return names

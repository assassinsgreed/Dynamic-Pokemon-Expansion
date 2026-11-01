"""Map headers, layouts and tilesets read from the built ROM, rendered to images; plus CFRU script lookups.

init(paths) must run before places.py is imported: the readers below and places.py's tables use the ROM it loads."""

import re
import struct

from PIL import Image

from ..field_items import MAP_GROUPS_PTR
from ..rom import _rom_bytes, lz77

P = None
ROM = b""
u8 = lambda o: ROM[o]
u16 = lambda o: struct.unpack_from("<H", ROM, o)[0]
s16 = lambda o: struct.unpack_from("<h", ROM, o)[0]
u32 = lambda o: struct.unpack_from("<I", ROM, o)[0]
off = lambda v: v - 0x08000000
is_ptr = lambda v: 0x08000000 <= v < 0x08000000 + len(ROM)

NUM_PRIMARY = 640  # metatiles 0-639 come from a layout's primary tileset, the rest from its secondary one


def init(paths):
    global P, ROM
    P, ROM = paths, _rom_bytes(paths.rom)
    _tileset_cache.clear()


def header(group, num):
    groups = off(u32(MAP_GROUPS_PTR))
    return off(u32(off(u32(groups + 4 * group)) + 4 * num))


# ---------- rendering ----------

_tileset_cache = {}


def tileset(ptr):
    if ptr in _tileset_cache:
        return _tileset_cache[ptr]
    t = off(ptr)
    compressed = u8(t)
    tiles_ptr, pal_ptr, meta_ptr = u32(t + 4), u32(t + 8), u32(t + 12)
    tiles = lz77(ROM, tiles_ptr) if compressed else ROM[off(tiles_ptr):off(tiles_ptr) + 1024 * 32]
    pals = []
    for p in range(16):
        cols = []
        for c in range(16):
            v = u16(off(pal_ptr) + 32 * p + 2 * c)
            cols.append(((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31))
        pals.append(cols)
    _tileset_cache[ptr] = (tiles, pals, off(meta_ptr))
    return _tileset_cache[ptr]


class Renderer:
    def __init__(self, layout):
        self.prim = tileset(u32(layout + 16))
        self.sec = tileset(u32(layout + 20))
        self.pals = self.prim[1][:7] + self.sec[1][7:]
        self.cache = {}

    def tile_pixels(self, tid):
        tiles = self.prim[0] if tid < NUM_PRIMARY else self.sec[0]
        base = (tid % NUM_PRIMARY) * 32
        data = tiles[base:base + 32]
        if len(data) < 32:
            data = bytes(32)
        return [[(data[y * 4 + x // 2] >> (4 * (x & 1))) & 15 for x in range(8)] for y in range(8)]

    def metatile(self, mid):
        if mid in self.cache:
            return self.cache[mid]
        meta = self.prim[2] + 16 * mid if mid < NUM_PRIMARY else self.sec[2] + 16 * (mid - NUM_PRIMARY)
        img = Image.new("RGBA", (16, 16))
        px = img.load()
        for layer in range(2):
            for k in range(4):
                e = u16(meta + 2 * (4 * layer + k))
                tid, hf, vf, pal = e & 0x3FF, e >> 10 & 1, e >> 11 & 1, e >> 12
                pix = self.tile_pixels(tid)
                ox, oy = (k & 1) * 8, (k >> 1) * 8
                for y in range(8):
                    for x in range(8):
                        c = pix[7 - y if vf else y][7 - x if hf else x]
                        if c == 0 and layer:
                            continue
                        px[ox + x, oy + y] = self.pals[pal][c] + (255,)
        self.cache[mid] = img
        return img


def render(group, num):
    h = header(group, num)
    layout = off(u32(h))
    w, ht = u32(layout), u32(layout + 4)
    blocks = off(u32(layout + 12))
    r = Renderer(layout)
    img = Image.new("RGBA", (w * 16, ht * 16))
    for y in range(ht):
        for x in range(w):
            img.paste(r.metatile(u16(blocks + 2 * (y * w + x)) & 0x3FF), (x * 16, y * 16))
    return img, w, ht, r


# ---------- scripts ----------

def script_labels():
    """offsets.ini: ROM address → label."""
    names = {}
    for line in (P.cfru / "offsets.ini").read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^(\w+):\s+([0-9A-Fa-f]{8})", line)
        if m:
            names[int(m.group(2), 16)] = m.group(1)
    return names


def script_blocks(text):
    blocks, label = {}, None
    for line in text.splitlines():
        line = line.split("@")[0].rstrip()
        m = re.match(r"^(\w+):", line)
        if m:
            label = m.group(1)
            blocks[label] = []
        elif label and line.strip():
            blocks[label].append(line.strip())
    return blocks


def equs(text):
    return {m.group(1): int(m.group(2), 0) for m in re.finditer(r"^\.equ\s+(\w+),\s*(\S+)", text, re.M)}


def tiles_set(blocks, consts, label, seen=None):
    """Every setmaptile reached from a label (following goto/call), as (x, y, metatile)."""
    seen = seen if seen is not None else set()
    if label in seen or label not in blocks:
        return []
    seen.add(label)
    out = []
    num = lambda s: consts[s] if s in consts else int(s, 0)
    for line in blocks[label]:
        parts = line.split()
        if parts[0] == "setmaptile":
            out.append((num(parts[1]), num(parts[2]), num(parts[3])))
        elif parts[0] in ("goto", "call"):
            out += tiles_set(blocks, consts, parts[1], seen)
        elif parts[0] in ("return", "end"):
            break
    return out

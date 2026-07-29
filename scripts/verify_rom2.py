#!/usr/bin/env python3
"""Verify that relocated .rom2 data survived the whole build chain.

Run this on the FINAL rom (Complete-Fire-Red-Upgrade/test.gba), not on this
repo's intermediate test.gba. The point is to catch a later stage -- CFRU,
an .ips patch, the music patch -- writing over data DPE parked at 0x1000000.

    python scripts/verify_rom2.py "../Complete-Fire-Red-Upgrade/test.gba"

Exits 0 if everything checks out, 1 otherwise.
"""

import os
import re
import struct
import subprocess
import sys
from glob import glob

LINKED = 'build/linked.o'
NUM_SPECIES = 1268
ROM2_START = 0x09000000
MUSIC_PATCH_START = 0x1200000   # file offset the B2W2 patch is written to
ROM_SIZE_LIMIT = 0x2000000

# table name -> (entry stride, substring every target symbol must contain)
POINTER_TABLES = {
    'gMonIconTable': (4, 'IconSprite'),
    'gMonFrontPicTable': (8, 'FrontSprite'),
    'gMonBackPicTable': (8, 'BackShinySprite'),
    'gMonPaletteTable': (8, 'FrontSprite'),
    'gMonShinyPaletteTable': (8, 'BackShinySprite'),
}


def Nm():
    prefix = 'arm-none-eabi-'
    path = ''
    if sys.platform.startswith('win'):
        for candidate in (os.environ.get('Path') or '').split(';'):
            if 'devkitARM' in candidate:
                path = candidate
                break
        if not path:
            path = 'C://devkitPro//devkitARM//bin'
    return os.path.join(path, prefix + 'nm') if path else (prefix + 'nm')


def LoadSymbols():
    out = subprocess.check_output([Nm(), LINKED]).decode()
    byName, byAddr = {}, {}
    for line in out.split('\n'):
        parts = line.split()
        if len(parts) == 3:
            addr = int(parts[0], 16)
            byName[parts[2]] = addr
            byAddr.setdefault(addr, []).append(parts[2])
    return byName, byAddr


def ParseSpriteAsm(path):
    """Pull each symbol's assembled bytes out of a grit-generated .s file."""
    out, current = {}, None
    for line in open(path):
        stripped = line.strip()
        match = re.match(r'^(g\w+):$', stripped)
        if match:
            current = match.group(1)
            out[current] = bytearray()
            continue
        if stripped.startswith('.byte') and current:
            out[current] += bytes(int(x, 16) for x in stripped[5:].split(','))
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    romPath = sys.argv[1]
    if not os.path.isfile(romPath):
        print('Error: no such rom: ' + romPath)
        return 1
    if not os.path.isfile(LINKED):
        print('Error: ' + LINKED + ' not found. Run scripts/make.py first, and run '
              'this from the Dynamic-Pokemon-Expansion directory.')
        return 1

    rom = open(romPath, 'rb').read()
    byName, byAddr = LoadSymbols()
    failures = []

    print('rom:  {} ({} bytes, {:.2f} MiB)'.format(romPath, len(rom), len(rom) / 1048576.0))
    if len(rom) > ROM_SIZE_LIMIT:
        failures.append('rom is {} bytes past the 0x{:X} hard cap'
                        .format(len(rom) - ROM_SIZE_LIMIT, ROM_SIZE_LIMIT))

    # 1. .rom2 must not have grown into the music patch.
    start, end = byName['__rom2_start'], byName['__rom2_end']
    print('.rom2: 0x{:08X} - 0x{:08X} ({} bytes)'.format(start, end, end - start))
    if end - 0x08000000 > MUSIC_PATCH_START:
        failures.append('.rom2 ends at file offset 0x{:X}, past the music patch at 0x{:X}'
                        .format(end - 0x08000000, MUSIC_PATCH_START))

    # 2. Every species pointer must still resolve to a correctly named symbol.
    for table, (stride, want) in sorted(POINTER_TABLES.items()):
        base = byName[table] - 0x08000000
        bad, inRom2 = 0, 0
        for i in range(NUM_SPECIES):
            pointer = struct.unpack_from('<I', rom, base + i * stride)[0]
            names = byAddr.get(pointer, [])
            if not any(want in n for n in names):
                bad += 1
            if start <= pointer < end:
                inRom2 += 1
        print('  {:<24} ok={:<5} broken={:<5} in .rom2={}'
              .format(table, NUM_SPECIES - bad, bad, inRom2))
        if bad:
            failures.append('{}: {} of {} pointers do not resolve to a {} symbol'
                            .format(table, bad, NUM_SPECIES, want))

    # 3. Sprite bytes in the rom must still match the source graphics.
    checked = mismatched = 0
    for directory in ('graphics/pokeicon', 'graphics/frontspr', 'graphics/backspr', 'graphics/castform'):
        for asmFile in glob(directory + '/*.s'):
            for name, data in ParseSpriteAsm(asmFile).items():
                if name not in byName:
                    continue
                offset = byName[name] - 0x08000000
                checked += 1
                if rom[offset:offset + len(data)] != bytes(data):
                    mismatched += 1
                    if mismatched <= 10:
                        print('  CORRUPT {} at 0x{:08X} ({})'.format(name, byName[name], asmFile))
    print('  sprite symbols byte-compared: {}, corrupt: {}'.format(checked, mismatched))
    if mismatched:
        failures.append('{} of {} sprite symbols were overwritten after DPE inserted them'
                        .format(mismatched, checked))

    print()
    if failures:
        print('FAILED:')
        for f in failures:
            print('  - ' + f)
        return 1

    print('PASSED: .rom2 data intact and every species pointer resolves.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""python -m tools.dexpage --out site"""

import argparse
import sys
from pathlib import Path

from .build import build
from .cparse import UnresolvedConditional
from .paths import Paths
from .rom import RomError


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the searchable Pokédex reference site.")
    parser.add_argument("--out", type=Path, default=Path("site"), help="output folder (default: site)")
    parser.add_argument("--cfru", type=Path, help="Complete-Fire-Red-Upgrade checkout (default: sibling folder)")
    parser.add_argument("--rom", type=Path, help="built game ROM (default: <cfru>/test.gba)")
    args = parser.parse_args()

    paths = Paths.default(cfru=args.cfru, rom=args.rom)
    try:
        build(paths, args.out)
    except (RomError, UnresolvedConditional, ValueError, KeyError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Wrote {args.out.resolve()} (ROM: {paths.rom})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

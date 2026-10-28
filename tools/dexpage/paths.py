from dataclasses import dataclass
from pathlib import Path

DPE_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    dpe: Path
    cfru: Path
    rom: Path

    @classmethod
    def default(cls, cfru: Path | None = None, rom: Path | None = None) -> "Paths":
        cfru = (cfru or DPE_ROOT.parent / "Complete-Fire-Red-Upgrade").resolve()
        return cls(DPE_ROOT, cfru, (rom or cfru / "test.gba").resolve())

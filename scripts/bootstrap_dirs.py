from __future__ import annotations

from pathlib import Path


def _write_dir(path: str) -> None:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    (p / ".gitkeep").touch(exist_ok=True)


for d in ["data/raw", "data/processed", "notebooks"]:
    _write_dir(d)

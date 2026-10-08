"""Masal tanimlari: her modul bir masal (SAYFALAR listesi)."""
from pathlib import Path


def tum_kimlikler():
    return sorted(p.stem for p in Path(__file__).parent.glob("*.py") if not p.stem.startswith("_"))

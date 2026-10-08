"""
Harita animasyonu senaryolari. Her modul bir konu (imparatorluk/donem) tanimlar.

Yeni senaryo yazmak icin: senaryolar/YAZIM_REHBERI.md
Yayin sirasi: senaryolar/sira.json
"""
from pathlib import Path


def tum_kimlikler():
    """Klasordeki tum senaryo kimlikleri (alt cizgiyle baslayanlar haric)."""
    return sorted(p.stem for p in Path(__file__).parent.glob("*.py")
                  if not p.stem.startswith("_"))

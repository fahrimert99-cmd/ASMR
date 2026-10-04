"""
Osmanli harita animasyonu icin cografi veri hazirlayici (tek seferlik).

Natural Earth (kamu malı / public domain) katmanlarini indirir, Osmanli
haritasinin gorunen bolgesine kirpar, sadelestirir ve renderer'in internetsiz
okuyacagi kucuk bir JSON uretir:

    veri/osmanli/harita.json
        kara_ince : 10m kara poligonlari (yakin cekim icin, ~0.4 km sadelestirme)
        kara_kaba : ayni kara, kaba (uzak cekim icin, ~3 km sadelestirme)
        goller    : dogal goller (baraj gölleri haric — 1683'te yoklardi)
        nehirler  : buyuk nehirler (Tuna, Nil, Firat, Dicle, Dinyeper ...)

Ayrica baslik yazi tiplerini (Cinzel, EB Garamond — SIL OFL) indirir:

    veri/fontlar/

Kullanim (yalnizca veri yenilenecekse; hazir JSON repoda bulunur):
    pip install shapely requests
    python scripts/osmanli_veri_hazirla.py
"""
import json
import sys
from pathlib import Path

import requests
from shapely.geometry import box, shape
from shapely.ops import unary_union

KOK = Path(__file__).resolve().parent.parent
HEDEF = KOK / "veri" / "osmanli" / "harita.json"
FONT_KLASOR = KOK / "veri" / "fontlar"
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
GF = "https://raw.githubusercontent.com/google/fonts/main/ofl/"

# Haritanin hicbir kamera acisinda disina cikilmayan genis kutu (boylam/enlem)
KUTU = box(-22.0, 2.0, 74.0, 60.0)

# 1683'te var olmayan / yapay su kutleleri
HARIC_GOLLER = {"Lake Razazah", "Lake Nasser", "Buhayrat ath Tharthar"}

# Natural Earth 50m nehir adlari -> cizilecek buyuk nehirler
NEHIRLER = {
    "Danube", "Donau", "Soroksari Duna", "Bratul Chillia", "Bratul Sulina",
    "Bratul Sfintu Gheorghe", "Nile", "Rosetta Branch", "Damietta Branch",
    "Euphrates", "Al Furat", "Firat", "Tigris", "Dicle", "Shatt al Arab",
    "Dniester", "Dnipro", "Dnepre", "Don", "Sava", "Drava", "Tisa", "Tisza",
    "Jordan", "Volga", "Vistula", "Po", "Rhône",
}


def _indir(ad: str) -> dict:
    onbellek = KOK / "veri" / "osmanli" / "_ne" / f"{ad}.geojson"
    if not onbellek.exists():
        onbellek.parent.mkdir(parents=True, exist_ok=True)
        print(f"  indiriliyor: {ad}")
        r = requests.get(NE + f"{ad}.geojson", timeout=180)
        r.raise_for_status()
        onbellek.write_bytes(r.content)
    return json.loads(onbellek.read_text(encoding="utf-8"))


def _yuvarla(halka, basamak=3):
    return [[round(x, basamak), round(y, basamak)] for x, y in halka]


def _poligonlar(geom, tol, min_alan):
    """(Multi)Polygon -> [[dis_halka, delik1, ...], ...] (sadelestirilmis)."""
    geom = geom.simplify(tol, preserve_topology=True)
    parcalar = getattr(geom, "geoms", [geom])
    cikis = []
    for p in parcalar:
        if p.geom_type != "Polygon" or p.area < min_alan:
            continue
        halkalar = [_yuvarla(p.exterior.coords)]
        for ic in p.interiors:
            if abs(_alan(ic.coords)) >= min_alan:
                halkalar.append(_yuvarla(ic.coords))
        cikis.append(halkalar)
    return cikis


def _alan(halka):
    s = 0.0
    pts = list(halka)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        s += x1 * y2 - x2 * y1
    return s / 2.0


def kara_hazirla():
    d = _indir("ne_10m_land")
    parcalar = []
    for f in d["features"]:
        g = shape(f["geometry"])
        if g.intersects(KUTU):
            parcalar.append(g.intersection(KUTU))
    kara = unary_union(parcalar)
    return (_poligonlar(kara, 0.004, 0.0004),   # ince: ~0.4 km, ~4 km2 alti adalar atilir
            _poligonlar(kara, 0.03, 0.01))      # kaba


def goller_hazirla():
    d = _indir("ne_10m_lakes")
    cikis = []
    for f in d["features"]:
        p = f["properties"]
        if p.get("featurecla") not in ("Lake", "Alkaline Lake"):
            continue
        if p.get("name") in HARIC_GOLLER:
            continue
        g = shape(f["geometry"])
        if not g.intersects(KUTU) or g.area < 0.008:
            continue
        cikis.extend(_poligonlar(g.intersection(KUTU), 0.004, 0.004))
    return cikis


def nehirler_hazirla():
    d = _indir("ne_50m_rivers_lake_centerlines")
    cikis = []
    for f in d["features"]:
        ad = (f["properties"].get("name") or "").strip()
        if ad not in NEHIRLER:
            continue
        g = shape(f["geometry"]).intersection(KUTU).simplify(0.01)
        for c in getattr(g, "geoms", [g]):
            if c.geom_type == "LineString" and len(c.coords) > 1:
                cikis.append(_yuvarla(c.coords))
    return cikis


def fontlari_indir():
    FONT_KLASOR.mkdir(parents=True, exist_ok=True)
    dosyalar = {
        "Cinzel.ttf": "cinzel/Cinzel%5Bwght%5D.ttf",
        "EBGaramond.ttf": "ebgaramond/EBGaramond%5Bwght%5D.ttf",
        "EBGaramond-Italic.ttf": "ebgaramond/EBGaramond-Italic%5Bwght%5D.ttf",
        "OFL-Cinzel.txt": "cinzel/OFL.txt",
        "OFL-EBGaramond.txt": "ebgaramond/OFL.txt",
    }
    for ad, yol in dosyalar.items():
        hedef = FONT_KLASOR / ad
        if hedef.exists():
            continue
        print(f"  font indiriliyor: {ad}")
        r = requests.get(GF + yol, timeout=120)
        r.raise_for_status()
        hedef.write_bytes(r.content)


def main():
    print("Natural Earth katmanlari hazirlaniyor...")
    ince, kaba = kara_hazirla()
    veri = {
        "kaynak": "Natural Earth (public domain) — naturalearthdata.com",
        "kara_ince": ince,
        "kara_kaba": kaba,
        "goller": goller_hazirla(),
        "nehirler": nehirler_hazirla(),
    }
    HEDEF.parent.mkdir(parents=True, exist_ok=True)
    HEDEF.write_text(json.dumps(veri, separators=(",", ":")), encoding="utf-8")
    nokta = sum(len(h) for p in ince for h in p)
    print(f"Yazildi: {HEDEF} ({HEDEF.stat().st_size // 1024} KB, "
          f"ince kara {len(ince)} poligon / {nokta} nokta)")
    fontlari_indir()
    print("Fontlar hazir:", FONT_KLASOR)


if __name__ == "__main__":
    sys.exit(main())

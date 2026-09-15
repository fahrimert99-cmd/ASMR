#!/usr/bin/env python3
"""Ortak modulleri eklentilere kopyalar.

Tarayici eklentileri paket yoneticisi kullanmadigi ve Manifest V3 uzaktan kod
yuklemeyi yasakladigi icin, paylasilan dosyalarin her eklentinin ICINDE
bulunmasi gerekir. Tek kaynak `ortak/` klasorudur; buradaki dosyalar asagidaki
eklentilere kopyalanir.

ONEMLI: Eklenti klasorlerindeki bu dosyalar URETILMISTIR. Duzenleme yapacaksaniz
`ortak/` altindakini duzenleyin, sonra bu betigi calistirin:

    python3 eklenti/esitle.py
"""
import filecmp
import shutil
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent
ORTAK = KOK / "ortak"
# Her eklentinin ortak/ altindan aldigi dosyalar farkli: toplu-uretim render
# motorunu paylasmaz, yalnizca gorunumu ayni tutmak icin stil dosyasini alir.
PAYLASIM = {
    "kurgu-canavari": [
        ("render.js", "js/render.js"),
        ("altyazi.js", "js/altyazi.js"),
        ("eslestirme.js", "js/eslestirme.js"),
        ("arka_plan.js", "js/arka_plan.js"),
        ("dashboard.css", "css/dashboard.css"),
        ("vendor/mediabunny.min.mjs", "vendor/mediabunny.min.mjs"),
        ("vendor/mp4-muxer.mjs", "vendor/mp4-muxer.mjs"),
        ("vendor/webm-muxer.mjs", "vendor/webm-muxer.mjs"),
    ],
    "gorsel-kurgu": [
        ("render.js", "js/render.js"),
        ("altyazi.js", "js/altyazi.js"),
        ("eslestirme.js", "js/eslestirme.js"),
        ("arka_plan.js", "js/arka_plan.js"),
        ("dashboard.css", "css/dashboard.css"),
        ("vendor/mediabunny.min.mjs", "vendor/mediabunny.min.mjs"),
        ("vendor/mp4-muxer.mjs", "vendor/mp4-muxer.mjs"),
        ("vendor/webm-muxer.mjs", "vendor/webm-muxer.mjs"),
    ],
    "toplu-uretim": [
        ("dashboard.css", "css/dashboard.css"),
    ],
}


def main() -> int:
    denetim = "--denetle" in sys.argv      # kopyalama, yalnizca farkliysa bildir
    farkli = []
    for eklenti, dosyalar in PAYLASIM.items():
        hedef_kok = KOK / eklenti
        if not hedef_kok.is_dir():
            print(f"atlandi (klasor yok): {eklenti}")
            continue
        for kaynak_ad, hedef_ad in dosyalar:
            kaynak = ORTAK / kaynak_ad
            hedef = hedef_kok / hedef_ad
            if not kaynak.is_file():
                print(f"HATA: ortak dosya yok: {kaynak}")
                return 1
            ayni = hedef.is_file() and filecmp.cmp(kaynak, hedef, shallow=False)
            if ayni:
                continue
            farkli.append(f"{eklenti}/{hedef_ad}")
            if not denetim:
                hedef.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(kaynak, hedef)

    if denetim:
        if farkli:
            print("Esitlenmemis dosyalar:\n  " + "\n  ".join(farkli))
            print("\nDuzeltmek icin: python3 eklenti/esitle.py")
            return 1
        print("Tum eklentiler ortak/ ile esitli.")
        return 0

    print(f"Esitlendi: {len(farkli)} dosya guncellendi." if farkli else "Zaten guncel.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

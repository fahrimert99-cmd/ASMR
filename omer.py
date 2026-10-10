"""
Cocuk animasyonu orkestratoru: "Omer Asil ve Kayip Yildiz" (~15 dk).

Avatar gorselinden (avatar/avatar.jpg) konusan, goz kirpan, ifade degistiren
bir cizgi film uretir. Anlatici Omer Asil'dir; arka plan hikayeye gore degisir
(oda, gunduz, aksam, gece, orman, yagmur, gokkusagi, yildizlar).

    python omer.py                                  # 15 dk, ses motoru: auto
    python omer.py --ses-motoru elevenlabs          # ElevenLabs (ELEVENLABS_API_KEY)
    python omer.py --metin-listesi                  # satir listesini yaz, cik
    python omer.py --onizleme 0:45                  # yalnizca bir araligi render et
    python omer.py --senaryo senaryolar/baska.yaml  # baska bir hikaye

Adimlar: senaryo -> satir satir seslendirme -> 15 dk'ya zamanlama -> ses
karisimi (anlatim + muzik + efekt + ortam) -> kare parametreleri (agiz, ifade,
kamera) -> paralel render -> mux.
"""
import argparse
import hashlib
import sys
from pathlib import Path

from src import KOK, ayarlari_yukle, cikti_klasoru
from src import cocuk_senaryo as m_senaryo
from src import cocuk_ses as m_ses
from src import cocuk_muzik as m_muzik
from src import cocuk_montaj as m_montaj


def _profil_ve_gorsel(profil_yolu: Path, en: int, boy: int):
    """Avatar profilini okur; gorseli en x boy'a 'cover' ile oturtup koordinatlari tasir."""
    import numpy as np
    import yaml
    from PIL import Image

    profil = yaml.safe_load(profil_yolu.read_text(encoding="utf-8"))
    img = Image.open(profil_yolu.parent / profil.get("gorsel", "avatar.jpg")).convert("RGB")
    w, h = img.size
    s = max(en / w, boy / h)
    yw, yh = int(round(w * s)), int(round(h * s))
    odak = profil.get("odak") or [w / 2, h * 0.42]
    ox = int(np.clip(odak[0] * s - en / 2, 0, yw - en))
    oy = int(np.clip(odak[1] * s - boy * 0.42, 0, yh - boy))
    img = img.resize((yw, yh), Image.LANCZOS).crop((ox, oy, ox + en, oy + boy))

    def p(nokta):
        return [nokta[0] * s - ox, nokta[1] * s - oy]

    yeni = dict(profil)
    yeni["odak"] = p(odak)
    yeni["gogus_y"] = float(profil.get("gogus_y", h * 0.68)) * s - oy
    yeni["gozler"] = [{"ust": [p(q) for q in g["ust"]], "alt": [p(q) for q in g["alt"]]}
                      for g in profil.get("gozler", [])]
    if profil.get("agiz"):
        a = dict(profil["agiz"])
        a["cizgi"] = [p(q) for q in a["cizgi"]]
        a["acilma_sol"] = a["acilma_sol"] * s - ox
        a["acilma_sag"] = a["acilma_sag"] * s - ox
        a["tepe_x"] = a["tepe_x"] * s - ox
        a["cene_y"] = a["cene_y"] * s - oy
        a["acik_max"] = a.get("acik_max", 15) * s
        yeni["agiz"] = a
    yeni["kaslar"] = [[k[0] * s - ox, k[1] * s - oy, k[2] * s, k[3] * s]
                      for k in profil.get("kaslar", [])]
    yeni["duvar_alt"] = [p(q) for q in profil.get("duvar_alt", [[0, boy], [en, boy]])]
    return yeni, np.asarray(img, dtype=np.float32)


def _ayrim_hazirla(profil, gorsel, klasor: Path) -> Path:
    """Duvar ayrimini (bir kez) hesaplayip .npz olarak onbellege yazar."""
    import numpy as np

    h = hashlib.sha1(gorsel.tobytes() + repr(profil["duvar_alt"]).encode()).hexdigest()[:12]
    yol = klasor / f"ayrim_{h}.npz"
    if not yol.exists():
        alfa, duvar, on = m_montaj.duvar_ayir(gorsel, profil["duvar_alt"])
        np.savez(yol, gorsel=gorsel, alfa=alfa, duvar=duvar, on=on)
    return yol


def _aralik(metin: str):
    """'0:45' ya da '120:150' -> (bas_sn, bit_sn)."""
    a, b = metin.split(":")
    return float(a), float(b)


def main():
    p = argparse.ArgumentParser(description="Omer Asil cocuk animasyonu")
    p.add_argument("--senaryo", default="senaryolar/omer_asil_kayip_yildiz.yaml")
    p.add_argument("--profil", default="avatar/avatar.yaml")
    p.add_argument("--sure", type=float, default=None, help="Hedef sure (sn); bos ise senaryodaki")
    p.add_argument("--ses-motoru", default="", help="auto | dosya | elevenlabs | edge | piper")
    p.add_argument("--yedeksiz", action="store_true",
                   help="Secilen ses motoru calismazsa yedek sese dusme, dur (ornek: ElevenLabs)")
    p.add_argument("--metin-listesi", action="store_true",
                   help="Satir listesini (id + metin) yazip cik - harici seslendirme icin")
    p.add_argument("--onizleme", default="", help="Yalnizca bir araligi render et, ornek 0:45")
    p.add_argument("--yukle", action="store_true", help="Bitince YouTube'a yukle")
    args = p.parse_args()

    ayar = ayarlari_yukle()
    a = ayar.setdefault("cocuk", {})
    if args.ses_motoru:
        a["ses_motoru"] = args.ses_motoru
    if args.yedeksiz:
        a["yedek"] = False
    en, boy = a.get("cozunurluk", [720, 1280])
    fps = int(a.get("fps", 24))

    c = m_senaryo.yukle(KOK / args.senaryo)
    cikti = cikti_klasoru("omer-asil")
    if args.metin_listesi:
        yol = cikti / "satirlar.tsv"
        yol.write_text(m_senaryo.metin_ozeti(c), encoding="utf-8")
        print(f"{len(c.satirlar)} satir yazildi: {yol}\n"
              f"Her satiri <id>.mp3 olarak '{a.get('ses_klasoru', 'sesler/omer_asil')}' "
              f"klasorune koyup --ses-motoru dosya ile calistirin.")
        return
    print(f"Omer Asil  |  {len(c.bolumler)} bolum, {len(c.satirlar)} satir  |  "
          f"hedef {args.sure or c.hedef:.0f} sn")

    print("1/5  Satirlar seslendiriliyor...")
    motor = m_ses.seslendir(c, ayar, cikti / "ses")
    print(f"     ses motoru: {motor}  |  toplam konusma "
          f"{sum(s.sure for s in c.satirlar):.0f} sn")
    m_senaryo.zamanla(c, args.sure)
    print(f"     zaman cizelgesi: {c.toplam:.1f} sn ({c.toplam / 60:.1f} dk)")

    print("2/5  Ses karisimi (anlatim + muzik + efekt + ortam)...")
    ses, agiz, konusma = m_muzik.karistir(c, ayar, cikti / "ses" / "karisim.wav", fps)

    print("3/5  Animasyon parametreleri ve duvar ayrimi...")
    profil, gorsel = _profil_ve_gorsel(KOK / args.profil, int(en), int(boy))
    ayrim = _ayrim_hazirla(profil, gorsel, cikti)
    P = m_montaj.kare_parametreleri(c, agiz, konusma, fps)

    print("4/5  Kareler render ediliyor...")
    aralik = _aralik(args.onizleme) if args.onizleme else None
    ad = "omer_asil_onizleme.mp4" if aralik else "omer_asil_kayip_yildiz.mp4"
    video = m_montaj.render(c, profil, ayrim, P, ses, cikti / "video" / ad, ayar, aralik,
                            kapak=None if aralik else cikti / "video" / "kapak.jpg")

    baslik = a.get("baslik", f"{c.baslik} {c.alt_baslik}".strip())
    if (args.yukle or ayar.get("yukleme", {}).get("aktif")) and not aralik:
        from src import yukleme as m_yukleme
        print("5/5  YouTube'a yukleniyor...")
        url = m_yukleme.yukle(str(video), baslik,
                              f"{baslik}\n\n#cocuk #masal #cizgifilm #omerasil", ayar)
        print(f"     Yuklendi: {url}")
    else:
        print("5/5  Yukleme atlandi.")
    if not video.exists() or video.stat().st_size == 0:
        raise RuntimeError(f"Video olusmadi: {video}")
    print(f"\nBITTI ✅  {video.resolve()} ({video.stat().st_size // (1024 * 1024)} MB, "
          f"ses: {motor})")


if __name__ == "__main__":
    sys.exit(main())

"""
Masal doğrulayıcı: yeni bir masal (özellikle haftalık rutinin yazdığı) yayına
girmeden önce yapı, metin, ses ipuçları ve sahne kodunun çalıştığını denetler.

    python masal.py --masal keloglan_kapi --kontrol
"""
import re
import traceback

from src.masal_motoru import cumlelere_bol
from src.masal_ses import EFEKTLER, ruh_halleri

ZAMAN_RE = re.compile(r"^c(\d+)([+-]\d+(\.\d+)?)?$")


def yapisal(masal):
    """(hatalar, uyarilar)."""
    H, U = [], []
    mod = masal.mod
    if not getattr(mod, "BASLIK", None):
        H.append("BASLIK tanimli degil")
    yt = getattr(mod, "YOUTUBE", None) or {}
    if not yt.get("baslik"):
        H.append("YOUTUBE['baslik'] yok")
    elif len(yt["baslik"]) > 100:
        H.append("YOUTUBE['baslik'] 100 karakteri asiyor")
    if not yt.get("aciklama"):
        U.append("YOUTUBE['aciklama'] bos")
    if not yt.get("etiketler"):
        U.append("YOUTUBE['etiketler'] bos")
    sayfalar = getattr(mod, "SAYFALAR", [])
    if not 8 <= len(sayfalar) <= 16:
        U.append(f"{len(sayfalar)} sayfa var (onerilen 10-14)")
    ruhlar = set(ruh_halleri())
    gorulen = set()
    for i, t in enumerate(sayfalar):
        ad = t.get("kimlik", f"#{i}")
        if not t.get("kimlik"):
            H.append(f"sayfa {i}: 'kimlik' yok")
        elif ad in gorulen:
            H.append(f"sayfa '{ad}': kimlik tekrar ediyor")
        gorulen.add(ad)
        sahne = t.get("sahne")
        if not (sahne is not None and callable(getattr(sahne, "arka", None)) and callable(getattr(sahne, "on", None))):
            H.append(f"sayfa '{ad}': sahne arka() ve on() metotlarini icermeli")
        if t.get("muzik", "koy") not in ruhlar:
            H.append(f"sayfa '{ad}': bilinmeyen muzik '{t.get('muzik')}' (secenekler: {', '.join(sorted(ruhlar))})")
        metin = t.get("metin")
        cumleler = cumlelere_bol(metin) if metin else []
        if metin:
            n = len(metin.split())
            if n < 8 or n > 48:
                U.append(f"sayfa '{ad}': {n} kelime (onerilen 15-40)")
            if len(t.get("konusanlar") or []) > len(cumleler):
                H.append(f"sayfa '{ad}': konusanlar ({len(t['konusanlar'])}) cumle sayisindan ({len(cumleler)}) fazla")
        elif i == 0 and not t.get("seslendirme"):
            U.append("kapak sayfasinda 'seslendirme' metni yok (ör. 'Bir varmış, bir yokmuş…')")
        for kayit in t.get("sesler", []):
            if not isinstance(kayit, (tuple, list)) or len(kayit) < 2:
                H.append(f"sayfa '{ad}': ses ipucu (ad, zaman[, secenekler]) olmali: {kayit}")
                continue
            if kayit[0] not in EFEKTLER:
                H.append(f"sayfa '{ad}': bilinmeyen efekt '{kayit[0]}'")
            for z in [kayit[1]] + ([kayit[2].get("sure")] if len(kayit) > 2 and isinstance(kayit[2], dict) else []):
                if z is None or isinstance(z, (int, float)):
                    continue
                if isinstance(z, str) and z.startswith("k:"):
                    continue
                mm = ZAMAN_RE.match(str(z))
                if not mm:
                    H.append(f"sayfa '{ad}': gecersiz ses zamani '{z}' (sayi, 'cN', 'cN+x' ya da 'k:kelime|yedek')")
                elif int(mm.group(1)) >= max(1, len(cumleler)):
                    U.append(f"sayfa '{ad}': '{z}' cumle {mm.group(1)} yok")
    spec = getattr(mod, "SHORTS", None)
    ids = [t.get("kimlik") for t in sayfalar]
    if not spec:
        U.append("SHORTS tanimli degil (varsayilan: ortadaki iki sayfa)")
    else:
        eksik = [a for a in spec.get("sayfalar", []) if a not in ids]
        if eksik:
            H.append(f"SHORTS sayfalari yok: {eksik}")
        else:
            idx = sorted(ids.index(a) for a in spec.get("sayfalar", []))
            if idx and idx[-1] - idx[0] + 1 > 3:
                U.append("SHORTS 3'ten fazla sayfayi kapsiyor (60 sn'yi asabilir)")
    if not 90 <= masal.SURE <= 230:
        U.append(f"toplam sure {masal.SURE:.0f} sn (onerilen 120-200; seslendirmeyle uzar)")
    return H, U


def sahne_denemesi(masal):
    """Her sayfanin arka plani ve birkac karesi hatasiz cizilmeli -> hata listesi."""
    H = []
    for s in masal.sayfalar:
        ad = s.t.get("kimlik")
        try:
            s.arka_resmi()
            for u in (0.02, 0.5, 0.98):
                s.kare(s.sure * u)
        except Exception as e:                        # noqa: BLE001 - kullaniciya tam iz
            iz = traceback.format_exc().strip().splitlines()[-3:]
            H.append(f"sayfa '{ad}': sahne cizilemedi: {e!r} | " + " / ".join(x.strip() for x in iz))
    try:
        from src.masal_shorts import ShortsKurgu
        k = ShortsKurgu(masal)
        k.kare(1.0)
    except Exception as e:                            # noqa: BLE001
        H.append(f"Shorts karesi cizilemedi: {e!r}")
    return H

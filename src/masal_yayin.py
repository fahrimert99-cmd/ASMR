"""
Masal yayın kuyruğu + YouTube'a zamanlı yükleme (yatay masal + dikey Shorts tanıtımı).

Kuyruk: masallar/sira.json  {"sira": [...], "yayinlanan": {kimlik: {...}}}
Harita hattının kuyruk ve yükleme kodunu (src/harita_yayin.py) kullanır.

Yükleme sırası: önce yatay masal yüklenir, ardından Shorts açıklamasına ana videonun
bağlantısı konarak Shorts yüklenir. "zamanli" modda ikisi de gizli yüklenir ve
ertesi gün seçilen saatte (varsayılan 19:00, Europe/Istanbul) kendiliğinden yayınlanır.
"""
from datetime import datetime, timezone
from pathlib import Path

from src.harita_yayin import YuklemeAtlandi, _yukleyici, bekleyenler, isaretle, kimlik_var, sira_oku, yayin_zamani

KOK = Path(__file__).resolve().parent.parent
SIRA = KOK / "masallar" / "sira.json"
KATEGORI = "1"                                       # Film & Animasyon


def kuyruk():
    return sira_oku(SIRA)


def siradaki():
    b = bekleyenler(yol=SIRA)
    return b[0] if b else None


def masal_metni(masal):
    """Sayfa metinlerinden masalin tam metni (aciklama icin)."""
    parcalar = [s.metin for s in masal.sayfalar if s.metin]
    return "\n\n".join(parcalar)


def _etiket_satiri(etiketler, n=8):
    return " ".join("#" + e.replace(" ", "").replace("'", "").replace("’", "") for e in etiketler[:n])


def youtube_metni(masal, tur="ana", ana_url=None, ses_bilgisi=None):
    """(baslik, aciklama, etiketler). tur: 'ana' (yatay masal) | 'shorts'."""
    mod = masal.mod
    yt = getattr(mod, "YOUTUBE", {}) or {}
    baslik_ad = getattr(mod, "BASLIK", masal.kimlik)
    etiketler = list(dict.fromkeys(list(yt.get("etiketler", [])) + ["masal", "çocuk masalları", "resimli masal"]))
    emek = ("Resimler, animasyon, müzik ve ses efektleri tamamen kodla üretilmiştir."
            + (f" Seslendirme: {ses_bilgisi}." if ses_bilgisi else ""))
    if tur == "shorts":
        baslik = yt.get("shorts_baslik") or f"{baslik_ad} 📖 #Shorts"
        if "#shorts" not in baslik.lower():
            baslik = baslik[:91] + " #Shorts"
        satirlar = [yt.get("shorts_aciklama") or yt.get("aciklama", "").split(".")[0] + ".", ""]
        if ana_url:
            satirlar += [f"▶ Masalın tamamı: {ana_url}", ""]
        satirlar += [emek, "", _etiket_satiri(etiketler + ["Shorts"])]
        return baslik[:100], "\n".join(satirlar).strip()[:4900], etiketler + ["Shorts"]
    baslik = yt.get("baslik") or f"{baslik_ad} | Resimli Masal"
    satirlar = [yt.get("aciklama", "").strip(), "", "📖 Masal:", "", masal_metni(masal), "", emek, "",
                _etiket_satiri(etiketler)]
    return baslik[:100], "\n".join(satirlar).strip()[:4900], etiketler


def yukle(masal, video: Path, shorts: Path = None, mod="zamanli", saat="19:00", ses_bilgisi=None) -> dict:
    """Masali (ve varsa Shorts'u) yukler. mod: zamanli | hemen | gizli."""
    if not kimlik_var():
        raise YuklemeAtlandi("YOUTUBE_TOKEN_JSON (ya da token.json) bulunamadi")
    yy = _yukleyici()
    yayin = yayin_zamani(saat) if mod == "zamanli" else None
    gizlilik = {"zamanli": "private", "hemen": "public", "gizli": "private"}[mod]
    cocuk = bool(getattr(masal.mod, "COCUKLARA_YONELIK", True))
    b, a, e = youtube_metni(masal, "ana", ses_bilgisi=ses_bilgisi)
    vid = yy.video_yukle(video_yolu=str(video), baslik=b, aciklama=a, etiketler=e, kategori_id=KATEGORI,
                         gizlilik=gizlilik, yayin_zamani=yayin, cocuklara_ozel=cocuk)
    bilgi = {"video_id": vid, "url": f"https://youtu.be/{vid}", "baslik": b,
             "yuklenme": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "yayin": yayin or ("hemen" if mod == "hemen" else "gizli")}
    if shorts is not None and Path(shorts).exists():
        b2, a2, e2 = youtube_metni(masal, "shorts", ana_url=bilgi["url"], ses_bilgisi=ses_bilgisi)
        sid = yy.video_yukle(video_yolu=str(shorts), baslik=b2, aciklama=a2, etiketler=e2, kategori_id=KATEGORI,
                             gizlilik=gizlilik, yayin_zamani=yayin, cocuklara_ozel=cocuk)
        bilgi["shorts_id"] = sid
        bilgi["shorts_url"] = f"https://youtube.com/shorts/{sid}"
    return bilgi


def isaretle_yayinlandi(kimlik, bilgi):
    isaretle(kimlik, bilgi, yol=SIRA)

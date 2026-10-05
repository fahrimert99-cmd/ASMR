"""
Harita Shorts yayin kuyrugu + YouTube'a zamanli yukleme.

Kuyruk: senaryolar/sira.json
    {
      "sira": ["osmanli", "roma", ...],          # yayin sirasi
      "yayinlanan": {"osmanli": {"video_id": "...", "yuklenme": "...", "yayin": "..."}}
    }

Yukleme, repodaki scripts/youtube_yukle.py'yi kullanir (YOUTUBE_TOKEN_JSON /
YOUTUBE_OAUTH_JSON ortam degiskenleri ya da kokteki token.json).

"zamanli" modda video GIZLI yuklenir ve YouTube onu ertesi gun belirtilen saatte
(varsayilan 19:00, Europe/Istanbul) kendiliginden yayinlar; arada YouTube
Studio'dan kontrol edip durdurabilirsiniz.
"""
import importlib.util
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
SIRA = KOK / "senaryolar" / "sira.json"


class YuklemeAtlandi(RuntimeError):
    """Kimlik bilgisi yok: video uretildi ama yuklenmedi."""


# ------------------------------------------------------------------ kuyruk
def sira_oku() -> dict:
    if not SIRA.exists():
        return {"sira": [], "yayinlanan": {}}
    d = json.loads(SIRA.read_text(encoding="utf-8"))
    d.setdefault("sira", [])
    d.setdefault("yayinlanan", {})
    return d


def sira_yaz(d: dict):
    SIRA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bekleyenler(d=None):
    d = d or sira_oku()
    return [k for k in d["sira"] if k not in d["yayinlanan"]]


def siradaki():
    b = bekleyenler()
    return b[0] if b else None


def isaretle(kimlik: str, bilgi: dict):
    d = sira_oku()
    d["yayinlanan"][kimlik] = bilgi
    if kimlik not in d["sira"]:
        d["sira"].append(kimlik)
    sira_yaz(d)


# ------------------------------------------------------------------ zaman
def yayin_zamani(saat="19:00", bolge="Europe/Istanbul", en_az_saat=18.0) -> str:
    """Ertesi gun 'saat'te (yerel) yayin; en az 'en_az_saat' kontrol penceresi birakir.

    Donus: YouTube'un bekledigi UTC ISO 8601 ("2026-10-05T16:00:00Z").
    """
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(bolge)
    except Exception:                                    # tzdata yoksa Turkiye = UTC+3
        tz = timezone(timedelta(hours=3))
    simdi = datetime.now(tz)
    hh, mm = (int(x) for x in saat.split(":"))
    hedef = (simdi + timedelta(days=1)).replace(hour=hh, minute=mm, second=0, microsecond=0)
    while (hedef - simdi).total_seconds() < en_az_saat * 3600:
        hedef += timedelta(days=1)
    return hedef.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------ metin
def tr_baslik(metin: str) -> str:
    """Turkce buyuk harfli basligi kelime basi buyuk hale getirir.

    "LATİUM'UN BİRLEŞMESİ" -> "Latium'un Birleşmesi", "I. PÖN SAVAŞI" -> "I. Pön Savaşı"
    (str.title() Turkce I/İ harflerini ve kesme isaretini bozar).
    """
    kelimeler = []
    for k in metin.split(" "):
        if re.fullmatch(r"[IVXLC]+\.?", k):              # Roma rakamlari aynen kalir
            kelimeler.append(k)
            continue
        kucuk = k.replace("I", "ı").replace("İ", "i").lower()
        if kucuk[:1].isalpha():
            ilk = {"i": "İ", "ı": "I"}.get(kucuk[0], kucuk[0].upper())
            kucuk = ilk + kucuk[1:]
        kelimeler.append(kucuk)
    return " ".join(kelimeler)


def _tr_sayi(x, ondalik=0):
    s = f"{x:,.{ondalik}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def youtube_metni(S, alan_km2: float):
    """(baslik, aciklama, etiketler) — senaryonun YOUTUBE alanindan + otomatik ozet."""
    yt = S.YOUTUBE
    baslik = yt.get("baslik") or f"{S.BASLIK} ({S.yil_araligi()}) #Shorts"
    if "#shorts" not in baslik.lower():
        baslik = (baslik + " #Shorts") if len(baslik) <= 92 else baslik
    satirlar = [yt.get("aciklama", "").strip(), "", "📜 Dönüm noktaları:"]
    for o in S.OLAYLAR:
        satirlar.append(f"• {S.yil_metni(o['yil'])} · {tr_baslik(o['baslik'])} — {o['alt']}")
    if alan_km2 >= 1e6:
        alan = f"≈ {_tr_sayi(alan_km2 / 1e6, 2)} milyon km²"
    else:
        alan = f"≈ {_tr_sayi(round(alan_km2 / 1000) * 1000)} km²"
    satirlar += [
        "",
        f"🗺️ Haritadaki en geniş yüzölçümü: {alan}",
        "Sınırlar 20 saniyelik anlatım için özetlenmiş yaklaşık sınırlardır.",
        "",
        "Harita verisi: Natural Earth (kamu malı). Görüntü, müzik ve ses efektleri tamamen kodla üretilmiştir.",
        "",
    ]
    etiketler = list(dict.fromkeys(list(yt.get("etiketler", [])) +
                                   ["tarih", "harita", "tarihi harita", "Shorts"]))
    satirlar.append(" ".join("#" + e.replace(" ", "").replace("'", "") for e in etiketler[:8]))
    aciklama = "\n".join(satirlar).strip()
    return baslik[:100], aciklama[:4900], etiketler


# ------------------------------------------------------------------ yukleme
def _yukleyici():
    yol = KOK / "scripts" / "youtube_yukle.py"
    spec = importlib.util.spec_from_file_location("youtube_yukle", yol)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def kimlik_var() -> bool:
    return bool(os.environ.get("YOUTUBE_TOKEN_JSON", "").strip()) or (KOK / "token.json").exists()


def yukle(S, video: Path, alan_km2: float, mod="zamanli", saat="19:00") -> dict:
    """Videoyu yukler. mod: zamanli (gizli + publishAt) | hemen (herkese acik) | gizli."""
    if not kimlik_var():
        raise YuklemeAtlandi("YOUTUBE_TOKEN_JSON (ya da token.json) bulunamadi")
    baslik, aciklama, etiketler = youtube_metni(S, alan_km2)
    yayin = yayin_zamani(saat) if mod == "zamanli" else None
    gizlilik = {"zamanli": "private", "hemen": "public", "gizli": "private"}[mod]
    yy = _yukleyici()
    video_id = yy.video_yukle(
        video_yolu=str(video), baslik=baslik, aciklama=aciklama, etiketler=etiketler,
        kategori_id="27", gizlilik=gizlilik, yayin_zamani=yayin,
    )
    return {
        "video_id": video_id,
        "url": f"https://youtube.com/shorts/{video_id}",
        "yuklenme": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "yayin": yayin or ("hemen" if mod == "hemen" else "gizli"),
        "baslik": baslik,
    }

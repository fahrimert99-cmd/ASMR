"""
Profesyonel YouTube meta verisi ureteci (iki dilli: TR + EN).

Her gunku ASMR videosuna OZGUN, SEO dostu bir baslik/aciklama/etiket seti
uretir (YouTube ayni basligi tekrar tekrar kullanmayi cezalandirir). Cikti
bir meta.json dosyasina yazilir; youtube_yukle.py --meta ile okur.

Kullanim:
    python scripts/video_meta.py --tema yagmur --tur asmr --sure 1800 --cikti meta.json
    python scripts/video_meta.py --tur klip --tema "" --cikti meta.json
"""
import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Tema -> (TR ad, EN ad, emoji, ekstra etiketler)
TEMALAR = {
    "yagmur":  ("Yağmur Sesi",        "Rain Sounds",         "🌧️", ["yağmur", "rain", "rain sounds", "yağmur sesi"]),
    "okyanus": ("Okyanus Dalgaları",  "Ocean Waves",         "🌊", ["okyanus", "deniz", "ocean", "waves", "sea sounds"]),
    "somine":  ("Şömine Sesi",        "Fireplace Crackling", "🔥", ["şömine", "ateş", "fireplace", "campfire", "crackling fire"]),
    "ates":    ("Şömine Sesi",        "Fireplace Crackling", "🔥", ["şömine", "ateş", "fireplace", "campfire", "crackling fire"]),
    "gece":    ("Gece Sesleri",       "Night Ambience",      "🌙", ["gece", "orman", "night", "forest", "crickets"]),
    "ruzgar":  ("Rüzgar Sesi",        "Wind Sounds",         "🌬️", ["rüzgar", "wind", "wind sounds"]),
    "beyaz":   ("Beyaz Gürültü",      "White Noise",         "⚪", ["beyaz gürültü", "white noise"]),
    "pembe":   ("Pembe Gürültü",      "Pink Noise",          "🎧", ["pembe gürültü", "pink noise"]),
    "kahve":   ("Kahverengi Gürültü", "Brown Noise",         "🟤", ["kahverengi gürültü", "brown noise"]),
}

# Tema bilinmiyorsa / klip birlestirmede tema verilmediyse genel set.
GENEL = ("Rahatlatıcı", "Relaxing Sounds", "🌙",
         ["asmr", "rahatlama", "relaxation"])

AYLAR = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def _tr_tarih() -> str:
    """Turkiye saatine gore '3 Eylül 2026' formatinda tarih."""
    try:
        from zoneinfo import ZoneInfo
        simdi = datetime.now(ZoneInfo("Europe/Istanbul"))
    except Exception:
        simdi = datetime.now(timezone.utc) + timedelta(hours=3)  # TR = UTC+3
    return f"{simdi.day} {AYLAR[simdi.month]} {simdi.year}"


def _tema_bilgi(tema: str):
    anahtar = (tema or "").strip().lower()
    return TEMALAR.get(anahtar, GENEL)


def meta_uret(tema: str, tur: str, sure: int) -> dict:
    tr_ad, en_ad, emoji, tema_etiketleri = _tema_bilgi(tema)
    tarih = _tr_tarih()
    dk = max(1, round(int(sure) / 60))

    # --- Baslik (<=100 karakter; YouTube fazlasini keser) ---
    baslik = f"{emoji} {tr_ad} ASMR — Rahatlama & Uyku | {en_ad} for Sleep · {tarih}"
    baslik = baslik[:100]

    # --- Aciklama (iki dilli) ---
    aciklama = (
        f"{tr_ad} ASMR ile rahatla ve huzurla uykuya dal. Yaklaşık {dk} dakikalık "
        f"kesintisiz, telifsiz ambient ses. Kulaklıkla dinlemeni öneririm. 🎧\n\n"
        f"Relax and drift into a peaceful sleep with {en_ad} ASMR. About {dk} minutes "
        f"of seamless, copyright-free ambient sound. Best experienced with headphones. 🎧\n\n"
        f"⏱️ İpucu: Uyku, çalışma, meditasyon ve odaklanma için idealdir.\n"
        f"⏱️ Great for sleep, study, meditation and focus.\n\n"
        f"▶ Her gün yeni ASMR için abone ol / Subscribe for daily ASMR & relaxation.\n\n"
        f"#asmr #rahatlama #uyku #sleep #relaxing #ambient #whitenoise #sleepsounds"
    )

    # --- Etiketler (iki dilli; youtube_yukle.py 500 karaktere kirpar) ---
    etiketler = (tema_etiketleri + [
        "asmr", "rahatlama", "uyku", "relaxing", "sleep", "sleep sounds",
        "meditation", "ambient", "relaxing sounds", "uyku sesleri",
        "study music", "focus", "calm", "sakinleştirici",
    ])
    # Tekrarları koru-sıralı temizle
    gorulen, temiz = set(), []
    for e in etiketler:
        k = e.lower()
        if k not in gorulen:
            gorulen.add(k)
            temiz.append(e)

    return {"baslik": baslik, "aciklama": aciklama, "etiketler": temiz}


def main():
    p = argparse.ArgumentParser(description="YouTube meta verisi uret (TR+EN)")
    p.add_argument("--tema", default="", help="yagmur/okyanus/somine/gece/... (bos = genel)")
    p.add_argument("--tur", default="asmr", choices=["asmr", "klip"],
                   help="Uretim turu (yalnizca bilgi amacli)")
    p.add_argument("--sure", type=int, default=1800, help="Video suresi (saniye)")
    p.add_argument("--cikti", default="meta.json", help="Yazilacak JSON yolu")
    args = p.parse_args()

    meta = meta_uret(args.tema, args.tur, args.sure)
    Path(args.cikti).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print("🎬 Üretilen meta veri:")
    print(f"   Başlık : {meta['baslik']}")
    print(f"   Etiket : {', '.join(meta['etiketler'][:8])} ...")
    print(f"   -> {args.cikti}")

    # GitHub Actions is akisinda ozet olarak goster.
    ozet = os.environ.get("GITHUB_STEP_SUMMARY")
    if ozet:
        with open(ozet, "a", encoding="utf-8") as f:
            f.write(f"### 🎬 Video meta verisi\n\n")
            f.write(f"- **Başlık:** {meta['baslik']}\n")
            f.write(f"- **Etiket sayısı:** {len(meta['etiketler'])}\n")


if __name__ == "__main__":
    main()

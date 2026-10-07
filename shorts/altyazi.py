"""
Kliplere Turkce altyazi yazar (burn-in).

AI-Youtube-Shorts-Generator'in yerel modu klibi keser ve dikeye cevirir ama
altyaziyi videoya yazmaz. Bu modul Whisper segmentlerini kisa parcalara
(TikTok/Reels tarzi 2-4 kelime) boler, Pillow ile cizer, OpenCV ile karelere
bindirir; sonra ffmpeg ile sesi ekleyip H.264'e cevirir (telefon/Instagram/
TikTok uyumlu).

ffmpeg'in libass destegine ihtiyac duymaz; Windows/macOS/Linux'ta ayni calisir.
"""
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Turkce karakterleri (s, g, i, o, u, c) destekleyen yaygin sistem fontlari.
FONT_ADAYLARI = [
    # Windows
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    # macOS
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]

MAKS_KELIME = 4
MAKS_KARAKTER = 26


def font_bul(tercih: Optional[str] = None) -> Optional[str]:
    """Kullanilabilir ilk font dosyasini dondurur (yoksa None)."""
    for yol in ([tercih] if tercih else []) + FONT_ADAYLARI:
        if yol and os.path.exists(yol):
            return yol
    return None


def kliple_kesis(segmentler: List[Dict], bas: float, son: float) -> List[Dict]:
    """Tum videonun segmentlerinden klip araligina dusenleri, klibe gore
    (0'dan baslayan) zamanlarla dondurur."""
    sonuc = []
    for s in segmentler:
        s_bas, s_son = float(s["start"]), float(s["end"])
        if s_son <= bas or s_bas >= son:
            continue
        metin = (s.get("text") or "").strip()
        if not metin:
            continue
        sonuc.append({
            "start": max(0.0, s_bas - bas),
            "end": min(son, s_son) - bas,
            "text": metin,
        })
    return sonuc


def parcala(segmentler: List[Dict]) -> List[Dict]:
    """Segmentleri ekranda okunur kisa parcalara boler; sure, karakter
    sayisina orantili dagitilir."""
    parcalar = []
    for s in segmentler:
        kelimeler = s["text"].split()
        if not kelimeler:
            continue
        gruplar, grup = [], []
        for k in kelimeler:
            aday = " ".join(grup + [k])
            if grup and (len(grup) >= MAKS_KELIME or len(aday) > MAKS_KARAKTER):
                gruplar.append(" ".join(grup))
                grup = []
            grup.append(k)
        if grup:
            gruplar.append(" ".join(grup))

        toplam = sum(len(g) for g in gruplar) or 1
        sure = max(0.0, s["end"] - s["start"])
        t = s["start"]
        for g in gruplar:
            d = sure * len(g) / toplam
            parcalar.append({"start": t, "end": t + d, "text": g})
            t += d
    return parcalar


def tr_buyuk(metin: str) -> str:
    """Turkce kurallariyla buyuk harf: i -> İ, ı -> I (str.upper() i'yi I yapar)."""
    return metin.replace("i", "İ").replace("ı", "I").upper()


def _yazi_gorseli(metin: str, genislik: int, font_yolu: Optional[str]):
    """Altyazi parcasini seffaf RGBA gorsel olarak cizer (beyaz yazi, siyah
    kontur), numpy dizisi olarak dondurur."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    boyut = max(24, int(genislik * 0.075))
    kontur = max(2, boyut // 12)
    if font_yolu:
        font = ImageFont.truetype(font_yolu, boyut)
    else:
        font = ImageFont.load_default(size=boyut)

    if os.getenv("ALTYAZI_BUYUK_HARF", "1") == "1":
        metin = tr_buyuk(metin)

    cizici = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    x0, y0, x1, y1 = cizici.textbbox((0, 0), metin, font=font, stroke_width=kontur)
    w, h = x1 - x0 + 2 * kontur, y1 - y0 + 2 * kontur

    # Cok uzun satirlari klip genisligine sigdir.
    maks_w = int(genislik * 0.92)
    gorsel = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(gorsel).text(
        (kontur - x0, kontur - y0), metin, font=font,
        fill=(255, 255, 255, 255), stroke_width=kontur, stroke_fill=(0, 0, 0, 255),
    )
    if w > maks_w:
        oran = maks_w / w
        gorsel = gorsel.resize((maks_w, max(1, int(h * oran))), Image.LANCZOS)
    return np.array(gorsel)


def _bindir(kare, rgba, cx: int, cy: int) -> None:
    """RGBA gorseli BGR kareye (yerinde) alfa karisimla bindirir."""
    import numpy as np

    h, w = rgba.shape[:2]
    H, W = kare.shape[:2]
    x0, y0 = max(0, cx - w // 2), max(0, cy - h // 2)
    x1, y1 = min(W, x0 + w), min(H, y0 + h)
    parca = rgba[: y1 - y0, : x1 - x0]
    alfa = parca[:, :, 3:4].astype(np.float32) / 255.0
    bgr = parca[:, :, 2::-1].astype(np.float32)
    bolge = kare[y0:y1, x0:x1].astype(np.float32)
    kare[y0:y1, x0:x1] = (bgr * alfa + bolge * (1 - alfa)).astype(np.uint8)


def altyazi_yaz(
    girdi: str,
    cikti: str,
    segmentler: List[Dict],
    oran: str = "9:16",
    font_yolu: Optional[str] = None,
) -> str:
    """girdi klibine segmentlerdeki altyaziyi yazar, ciktiyi 1080 genislikte
    H.264/AAC mp4 olarak kaydeder. segmentler klibe gore zamanlanmis olmalidir;
    bos liste verilirse yalnizca olceklenir ve H.264'e cevrilir."""
    import cv2

    font_yolu = font_bul(font_yolu)
    parcalar = parcala(segmentler)

    cap = cv2.VideoCapture(girdi)
    if not cap.isOpened():
        raise RuntimeError(f"Klip acilamadi: {girdi}")
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    sessiz = cikti + ".sessiz.mp4"
    yazici = cv2.VideoWriter(sessiz, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    onbellek = {}
    cy = int(H * 0.70)

    i = 0
    kare_no = 0
    while True:
        ok, kare = cap.read()
        if not ok:
            break
        t = kare_no / fps
        while i < len(parcalar) and parcalar[i]["end"] <= t:
            i += 1
        if i < len(parcalar) and parcalar[i]["start"] <= t:
            if i not in onbellek:
                onbellek[i] = _yazi_gorseli(parcalar[i]["text"], W, font_yolu)
            _bindir(kare, onbellek[i], W // 2, cy)
        yazici.write(kare)
        kare_no += 1

    cap.release()
    yazici.release()

    # Platform standardi: 9:16 -> 1080x1920, 1:1 -> 1080x1080, 4:5 -> 1080x1350
    try:
        ow, oh = (float(x) for x in oran.split(":"))
        hw, hh = 1080, int(round(1080 * oh / ow / 2)) * 2
    except (ValueError, ZeroDivisionError):
        hw, hh = 1080, int(round(1080 * H / W / 2)) * 2

    # Sesi geri ekle, platform standardina olcekle, H.264'e cevir
    # (mp4v cogu sosyal medya/telefonda oynamaz).
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", sessiz, "-i", girdi,
        "-map", "0:v:0", "-map", "1:a:0?",
        "-vf", f"scale={hw}:{hh}:force_original_aspect_ratio=increase:flags=lanczos,crop={hw}:{hh}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", "-shortest",
        cikti,
    ]
    subprocess.run(cmd, check=True)
    Path(sessiz).unlink(missing_ok=True)
    return cikti

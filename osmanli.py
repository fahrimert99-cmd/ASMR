"""
Osmanli Imparatorlugu 1299-1683 — 20 saniyelik harita animasyonu (sesli).

Kurulustan (1299, Sogut) en genis sinirlara (1683) kadar olan donemi,
yil sayaci, olay basliklari ve sentez ses efektleriyle anlatan kisa video:

    python osmanli.py                       # yatay 1920x1080 + dikey 1080x1920 (Shorts/Reels)
    python osmanli.py --format yatay        # yalnizca YouTube yatay
    python osmanli.py --format dikey --fps 60
    python osmanli.py --onizleme 7.0        # 7. saniyenin tek kare PNG onizlemesi

Gereken: numpy, scipy, Pillow ve ffmpeg. Harita verisi (Natural Earth) ve
yazi tipleri repoda hazir gelir; internet / API anahtari / GPU gerekmez.
Ses tamamen kodla sentezlenir (src/osmanli_ses.py) — telif derdi yoktur.
"""
import argparse
import json
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from src import cikti_klasoru
from src import osmanli_harita as H
from src import osmanli_ses as S
from src import osmanli_veri as V

_CIZER = None
_FPS = 30


def _kare(i):
    return _CIZER.kare(i / _FPS).tobytes()


def _ffmpeg():
    yol = shutil.which("ffmpeg")
    if yol:
        return yol
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def ses_uret(alanlar, hedef: Path) -> Path:
    """Sentez sesi uretir ve iki gecisli loudnorm ile -14 LUFS'a ayarlar."""
    ts = np.linspace(0.0, H.SURE, 2001)
    alan = alanlar.alan(ts)
    hiz = np.gradient(alan, ts)
    hiz = np.clip(hiz / (np.percentile(hiz[hiz > 0], 97) + 1e-9), 0, 1.3)
    hiz = np.convolve(hiz, np.ones(15) / 15, mode="same")
    yillar = H.yil(ts)

    cizer = H.Cizer(alanlar, "yatay")             # stereo pan: olayin ekrandaki yeri
    panlar = []
    for o, (x, y) in zip(V.OLAYLAR, cizer.olay_xy):
        px, _ = cizer.ekran(cizer.kamera(o["t"]), x, y)
        panlar.append(float(np.clip((px / cizer.W) * 2 - 1, -1, 1) * 0.6))

    ham = hedef.with_name("ses_ham.wav")
    S.uret(ham, V.OLAYLAR, H.SURE, buyume=(ts, hiz, yillar), panlar=panlar)

    ff = _ffmpeg()
    olc = subprocess.run([ff, "-hide_banner", "-i", str(ham), "-af",
                          "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True)
    try:
        js = json.loads(olc.stderr[olc.stderr.rindex("{"):olc.stderr.rindex("}") + 1])
        af = ("loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
              f"measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
              f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:"
              f"offset={js['target_offset']}")
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(ham),
                        "-af", af, "-ar", str(S.SR), str(hedef)], check=True)
    except Exception as e:                        # olcum basarisizsa ham sesle devam
        print(f"  (loudnorm atlandi: {e})")
        shutil.copy(ham, hedef)
    return hedef


def video_uret(alanlar, duzen: str, ses: Path, hedef: Path, fps: int, isci: int) -> Path:
    global _CIZER, _FPS
    _CIZER = H.Cizer(alanlar, duzen)
    _FPS = fps
    W, Hh = _CIZER.W, _CIZER.H
    n = int(round(H.SURE * fps))
    komut = [_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{Hh}", "-r", str(fps), "-i", "-",
             "-i", str(ses),
             "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(hedef)]
    ff = subprocess.Popen(komut, stdin=subprocess.PIPE)
    t0 = time.time()
    baglam = mp.get_context("fork") if "fork" in mp.get_all_start_methods() else mp.get_context()
    with baglam.Pool(isci) as havuz:
        for i, kare in enumerate(havuz.imap(_kare, range(n), chunksize=2)):
            ff.stdin.write(kare)
            if (i + 1) % (fps * 2) == 0 or i + 1 == n:
                gecen = time.time() - t0
                print(f"  [{duzen}] {i + 1}/{n} kare  ({gecen:.0f} sn)", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg kodlama hatasi")
    return hedef


def main():
    p = argparse.ArgumentParser(description="Osmanli 1299-1683 harita animasyonu (20 sn)")
    p.add_argument("--format", choices=["yatay", "dikey", "ikisi"], default="ikisi")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--isci", type=int, default=max(1, (os.cpu_count() or 2)))
    p.add_argument("--cikti", default=None, help="Cikti klasoru (varsayilan cikti/osmanli)")
    p.add_argument("--onizleme", type=float, default=None, help="Yalnizca bu saniyenin PNG karesi")
    args = p.parse_args()

    cikti = Path(args.cikti) if args.cikti else cikti_klasoru("osmanli")
    cikti.mkdir(parents=True, exist_ok=True)
    print("Zaman alanlari hesaplaniyor (bolgelerin fetih sirasi)...")
    alanlar = H.Alanlar()
    print(f"  1683 yuzolcumu (harita): ~{alanlar.alan(H.SURE) / 1e6:.2f} milyon km2")

    duzenler = ["yatay", "dikey"] if args.format == "ikisi" else [args.format]
    if args.onizleme is not None:
        from PIL import Image
        for d in duzenler:
            yol = cikti / f"onizleme_{d}_{args.onizleme:.2f}.png"
            Image.fromarray(H.Cizer(alanlar, d).kare(args.onizleme)).save(yol)
            print("Onizleme:", yol)
        return

    print("Ses sentezleniyor (davul, top, kilic, ney, dem...)...")
    ses = ses_uret(alanlar, cikti / "ses.wav")
    for d in duzenler:
        hedef = cikti / f"osmanli_1299_1683_{d}.mp4"
        print(f"Video render ediliyor: {d} ({args.fps} fps)...")
        video_uret(alanlar, d, ses, hedef, args.fps, args.isci)
        print(f"BITTI ✅  {hedef} ({hedef.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    sys.exit(main())

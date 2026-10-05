#!/usr/bin/env python3
"""
Resimli kitap üslubunda masal videosu — görüntü, müzik ve efektler tamamen kodla.

    python masal.py --liste
    python masal.py --masal keloglan_kapi                 # tam video (1920x1080, 30 fps)
    python masal.py --masal keloglan_kapi --onizleme 52   # tek kare (PNG)
    python masal.py --masal keloglan_kapi --kontak        # her sayfadan kareler (kontak sayfasi)
    python masal.py --masal keloglan_kapi --sadece-ses    # yalnizca ses izi (wav)

Çıktı: cikti/masal/<kimlik>/<kimlik>.mp4
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


KOK = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK))

from src import masal_motoru as MM  # noqa: E402
from src import masal_ses as MS  # noqa: E402

_MASAL = None
_FPS = 30


def _ffmpeg():
    yol = shutil.which("ffmpeg")
    if yol:
        return yol
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _kare(i):
    return _MASAL.kare(i / _FPS).tobytes()


def ses_uret(masal, hedef: Path) -> Path:
    """Sentez ses + iki gecisli loudnorm (-14 LUFS)."""
    ham = hedef.with_name("ses_ham.wav")
    MS.uret(ham, masal)
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
    except (ValueError, KeyError):
        af = "loudnorm=I=-14:TP=-1.5:LRA=11"
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(ham), "-af", af, "-ar", "48000",
                    str(hedef)], check=True)
    ham.unlink(missing_ok=True)
    return hedef


def video_uret(masal, ses: Path, hedef: Path, fps: int, isci: int) -> Path:
    global _MASAL, _FPS
    _MASAL, _FPS = masal, fps
    masal.hazirla()                                   # arka plan resimleri: catallanmadan once
    n = int(round(masal.SURE * fps))
    komut = [_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{MM.W}x{MM.H}", "-r", str(fps), "-i", "-",
             "-i", str(ses),
             "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(hedef)]
    ff = subprocess.Popen(komut, stdin=subprocess.PIPE)
    t0 = time.time()
    baglam = mp.get_context("fork") if "fork" in mp.get_all_start_methods() else mp.get_context()
    with baglam.Pool(isci) as havuz:
        for i, kare in enumerate(havuz.imap(_kare, range(n), chunksize=4)):
            ff.stdin.write(kare)
            if (i + 1) % (fps * 10) == 0 or i + 1 == n:
                print(f"  {i + 1}/{n} kare  ({time.time() - t0:.0f} sn)", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg kodlama hatasi")
    return hedef


def kontak(masal, yol: Path):
    from PIL import Image
    kareler = []
    for s in masal.sayfalar:
        for u in (0.3, 0.92):
            kareler.append(Image.fromarray(s.kare(s.sure * u)).resize((480, 270), Image.LANCZOS))
    sut = 6
    satir = (len(kareler) + sut - 1) // sut
    sayfa = Image.new("RGB", (480 * sut, 270 * satir))
    for k, im in enumerate(kareler):
        sayfa.paste(im, ((k % sut) * 480, (k // sut) * 270))
    sayfa.save(yol)
    return yol


def main():
    p = argparse.ArgumentParser(description="Resimli kitap üslubunda masal videosu")
    hedef = p.add_mutually_exclusive_group(required=True)
    hedef.add_argument("--masal", help="masallar/<kimlik>.py")
    hedef.add_argument("--liste", action="store_true")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--isci", type=int, default=max(1, (os.cpu_count() or 2)))
    p.add_argument("--cikti", default=None)
    p.add_argument("--onizleme", type=float, default=None, help="Yalnizca bu saniyenin PNG karesi")
    p.add_argument("--kontak", action="store_true", help="Her sayfadan iki kare (kontak.png)")
    p.add_argument("--sadece-ses", action="store_true")
    a = p.parse_args()

    if a.liste:
        from masallar import tum_kimlikler
        for k in tum_kimlikler():
            m = MM.Masal(k)
            print(f"  {k:<18} {m.BASLIK:<28} {len(m.sayfalar)} sayfa  {m.SURE:.0f} sn")
        return 0

    masal = MM.Masal(a.masal)
    cikti = Path(a.cikti) if a.cikti else KOK / "cikti" / "masal" / a.masal
    cikti.mkdir(parents=True, exist_ok=True)
    print(f"Masal: {a.masal} — {masal.BASLIK}  ({len(masal.sayfalar)} sayfa, {masal.SURE:.1f} sn)")

    if a.onizleme is not None:
        from PIL import Image
        yol = cikti / f"onizleme_{a.onizleme:.1f}.png"
        Image.fromarray(masal.kare(a.onizleme)).save(yol)
        print(f"  {yol}")
        return 0
    if a.kontak:
        print(f"  {kontak(masal, cikti / 'kontak.png')}")
        return 0

    print("Ses sentezleniyor...")
    ses = ses_uret(masal, cikti / "ses.wav")
    if a.sadece_ses:
        print(f"  {ses}")
        return 0
    print(f"Video render ediliyor ({a.fps} fps, {a.isci} isci)...")
    yol = video_uret(masal, ses, cikti / f"{a.masal}.mp4", a.fps, a.isci)
    print(f"BITTI ✅  {yol} ({yol.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

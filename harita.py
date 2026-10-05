"""
Tarihi harita animasyonu — 20 saniyelik sesli Shorts / video uretimi ve yayini.

Her konu senaryolar/<kimlik>.py dosyasinda tanimlidir (olaylar, bolgeler,
kamera, muzik). Ornekler:

    python harita.py --liste                          # senaryolar + yayin kuyrugu
    python harita.py --senaryo osmanli                # dikey (Shorts) + yatay video
    python harita.py --senaryo roma --format dikey
    python harita.py --senaryo mogol --onizleme 9.0   # tek kare PNG
    python harita.py --senaryo timur --kontrol        # dogrulama + kontak sayfasi
    python harita.py --siradaki --format dikey --yukle            # kuyruktaki ilk konu -> YouTube
    python harita.py --siradaki --yukle --yayin hemen             # zamanlama olmadan yayinla

Gereken: numpy, scipy, Pillow ve ffmpeg (yukleme icin google-api-python-client).
Harita verisi ve yazi tipleri repoda; internet/GPU gerekmez. Ses tamamen sentezdir.
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

from src import harita_motoru as H
from src import harita_ses as SES
from src import harita_yayin as Y

KOK = Path(__file__).resolve().parent
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


def _whooshlar(cizer):
    """Kameranin hizla uzaklastigi anlar -> whoosh efekti (zaman, kazanc)."""
    S = cizer.S
    ts = np.linspace(0, S.SURE, 401)
    kam = np.array([cizer.kamera(t)[:3] for t in ts])
    hiz = np.abs(np.gradient(np.log(kam[:, 0]), ts))
    hiz += np.hypot(np.gradient(kam[:, 1], ts), np.gradient(kam[:, 2], ts)) * kam[:, 0] / cizer.W
    hiz[ts < S.OLAYLAR[0]["t"]] = 0
    secilen = []
    for i in np.argsort(-hiz):
        if hiz[i] < 0.25 or len(secilen) >= 4:
            break
        if all(abs(ts[i] - t) > 1.4 for t, _ in secilen):
            secilen.append((float(ts[i]), float(min(0.45, 0.2 + 0.25 * hiz[i]))))
    return sorted(secilen)


def ses_uret(alanlar, hedef: Path) -> Path:
    """Sentez sesi uretir ve iki gecisli loudnorm ile -14 LUFS'a ayarlar."""
    S = alanlar.S
    ts = np.linspace(0.0, S.SURE, 2001)
    alan = alanlar.alan(ts)
    hiz = np.gradient(alan, ts)
    pozitif = hiz[hiz > 0]
    hiz = np.clip(hiz / (np.percentile(pozitif, 97) + 1e-9 if len(pozitif) else 1.0), 0, 1.3)
    hiz = np.convolve(hiz, np.ones(15) / 15, mode="same")
    yillar = S.yil(ts)

    cizer = H.Cizer(alanlar, "yatay")             # stereo pan: olayin ekrandaki yeri
    panlar = []
    for o, (x, y) in zip(S.OLAYLAR, cizer.olay_xy):
        px, _ = cizer.ekran(cizer.kamera(o["t"]), x, y)
        panlar.append(float(np.clip((px / cizer.W) * 2 - 1, -1, 1) * 0.6))

    ham = hedef.with_name("ses_ham.wav")
    SES.uret(ham, S.OLAYLAR, S.SURE, buyume=(ts, hiz, yillar), panlar=panlar,
             muzik=S.MUZIK, barut=S.BARUT, whooshlar=_whooshlar(cizer))

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
                        "-af", af, "-ar", str(SES.SR), str(hedef)], check=True)
    except Exception as e:                        # olcum basarisizsa ham sesle devam
        print(f"  (loudnorm atlandi: {e})")
        shutil.copy(ham, hedef)
    return hedef


def video_uret(alanlar, duzen: str, ses: Path, hedef: Path, fps: int, isci: int) -> Path:
    global _CIZER, _FPS
    _CIZER = H.Cizer(alanlar, duzen)
    _FPS = fps
    W, Hh = _CIZER.W, _CIZER.H
    n = int(round(alanlar.S.SURE * fps))
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
            if (i + 1) % (fps * 4) == 0 or i + 1 == n:
                print(f"  [{duzen}] {i + 1}/{n} kare  ({time.time() - t0:.0f} sn)", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg kodlama hatasi")
    return hedef


def kontrol(S, alanlar, cikti: Path) -> bool:
    from src import harita_kontrol as K
    hatalar, uyarilar = K.yapisal(S, SES.MAKAMLAR)
    for u in uyarilar:
        print(f"  UYARI: {u}")
    for h in hatalar:
        print(f"  HATA : {h}")
    if alanlar is not None:
        dl = K.delikler(alanlar)
        for alan, lon, lat, oran in dl[:12]:
            print(f"  DELIK: ~{alan:,.0f} km2  boylam {lon:.2f}  enlem {lat:.2f}  "
                  f"(cevrenin %{oran * 100:.0f}'i devlet topragi)")
        if not dl:
            print("  Delik yok (bolgeler arasinda bosluk kalmamis).")
        print(f"  En genis yuzolcumu: ~{alanlar.alan(S.SURE) / 1e6:.2f} milyon km2")
        yol = K.kontak_sayfasi(H.Cizer(alanlar, "dikey"), cikti / "kontrol.png")
        print(f"  Kontak sayfasi: {yol}")
    return not hatalar


def liste():
    from senaryolar import tum_kimlikler
    d = Y.sira_oku()
    print("Senaryolar:")
    for k in tum_kimlikler():
        durum = "yayinlandi" if k in d["yayinlanan"] else ("kuyrukta" if k in d["sira"] else "-")
        try:
            S = H.Senaryo(k)
            print(f"  {k:<14} {S.BASLIK:<38} {S.yil_araligi():<16} [{durum}]")
        except Exception as e:
            print(f"  {k:<14} YUKLENEMEDI: {e}")
    print(f"Kuyrukta bekleyen: {', '.join(Y.bekleyenler(d)) or '(bos)'}")


def main():
    p = argparse.ArgumentParser(description="Tarihi harita animasyonu (20 sn, sesli)")
    hedef = p.add_mutually_exclusive_group(required=True)
    hedef.add_argument("--senaryo", help="senaryolar/<kimlik>.py")
    hedef.add_argument("--siradaki", action="store_true", help="senaryolar/sira.json'daki ilk bekleyen")
    hedef.add_argument("--liste", action="store_true", help="Senaryolari ve kuyrugu listele")
    p.add_argument("--format", choices=["yatay", "dikey", "ikisi"], default="ikisi")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--isci", type=int, default=max(1, (os.cpu_count() or 2)))
    p.add_argument("--cikti", default=None, help="Cikti klasoru (varsayilan cikti/harita/<kimlik>)")
    p.add_argument("--onizleme", type=float, default=None, help="Yalnizca bu saniyenin PNG karesi")
    p.add_argument("--kontrol", action="store_true", help="Dogrula + delik raporu + kontak sayfasi")
    p.add_argument("--yukle", action="store_true", help="Dikey videoyu YouTube'a yukle (kuyrugu gunceller)")
    p.add_argument("--yayin", choices=["zamanli", "hemen", "gizli"], default="zamanli",
                   help="zamanli: gizli yukle, ertesi gun --yayin-saati'nde yayinla (varsayilan)")
    p.add_argument("--yayin-saati", default="19:00", help="Zamanli yayin saati (Europe/Istanbul)")
    args = p.parse_args()

    if args.liste:
        return liste()
    kimlik = args.senaryo or Y.siradaki()
    if not kimlik:
        print("HATA: yayin kuyrugu bos — senaryolar/sira.json'a yeni senaryo ekleyin.")
        return 2
    S = H.Senaryo(kimlik)
    cikti = Path(args.cikti) if args.cikti else KOK / "cikti" / "harita" / kimlik
    cikti.mkdir(parents=True, exist_ok=True)
    print(f"Senaryo: {kimlik} — {S.BASLIK} ({S.yil_araligi()})")

    if args.kontrol:
        print("Yapisal kontrol...")
        from src import harita_kontrol as K
        hatalar, _ = K.yapisal(S, SES.MAKAMLAR)
        alanlar = None if hatalar else H.Alanlar(S)
        return 0 if kontrol(S, alanlar, cikti) else 1

    print("Zaman alanlari hesaplaniyor (bolgelerin fetih sirasi)...")
    alanlar = H.Alanlar(S)
    print(f"  En genis yuzolcumu (harita): ~{alanlar.alan(S.SURE) / 1e6:.2f} milyon km2")

    duzenler = ["dikey", "yatay"] if args.format == "ikisi" else [args.format]
    if args.yukle and "dikey" not in duzenler:
        duzenler.insert(0, "dikey")
    if args.onizleme is not None:
        from PIL import Image
        for d in duzenler:
            yol = cikti / f"onizleme_{d}_{args.onizleme:.2f}.png"
            Image.fromarray(H.Cizer(alanlar, d).kare(args.onizleme)).save(yol)
            print("Onizleme:", yol)
        return 0

    print("Ses sentezleniyor...")
    ses = ses_uret(alanlar, cikti / "ses.wav")
    videolar = {}
    for d in duzenler:
        yol = cikti / f"{kimlik}_{d}.mp4"
        print(f"Video render ediliyor: {d} ({args.fps} fps)...")
        video_uret(alanlar, d, ses, yol, args.fps, args.isci)
        videolar[d] = yol
        print(f"BITTI ✅  {yol} ({yol.stat().st_size // 1024} KB)")

    if args.yukle:
        try:
            bilgi = Y.yukle(S, videolar["dikey"], float(alanlar.alan(S.SURE)),
                            mod=args.yayin, saat=args.yayin_saati)
        except Y.YuklemeAtlandi as e:
            print(f"UYARI: yukleme atlandi — {e}. Video artifact olarak kaydedildi.")
            return 0
        Y.isaretle(kimlik, bilgi)
        print(f"YUKLENDI ✅  {bilgi['url']}  (yayin: {bilgi['yayin']})")
        gh = os.environ.get("GITHUB_OUTPUT")
        if gh:
            with open(gh, "a", encoding="utf-8") as f:
                f.write(f"video_id={bilgi['video_id']}\nkimlik={kimlik}\nyuklendi=1\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

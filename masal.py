#!/usr/bin/env python3
"""
Resimli kitap üslubunda masal üretim sistemi — görüntü, müzik ve efektler kodla,
anlatım Piper (ücretsiz) ya da ElevenLabs ile.

    python masal.py --liste                                   # masallar + yayın kuyruğu
    python masal.py --masal keloglan_kapi --kontrol           # doğrulama + kontak sayfası
    python masal.py --masal keloglan_kapi --seslendirme piper --format ikisi
    python masal.py --siradaki --seslendirme piper --format ikisi --yukle   # kuyruk → YouTube (zamanlı)
    python masal.py --masal keloglan_kapi --onizleme 52       # tek kare (PNG)
    python masal.py --masal keloglan_kapi --sadece-ses        # yalnızca ses izi (wav)

Seslendirme: --seslendirme piper (ücretsiz Türkçe ses; model huggingface.co'dan iner)
             --seslendirme elevenlabs (ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID)
Sesler veri/seslendirme/<kimlik>/ altında önbelleğe alınır.

Çıktı: cikti/masal/<kimlik>/<kimlik>.mp4 (yatay) ve <kimlik>_shorts.mp4 (dikey tanıtım)
"""
import argparse
import json
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK))

from src import masal_motoru as MM  # noqa: E402
from src import masal_ses as MS  # noqa: E402

_KAYNAK = None
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
    return _KAYNAK.kare(i / _FPS).tobytes()


def _loudnorm(ham: Path, hedef: Path):
    """Iki gecisli loudnorm: -14 LUFS, -2 dBTP."""
    ff = _ffmpeg()
    olc = subprocess.run([ff, "-hide_banner", "-i", str(ham), "-af",
                          "loudnorm=I=-14:TP=-2.0:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True)
    try:
        js = json.loads(olc.stderr[olc.stderr.rindex("{"):olc.stderr.rindex("}") + 1])
        af = ("loudnorm=I=-14:TP=-2.0:LRA=11:linear=true:"
              f"measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
              f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:"
              f"offset={js['target_offset']}")
    except (ValueError, KeyError):
        af = "loudnorm=I=-14:TP=-2.0:LRA=11"
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(ham), "-af", af, "-ar", "48000",
                    str(hedef)], check=True)
    return hedef


def ses_uret(masal, hedef: Path) -> Path:
    """Sentez ses (+ varsa seslendirme) -> -14 LUFS."""
    ham = hedef.with_name("ses_ham.wav")
    MS.uret(ham, masal, anlatim=masal.anlatim_olaylari() if masal.anlatimli else None)
    _loudnorm(ham, hedef)
    ham.unlink(missing_ok=True)
    return hedef


def shorts_ses(tam: Path, kurgu, hedef: Path) -> Path:
    """Tam ses izinden Shorts araligi + kapanis ezgisi -> -14 LUFS."""
    with wave.open(str(tam)) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float64) / 32768
    a = int(kurgu.T0 * sr)
    b = min(len(x), int((kurgu.T1 + 1.0) * sr))
    parca = x[a:b].copy()
    gir = int(0.15 * sr)
    parca[:gir] *= np.linspace(0, 1, gir)[:, None]
    cik = int(1.2 * sr)
    parca[-cik:] *= np.linspace(1, 0, cik)[:, None] ** 1.5
    n = int(kurgu.SURE * sr)
    out = np.zeros((n, 2))
    out[:min(n, len(parca))] = parca[:n]
    rng = np.random.default_rng(3)
    kuyruk = MS.cinlama(rng, 392.0, 1.0)
    t0 = int((kurgu.T1 - kurgu.T0 + 0.2) * sr)
    m = max(0, min(len(kuyruk), n - t0))
    out[t0:t0 + m] += 0.25 * kuyruk[:m, None]
    out[-int(0.5 * sr):] *= np.linspace(1, 0, int(0.5 * sr))[:, None]
    ham = hedef.with_name("shorts_ham.wav")
    pcm = (np.clip(out, -1, 1) * 32767).astype("<i2")
    with wave.open(str(ham), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    _loudnorm(ham, hedef)
    ham.unlink(missing_ok=True)
    return hedef


def video_uret(kaynak, gen, yuk, sure, ses: Path, hedef: Path, fps: int, isci: int, etiket="") -> Path:
    """kaynak.kare(t) -> (yuk, gen, 3) uint8 kareleri paralel uretip ffmpeg ile kodlar."""
    global _KAYNAK, _FPS
    _KAYNAK, _FPS = kaynak, fps
    n = int(round(sure * fps))
    komut = [_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{gen}x{yuk}", "-r", str(fps), "-i", "-",
             "-i", str(ses),
             "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", str(hedef)]
    ff = subprocess.Popen(komut, stdin=subprocess.PIPE)
    t0 = time.time()
    baglam = mp.get_context("fork") if "fork" in mp.get_all_start_methods() else mp.get_context()
    with baglam.Pool(isci) as havuz:
        for i, kare in enumerate(havuz.imap(_kare, range(n), chunksize=4)):
            ff.stdin.write(kare)
            if (i + 1) % (fps * 10) == 0 or i + 1 == n:
                print(f"  {etiket}{i + 1}/{n} kare  ({time.time() - t0:.0f} sn)", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg kodlama hatasi")
    return hedef


def kontak(masal, yol: Path):
    from PIL import Image
    kareler = []
    for s in masal.sayfalar:
        for u in (0.3, 0.92):
            try:
                kareler.append(Image.fromarray(s.kare(s.sure * u)).resize((480, 270), Image.LANCZOS))
            except Exception:                         # noqa: BLE001 - hatali sahne: kirmizi bos kare
                kareler.append(Image.new("RGB", (480, 270), (150, 30, 30)))
    sut = 6
    satir = (len(kareler) + sut - 1) // sut
    sayfa = Image.new("RGB", (480 * sut, 270 * satir))
    for k, im in enumerate(kareler):
        sayfa.paste(im, ((k % sut) * 480, (k // sut) * 270))
    sayfa.save(yol)
    return yol


def liste():
    from masallar import tum_kimlikler
    from src import masal_yayin as Y
    d = Y.kuyruk()
    print("Masallar:")
    for k in tum_kimlikler():
        durum = "yayinlandi" if k in d["yayinlanan"] else ("kuyrukta" if k in d["sira"] else "-")
        try:
            m = MM.Masal(k)
            print(f"  {k:<20} {m.BASLIK:<30} {len(m.sayfalar):2d} sayfa  ~{m.SURE:.0f} sn  [{durum}]")
        except Exception as e:                       # noqa: BLE001
            print(f"  {k:<20} YUKLENEMEDI: {e}")
    b = [k for k in d["sira"] if k not in d["yayinlanan"]]
    print(f"Kuyrukta bekleyen: {', '.join(b) or '(bos)'}")


def _github_cikti(**kv):
    yol = os.environ.get("GITHUB_OUTPUT")
    if yol:
        with open(yol, "a", encoding="utf-8") as f:
            for k, v in kv.items():
                f.write(f"{k}={v}\n")


def main():
    p = argparse.ArgumentParser(description="Resimli kitap üslubunda masal üretim sistemi")
    hedef = p.add_mutually_exclusive_group(required=True)
    hedef.add_argument("--masal", help="masallar/<kimlik>.py")
    hedef.add_argument("--siradaki", action="store_true", help="masallar/sira.json'daki ilk bekleyen masal")
    hedef.add_argument("--liste", action="store_true", help="Masallari ve kuyrugu listele")
    p.add_argument("--format", choices=["yatay", "shorts", "ikisi"], default="yatay")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--isci", type=int, default=max(1, (os.cpu_count() or 2)))
    p.add_argument("--cikti", default=None)
    p.add_argument("--onizleme", type=float, default=None, help="Yalnizca bu saniyenin PNG karesi")
    p.add_argument("--kontak", action="store_true", help="Her sayfadan iki kare (kontak.png)")
    p.add_argument("--kontrol", action="store_true", help="Dogrula + sahneleri dene + kontak sayfasi")
    p.add_argument("--sadece-ses", action="store_true")
    p.add_argument("--seslendirme", choices=["yok", "elevenlabs", "piper", "espeak"], default="yok",
                   help="Anlatici: piper (ucretsiz Turkce) | elevenlabs (ucretli, en dogal) | espeak (yalnizca test)")
    p.add_argument("--yukle", action="store_true", help="Videolari YouTube'a yukle (kuyrugu gunceller)")
    p.add_argument("--yayin", choices=["zamanli", "hemen", "gizli"], default="zamanli")
    p.add_argument("--yayin-saati", default="19:00", help="Zamanli yayin saati (Europe/Istanbul)")
    a = p.parse_args()

    if a.liste:
        liste()
        return 0
    kimlik = a.masal
    if a.siradaki:
        from src import masal_yayin as Y
        kimlik = Y.siradaki()
        if not kimlik:
            print("Kuyrukta bekleyen masal yok (masallar/sira.json).")
            return 2
    masal = MM.Masal(kimlik)
    cikti = Path(a.cikti) if a.cikti else KOK / "cikti" / "masal" / kimlik
    cikti.mkdir(parents=True, exist_ok=True)

    if a.kontrol:
        from src import masal_kontrol as K
        print(f"Kontrol: {kimlik} — {masal.BASLIK}")
        hatalar, uyarilar = K.yapisal(masal)
        hatalar += K.sahne_denemesi(masal)
        for u in uyarilar:
            print(f"  UYARI: {u}")
        for h in hatalar:
            print(f"  HATA : {h}")
        print(f"  {len(masal.sayfalar)} sayfa, ~{masal.SURE:.0f} sn (seslendirmesiz tahmin)")
        print(f"  Kontak sayfasi: {kontak(masal, cikti / 'kontak.png')}")
        print("  Sonuc: " + ("HATA VAR" if hatalar else "temiz"))
        return 1 if hatalar else 0

    if a.seslendirme != "yok":
        from src import masal_seslendirme as SL
        print(f"Seslendiriliyor ({a.seslendirme})...")
        try:
            plan = SL.masali_seslendir(masal, a.seslendirme)
        except SL.SeslendirmeHatasi as e:
            print(f"HATA: {e}")
            return 3
        masal.seslendirme_uygula(plan)
    print(f"Masal: {kimlik} — {masal.BASLIK}  ({len(masal.sayfalar)} sayfa, {masal.SURE:.1f} sn)")

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
    masal.hazirla()                                   # arka plan resimleri: catallanmadan once
    yatay = shorts = None
    if a.format in ("yatay", "ikisi"):
        print(f"Yatay video render ediliyor ({a.fps} fps, {a.isci} isci)...")
        yatay = video_uret(masal, MM.W, MM.H, masal.SURE, ses, cikti / f"{kimlik}.mp4", a.fps, a.isci)
        print(f"  ✅ {yatay} ({yatay.stat().st_size // 1024} KB)")
    if a.format in ("shorts", "ikisi"):
        from src import masal_shorts as SS
        kurgu = SS.ShortsKurgu(masal)
        kurgu.hazirla()
        print(f"Shorts render ediliyor ({kurgu.SURE:.1f} sn)...")
        s_ses = shorts_ses(ses, kurgu, cikti / "shorts_ses.wav")
        shorts = video_uret(kurgu, SS.SW, SS.SH, kurgu.SURE, s_ses, cikti / f"{kimlik}_shorts.mp4", a.fps, a.isci,
                            etiket="[shorts] ")
        print(f"  ✅ {shorts} ({shorts.stat().st_size // 1024} KB)")
    _github_cikti(kimlik=kimlik)

    if a.yukle:
        from src import masal_yayin as Y
        from src.harita_yayin import YuklemeAtlandi
        ses_bilgisi = None
        if a.seslendirme == "piper":
            from src.masal_seslendirme import ayarlar
            ses_bilgisi = f"Piper TTS ({ayarlar()['piper_ses']})"
        elif a.seslendirme == "elevenlabs":
            ses_bilgisi = "ElevenLabs"
        try:
            bilgi = Y.yukle(masal, yatay or shorts, shorts if yatay else None, a.yayin, a.yayin_saati, ses_bilgisi)
        except YuklemeAtlandi as e:
            print(f"YouTube yuklemesi atlandi: {e}")
            return 0
        Y.isaretle_yayinlandi(kimlik, bilgi)
        print(f"YouTube: {bilgi['url']}  (yayin: {bilgi['yayin']})" +
              (f"  Shorts: {bilgi['shorts_url']}" if bilgi.get("shorts_url") else ""))
        _github_cikti(video_id=bilgi["video_id"], yuklendi="1")
    print("BITTI ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())

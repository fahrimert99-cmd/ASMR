"""
SRT'ye gore seslendirme + kodla uretilen giris sesi + miks.

Hazir (muzikli) bir videoyu alir; .srt altyazisindaki her satiri Turkce TTS
ile seslendirip satirin zaman araligina yerlestirir, video girisine numpy ile
uretilen foley katmanini (src/giris_sfx.py) ekler, muzigi anlatimin altinda
otomatik kisar (ducking) ve sonucu altyazi izi ile birlikte yeni bir mp4'e
yazar. Video goruntusu yeniden kodlanmaz (kalite kaybi yok).

    python srt_seslendir.py --video film.mp4 --srt film.srt
    python srt_seslendir.py --video film.mp4 --srt film.srt --motor edge
    python srt_seslendir.py ... --ses tr_TR-fahrettin-medium --giris-yok

Motorlar:
  - "piper" : cevrimdisi Piper/VITS Turkce sesi (sherpa-onnx). Model ilk
              calistirmada GitHub'dan modeller/ altina indirilir. Ag/anahtar
              gerektirmez; GitHub Actions ve kapali aglarda da calisir.
  - "edge"  : Microsoft edge-tts (src/seslendirme.py); internet gerektirir.
"""
import argparse
import json
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import wave
from pathlib import Path

import numpy as np

from src import KOK
from src import giris_sfx

SR = 44100
MODEL_URL = ("https://github.com/k2-fsa/sherpa-onnx/releases/download/"
             "tts-models/vits-piper-{ses}.tar.bz2")

# TTS'in yanlis okudugu yabanci ozel adlar icin telaffuz sozlugu.
# Yalnizca seslendirilen metne uygulanir; .srt ve ekrandaki altyazi degismez.
TELAFFUZ = {
    "The Food Almanac": "Dı Fud Olmınak",
    "Alice": "Elis",
    "Campbell": "Kembıl",
    "Dyer": "Dayır",
    "Lammas": "Lamas",
}


# ------------------------------------------------------------------ SRT

def srt_oku(yol: Path) -> list:
    """[(bas_sn, bit_sn, metin), ...] dondurur."""
    metin = Path(yol).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    zaman = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")
    satirlar = []
    for blok in re.split(r"\n\s*\n", metin.strip()):
        parca = blok.strip().split("\n")
        for i, s in enumerate(parca):
            m = zaman.search(s)
            if m:
                g = [int(x) for x in m.groups()]
                bas = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
                bit = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
                yazi = " ".join(parca[i + 1:]).strip()
                if yazi:
                    satirlar.append((bas, bit, yazi))
                break
    return satirlar


def telaffuz_uygula(metin: str, sozluk: dict) -> str:
    for kaynak, hedef in sorted(sozluk.items(), key=lambda kv: -len(kv[0])):
        metin = re.sub(rf"\b{re.escape(kaynak)}\b", hedef, metin)
    # "Baslik - alt baslik" tirelerini duraklamaya cevir
    return re.sub(r"\s+[-–—]\s+", ". ", metin)


# ------------------------------------------------------------------ ses G/C

def ses_oku(yol, sr: int = SR, kanal: int = 2) -> np.ndarray:
    """ffmpeg ile herhangi bir ses/video dosyasini (n, kanal) float32 okur."""
    ham = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(yol), "-vn", "-ac", str(kanal),
         "-ar", str(sr), "-f", "f32le", "-"],
        check=True, capture_output=True).stdout
    return np.frombuffer(ham, np.float32).reshape(-1, kanal).copy()


def wav_yaz(yol, x: np.ndarray, sr: int = SR):
    x = np.atleast_2d(x.T).T if x.ndim == 1 else x
    with wave.open(str(yol), "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


# ------------------------------------------------------------------ TTS

class PiperTTS:
    def __init__(self, ses: str, klasor: Path):
        import sherpa_onnx

        d = Path(klasor) / f"vits-piper-{ses}"
        if not (d / f"{ses}.onnx").exists():
            Path(klasor).mkdir(parents=True, exist_ok=True)
            url = MODEL_URL.format(ses=ses)
            print(f"Ses modeli indiriliyor: {url}")
            arsiv = Path(klasor) / f"{ses}.tar.bz2"
            urllib.request.urlretrieve(url, arsiv)
            with tarfile.open(arsiv) as t:
                t.extractall(klasor, filter="data")
            arsiv.unlink()
        cfg = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=str(d / f"{ses}.onnx"), tokens=str(d / "tokens.txt"),
                    data_dir=str(d / "espeak-ng-data")),
                num_threads=4))
        self.tts = sherpa_onnx.OfflineTts(cfg)

    def __call__(self, metin: str, hiz: float, gecici: Path) -> np.ndarray:
        a = self.tts.generate(metin, sid=0, speed=hiz)
        yol = gecici / "piper.wav"
        wav_yaz(yol, np.asarray(a.samples, np.float32), a.sample_rate)
        return ses_oku(yol, SR, 1)[:, 0]


class EdgeTTS:
    def __init__(self, ses: str):
        self.ses = ses

    def __call__(self, metin: str, hiz: float, gecici: Path) -> np.ndarray:
        from src.seslendirme import _edge_seslendir

        oran = f"{int(round((hiz - 1) * 100)):+d}%"
        mp3 = gecici / "edge.mp3"
        _edge_seslendir(metin, self.ses, oran, "-2Hz", mp3, gecici / "edge.srt")
        return ses_oku(mp3, SR, 1)[:, 0]


def sessizlik_kirp(x: np.ndarray, esik_db: float = -45) -> np.ndarray:
    """TTS ciktisinin basindaki/sonundaki sessizligi kirpar."""
    zarf = np.convolve(np.abs(x), np.ones(441) / 441, "same")
    dolu = np.nonzero(zarf > 10 ** (esik_db / 20) * max(np.abs(x).max(), 1e-9))[0]
    if len(dolu) == 0:
        return x
    a = max(0, dolu[0] - int(0.02 * SR))
    b = min(len(x), dolu[-1] + int(0.08 * SR))
    return x[a:b]


def anlatim_rengi(x: np.ndarray, gecici: Path) -> np.ndarray:
    """Belgesel anlatici tonu: alcak kesim, hafif sicaklik, kompresyon."""
    giris, cikis = gecici / "kuru.wav", gecici / "islenmis.wav"
    wav_yaz(giris, x[:, None])
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(giris), "-af",
         "highpass=f=75,equalizer=f=180:t=q:w=1:g=2.5,"
         "equalizer=f=3200:t=q:w=1.2:g=1.5,deesser=i=0.35,"
         "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,"
         "aecho=0.9:0.6:28|47:0.10|0.06",
         str(cikis)], check=True)
    return ses_oku(cikis, SR, 1)[:, 0]


# ------------------------------------------------------------------ miks

def zarf_cikar(x: np.ndarray, atak: float = 0.04, salinim: float = 0.45) -> np.ndarray:
    """Ducking icin anlatimin yumusatilmis 0..1 aktiflik zarfi."""
    aktif = (np.convolve(np.abs(x), np.ones(882) / 882, "same") > 0.01).astype(float)
    # once genislet (kelime aralari kapanmasin), sonra yumusat
    gen = int(salinim * SR)
    aktif = np.convolve(aktif, np.ones(gen), "same") > 0
    k = int(atak * SR) * 2 + 1
    return np.convolve(aktif.astype(float), np.hanning(k) / np.hanning(k).sum(), "same")


def main():
    p = argparse.ArgumentParser(description="SRT'ye gore seslendir + giris sesi + miks")
    p.add_argument("--video", required=True)
    p.add_argument("--srt", required=True)
    p.add_argument("--cikti", default=None, help="Cikti mp4 (varsayilan cikti/<ad>_seslendirilmis.mp4)")
    p.add_argument("--motor", choices=["piper", "edge"], default="piper")
    p.add_argument("--ses", default=None,
                   help="piper: tr_TR-dfki-medium | tr_TR-fahrettin-medium | tr_TR-fettah-medium; "
                        "edge: tr-TR-AhmetNeural ...")
    p.add_argument("--hiz", type=float, default=0.92, help="Temel konusma hizi (1.0 = normal)")
    p.add_argument("--max-hiz", type=float, default=1.3, help="Satira sigdirmak icin ust hiz siniri")
    p.add_argument("--on-bosluk", type=float, default=0.35, help="Satir basindan sonra anlatim gecikmesi (sn)")
    p.add_argument("--giris-bosluk", type=float, default=2.3,
                   help="Ilk satirda anlatim gecikmesi (giris efektleri duyulsun diye)")
    p.add_argument("--muzik-db", type=float, default=6.0, help="Orijinal ses/muzik kazanci (dB)")
    p.add_argument("--duck-db", type=float, default=-9.0, help="Anlatim sirasinda muzik kismasi (dB)")
    p.add_argument("--giris-yok", action="store_true", help="Kodla uretilen giris sesini ekleme")
    p.add_argument("--lufs", type=float, default=-15.0, help="Hedef butunlesik yukluk (LUFS)")
    args = p.parse_args()

    video, srt = Path(args.video), Path(args.srt)
    cikti = Path(args.cikti) if args.cikti else KOK / "cikti" / f"{video.stem}_seslendirilmis.mp4"
    cikti.parent.mkdir(parents=True, exist_ok=True)

    satirlar = srt_oku(srt)
    print(f"{len(satirlar)} altyazi satiri okundu.")
    if args.motor == "piper":
        tts = PiperTTS(args.ses or "tr_TR-dfki-medium", KOK / "modeller")
    else:
        tts = EdgeTTS(args.ses or "tr-TR-AhmetNeural")

    muzik = ses_oku(video)
    n = len(muzik)
    anlatim = np.zeros(n, np.float32)
    rapor = []

    with tempfile.TemporaryDirectory() as g:
        gecici = Path(g)
        for k, (bas, bit, yazi) in enumerate(satirlar):
            okunacak = telaffuz_uygula(yazi, TELAFFUZ)
            on = args.giris_bosluk if k == 0 and not args.giris_yok else args.on_bosluk
            sigacak = max(0.5, (bit - bas) - on - 0.25)
            hiz = args.hiz
            ses = sessizlik_kirp(tts(okunacak, hiz, gecici))
            if len(ses) / SR > sigacak:
                # satira sigmiyor: hizi orantili artir (ust sinirla), tekrar uret
                hiz = min(args.max_hiz, hiz * (len(ses) / SR) / sigacak * 1.02)
                ses = sessizlik_kirp(tts(okunacak, hiz, gecici))
            if len(ses) / SR > sigacak and on > args.on_bosluk:
                on = max(args.on_bosluk, (bit - bas) - 0.25 - len(ses) / SR)
            ses = anlatim_rengi(ses, gecici)
            ses = ses / (np.sqrt(np.mean(ses ** 2)) + 1e-9) * 10 ** (-18 / 20)
            i = int((bas + on) * SR)
            j = min(n, i + len(ses))
            anlatim[i:j] += ses[: j - i]
            rapor.append((bas, bas + on, bas + on + len(ses) / SR, bit, hiz))
            print(f"  [{k + 1:02d}] {bas + on:6.2f}-{bas + on + len(ses) / SR:6.2f} sn "
                  f"(satir {bas:.0f}-{bit:.0f}, hiz {hiz:.2f})  {yazi[:60]}")

        # muzik ducking
        zarf = zarf_cikar(anlatim)
        kazanc = 10 ** (args.muzik_db / 20) * (1 - zarf * (1 - 10 ** (args.duck_db / 20)))
        miks = muzik * kazanc[:, None].astype(np.float32)
        miks += anlatim[:, None]

        if not args.giris_yok:
            sfx = giris_sfx.uret(SR)
            m = min(n, len(sfx))
            miks[:m] += sfx[:m]

        ham = gecici / "miks.wav"
        tepe = np.abs(miks).max()
        wav_yaz(ham, miks / max(1.0, tepe / 0.98))
        altyazi = gecici / "altyazi.srt"
        altyazi.write_text(srt.read_text(encoding="utf-8-sig"), encoding="utf-8")

        # iki gecisli dogrusal loudnorm (pompalamasiz) + video kopyala + altyazi izi
        olc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", str(ham), "-af",
             f"loudnorm=I={args.lufs}:TP=-1.5:LRA=14:print_format=json", "-f", "null", "-"],
            capture_output=True, text=True).stderr
        o = json.loads(olc[olc.rindex("{"): olc.rindex("}") + 1])
        ln = (f"loudnorm=I={args.lufs}:TP=-1.5:LRA=14:linear=true:"
              f"measured_I={o['input_i']}:measured_TP={o['input_tp']}:"
              f"measured_LRA={o['input_lra']}:measured_thresh={o['input_thresh']}:"
              f"offset={o['target_offset']}")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(ham),
             "-i", str(altyazi), "-map", "0:v:0", "-map", "1:a:0", "-map", "2:s:0",
             "-c:v", "copy", "-af", ln, "-ar", str(SR), "-c:a", "aac", "-b:a", "192k",
             "-c:s", "mov_text", "-metadata:s:s:0", "language=tur",
             "-metadata:s:a:0", "language=tur", "-movflags", "+faststart",
             "-shortest", str(cikti)], check=True)

    print(f"\nBITTI ✅  {cikti} ({cikti.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

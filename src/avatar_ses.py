"""
Avatar videosu ses katmani.

  1. Seslendirme: her replik ayri seslendirilir ve cizelgedeki zamanina konur.
     Motor sirasi (config avatar.ses_motoru = "auto"):
       edge  -> Microsoft edge-tts (bedava, anahtarsiz; internet ister)
       piper -> Piper/VITS Turkce ses, sherpa-onnx ile TAMAMEN CEVRIMDISI
                (model ilk calismada GitHub'dan bir kez indirilir: modeller/)
       yok   -> anlatimsiz (yalnizca muzik + can + nefes sesi)
     Bir motor herhangi bir replikte basarisiz olursa TUM replikler bir
     sonraki motorla yeniden uretilir (videoda tek, tutarli bir ses olsun).
  2. Muzik: nefes dongulerine hizali, yumusak akor "pad"i (numpy, telifsiz).
  3. Can: her faz basinda (AL / TUT / VER) yumusak bir can sesi -> izleyici
     ekrana bakmasa da ritmi takip eder.
  4. Nefes sesi: hava akisina gore kabarip sonen yumusak gurultu (ASMR hissi).
  5. Ambient: asmr_ses ile dusuk seviyede yagmur vb. (opsiyonel).

Hepsi numpy ile 44.1 kHz stereo olarak karistirilir ve tek bir WAV yazilir.
"""
import math
import shutil
import subprocess
import tarfile
import wave
from pathlib import Path

from src import KOK
from src import asmr_ses
from src.avatar_senaryo import Cizelge, nefes_seviyesi, hava_akisi

SR = 44100

PIPER_URL = ("https://github.com/k2-fsa/sherpa-onnx/releases/download/"
             "tts-models/vits-piper-{ses}.tar.bz2")


def _ffmpeg() -> str:
    yol = shutil.which("ffmpeg")
    if yol:
        return yol
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _wav_oku(yol: Path):
    """Herhangi bir ses dosyasini ffmpeg ile 44.1 kHz mono float diziye cevirir."""
    import numpy as np

    ham = subprocess.run(
        [_ffmpeg(), "-v", "error", "-i", str(yol), "-f", "s16le", "-ac", "1",
         "-ar", str(SR), "-"],
        check=True, capture_output=True).stdout
    return np.frombuffer(ham, dtype="<i2").astype(np.float32) / 32768.0


def _wav_yaz(yol: Path, x, sr: int = SR):
    """Mono (n,) ya da stereo (n, 2) float diziyi 16-bit WAV olarak yazar."""
    import numpy as np

    x = np.clip(x, -1.0, 1.0)
    kanal = 1 if x.ndim == 1 else x.shape[1]
    yol.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(yol), "w") as w:
        w.setnchannels(kanal)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767.0).astype("<i2").tobytes())


# ------------------------------------------------------------------ seslendirme

def _edge(replikler, a: dict, klasor: Path):
    from src.seslendirme import _edge_seslendir

    ses = a.get("edge_ses", "tr-TR-EmelNeural")
    hiz = a.get("edge_hiz", "-10%")
    pitch = a.get("edge_pitch", "+0Hz")
    for i, r in enumerate(replikler, start=1):
        mp3 = klasor / f"replik_{i:02d}.mp3"
        _edge_seslendir(r.metin, ses, hiz, pitch, mp3, mp3.with_suffix(".srt"))
        r.ses_yolu = str(mp3)


def _piper_model(ses: str) -> Path:
    """Piper (sherpa-onnx) modelini modeller/ altinda bulur, yoksa indirir."""
    import requests

    klasor = KOK / "modeller" / f"vits-piper-{ses}"
    if (klasor / f"{ses}.onnx").exists():
        return klasor
    klasor.parent.mkdir(parents=True, exist_ok=True)
    arsiv = klasor.parent / f"vits-piper-{ses}.tar.bz2"
    print(f"     Piper sesi indiriliyor ({ses}, ~65 MB, yalnizca ilk sefer)...")
    with requests.get(PIPER_URL.format(ses=ses), stream=True, timeout=300) as y:
        y.raise_for_status()
        with open(arsiv, "wb") as f:
            for parca in y.iter_content(chunk_size=1 << 20):
                f.write(parca)
    with tarfile.open(arsiv, "r:bz2") as tar:
        try:
            tar.extractall(klasor.parent, filter="data")
        except TypeError:                  # Python < 3.12: filter parametresi yok
            tar.extractall(klasor.parent)
    arsiv.unlink(missing_ok=True)
    return klasor


def _piper(replikler, a: dict, klasor: Path):
    import numpy as np
    import sherpa_onnx

    ses = a.get("piper_ses", "tr_TR-dfki-medium")
    model = _piper_model(ses)
    tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=str(model / f"{ses}.onnx"),
                tokens=str(model / "tokens.txt"),
                data_dir=str(model / "espeak-ng-data")),
            num_threads=4)))
    hiz = float(a.get("piper_hiz", 0.88))
    for i, r in enumerate(replikler, start=1):
        cikti = tts.generate(r.metin, sid=0, speed=hiz)
        wav = klasor / f"replik_{i:02d}.wav"
        _wav_yaz(wav, np.array(cikti.samples, dtype=np.float32), cikti.sample_rate)
        r.ses_yolu = str(wav)


def seslendir(c: Cizelge, ayar: dict, klasor: Path) -> str:
    """Tum replikleri seslendirir; kullanilan motorun adini dondurur."""
    a = ayar.get("avatar", {})
    istenen = a.get("ses_motoru", "auto")
    sira = {"auto": ["edge", "piper"], "edge": ["edge", "piper"],
            "piper": ["piper"], "yok": []}.get(istenen, ["edge", "piper"])
    motorlar = {"edge": _edge, "piper": _piper}
    klasor.mkdir(parents=True, exist_ok=True)

    for ad in sira:
        try:
            motorlar[ad](c.replikler, a, klasor)
        except Exception as e:
            print(f"     [ses] {ad} kullanilamadi ({type(e).__name__}: {e})")
            for r in c.replikler:
                r.ses_yolu = ""
            continue
        for r in c.replikler:
            r.sure = len(_wav_oku(Path(r.ses_yolu))) / SR
            if r.sure > r.yuva + 0.05:
                print(f"     [uyari] '{r.metin}' {r.sure:.1f} sn; "
                      f"yuvasi {r.yuva:.1f} sn (bir sonrakiyle cakisabilir)")
        return ad

    # Anlatimsiz: altyazilar yine de okunabilir surelerle gosterilir.
    for r in c.replikler:
        r.sure = min(r.yuva, max(1.2, 0.075 * len(r.metin)))
    return "yok"


# ------------------------------------------------------------------ sentez

def _nota(ad: str) -> float:
    """'A3', 'F#4' gibi nota adini frekansa cevirir (A4 = 440 Hz)."""
    adlar = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3,
             "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    return 440.0 * 2 ** ((adlar[ad[:-1]] + 12 * (int(ad[-1]) - 4)) / 12)


# Dongu basina bir akor (Re majorde huzurlu bir ilerleme).
AKORLAR = [
    ["D3", "A3", "C#4", "F#4"],      # Dmaj7
    ["B2", "F#3", "A3", "D4"],       # Bm7
    ["G2", "D3", "F#3", "B3"],       # Gmaj7
    ["A2", "E3", "A3", "C#4"],       # A
]


def _pad(c: Cizelge, n: int):
    """Dongulere hizali, nefesle hafifce kabaran yumusak akor pad'i."""
    import numpy as np

    # Akor degisim noktalari: giris, her dongu basi, kapanis.
    sinirlar = sorted({0.0, c.kapanis_bas, c.toplam}
                      | {f.bas for f in c.fazlar if f.tur == "al"})
    sig = np.zeros(n, dtype=np.float64)
    for k in range(len(sinirlar) - 1):
        t0, t1 = sinirlar[k], sinirlar[k + 1]
        son = (k == len(sinirlar) - 2)
        akor = AKORLAR[0] if (k == 0 or son) else AKORLAR[(k - 1) % len(AKORLAR)]
        i0 = int(t0 * SR)
        i1 = min(n, int((t1 + 2.5) * SR))           # 2.5 sn sonuma (release)
        t = np.arange(i1 - i0) / SR
        zarf = np.minimum(1.0, t / 1.6)              # yumusak atak
        kuyruk = np.clip((t1 - t0 + 2.5 - t) / 2.5, 0.0, 1.0)
        zarf = zarf * np.minimum(1.0, kuyruk) if not son else zarf
        for j, ad in enumerate(akor):
            f = _nota(ad)
            ton = np.zeros_like(t)
            for detune in (-0.0015, 0.0015):         # hafif koro -> sicaklik
                fd = f * (1 + detune)
                ton += np.sin(2 * math.pi * fd * t + j)
                ton += 0.18 * np.sin(2 * math.pi * 2 * fd * t)
                ton += 0.05 * np.sin(2 * math.pi * 3 * fd * t)
            sig[i0:i1] += ton * zarf / (len(akor) * 2)
    zaman = np.arange(n) / SR
    nefes = np.array([nefes_seviyesi(c, x) for x in zaman[::441]])
    sig *= 0.8 + 0.2 * np.interp(zaman, zaman[::441], nefes)
    return sig / (np.max(np.abs(sig)) or 1.0)


def _can(frekans: float, sure: float = 3.0):
    """Yumusak can/kase sesi (eksponansiyel sonen kismi harmonikler)."""
    import numpy as np

    t = np.arange(int(sure * SR)) / SR
    ses = np.zeros_like(t)
    for oran, genlik, sonum in ((1.0, 1.0, 2.6), (2.0, 0.32, 1.6),
                                (2.76, 0.18, 1.1), (5.4, 0.06, 0.5)):
        ses += genlik * np.sin(2 * math.pi * frekans * oran * t) * np.exp(-t / sonum * 2.2)
    ses *= np.minimum(1.0, t / 0.006)                # tiklamasiz atak
    return ses / np.max(np.abs(ses))


def _canlar(c: Cizelge, n: int):
    import numpy as np

    sig = np.zeros(n)
    tonlar = {"al": _can(_nota("A5")), "tut": _can(_nota("E5")) * 0.55,
              "ver": _can(_nota("D5"))}
    for f in c.fazlar:
        ses = tonlar[f.tur]
        i0 = int(f.bas * SR)
        i1 = min(n, i0 + len(ses))
        sig[i0:i1] += ses[:i1 - i0]
    return sig


def _nefes_sesi(c: Cizelge, n: int, rng):
    """Hava akisina gore kabarip sonen yumusak pembe gurultu (stereo)."""
    import numpy as np

    zaman = np.arange(n) / SR
    adim = 441
    akis = np.array([hava_akisi(c, x) for x in zaman[::adim]])
    zarf = np.interp(zaman, zaman[::adim], akis) ** 1.5
    sol = asmr_ses._renkli_gurultu(n, 1.3, rng)
    sag = asmr_ses._renkli_gurultu(n, 1.3, rng)
    return np.column_stack([sol * zarf, sag * zarf])


def _yanki(x, rng, sure: float = 0.7, islak: float = 0.16):
    """Sese kucuk oda yankisi ekler (FFT konvolusyon, mono)."""
    import numpy as np

    t = np.arange(int(sure * SR)) / SR
    ir = rng.standard_normal(len(t)) * np.exp(-t / sure * 5.0)
    ir[:int(0.012 * SR)] = 0.0                      # 12 ms on-gecikme
    ir /= np.sqrt(np.sum(ir ** 2)) or 1.0
    m = len(x) + len(ir) - 1
    boy = 1 << (m - 1).bit_length()
    yas = np.fft.irfft(np.fft.rfft(x, boy) * np.fft.rfft(ir, boy), boy)[:len(x)]
    return x + islak * yas


def _zarf_takip(x, pencere_sn: float = 0.25):
    """Sesin yumusatilmis genlik zarfi (ducking icin)."""
    import numpy as np

    k = max(1, int(pencere_sn * SR))
    return np.convolve(np.abs(x), np.ones(k) / k, mode="same")


def karistir(c: Cizelge, ayar: dict, hedef: Path) -> Path:
    """Tum ses katmanlarini karistirip stereo WAV yazar."""
    import numpy as np

    a = ayar.get("avatar", {})
    rng = np.random.default_rng(int(a.get("tohum", 7)))
    n = int(c.toplam * SR)

    # 1) Anlatim
    anlatim = np.zeros(n)
    for r in c.replikler:
        if not r.ses_yolu:
            continue
        x = _wav_oku(Path(r.ses_yolu)).astype(np.float64)
        x = x / (np.max(np.abs(x)) or 1.0) * 0.8
        i0 = int(r.bas * SR)
        i1 = min(n, i0 + len(x))
        anlatim[i0:i1] += x[:i1 - i0]
    anlatim = _yanki(anlatim, rng)

    # Anlatim varken arka plani hafifce kis (ducking).
    zarf = _zarf_takip(anlatim)
    duck = 1.0 - 0.35 * np.clip(zarf / (np.max(zarf) or 1.0) * 3.0, 0.0, 1.0)

    # 2) Muzik, can, nefes sesi, ambient
    pad = _pad(c, n) * float(a.get("muzik_seviye", 0.16)) * duck
    canlar = _canlar(c, n) * float(a.get("can_seviye", 0.11))
    nefes = _nefes_sesi(c, n, rng) * float(a.get("nefes_sesi_seviye", 0.05))

    karisim = np.zeros((n, 2))
    karisim += (anlatim * float(a.get("anlatim_seviye", 1.0)))[:, None]
    karisim += pad[:, None]
    karisim[:, 0] += canlar * 0.9
    karisim[:, 1] += canlar
    karisim += nefes

    ambient_tip = a.get("ambient", "yagmur")
    if ambient_tip and ambient_tip != "yok":
        sol, sag = asmr_ses.loop_uret(ambient_tip, c.toplam + 3.5, SR, rng)
        amb = np.column_stack([sol[:n], sag[:n]]) * float(a.get("ambient_seviye", 0.07))
        karisim += amb * duck[:, None]

    # Bas/son yumusak fade + tepe normalizasyonu (-1 dBFS).
    fade_in, fade_out = int(1.2 * SR), int(3.0 * SR)
    karisim[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    karisim[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]
    karisim /= (np.max(np.abs(karisim)) or 1.0) / 0.89

    _wav_yaz(Path(hedef), karisim.astype(np.float32))
    return Path(hedef)

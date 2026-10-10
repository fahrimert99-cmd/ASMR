"""
Cocuk animasyonu muzigi, efekt sesleri ve son karisim (telifsiz, numpy).

  - Muzik: her bolumun ortamina gore akor ilerlemesi + enstruman (marimba,
    kalimba, muzik kutusu, pad); bolum gecislerinde yumusak crossfade.
  - Efektler: senaryodaki olaylara (pirilti, kayan yildiz, konfeti, baykus,
    gokkusagi ...) ve ekrandaki sayi/renk yazilarina bagli kisa sesler.
  - Ortam sesi: yagmur (yagmur durana kadar), gece cirtlaklari, gunduz kuslari.
  - Karisim: anlatim + (anlatim altinda kisilan) muzik + efekt + ortam.
  - Dudak senkronu: kuru anlatim izinden kare basina agiz acikligi.
"""
import math
from pathlib import Path

from src import asmr_ses
from src.avatar_ses import SR, _nota, _wav_oku, _wav_yaz, _yanki

# Ortam -> muzik karakteri.
MUZIK = {
    "oda":        dict(tempo=96, olcu=4, akorlar=["C", "G", "Am", "F"], enstruman="marimba", bas=True, shaker=True),
    "gunduz":     dict(tempo=104, olcu=4, akorlar=["G", "D", "Em", "C"], enstruman="marimba", bas=True, shaker=True),
    "aksam":      dict(tempo=84, olcu=4, akorlar=["F", "C", "Dm", "A#"], enstruman="kalimba", bas=True, shaker=False),
    "gece":       dict(tempo=72, olcu=3, akorlar=["C", "Am", "F", "G"], enstruman="kutu", bas=False, shaker=False),
    "gece_orman": dict(tempo=70, olcu=3, akorlar=["Am", "F", "C", "G"], enstruman="kalimba", bas=False, shaker=False),
    "yagmur":     dict(tempo=64, olcu=4, akorlar=["Dm", "A#", "F", "C"], enstruman="kalimba", bas=False, shaker=False),
    "gokkusagi":  dict(tempo=92, olcu=4, akorlar=["D", "A", "Bm", "G"], enstruman="kutu", bas=True, shaker=True),
    "yildizlar":  dict(tempo=84, olcu=4, akorlar=["F", "G", "Em", "Am"], enstruman="kutu", bas=True, shaker=False),
    "gece_sakin": dict(tempo=60, olcu=3, akorlar=["C", "F", "C", "G"], enstruman="kutu", bas=False, shaker=False),
}

_ISIM = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7,
         "G#": 8, "A": 9, "A#": 10, "B": 11}


def _akor(ad: str, oktav: int = 4):
    """'Am', 'F', 'A#' -> [kok, ters, besli, kok+12] frekanslari."""
    minor = ad.endswith("m")
    kok = _ISIM[ad[:-1] if minor else ad]
    yari = 60 + 12 * (oktav - 4) + kok           # MIDI
    if yari > 64 + 12 * (oktav - 4):            # akoru ayni bolgede tut
        yari -= 12
    araliklar = [0, 3 if minor else 4, 7, 12]
    return [440.0 * 2 ** ((yari + a - 69) / 12) for a in araliklar]


_NOTA_ONBELLEK = {}


def _ton(f: float, tur: str):
    """Tek nota (onbellekli). marimba | kalimba | kutu (muzik kutusu)."""
    import numpy as np

    anahtar = (round(f, 2), tur)
    if anahtar in _NOTA_ONBELLEK:
        return _NOTA_ONBELLEK[anahtar]
    ayar = {"marimba": ([(1, 1.0, 0.45), (4.0, 0.22, 0.08), (10.0, 0.05, 0.02)], 0.9),
            "kalimba": ([(1, 1.0, 0.9), (5.4, 0.16, 0.12), (2.0, 0.08, 0.3)], 1.6),
            "kutu": ([(1, 1.0, 1.4), (2.0, 0.28, 0.6), (3.0, 0.12, 0.35), (4.2, 0.07, 0.2)], 2.2)}
    kismi, sure = ayar[tur]
    t = np.arange(int(sure * SR)) / SR
    x = np.zeros_like(t)
    for oran, genlik, sonum in kismi:
        x += genlik * np.sin(2 * math.pi * f * oran * t) * np.exp(-t / sonum)
    x *= np.minimum(1.0, t / 0.004)
    x /= np.max(np.abs(x))
    _NOTA_ONBELLEK[anahtar] = x
    return x


def _ekle(hedef, ses, t0: float, kazanc: float = 1.0):
    i0 = int(t0 * SR)
    if i0 >= len(hedef) or i0 + len(ses) <= 0:
        return
    if i0 < 0:
        ses, i0 = ses[-i0:], 0
    i1 = min(len(hedef), i0 + len(ses))
    hedef[i0:i1] += ses[:i1 - i0] * kazanc


def _muzik_parcasi(mod: str, sure: float, rng):
    """Bir ortamin `sure` saniyelik muzigini uretir (yerel dizi, t=0'dan)."""
    import numpy as np

    m = MUZIK[mod]
    x = np.zeros(int((sure + 2.5) * SR))
    vurus = 60.0 / m["tempo"]
    olcu_sn = vurus * m["olcu"]
    desen = [0, 1, 2, 3, 2, 1, 2, 1] if m["olcu"] == 4 else [0, 1, 2, 3, 2, 1]
    oktav = 5 if m["enstruman"] == "kutu" else 4
    melodi = 2
    t, olcu = 0.0, 0
    while t < sure:
        akor = m["akorlar"][olcu % len(m["akorlar"])]
        notalar = _akor(akor, oktav)
        ust = olcu % 8 >= 4                       # her 8 olcude bir varyasyon
        for k, i in enumerate(desen):
            f = notalar[i] * (2 if (ust and k % 4 == 3) else 1)
            vurgu = 1.0 if k == 0 else (0.8 if k % 2 == 0 else 0.62)
            _ekle(x, _ton(f, m["enstruman"]), t + k * vurus / 2, 0.30 * vurgu)
        # Basit melodi: olcu basinda akor sesleri arasinda rastgele yuruyus.
        melodi = int(np.clip(melodi + rng.integers(-1, 2), 0, 3))
        _ekle(x, _ton(notalar[melodi] * 2, "kutu"), t, 0.22)
        if m["bas"]:
            _ekle(x, _ton(notalar[0] / 4, "kalimba"), t, 0.55)
        if m["shaker"]:
            for k in range(m["olcu"] * 2):
                if k % 2 == 1:
                    gurultu = rng.standard_normal(int(0.035 * SR))
                    gurultu = np.diff(gurultu, prepend=0) * np.exp(-np.arange(len(gurultu)) / (0.008 * SR))
                    _ekle(x, gurultu, t + k * vurus / 2, 0.035)
        # Yumusak pad (akorun uclusu, yavas atak).
        tp = np.arange(int(olcu_sn * SR * 1.3)) / SR
        zarf = np.minimum(1.0, tp / 0.6) * np.clip((olcu_sn * 1.3 - tp) / 0.7, 0, 1)
        pad = sum(np.sin(2 * math.pi * f / 2 * tp) for f in notalar[:3]) / 3
        _ekle(x, pad * zarf, t, 0.10)
        t += olcu_sn
        olcu += 1
    return x[:int(sure * SR)]


def _muzik(c, n: int, rng):
    """Bolum ortamlarina gore tum videonun muzigi (gecislerde crossfade)."""
    import numpy as np

    x = np.zeros(n, dtype=np.float32)
    sinirlar = [0.0] + [b.bas - 0.8 for b in c.bolumler[1:]] + [c.toplam]
    ortamlar = [b.ortam for b in c.bolumler]
    ortu = 2.5
    for i, mod in enumerate(ortamlar):
        t0, t1 = sinirlar[i], sinirlar[i + 1]
        p0 = max(0.0, t0 - ortu)
        p1 = min(c.toplam, t1 + ortu)
        parca = _muzik_parcasi(mod, p1 - p0, rng)
        zaman = p0 + np.arange(len(parca)) / SR
        if i > 0:
            parca = parca * np.clip((zaman - t0 + ortu / 2) / ortu, 0, 1)
        if i < len(ortamlar) - 1:
            parca = parca * np.clip((t1 + ortu / 2 - zaman) / ortu, 0, 1)
        _ekle(x, parca.astype(np.float32), p0)
    return x / (np.max(np.abs(x)) or 1.0)


# ------------------------------------------------------------------ efektler

def _gurultu_suzgec(n: int, merkez, genislik: float, rng):
    """Merkez frekansi zamanla degisen bant geciren gurultu (STFT ile)."""
    import numpy as np

    pencere = 1024
    adim = pencere // 2
    w = np.hanning(pencere)
    x = rng.standard_normal(n + pencere)
    y = np.zeros(n + pencere)
    f = np.fft.rfftfreq(pencere, 1 / SR)
    for i in range(0, n, adim):
        fc = merkez(i / max(1, n - 1))
        maske = np.exp(-((f - fc) / genislik) ** 2)
        y[i:i + pencere] += np.fft.irfft(np.fft.rfft(x[i:i + pencere] * w) * maske, pencere) * w
    y = y[:n]
    return y / (np.max(np.abs(y)) or 1.0)


def _pirilti(yukari: bool = True):
    import numpy as np

    notalar = ["C6", "E6", "G6", "C7", "E7", "G7"]
    if not yukari:
        notalar = notalar[::-1]
    x = np.zeros(int(2.2 * SR))
    for i, ad in enumerate(notalar):
        _ekle(x, _ton(_nota(ad), "kutu") * (0.9 - 0.08 * i), i * 0.055)
    return x / np.max(np.abs(x))


def _vuus(sure: float, yukari: bool, rng):
    import numpy as np

    n = int(sure * SR)
    merkez = (lambda u: 400 + 3200 * u) if yukari else (lambda u: 3600 - 3200 * u)
    x = _gurultu_suzgec(n, merkez, 700.0, rng)
    u = np.linspace(0, 1, n)
    return x * np.sin(math.pi * u) ** 1.5


def _pop(f0: float = 700.0):
    import numpy as np

    t = np.arange(int(0.12 * SR)) / SR
    f = f0 * (1 - 0.45 * np.minimum(1, t / 0.06))
    faz = 2 * math.pi * np.cumsum(f) / SR
    return np.sin(faz) * np.exp(-t / 0.035) * np.minimum(1, t / 0.002)


def _fanfar():
    import numpy as np

    x = np.zeros(int(2.4 * SR))
    for i, ad in enumerate(["C5", "E5", "G5", "C6"]):
        _ekle(x, _ton(_nota(ad), "marimba"), i * 0.09, 0.8)
    for ad in ("C5", "E5", "G5", "C6"):
        _ekle(x, _ton(_nota(ad), "kutu"), 0.42, 0.35)
    return x / np.max(np.abs(x))


def _baykus():
    import numpy as np

    x = np.zeros(int(1.6 * SR))
    for t0, sure, f0 in ((0.0, 0.28, 400.0), (0.42, 0.75, 385.0)):
        t = np.arange(int(sure * SR)) / SR
        f = f0 * (1 - 0.08 * t / sure) * (1 + 0.012 * np.sin(2 * math.pi * 5.5 * t))
        faz = 2 * math.pi * np.cumsum(f) / SR
        zarf = np.sin(math.pi * np.clip(t / sure, 0, 1)) ** 0.8
        _ekle(x, (np.sin(faz) + 0.18 * np.sin(2 * faz)) * zarf, t0)
    return x / np.max(np.abs(x))


def _arp_gliss():
    import numpy as np

    x = np.zeros(int(3.0 * SR))
    for i, ad in enumerate(["C5", "D5", "E5", "G5", "A5", "C6", "D6", "E6", "G6"]):
        _ekle(x, _ton(_nota(ad), "kalimba"), i * 0.12, 0.8)
    return x / np.max(np.abs(x))


def _puf(rng):
    import numpy as np

    n = int(0.7 * SR)
    x = _gurultu_suzgec(n, lambda u: 500 - 250 * u, 350.0, rng)
    return x * np.sin(math.pi * np.linspace(0, 1, n)) ** 2


def _kus(rng):
    import numpy as np

    x = np.zeros(int(0.5 * SR))
    for k in range(int(rng.integers(2, 4))):
        t = np.arange(int(0.07 * SR)) / SR
        f = rng.uniform(2600, 3400) + 1600 * t / 0.07
        faz = 2 * math.pi * np.cumsum(f) / SR
        _ekle(x, np.sin(faz) * np.sin(math.pi * t / 0.07), k * 0.11)
    return x


def _efektler(c, n: int, rng):
    """Olaylara, bolum baslarina ve ekran yazilarina bagli efekt izi."""
    import numpy as np

    x = np.zeros(n, dtype=np.float32)
    pir = _pirilti()
    _ekle(x, pir, 0.4, 0.8)
    _ekle(x, _fanfar(), 1.2, 0.6)
    for b in c.bolumler:
        _ekle(x, _ton(_nota("G5"), "kutu"), b.bas, 0.35)
        _ekle(x, _ton(_nota("C6"), "kutu"), b.bas + 0.16, 0.3)
    for t, olay, _ in c.olaylar:
        if olay in ("pirilti", "piril_gel", "bulut_mutlu"):
            _ekle(x, pir, t, 0.55)
        elif olay == "atesbocegi_cok":
            _ekle(x, pir, t, 0.3)
        elif olay == "kayan_yildiz":
            _ekle(x, _vuus(1.4, False, rng), t, 0.7)
            _ekle(x, _pirilti(False), t + 0.9, 0.45)
        elif olay == "piril_git":
            _ekle(x, _vuus(1.6, True, rng), t, 0.7)
            _ekle(x, pir, t + 0.5, 0.6)
        elif olay == "konfeti":
            _ekle(x, _fanfar(), t, 0.75)
            for k in range(5):
                _ekle(x, _pop(rng.uniform(600, 1100)), t + 0.1 + k * rng.uniform(0.08, 0.2), 0.35)
        elif olay == "kalpler":
            for k in range(3):
                _ekle(x, _pop(650 + 180 * k), t + 0.15 + k * 0.22, 0.4)
            _ekle(x, _ton(_nota("E6"), "kutu"), t + 0.8, 0.3)
        elif olay == "piril_mutlu" or olay == "yagmur_dur":
            _ekle(x, _ton(_nota("E6"), "kutu"), t, 0.4)
            _ekle(x, _ton(_nota("G6"), "kutu"), t + 0.12, 0.35)
        elif olay in ("bulut_gel", "bulut_git", "baykus_git"):
            _ekle(x, _puf(rng), t, 0.6)
        elif olay == "baykus_gel":
            _ekle(x, _baykus(), t + 0.6, 0.55)
        elif olay == "gokkusagi_cik":
            _ekle(x, _arp_gliss(), t, 0.65)
    for s in c.satirlar:
        if s.ekran:
            _ekle(x, _pop(900), s.bas, 0.45)
    return x


def _ortam_sesi(c, n: int, rng):
    """Yagmur / gece cirtlaklari / gunduz kuslari (stereo)."""
    import numpy as np

    x = np.zeros((n, 2), dtype=np.float32)
    dur = c.olay_zamani("yagmur_dur")
    for b in c.bolumler:
        bas, bit = max(0.0, b.bas - 1.0), min(c.toplam, b.bit + 1.0)
        m = int((bit - bas) * SR)
        zaman = bas + np.arange(m) / SR
        zarf = np.clip((zaman - bas) / 2.0, 0, 1) * np.clip((bit - zaman) / 2.0, 0, 1)
        if b.ortam in ("yagmur", "gece", "gece_orman", "gece_sakin"):
            tip = "yagmur" if b.ortam == "yagmur" else "gece"
            sol, sag = asmr_ses.loop_uret(tip, 30.0, SR, rng)
            tekrar = int(math.ceil(m / len(sol)))
            iz = np.column_stack([np.tile(sol, tekrar)[:m], np.tile(sag, tekrar)[:m]])
            if b.ortam == "yagmur":
                son = next((t for t in dur if bas <= t <= bit), bit)
                zarf = zarf * np.clip((son + 1.5 - zaman) / 2.5, 0, 1)
                seviye = 0.55
            else:
                seviye = 0.16 if b.ortam == "gece_orman" else 0.10
            i0 = int(bas * SR)
            x[i0:i0 + m] += (iz * (zarf * seviye)[:, None]).astype(np.float32)[:n - i0]
        elif b.ortam in ("gunduz", "oda"):
            t = bas + float(rng.uniform(1, 3))
            while t < bit:
                kus = _kus(rng) * (0.22 if b.ortam == "gunduz" else 0.10)
                kanal = int(rng.integers(0, 2))
                _ekle(x[:, kanal], kus, t)
                _ekle(x[:, 1 - kanal], kus * 0.4, t + 0.01)
                t += float(rng.uniform(2.0, 5.5))
    return x


# ------------------------------------------------------------------ agiz zarfi

def agiz_zarfi(anlatim, fps: int, toplam_kare: int):
    """Kuru anlatim izinden kare basina agiz acikligi (0..1) ve konusma (0..1)."""
    import numpy as np

    pencere = int(SR / fps)
    yarim = pencere
    ileri = int(0.015 * SR)                       # dudak, sesten hafif once acilir
    rms = np.zeros(toplam_kare)
    kare2 = np.concatenate([np.zeros(yarim), anlatim.astype(np.float64) ** 2,
                            np.zeros(yarim + ileri + pencere)])
    toplamli = np.concatenate([[0.0], np.cumsum(kare2)])
    for k in range(toplam_kare):
        merkez = k * pencere + yarim + ileri
        a, b = merkez - yarim // 2, merkez + yarim // 2 + pencere // 2
        rms[k] = math.sqrt(max(0.0, (toplamli[b] - toplamli[a]) / (b - a)))
    db = 20 * np.log10(rms + 1e-7)
    sesli = db[db > -60]
    tepe = np.percentile(sesli, 95) if len(sesli) else -20.0
    acik = np.clip((db - (tepe - 28)) / 22.0, 0, 1) ** 0.9
    # Asimetrik yumusatma: hizli acil, biraz daha yavas kapan.
    yum = np.zeros_like(acik)
    for k in range(1, toplam_kare):
        oran = 0.75 if acik[k] > yum[k - 1] else 0.5
        yum[k] = yum[k - 1] + (acik[k] - yum[k - 1]) * oran
    konusma = np.convolve((yum > 0.12).astype(float), np.ones(9) / 9, mode="same")
    return yum, konusma


# ------------------------------------------------------------------ karisim

def _yavas_zarf(x, n: int, pencere_sn: float = 0.25):
    """|x|'in hareketli ortalamasi (100 Hz cozunurlukte hesaplanip genisletilir)."""
    import numpy as np

    blok = SR // 100
    m = len(x) // blok
    kaba = np.abs(x[:m * blok]).reshape(m, blok).mean(axis=1)
    k = max(1, int(pencere_sn * 100))
    c = np.concatenate([[0.0], np.cumsum(np.pad(kaba, (k // 2, k - k // 2), mode="edge"))])
    ort = (c[k:] - c[:-k]) / k
    return np.interp(np.arange(n) / blok, np.arange(len(ort)), ort).astype(np.float32)


def karistir(c, ayar: dict, hedef: Path, fps: int):
    """Tum sesleri karistirip WAV yazar; (wav_yolu, agiz, konusma) dondurur."""
    import numpy as np

    a = ayar.get("cocuk", {})
    rng = np.random.default_rng(int(a.get("tohum", 11)))
    n = int(c.toplam * SR)

    kuru = np.zeros(n, dtype=np.float32)
    islak = np.zeros(n, dtype=np.float32)
    for s in c.satirlar:
        if s.ses_yolu:
            ses = _wav_oku(Path(s.ses_yolu)).astype(np.float64)
            ses = ses / (np.max(np.abs(ses)) or 1.0) * 0.8
            _ekle(kuru, ses.astype(np.float32), s.bas)
            ses = np.concatenate([ses, np.zeros(int(0.5 * SR))])
            _ekle(islak, _yanki(ses, rng, sure=0.5, islak=0.10).astype(np.float32), s.bas)
    toplam_kare = int(round(c.toplam * fps))
    agiz, konusma = agiz_zarfi(kuru, fps, toplam_kare)

    zarf = _yavas_zarf(kuru, n)
    duck = 1.0 - 0.45 * np.clip(zarf / (np.max(zarf) or 1.0) * 3.0, 0.0, 1.0)

    karisim = np.zeros((n, 2), dtype=np.float32)
    karisim += (islak * float(a.get("anlatim_seviye", 1.0)))[:, None]
    muzik = _muzik(c, n, rng) * float(a.get("muzik_seviye", 0.13)) * duck
    karisim[:, 0] += muzik * 0.95
    karisim[:, 1] += muzik
    del muzik
    efekt = _efektler(c, n, rng) * float(a.get("efekt_seviye", 0.30))
    karisim[:, 0] += efekt * 0.9
    karisim[:, 1] += efekt
    del efekt
    karisim += _ortam_sesi(c, n, rng) * float(a.get("ortam_seviye", 0.10)) * duck[:, None]

    fade_in, fade_out = int(0.8 * SR), int(4.0 * SR)
    karisim[:fade_in] *= np.linspace(0, 1, fade_in, dtype=np.float32)[:, None]
    karisim[-fade_out:] *= np.linspace(1, 0, fade_out, dtype=np.float32)[:, None]
    karisim *= 0.89 / (float(np.max(np.abs(karisim))) or 1.0)
    _wav_yaz(Path(hedef), karisim)
    return Path(hedef), agiz, konusma

"""
Masal videosu — sentez müzik ve ses efektleri (telifsiz, tamamen kod).

Enstrümanlar
  * Bağlama : Karplus-Strong telli çalgı (çift tel, kesirli gecikme ile doğru
              perde → makam mikrotonları), tezene tremolosu.
  * Kaval   : nefesli, vibratolu, portamentolu ezgi.
  * Def     : düm / tek / zilli şıkırtı.
  * Davul-zurna : düğün halayı (davul: harita_ses; zurna: genizden, formantlı).
  * Dem     : gece ve gerilim için uzun alt ses.

Efektler: sayfa hışırtısı, kapı gıcırtısı, tahta çatırtısı, GÜM, düşüş, adımlar,
koşma, ateş çıtırtısı, cırcır böceği, baykuş, kurt uluması, kuşlar, horoz,
altın şıngırtısı, elma "pıt"ı, çınlama.

Makam perdeleri cent cinsindendir (koma doğruluğunda): örn. Rast'ın segâhı 384 c.
"""
import math

import numpy as np
from scipy import signal

from src.harita_ses import (SR, Mikser, _filtre, _gurultu, _oda_yankisi, _sos, _t, _wav_yaz, davul_dum, davul_tek,
                            parsomen, whoosh, zil)

MAKAM = {
    "rast": [0, 204, 384, 498, 702, 906, 1088],
    "ussak": [0, 150, 294, 498, 702, 792, 996],
    "huseyni": [0, 150, 294, 498, 702, 884, 996],
    "hicaz": [0, 114, 384, 498, 702, 792, 996],
    "kurdi": [0, 90, 294, 498, 702, 792, 996],
    "nihavend": [0, 204, 294, 498, 702, 792, 1088],
}


def perde(karar, makam, derece):
    o, s = divmod(int(derece), 7)
    return karar * 2 ** ((MAKAM[makam][s] + 1200 * o) / 1200)


# ================================================================ enstrumanlar
def baglama(f, sure=1.6, guc=1.0, rng=None, parlak=0.55, cent=3.0):
    """Karplus-Strong cift tel (hafif akort farki) + govde rezonansi."""
    rng = rng or np.random.default_rng(int(f * 10) % 9999)
    n = int(sure * SR)
    out = np.zeros(n)
    for detune in (-cent, cent):
        fd = f * 2 ** (detune / 1200)
        D = SR / fd
        N = int(math.floor(D))
        d = D - N
        g = 0.9965 if f < 500 else 0.993
        x = np.zeros(n)
        uyar = rng.uniform(-1, 1, N)
        uyar = signal.lfilter([parlak, 1 - parlak], [1], uyar)          # mizrap parlakligi
        x[:N] = uyar
        a = np.zeros(N + 2)
        a[0] = 1.0
        a[N] = -g * (1 - d)
        a[N + 1] = -g * d
        out += signal.lfilter([1.0], a, x)
    out = out + 0.35 * _filtre(out, "bp", (180, 320)) + 0.25 * _filtre(out, "bp", (1800, 3200))
    zarf = np.ones(n)
    k = int(0.06 * SR)
    zarf[-k:] = np.linspace(1, 0, k)
    return out * zarf * guc * 0.32


def kaval(notalar, sure, rng, parlak=1.0, vibrato=14.0):
    """notalar: [(t, dur, f)] -> nefesli ezgi (portamento + vibrato + nefes)."""
    n = int(sure * SR)
    fr = np.zeros(n)
    amp = np.zeros(n)
    son_f = notalar[0][2] if notalar else 440.0
    for (t0, dur, f) in notalar:
        i0, i1 = int(t0 * SR), min(n, int((t0 + dur) * SR))
        if i1 <= i0:
            continue
        L = i1 - i0
        u = np.arange(L) / SR
        kay = np.clip(u / 0.045, 0, 1)
        fr[i0:i1] = son_f + (f - son_f) * (1 - (1 - kay) ** 2)
        vib = 1 + (vibrato / 1200) * math.log(2) * np.sin(2 * np.pi * 5.4 * u) * np.clip((u - 0.18) / 0.25, 0, 1)
        fr[i0:i1] *= vib
        a = np.minimum(1.0, u / 0.05) * np.minimum(1.0, (dur - u) / 0.09).clip(0, 1)
        amp[i0:i1] = np.maximum(amp[i0:i1], a)
        son_f = f
    fr[fr == 0] = son_f
    amp = signal.sosfiltfilt(signal.butter(1, 40 / (SR / 2), output="sos"), amp)
    faz = 2 * np.pi * np.cumsum(fr) / SR
    ton = np.sin(faz) + 0.22 * parlak * np.sin(2 * faz) + 0.07 * parlak * np.sin(3 * faz)
    nefes = _filtre(rng.standard_normal(n), "bp", (900, 4200)) * 0.18
    return (ton + nefes) * amp * 0.28


def zurna(notalar, sure, rng):
    """Genizden, keskin zurna: zengin harmonik + formant + hizli vibrato."""
    n = int(sure * SR)
    fr = np.zeros(n)
    amp = np.zeros(n)
    son_f = notalar[0][2]
    for (t0, dur, f) in notalar:
        i0, i1 = int(t0 * SR), min(n, int((t0 + dur) * SR))
        if i1 <= i0:
            continue
        u = np.arange(i1 - i0) / SR
        kay = np.clip(u / 0.025, 0, 1)
        fr[i0:i1] = (son_f + (f - son_f) * kay) * (1 + 0.006 * np.sin(2 * np.pi * 6.5 * u))
        amp[i0:i1] = np.minimum(1, u / 0.02) * np.clip((dur - u) / 0.04, 0, 1)
        son_f = f
    fr[fr == 0] = son_f
    faz = 2 * np.pi * np.cumsum(fr) / SR
    ton = sum(np.sin(k * faz) / k ** 0.65 for k in range(1, 13))
    ton = 0.55 * _filtre(ton, "bp", (900, 1500)) + 0.45 * _filtre(ton, "bp", (2200, 3400)) + 0.15 * ton
    return np.tanh(ton * 1.5) * amp * 0.22


def def_dum(rng, guc=1.0):
    t = _t(0.55)
    f = 82 + 70 * np.exp(-t / 0.028)
    govde = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.20)
    tok = _filtre(_gurultu(rng, 0.55), "lp", 700) * np.exp(-t / 0.018) * 0.5
    return (govde + tok) * guc * 0.8


def def_tek(rng, guc=1.0):
    t = _t(0.3)
    deri = _filtre(_gurultu(rng, 0.3), "bp", (1400, 5500)) * np.exp(-t / 0.035)
    ton = np.sin(2 * np.pi * 640 * t) * np.exp(-t / 0.04) * 0.3
    zilli = _filtre(_gurultu(rng, 0.3), "hp", 6500) * np.exp(-t / 0.11) * 0.35
    return (deri * 0.6 + ton + zilli) * guc * 0.7


def dem(karar, sure, rng, makam="hicaz", parlak=0.4):
    """Uzun alt ses: karar + besli, yavas nefes alan genlik."""
    t = _t(sure)
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * t + rng.uniform(0, 6))
    x = (np.sin(2 * np.pi * karar / 2 * t) * 0.6 + np.sin(2 * np.pi * karar * t) * 0.35
         + np.sin(2 * np.pi * perde(karar, makam, 4) * t) * 0.22 * parlak)
    x += _filtre(rng.standard_normal(len(t)), "lp", 300) * 0.04
    gir = np.clip(t / 1.2, 0, 1)
    cik = np.clip((sure - t) / 1.0, 0, 1)
    return x * lfo * gir * cik * 0.22


# ================================================================ efektler
def sayfa_hisirtisi(rng):
    x = parsomen(rng, 0.9, 1.0)
    t = _t(0.9)
    sw = _filtre(_gurultu(rng, 0.9), "bp", (1500, 6000)) * np.sin(np.pi * np.clip(t / 0.9, 0, 1)) ** 2 * 0.25
    return x + sw


def gicirti(rng, sure=1.2, guc=1.0):
    """Mentese gicirtisi: degisken hizli surtunme darbeleri + rezonans."""
    t = _t(sure)
    hiz = 35 + 45 * np.sin(np.pi * t / sure) + 10 * np.sin(2 * np.pi * 1.7 * t)
    faz = np.cumsum(hiz) / SR
    darbe = (np.mod(faz, 1.0) < 0.08).astype(float)
    x = _filtre(darbe, "bp", (700, 1600)) * 2 + _filtre(darbe, "bp", (2200, 3000))
    return x * np.sin(np.pi * t / sure) ** 0.5 * guc * 0.35


def catirti(rng, guc=1.0):
    """Tahta catirtisi / menteseden kopma."""
    t = _t(0.9)
    x = np.zeros_like(t)
    for _ in range(9):
        i = rng.integers(0, int(0.25 * SR))
        L = int(0.06 * SR)
        tt = np.arange(L) / SR
        x[i:i + L] += rng.standard_normal(L) * np.exp(-tt / rng.uniform(0.004, 0.02))
    x = _filtre(x, "bp", (300, 5000))
    gum = np.sin(2 * np.pi * (70 + 60 * np.exp(-t / 0.05)) * t) * np.exp(-t / 0.15)
    return (x * 0.8 + gum * 0.7) * guc


def gum(rng, guc=1.0):
    """Kocaman GUM: derin vurus + tahta kirilmasi + yer sarsintisi."""
    t = _t(2.4)
    f = 42 + 80 * np.exp(-t / 0.06)
    govde = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.5)
    tok = _filtre(_gurultu(rng, 2.4), "lp", 500) * np.exp(-t / 0.06)
    tahta = _filtre(_gurultu(rng, 2.4), "bp", (400, 3500)) * np.exp(-t / 0.09) * 0.7
    return (govde * 1.2 + tok * 0.8 + tahta) * guc


def adimlar(rng, sure, aralik=0.36, guc=1.0, agir=False):
    n = int(sure * SR)
    x = np.zeros(n)
    t = 0.0
    while t < sure - 0.2:
        i = int(t * SR)
        L = int(0.12 * SR)
        tt = np.arange(L) / SR
        darbe = _filtre(rng.standard_normal(L) * np.exp(-tt / (0.03 if agir else 0.02)), "lp", 700 if agir else 1100)
        m = min(L, n - i)
        x[i:i + m] += darbe[:m]
        t += aralik * rng.uniform(0.92, 1.08)
    return x * guc * 0.5


def ates_citirti(rng, sure, guc=1.0):
    n = int(sure * SR)
    x = _filtre(rng.standard_normal(n), "lp", 400) * 0.25
    for _ in range(int(sure * 14)):
        i = rng.integers(0, n - 2000)
        L = rng.integers(60, 900)
        tt = np.arange(L) / SR
        x[i:i + L] += rng.standard_normal(L) * np.exp(-tt / rng.uniform(0.0008, 0.004)) * rng.uniform(0.2, 1.2)
    x = _filtre(x, "hp", 80)
    gir = np.clip(np.arange(n) / (0.8 * SR), 0, 1)
    return x * gir * guc * 0.35


def circir(rng, sure, guc=1.0):
    """Cirkir bocekleri: 4.4-5 kHz cirpinma kumeleri."""
    n = int(sure * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(3):
        f = rng.uniform(4300, 5100)
        hiz = rng.uniform(2.2, 3.4)
        kapi = (np.sin(2 * np.pi * hiz * t + k) > 0.55).astype(float)
        titre = 0.5 + 0.5 * np.sin(2 * np.pi * 42 * t)
        x += np.sin(2 * np.pi * f * t) * kapi * titre * rng.uniform(0.5, 1.0)
    x = signal.sosfiltfilt(signal.butter(2, [3500 / (SR / 2), 7000 / (SR / 2)], "bandpass", output="sos"), x)
    gir = np.clip(t / 1.5, 0, 1) * np.clip((sure - t) / 1.0, 0, 1)
    return x * gir * guc * 0.05


def baykus(rng, guc=1.0):
    t = _t(1.6)
    x = np.zeros_like(t)
    for t0, f0, d in ((0.0, 390, 0.32), (0.55, 360, 0.55)):
        u = t - t0
        m = (u >= 0) & (u < d)
        f = f0 * (1 + 0.04 * np.sin(np.pi * np.clip(u / d, 0, 1)))
        x += np.where(m, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.clip(u / d, 0, 1)) ** 1.5, 0)
    return x * guc * 0.4


def kurt_ulumasi(rng, guc=1.0):
    t = _t(3.2)
    u = t / 3.2
    f = 380 + 330 * np.sin(np.pi * np.clip(u * 1.3, 0, 1)) ** 0.8 - 80 * u
    f *= 1 + 0.012 * np.sin(2 * np.pi * 5.5 * t)
    faz = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(faz) + 0.3 * np.sin(2 * faz) + 0.1 * np.sin(3 * faz)
    nefes = _filtre(rng.standard_normal(len(t)), "bp", (600, 2500)) * 0.15
    zarf = np.clip(u / 0.12, 0, 1) * np.clip((1 - u) / 0.3, 0, 1)
    return (x + nefes) * zarf * guc * 0.3


def kus_civiltisi(rng, sure, guc=1.0, yogun=1.0):
    n = int(sure * SR)
    x = np.zeros(n)
    t = rng.uniform(0, 0.6)
    while t < sure - 0.4:
        adet = rng.integers(2, 6)
        f0 = rng.uniform(2800, 5200)
        for j in range(adet):
            L = int(rng.uniform(0.04, 0.09) * SR)
            tt = np.arange(L) / SR
            f = f0 * (1 + rng.uniform(0.15, 0.45) * np.sin(np.pi * tt / tt[-1]) * rng.choice([-1, 1]))
            cp = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / tt[-1]) ** 2
            i = int((t + j * 0.09) * SR)
            if i + L < n:
                x[i:i + L] += cp * rng.uniform(0.4, 1.0)
        t += rng.uniform(0.6, 2.2) / yogun
    return x * guc * 0.12


def horoz(rng, guc=1.0):
    t = _t(1.6)
    egri = [(0.0, 520), (0.18, 640), (0.30, 600), (0.45, 760), (1.2, 720), (1.45, 560)]
    f = np.interp(t, [a for a, _ in egri], [b for _, b in egri])
    faz = 2 * np.pi * np.cumsum(f) / SR
    ton = sum(np.sin(k * faz) / k for k in range(1, 9))
    ton = _filtre(ton, "bp", (700, 2600))
    zarf = np.clip(t / 0.05, 0, 1) * np.clip((1.5 - t) / 0.2, 0, 1) * (0.7 + 0.3 * np.sin(2 * np.pi * 18 * t))
    return np.tanh(ton * 2) * zarf * guc * 0.18


def tavuk_gidaklama(rng, guc=1.0):
    t = _t(0.9)
    x = np.zeros_like(t)
    for t0 in (0.0, 0.17, 0.32, 0.55):
        u = t - t0
        m = (u >= 0) & (u < 0.11)
        f = 420 * (1 + 0.5 * np.clip(u / 0.11, 0, 1))
        x += np.where(m, np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.sin(np.pi * np.clip(u / 0.11, 0, 1)), 0)
    return _filtre(x, "bp", (500, 2000)) * guc * 0.12


def sikke_singirtisi(rng, adet=6, sure=2.0, guc=1.0):
    n = int(sure * SR)
    x = np.zeros(n)
    for _ in range(adet):
        i = rng.integers(0, max(1, n - int(0.5 * SR)))
        tt = np.arange(int(0.45 * SR)) / SR
        b = sum(np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * a * np.exp(-tt / d)
                for f, a, d in ((rng.uniform(3000, 3600), 0.5, 0.12), (rng.uniform(4600, 5200), 0.35, 0.08),
                                (rng.uniform(6400, 7200), 0.25, 0.05), (rng.uniform(8500, 9500), 0.2, 0.03)))
        x[i:i + len(tt)] += b * rng.uniform(0.4, 1.0)
    return x * guc * 0.18


def elma_pit(rng, guc=1.0):
    t = _t(0.4)
    pit = np.sin(2 * np.pi * (180 + 300 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.06)
    cin = np.sin(2 * np.pi * 1568 * t) * np.exp(-t / 0.25) * 0.25 + np.sin(2 * np.pi * 2349 * t) * np.exp(-t / 0.2) * 0.15
    return (pit * 0.8 + cin) * guc


def cinlama(rng, karar=392.0, guc=1.0):
    """Muzik kutusu benzeri yukselen arpej."""
    t = _t(2.6)
    x = np.zeros_like(t)
    for j, d in enumerate((0, 2, 4, 7, 9)):
        f = perde(karar * 2, "rast", d)
        u = t - j * 0.11
        x += np.where(u >= 0, np.sin(2 * np.pi * f * u) * np.exp(-np.clip(u, 0, None) / 0.6), 0) * 0.3
        x += np.where(u >= 0, np.sin(2 * np.pi * f * 2.76 * u) * np.exp(-np.clip(u, 0, None) / 0.18), 0) * 0.06
    return x * guc


def kalp(rng, sure, hiz=1.2, guc=1.0):
    n = int(sure * SR)
    x = np.zeros(n)
    t = 0.0
    while t < sure - 0.4:
        for d, g in ((0.0, 1.0), (0.22, 0.7)):
            i = int((t + d) * SR)
            s = def_dum(rng, g)
            m = min(len(s), n - i)
            if m > 0:
                x[i:i + m] += s[:m]
        t += 1.0 / hiz
        hiz *= 1.06
    return x * guc


def kalabalik(rng, sure, guc=1.0):
    """Uzak kalabalik ugultusu (konusma formantli gurultu)."""
    n = int(sure * SR)
    g = rng.standard_normal(n)
    x = 0.6 * _filtre(g, "bp", (250, 900)) + 0.3 * _filtre(g, "bp", (1100, 2400))
    lfo = 0.7 + 0.3 * signal.sosfiltfilt(signal.butter(1, 3 / (SR / 2), output="sos"), rng.standard_normal(n)) * 3
    return x * np.clip(lfo, 0.2, 1.3) * guc * 0.08


def ruzgar(rng, sure, guc=1.0):
    n = int(sure * SR)
    g = rng.standard_normal(n)
    mod = signal.sosfiltfilt(signal.butter(1, 0.4 / (SR / 2), output="sos"), rng.standard_normal(n))
    mod = 0.6 + 0.4 * mod / (np.abs(mod).max() + 1e-9)
    x = _filtre(g, "bp", (250, 1200)) * mod
    t = np.arange(n) / SR
    return x * np.clip(t / 1.5, 0, 1) * np.clip((sure - t) / 1.5, 0, 1) * guc * 0.12


# ================================================================ ezgiler
# (derece, vurus) — derece makam dizisinin basamagi (7 = ust oktav karar)
TEMA = [(4, 1), (5, .5), (4, .5), (3, 1), (2, 1), (3, .5), (4, .5), (3, .5), (2, .5), (1, 2),
        (2, 1), (3, .5), (2, .5), (1, 1), (0, 1), (1, .5), (2, .5), (1, .5), (0, .5), (0, 2)]
TEMA_B = [(7, 1), (6, .5), (5, .5), (4, 1), (5, 1), (6, .5), (5, .5), (4, .5), (3, .5), (4, 2),
          (4, 1), (3, .5), (2, .5), (3, 1), (2, 1), (1, .5), (2, .5), (1, .5), (0, .5), (0, 2)]
HALAY = [(4, .5), (4, .25), (5, .25), (4, .5), (3, .5), (4, .5), (2, .5), (3, 1),
         (2, .5), (3, .25), (4, .25), (3, .5), (2, .5), (1, .5), (2, .5), (0, 1)]
GECE = [(0, 2), (1, 1), (2, 1), (1, 2), (0, 2), (-1, 1), (0, 3)]


def ezgi_zaman(desen, t0, vurus, karar, makam, tekrar=1, oktav=0, tavan=None):
    out = []
    t = t0
    for _ in range(tekrar):
        for d, v in desen:
            if tavan is not None and t >= tavan:
                return out
            out.append((t, v * vurus * 0.96, perde(karar, makam, d + 7 * oktav)))
            t += v * vurus
    return out


# ================================================================ bolumler
class Besteci:
    """Sayfa zaman cizelgesine gore bolum bolum muzik + efekt yerlestirir."""

    def __init__(self, M, rng):
        self.M, self.rng = M, rng

    def ekle(self, sig, t, pan=0.0, kazanc=1.0, yanki=0.3):
        self.M.ekle(sig, t, pan=pan, kazanc=kazanc, yanki=yanki)

    def baglama_ezgi(self, notalar, kazanc=0.5, pan=-0.15, tremolo=False, uzunluk=1.4):
        for (t, d, f) in notalar:
            if tremolo and d > 0.3:
                k = 0.0
                while k < d - 0.05:
                    self.ekle(baglama(f, 0.5, 0.75 if k else 1.0, self.rng), t + k, pan=pan, kazanc=kazanc, yanki=0.3)
                    k += 1 / 12.0
            else:
                self.ekle(baglama(f, max(uzunluk, d + 0.3), 1.0, self.rng), t, pan=pan, kazanc=kazanc, yanki=0.3)

    def def_ritim(self, t0, t1, vurus, desen="DtTt", kazanc=0.35):
        t, k = t0, 0
        while t < t1 - 0.05:
            ch = desen[k % len(desen)]
            if ch == "D":
                self.ekle(def_dum(self.rng), t, pan=0.1, kazanc=kazanc, yanki=0.2)
            elif ch == "T":
                self.ekle(def_tek(self.rng), t, pan=0.25, kazanc=kazanc * 0.8, yanki=0.2)
            elif ch == "t":
                self.ekle(def_tek(self.rng, 0.5), t, pan=0.3, kazanc=kazanc * 0.6, yanki=0.2)
            t += vurus / 2
            k += 1

    def kaval_ekle(self, notalar, t0, sure, kazanc=0.6, pan=0.2):
        if not notalar:
            return
        yerel = [(t - t0, d, f) for t, d, f in notalar]
        self.ekle(kaval(yerel, sure, self.rng), t0, pan=pan, kazanc=kazanc, yanki=0.55)

    # ---------------------------------------------------------- ruh halleri
    def bolum(self, ruh, t0, t1, sayfa):
        getattr(self, "b_" + ruh)(t0, t1, sayfa)

    def b_giris(self, t0, t1, s):
        G = 392.0
        self.ekle(dem(G / 2, t1 - t0 + 1, self.rng, "rast", 0.6), t0, kazanc=0.7, yanki=0.4)
        n = ezgi_zaman(TEMA[:10], t0 + 0.8, 0.55, G * 2, "rast", tavan=t1 + 0.6)
        self.kaval_ekle(n, t0, t1 - t0 + 1.5, kazanc=0.7)

    def b_koy(self, t0, t1, s):
        G = 196.0
        v = 0.6
        b = ezgi_zaman(TEMA + TEMA_B, t0 + 0.3, v, G * 2, "rast", tekrar=3, tavan=t1 - 0.2)
        self.baglama_ezgi(b, kazanc=0.55)
        for t in np.arange(t0 + 0.3, t1 - 0.2, v * 2):                       # karar demi (bas tel)
            self.ekle(baglama(G, 1.4, 0.8, self.rng, parlak=0.3), t, pan=-0.3, kazanc=0.35)
        self.def_ritim(t0 + 0.3, t1 - 0.3, v, "DtTt", 0.28)
        if t1 - t0 > 9:
            k = ezgi_zaman(TEMA_B, t0 + 0.3 + v * 16, v, G * 4, "rast", tavan=t1 - 0.3)
            self.kaval_ekle(k, t0, t1 - t0 + 1, kazanc=0.32, pan=0.3)

    def b_merak(self, t0, t1, s):
        A = 220.0
        v = 0.75
        n = ezgi_zaman([(4, 1), (3, .5), (2, .5), (3, 1), (1, 1), (2, .5), (1, .5), (0, 2)], t0 + 0.4, v, A * 2, "ussak",
                       tekrar=3, tavan=t1 - 0.3)
        self.baglama_ezgi(n, kazanc=0.5, uzunluk=1.0)
        self.def_ritim(t0 + 0.4, t1 - 0.3, v, "D.t.", 0.22)
        self.ekle(dem(A, t1 - t0 + 0.8, self.rng, "ussak", 0.3), t0, kazanc=0.5, yanki=0.4)

    def b_komik(self, t0, t1, s):
        G = 196.0
        v = 0.42
        kop = s["cue"].get("kopma", t0 + 2.4)
        # cekis: tezene tremolosu, yukselen
        n = [(t0 + 0.3 + i * 0.5, 0.48, perde(G * 2, "rast", i % 5)) for i in range(int((kop - t0 - 0.3) / 0.5))]
        self.baglama_ezgi(n, kazanc=0.4, tremolo=True)
        # yuruyus marsi: bas + kesik ezgi
        bas = kop + 1.2
        t = bas
        k = 0
        while t < t1 - 0.2:
            f = perde(G, "rast", (0, 4, 2, 4)[k % 4])
            self.ekle(baglama(f, 0.5, 1.0, self.rng, parlak=0.3), t, pan=-0.3, kazanc=0.45)
            t += v
            k += 1
        m = ezgi_zaman([(4, .5), (4, .5), (5, .5), (4, .5), (2, 1), (3, .5), (3, .5), (4, .5), (3, .5), (1, 1),
                        (2, .5), (3, .5), (4, 1), (7, 1)], bas, v * 2, G * 2, "rast", tekrar=2, tavan=t1 - 0.2)
        self.baglama_ezgi(m, kazanc=0.5, uzunluk=0.6)
        self.def_ritim(bas, t1 - 0.2, v * 2, "DTDT", 0.25)

    def b_dugun(self, t0, t1, s):
        D = 293.66
        v = 0.5                                                              # 120 bpm
        z = ezgi_zaman(HALAY, t0 + 0.2, v * 2, D * 2, "hicaz", tekrar=6, tavan=t1 - 0.1)
        self.ekle(zurna([(t - t0, d, f) for t, d, f in z], t1 - t0 + 0.5, self.rng), t0, pan=-0.45, kazanc=0.55, yanki=0.35)
        t, k = t0 + 0.2, 0
        while t < t1 - 0.1:                                                  # davul: DUM . tek tek
            if k % 4 == 0:
                self.ekle(davul_dum(self.rng, 1.0), t, pan=-0.6, kazanc=0.35, yanki=0.25)
            elif k % 4 in (2, 3):
                self.ekle(davul_tek(self.rng, 1.0), t, pan=-0.55, kazanc=0.32, yanki=0.2)
            t += v / 2
            k += 1
        self.ekle(kalabalik(self.rng, t1 - t0 + 0.5), t0, kazanc=1.0, yanki=0.3)
        gul = s["cue"].get("gulme")
        if gul:                                                              # kahkaha yerine zurna trilli + davul cosmasi
            tril = [(gul - t0 + i * 0.07, 0.07, D * 4 * (1.0 if i % 2 else 2 ** (114 / 1200))) for i in range(14)]
            self.ekle(zurna(tril, 1.4, self.rng), t0, pan=0.0, kazanc=0.5, yanki=0.3)
            for i in range(6):
                self.ekle(davul_dum(self.rng, 1.0), gul + i * 0.12, kazanc=0.25, yanki=0.3)

    def b_aksam(self, t0, t1, s):
        A = 220.0
        n = ezgi_zaman([(4, 2), (3, 1), (2, 1), (3, 2), (1, 2), (2, 1), (1, 1), (0, 3)], t0 + 0.6, 0.62, A * 2, "huseyni",
                       tavan=t1)
        self.kaval_ekle(n, t0, t1 - t0 + 1.5, kazanc=0.55, pan=0.15)
        self.ekle(dem(A, t1 - t0 + 1.0, self.rng, "huseyni", 0.5), t0, kazanc=0.32, yanki=0.5)
        self.ekle(ruzgar(self.rng, t1 - t0 + 1), t0, kazanc=0.55, yanki=0.2)

    def b_gece(self, t0, t1, s):
        D = 146.83
        self.ekle(dem(D, t1 - t0 + 1.0, self.rng, "hicaz", 0.5), t0, kazanc=0.45, yanki=0.5)
        v = 0.55
        t, k = t0 + 0.5, 0
        desen = (0, 1, 2, 1, 0, -1 + 7, 0, 4)
        while t < t1 - 0.3:
            self.ekle(baglama(perde(D * 2, "hicaz", desen[k % 8] % 7), 0.6, 0.8, self.rng, parlak=0.35), t, pan=-0.2,
                      kazanc=0.30)
            t += v
            k += 1

    def b_gerilim(self, t0, t1, s):
        D = 146.83
        kay = s["cue"].get("kayma", t1 - 2)
        self.ekle(dem(D, t1 - t0 + 0.5, self.rng, "hicaz", 0.7), t0, kazanc=0.42, yanki=0.5)
        n = []
        t, d = t0 + 0.3, 0
        while t < kay - 0.1:
            n.append((t, 0.9, perde(D * 2, "hicaz", d)))
            t += 1.0
            d = min(d + 1, 7)
        self.baglama_ezgi(n, kazanc=0.30, tremolo=True)
        for i in range(7):                                                   # kayis: inen glissando
            self.ekle(baglama(perde(D * 2, "hicaz", 7 - i), 0.5, 1.0, self.rng), kay + i * 0.06, kazanc=0.4)

    def b_kacis(self, t0, t1, s):
        D = 293.66
        g = s["cue"].get("gum", t0 + 0.72)
        bas = g + 1.4
        v = 0.3
        n = ezgi_zaman([(0, .5), (1, .5), (2, .5), (3, .5), (4, .5), (3, .5), (2, .5), (1, .5),
                        (4, .5), (5, .5), (4, .5), (3, .5), (2, 1), (0, 1)], bas, v, D, "hicaz", tekrar=4, tavan=t1 - 0.2)
        self.baglama_ezgi(n, kazanc=0.5, uzunluk=0.5)
        self.def_ritim(bas, t1 - 0.2, v * 2, "DTtT", 0.3)

    def b_sabah(self, t0, t1, s):
        G = 196.0
        n = ezgi_zaman(TEMA, t0 + 0.6, 0.62, G * 4, "rast", tavan=t1)
        self.kaval_ekle(n, t0, t1 - t0 + 1.5, kazanc=0.55, pan=0.2)
        for t in np.arange(t0 + 0.6, t1 - 0.3, 1.24):
            for j, d in enumerate((0, 4, 7)):
                self.ekle(baglama(perde(G, "rast", d), 1.6, 0.8, self.rng, parlak=0.4), t + j * 0.08, pan=-0.25, kazanc=0.3)

    def b_final(self, t0, t1, s):
        G = 196.0
        v = 0.58
        b = ezgi_zaman(TEMA_B + TEMA, t0 + 0.3, v, G * 2, "rast", tavan=t1 - 0.1)
        self.baglama_ezgi(b, kazanc=0.5)
        k = ezgi_zaman(TEMA_B + TEMA, t0 + 0.3, v, G * 4, "rast", tavan=t1 - 0.1)
        self.kaval_ekle(k, t0, t1 - t0 + 1.0, kazanc=0.4, pan=0.3)
        self.def_ritim(t0 + 0.3, t1 - 0.2, v, "DtTt", 0.28)
        for t in np.arange(t0 + 0.3, t1 - 0.2, v * 2):
            self.ekle(baglama(G, 1.4, 0.8, self.rng, parlak=0.3), t, pan=-0.3, kazanc=0.32)

    def b_son(self, t0, t1, s):
        G = 196.0
        self.ekle(dem(G, t1 - t0 + 0.5, self.rng, "rast", 0.6), t0, kazanc=0.6, yanki=0.5)
        akor = t0 + 4.6
        for j, d in enumerate((0, 2, 4, 7)):
            self.ekle(baglama(perde(G * 2, "rast", d), 3.5, 1.0, self.rng), akor + j * 0.09, pan=-0.2 + j * 0.13,
                      kazanc=0.5, yanki=0.5)
        k = [(akor - t0 + 0.1, 3.2, G * 4)]
        self.ekle(kaval(k, 4.0, self.rng), t0, pan=0.2, kazanc=0.45, yanki=0.6)

    # ---------------------------------------------------------- efektler
    def efekt(self, ad, t, sure=None, sayfa_bit=None):
        r = self.rng
        e = self.ekle
        if ad == "cinlama":
            e(cinlama(r), t, kazanc=0.5, yanki=0.5)
        elif ad == "kuslar":
            e(kus_civiltisi(r, sure or 8), t, pan=0.4, kazanc=1.0, yanki=0.35)
        elif ad == "tavuk":
            e(tavuk_gidaklama(r), t, pan=-0.4, kazanc=1.0, yanki=0.2)
        elif ad == "adimlar":
            e(adimlar(r, sure or 4), t, pan=0.1, kazanc=0.7, yanki=0.15)
        elif ad == "agir_adimlar":
            e(adimlar(r, sure or 3, 0.45, agir=True), t, pan=-0.4, kazanc=0.8, yanki=0.2)
        elif ad == "kosma":
            x = adimlar(r, sure or 3, 0.16, agir=True)
            x *= np.linspace(1, 0.1, len(x))
            e(x, t, pan=-0.6, kazanc=0.9, yanki=0.25)
        elif ad == "gicirti":
            e(gicirti(r, sure or 1.2), t, pan=-0.2, kazanc=0.8, yanki=0.2)
        elif ad == "kopma":
            e(catirti(r, 1.0), t, pan=-0.2, kazanc=0.9, yanki=0.3)
        elif ad == "dusme":
            e(def_dum(r, 1.2), t, pan=0.1, kazanc=0.6, yanki=0.2)
        elif ad == "hayal":
            for j, d in enumerate((0, 2, 4, 7, 9, 11)):
                e(baglama(perde(392, "rast", d), 1.2, 0.8, r), t + j * 0.07, pan=0.3, kazanc=0.3, yanki=0.6)
        elif ad == "kurt":
            e(kurt_ulumasi(r), t, pan=-0.6, kazanc=0.7, yanki=0.8)
        elif ad == "circir":
            e(circir(r, sure or 8), t, pan=0.0, kazanc=1.0, yanki=0.2)
        elif ad == "baykus":
            e(baykus(r), t, pan=0.5, kazanc=0.8, yanki=0.6)
        elif ad == "ates":
            e(ates_citirti(r, sure or 8), t, pan=-0.1, kazanc=1.0, yanki=0.15)
        elif ad == "ates_uzak":
            e(ates_citirti(r, sure or 8), t, pan=-0.1, kazanc=0.4, yanki=0.3)
        elif ad == "altin":
            e(sikke_singirtisi(r, int((sure or 4) * 3), sure or 4), t, pan=0.15, kazanc=1.0, yanki=0.3)
        elif ad == "tirmanma":
            x = adimlar(r, sure or 2.4, 0.3)
            e(_filtre(x, "lp", 2500), t, pan=0.3, kazanc=0.6, yanki=0.2)
        elif ad == "kalp":
            e(kalp(r, sure or 5), t, kazanc=0.5, yanki=0.15)
        elif ad == "kayma":
            e(gicirti(r, 0.6), t, pan=0.3, kazanc=0.7, yanki=0.3)
        elif ad == "whoosh":
            e(whoosh(r, sure or 1.0, 300, 2400, 1.0), t, kazanc=0.45, yanki=0.2)
        elif ad == "gum":
            e(gum(r, 1.0), t, kazanc=1.0, yanki=0.45)
            e(catirti(r, 0.8), t + 0.02, kazanc=0.7, yanki=0.4)
            e(zil(r, 2.0), t, kazanc=0.12, yanki=0.4)
        elif ad == "altin_sacilma":
            e(sikke_singirtisi(r, 14, 1.4), t, pan=0.2, kazanc=1.2, yanki=0.3)
        elif ad == "horoz":
            e(horoz(r), t, pan=0.5, kazanc=0.8, yanki=0.6)
        elif ad == "elma":
            e(elma_pit(r), t, kazanc=0.7, yanki=0.35)
        elif ad == "ruzgar":
            e(ruzgar(r, sure or 8), t, kazanc=1.0, yanki=0.2)
        elif ad == "sayfa":
            e(sayfa_hisirtisi(r), t, pan=0.25, kazanc=0.8, yanki=0.15)
        elif ad in ("gulme",):                                             # yalnizca muzik icin isaret
            pass
        else:
            raise ValueError(f"bilinmeyen efekt: {ad}")


def zaman_coz(z, sayfa_bas, sure, cumle_t):
    """Efekt zamani: sayi (sayfa basindan; negatifse sayfa sonundan) ya da 'cN', 'cN+x', 'cN-x'."""
    if isinstance(z, str):
        z = z.strip()
        kayma = 0.0
        for isaret in ("+", "-"):
            if isaret in z[1:]:
                a, b = z.split(isaret, 1)
                kayma = float(b) * (1 if isaret == "+" else -1)
                z = a
                break
        i = int(z[1:])
        yerel = (cumle_t[i] if i < len(cumle_t) else sure - 1.0) + kayma
    else:
        yerel = float(z) if z >= 0 else sure + float(z)
    return sayfa_bas + yerel


def uret(yol, masal, tohum=7):
    """Masal nesnesinin zaman cizelgesinden tam ses izini uretir (wav)."""
    from src.masal_motoru import CEVIRME
    rng = np.random.default_rng(tohum)
    M = Mikser(masal.SURE + 1.0)
    B = Besteci(M, rng)
    for i, s in enumerate(masal.sayfalar):
        t0 = masal.bas[i]
        t1 = t0 + s.sure + (CEVIRME if i < len(masal.sayfalar) - 1 else 0.0)
        cumle_t = list(s.kart.zaman) if s.kart else []
        cue = {}
        for kayit in s.t.get("sesler", []):
            ad, z = kayit[0], kayit[1]
            ops = kayit[2] if len(kayit) > 2 else {}
            tt = zaman_coz(z, t0, s.sure, cumle_t)
            sure = ops.get("sure")
            if isinstance(sure, str):
                sure = zaman_coz(sure, t0, s.sure, cumle_t) - tt
            cue[ad] = tt
            B.efekt(ad, tt, sure)
        bolum = dict(cue=cue, sayfa=s)
        B.bolum(s.t.get("muzik", "koy"), t0, t1, bolum)
        if i < len(masal.sayfalar) - 1:
            B.efekt("sayfa", t0 + s.sure + 0.05)

    ir = _oda_yankisi(rng, rt60=1.8)
    islak = np.stack([signal.fftconvolve(M.yanki[c], ir[c])[: M.n] for c in range(2)])
    mix = M.kuru + islak * 0.85
    mix = signal.sosfilt(_sos("hp", 30, 2), mix, axis=1)
    tepe = np.abs(mix).max() + 1e-9
    mix = np.tanh(mix / tepe * 1.3) / np.tanh(1.3)
    son = int(1.2 * SR)
    mix[:, -son:] *= np.linspace(1, 0, son) ** 1.5
    mix *= 10 ** (-1.0 / 20)
    _wav_yaz(yol, mix[:, : int(masal.SURE * SR)])
    return yol

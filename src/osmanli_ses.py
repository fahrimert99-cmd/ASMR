"""
Osmanli harita animasyonu — sentez ses tasarimi (telifsiz, tamamen kod).

Hicbir ses dosyasi/ornek kullanilmaz; her sey numpy/scipy ile uretilir:

  * Muzik yatagi : Re (D) uzerine dem (drone) — finalde Hicaz rengi akor.
  * Ney          : nefesli, vibratolu Hicaz ezgisi (portamento ile).
  * Mehter davulu: duyek usulu (DUM . TEK TEK DUM . TEK .) + zil.
  * Efektler     : top atisi, kilic carpismasi, savas narasi, dalga/su,
                   gong, kamera "whoosh"u, yil sayaci tikirtisi, final
                   oncesi yukselen gerilim (riser) ve buyuk vurus.
  * Genisleme    : haritadaki yuzolcumu artis hizi (dA/dt) ile suren alcak
                   bir gurleme -> sinirlarin buyumesi "duyulur".
  * Mastering    : sentetik oda yankisi (konvolusyon), yumusak sinirlayici.

Kullanim:
    from src import osmanli_ses
    osmanli_ses.uret("ses.wav", olaylar, sure=20.0, buyume=(ts, hiz), panlar=[...])
"""
import math
import wave

import numpy as np
from scipy import signal

SR = 48000


# ================================================================ yardimcilar
class Mikser:
    def __init__(self, sure):
        self.n = int(round(sure * SR))
        self.kuru = np.zeros((2, self.n), np.float64)
        self.yanki = np.zeros((2, self.n), np.float64)

    def ekle(self, sig, t, pan=0.0, kazanc=1.0, yanki=0.25):
        sig = np.asarray(sig, np.float64)
        i0 = int(round(t * SR))
        if sig.ndim == 1:
            a = (pan + 1) * math.pi / 4                 # sabit guclu pan
            sig = np.stack([sig * math.cos(a), sig * math.sin(a)])
        if i0 < 0:
            sig, i0 = sig[:, -i0:], 0
        m = min(sig.shape[1], self.n - i0)
        if m <= 0:
            return
        self.kuru[:, i0:i0 + m] += sig[:, :m] * kazanc
        if yanki:
            self.yanki[:, i0:i0 + m] += sig[:, :m] * kazanc * yanki


def _t(sure):
    return np.arange(int(round(sure * SR))) / SR


def _sos(tur, f, derece=2):
    ny = SR / 2
    if tur == "bp":
        return signal.butter(derece, [max(f[0], 10) / ny, min(f[1], ny * 0.95) / ny], "bandpass", output="sos")
    return signal.butter(derece, min(f, ny * 0.95) / ny, "lowpass" if tur == "lp" else "highpass", output="sos")


def _filtre(x, tur, f, derece=2):
    return signal.sosfilt(_sos(tur, f, derece), x)


def _gurultu(rng, sure):
    return rng.standard_normal(int(round(sure * SR)))


def _kahve(rng, sure):
    x = np.cumsum(rng.standard_normal(int(round(sure * SR))))
    x = _filtre(x, "hp", 20)
    return x / (np.abs(x).max() + 1e-9)


def _yumusat(x, sn):
    """~sn saniyelik zarf yumusatma (sifir fazli)."""
    return signal.sosfiltfilt(signal.butter(1, (1.0 / sn) / (SR / 2), output="sos"), x)


# ================================================================ enstrumanlar
def davul_dum(rng, guc=1.0):
    t = _t(0.9)
    f = 50 + 72 * np.exp(-t / 0.045)
    faz = 2 * np.pi * np.cumsum(f) / SR
    govde = np.sin(faz) * np.exp(-t / 0.30)
    mod2 = 0.32 * np.sin(1.59 * faz) * np.exp(-t / 0.10)
    mod3 = 0.12 * np.sin(2.14 * faz) * np.exp(-t / 0.06)
    tok = _filtre(_gurultu(rng, 0.9), "lp", 900) * np.exp(-t / 0.012) * 0.55
    deri = _filtre(_gurultu(rng, 0.9), "bp", (1400, 3200)) * np.exp(-t / 0.005) * 0.25
    return (govde + mod2 + mod3 + tok + deri) * guc


def davul_tek(rng, guc=1.0):
    t = _t(0.25)
    cubuk = _filtre(_gurultu(rng, 0.25), "bp", (1800, 6500)) * np.exp(-t / 0.022)
    ton = np.sin(2 * np.pi * 395 * t) * np.exp(-t / 0.035) * 0.45
    tik = _filtre(_gurultu(rng, 0.25), "hp", 5000) * np.exp(-t / 0.002) * 0.4
    return (cubuk * 0.55 + ton + tik) * guc


def zil(rng, sure=2.2, guc=1.0):
    t = _t(sure)
    g = _filtre(_gurultu(rng, sure), "hp", 3500)
    ton = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * a
              for f, a in [(3150, .3), (4240, .25), (5480, .22), (6930, .18), (8120, .14)])
    zarf = np.exp(-t / (sure * 0.33)) * (1 - np.exp(-t / 0.002))
    return (g * 0.6 + ton * 0.35) * zarf * guc


def gong(rng, f0=96.0, sure=4.0, guc=1.0):
    t = _t(sure)
    x = np.zeros_like(t)
    for oran, a, tau in [(1, 1, 2.6), (1.47, .55, 1.9), (2.09, .45, 1.5), (2.56, .3, 1.2),
                         (3.2, .22, .9), (4.13, .16, .7), (5.4, .1, .5)]:
        f = f0 * oran * (1 - 0.012 * np.exp(-t / 0.4))
        x += a * np.sin(2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 6)) * np.exp(-t / tau)
    vurus = _filtre(_gurultu(rng, sure), "lp", 1200) * np.exp(-t / 0.02) * 0.4
    return (x * 0.5 + vurus) * (1 - np.exp(-t / 0.004)) * guc


def top_atisi(rng, guc=1.0, kuyruk=2.6):
    """Kale topu: catlak + patlama + alt bas + uzun gurleme kuyrugu."""
    t = _t(kuyruk)
    catlak = _filtre(_gurultu(rng, kuyruk), "hp", 1500) * np.exp(-t / 0.004) * 0.7
    patlama = _filtre(_gurultu(rng, kuyruk), "lp", 520, 3) * np.exp(-t / 0.18) * 2.2
    f = 36 + 40 * np.exp(-t / 0.07)
    alt = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55) * 1.1
    gurleme = _filtre(_kahve(rng, kuyruk), "lp", 160) * np.exp(-t / 0.9) * (1 - np.exp(-t / 0.08)) * 1.6
    x = catlak + patlama + alt + gurleme
    return np.tanh(x * 1.2) * guc


def kilic(rng, guc=1.0):
    t = _t(0.9)
    x = np.zeros_like(t)
    for f in [2150, 3320, 4870, 6270, 8090, 9700]:
        f *= rng.uniform(0.96, 1.04)
        x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / rng.uniform(0.12, 0.42)) * rng.uniform(.4, 1)
    vurus = _filtre(_gurultu(rng, 0.9), "bp", (1500, 9000)) * np.exp(-t / 0.008) * 0.8
    return (x * 0.35 + vurus) * guc


def nara(rng, sure=1.6, guc=1.0):
    """Uzaktan savas narasi / kalabalik ugultusu."""
    t = _t(sure)
    x = np.zeros_like(t)
    for _ in range(14):
        f0 = rng.uniform(260, 900)
        bant = _filtre(_gurultu(rng, sure), "bp", (f0 * 0.8, f0 * 1.35))
        am = 0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(4, 9) * t + rng.uniform(0, 6))
        x += bant * am
    zarf = np.clip(t / 0.35, 0, 1) * np.exp(-np.clip(t - 0.5, 0, None) / 0.6)
    return x / 6 * zarf * guc


def dalga(rng, sure=2.0, guc=1.0):
    t = _t(sure)
    x = _filtre(_gurultu(rng, sure), "lp", 1400) + 0.4 * _filtre(_gurultu(rng, sure), "bp", (2000, 6000))
    zarf = np.sin(np.pi * np.clip(t / sure, 0, 1)) ** 1.5
    return x * zarf * 0.5 * guc


def whoosh(rng, sure=0.9, f_bas=400, f_tepe=2800, guc=1.0):
    """Bant geciren gurultu; merkez frekans tepeye cikip iner (filtre bankasi ile)."""
    t = _t(sure)
    g = _gurultu(rng, sure)
    u = t / sure
    merkez = f_bas + (f_tepe - f_bas) * np.sin(np.pi * u) ** 1.2
    bantlar = np.geomspace(250, 5000, 9)
    x = np.zeros_like(t)
    for fc in bantlar:
        b = _filtre(g, "bp", (fc / 1.4, fc * 1.4))
        w = np.exp(-(np.log(merkez / fc) / 0.45) ** 2)
        x += b * w
    zarf = np.sin(np.pi * u) ** 2
    mono = x * zarf * guc
    pan = -0.7 + 1.4 * u
    a = (pan + 1) * np.pi / 4
    return np.stack([mono * np.cos(a), mono * np.sin(a)])


def riser(rng, sure=1.5, guc=1.0):
    t = _t(sure)
    u = t / sure
    g = _gurultu(rng, sure)
    x = np.zeros_like(t)
    for fc in np.geomspace(200, 7000, 10):
        b = _filtre(g, "bp", (fc / 1.35, fc * 1.35))
        merkez = 200 * (7000 / 200) ** (u ** 1.3)
        x += b * np.exp(-(np.log(merkez / fc) / 0.5) ** 2)
    f = 110 * 4 ** (u ** 1.6)
    ton = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35 + np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) * 0.15
    zarf = u ** 2.2
    return (x * 0.6 + ton) * zarf * guc


def tik(rng, guc=1.0):
    t = _t(0.03)
    return (np.sin(2 * np.pi * 2900 * t) * 0.5 + _filtre(_gurultu(rng, 0.03), "hp", 4000)) * np.exp(-t / 0.004) * guc


def parsomen(rng, sure=1.2, guc=1.0):
    """Harita/parsomen acilirken citirti."""
    n = int(sure * SR)
    x = np.zeros(n)
    for _ in range(int(sure * 55)):
        i = rng.integers(0, n - 2000)
        L = rng.integers(200, 1600)
        tt = np.arange(L) / SR
        x[i:i + L] += rng.standard_normal(L) * np.exp(-tt / rng.uniform(0.002, 0.012)) * rng.uniform(.2, 1)
    x = _filtre(x, "bp", (900, 7000))
    zarf = np.sin(np.pi * np.clip(np.arange(n) / n, 0, 1)) ** 0.7
    return x * zarf * 0.35 * guc


# ================================================================ muzik
HICAZ = {"D4": 293.66, "Eb4": 311.13, "F#4": 369.99, "G4": 392.00, "A4": 440.00,
         "Bb4": 466.16, "C5": 523.25, "D5": 587.33, "Eb5": 622.25, "F#5": 739.99,
         "G5": 783.99, "A5": 880.00}

# (baslangic sn, sure sn, nota) — Re Hicaz
NEY_EZGI = [
    (1.55, 0.85, "A4"), (2.40, 0.30, "Bb4"), (2.70, 0.40, "A4"), (3.10, 0.35, "G4"),
    (3.45, 0.70, "F#4"),
    (4.25, 0.40, "G4"), (4.65, 0.45, "A4"), (5.10, 0.30, "Bb4"), (5.40, 0.40, "C5"),
    (5.80, 0.85, "D5"), (6.65, 0.20, "C5"), (6.85, 0.20, "Bb4"),
    (7.05, 0.95, "A4"), (8.00, 0.45, "D5"), (8.45, 0.30, "Eb5"), (8.75, 0.40, "D5"),
    (9.15, 0.30, "C5"), (9.45, 0.30, "Bb4"), (9.75, 0.85, "A4"),
    (10.60, 0.35, "Bb4"), (10.95, 0.35, "C5"), (11.30, 0.55, "D5"), (11.85, 0.30, "Eb5"),
    (12.15, 0.60, "F#5"), (12.75, 0.40, "G5"), (13.15, 0.30, "F#5"), (13.45, 0.30, "Eb5"),
    (13.75, 0.75, "D5"),
    (15.75, 1.55, "D5"), (17.30, 0.25, "C5"), (17.55, 0.25, "Bb4"), (17.80, 0.45, "A4"),
    (18.25, 1.60, "D5"),
]


def ney(rng, sure, ezgi=NEY_EZGI):
    n = int(sure * SR)
    t = np.arange(n) / SR
    hedef_f = np.full(n, HICAZ[ezgi[0][2]])
    genlik = np.zeros(n)
    vib_derin = np.zeros(n)
    for bas, dur, nota in ezgi:
        i0, i1 = int(bas * SR), min(int((bas + dur) * SR), n)
        hedef_f[i0:] = HICAZ[nota]
        tt = np.arange(i1 - i0) / SR
        atak = 1 - np.exp(-tt / 0.05)
        birak = np.clip((dur - tt) / 0.12, 0, 1)
        sisme = 1 + 0.15 * np.clip(tt / max(dur, 0.1), 0, 1)
        genlik[i0:i1] = np.maximum(genlik[i0:i1], atak * birak * sisme)
        vib_derin[i0:i1] = np.clip((tt - 0.18) / 0.4, 0, 1) * 0.006
    # portamento: log-frekansta tek kutuplu yumusatma
    logf = np.log(hedef_f)
    a = math.exp(-1 / (0.035 * SR))
    logf = signal.lfilter([1 - a], [1, -a], logf, zi=[logf[0] * a])[0]
    f = np.exp(logf) * (1 + vib_derin * np.sin(2 * np.pi * 5.3 * t))
    faz = 2 * np.pi * np.cumsum(f) / SR
    ton = np.sin(faz) + 0.28 * np.sin(2 * faz + 0.3) + 0.09 * np.sin(3 * faz + 1.1) + 0.04 * np.sin(4 * faz)
    nefes = _filtre(rng.standard_normal(n), "bp", (900, 4200)) * 0.22
    genlik = _yumusat(genlik, 0.01)
    return (ton * 0.8 + nefes * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t) ** 2)) * genlik


def dem(rng, sure, akor_t=15.7):
    """Re demi: testere dalgalar + iki filtre arasi gecis (gittikce parlar)."""
    n = int(sure * SR)
    t = np.arange(n) / SR

    def testere(f, detune):
        faz = (f * (1 + detune) * t + rng.uniform()) % 1.0
        return 2 * faz - 1

    def ses(notalar):
        x = np.zeros(n)
        for f, a in notalar:
            for d in (-0.0016, 0.0, 0.0013):
                x += testere(f, d) * a
        return x

    once = ses([(73.42, 1.0), (110.0, 0.7), (146.83, 0.45), (220.0, 0.18)])
    sonra = ses([(73.42, 1.0), (110.0, 0.7), (146.83, 0.5), (185.0, 0.32), (220.0, 0.3), (293.66, 0.16)])
    gecis = np.clip((t - (akor_t - 0.05)) / 0.4, 0, 1)
    x = once * (1 - gecis) + sonra * gecis
    x = _filtre(x, "hp", 45)
    koyu = _filtre(x, "lp", 380, 2)
    acik = _filtre(x, "lp", 1900, 2)
    parlak = np.clip(t / akor_t, 0, 1) ** 1.4 * 0.75 + 0.25 * (t > akor_t)
    x = koyu * (1 - parlak) + acik * parlak
    zarf = (0.25 + 0.75 * np.clip(t / 2.0, 0, 1)) * np.clip(t / 0.5, 0, 1)
    zarf *= 0.7 + 0.3 * np.clip((t - 1.6) / (akor_t - 1.6), 0, 1)
    zarf *= np.clip((sure - t) / 1.4, 0, 1)
    return x * zarf * 0.06


# ================================================================ yanki / master
def _oda_yankisi(rng, rt60=2.1, sure=2.6):
    t = _t(sure)
    zarf = np.exp(-6.9 * t / rt60)
    ir = []
    for _ in range(2):
        g = rng.standard_normal(len(t))
        g = 0.6 * _filtre(g, "lp", 6500) + 0.4 * _filtre(g, "lp", 1800)
        g = g * zarf
        g[: int(0.018 * SR)] = 0                   # on gecikme
        ir.append(g / np.sqrt((g ** 2).sum()))
    return ir


def _wav_yaz(yol, stereo):
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2").T.copy()
    with wave.open(str(yol), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ================================================================ ana uretim
def uret(yol, olaylar, sure=20.0, buyume=None, panlar=None, tohum=1683):
    rng = np.random.default_rng(tohum)
    M = Mikser(sure)
    panlar = panlar or [0.0] * len(olaylar)
    olay_t = [o["t"] for o in olaylar]
    final_t = olay_t[-1]

    # --- muzik yatagi + ney
    M.ekle(dem(rng, sure, final_t), 0.0, kazanc=1.0, yanki=0.2)
    M.ekle(ney(rng, sure), 0.0, pan=0.12, kazanc=0.17, yanki=0.55)

    # --- giris: parsomen + derin sisme + ters zil
    M.ekle(parsomen(rng, 1.3), 0.0, pan=-0.2, kazanc=0.5, yanki=0.15)
    M.ekle(gong(rng, 61.0, 3.5, 0.5), 0.05, kazanc=0.35, yanki=0.35)
    ters = zil(rng, 1.1, 1.0)[::-1] * np.linspace(0, 1, int(1.1 * SR)) ** 2
    M.ekle(ters, olay_t[0] - 1.1, kazanc=0.18, yanki=0.3)

    # --- mehter davulu (duyek: DUM . TEK TEK DUM . TEK .)
    sekizlik = 0.25
    desen = {0: "D", 2: "T", 3: "T", 4: "D", 6: "T"}
    t = olay_t[0]
    k = 0
    bitis = olay_t[-2] + 0.55
    while t < bitis:
        adim = k % 8
        if adim in desen:
            yogun = 0.55 + 0.45 * (t - olay_t[0]) / (bitis - olay_t[0])
            if desen[adim] == "D":
                M.ekle(davul_dum(rng, 1.0), t, pan=-0.08, kazanc=0.32 * yogun, yanki=0.22)
            else:
                M.ekle(davul_tek(rng, 1.0), t, pan=0.18, kazanc=0.45 * yogun, yanki=0.18)
        t += sekizlik
        k += 1
    # final oncesi davul rulosu
    r0, r1 = olay_t[-2] + 0.6, final_t
    tt = r0
    while tt < r1 - 0.02:
        u = (tt - r0) / (r1 - r0)
        M.ekle(davul_tek(rng, 1.0), tt, pan=rng.uniform(-.3, .3), kazanc=0.08 + 0.22 * u, yanki=0.2)
        if u > 0.5 and rng.uniform() < 0.35:
            M.ekle(davul_dum(rng, 0.6), tt, kazanc=0.15 * u, yanki=0.2)
        tt += 0.11 - 0.06 * u

    # --- olay efektleri
    for o, pan in zip(olaylar, panlar):
        t0, tur = o["t"], o["ses"]
        if tur != "kurulus":
            M.ekle(whoosh(rng, 0.55, 500, 3200, 1.0), t0 - 0.5, kazanc=0.30, yanki=0.15)
        if tur == "kurulus":
            M.ekle(gong(rng, 98.0, 4.0), t0, pan=pan, kazanc=0.55, yanki=0.4)
            M.ekle(davul_dum(rng, 1.2), t0, pan=pan, kazanc=0.55, yanki=0.3)
            M.ekle(zil(rng, 2.5), t0, pan=pan, kazanc=0.12, yanki=0.3)
        elif tur == "fetih":
            M.ekle(davul_dum(rng, 1.2), t0, pan=pan, kazanc=0.6, yanki=0.3)
            M.ekle(davul_dum(rng, 0.9), t0 + 0.16, pan=pan, kazanc=0.45, yanki=0.3)
            M.ekle(zil(rng, 1.8), t0, pan=pan, kazanc=0.14, yanki=0.3)
            M.ekle(gong(rng, 110.0, 2.5, 0.6), t0, pan=pan, kazanc=0.25, yanki=0.35)
        elif tur == "savas":
            for j, d in enumerate((0.0, 0.17, 0.41, 0.66)):
                M.ekle(kilic(rng), t0 + d, pan=pan + rng.uniform(-.3, .3), kazanc=0.32 - 0.05 * j, yanki=0.3)
            M.ekle(nara(rng, 1.8), t0 - 0.15, pan=pan, kazanc=1.6, yanki=0.35)
            M.ekle(davul_dum(rng, 1.3), t0, pan=pan, kazanc=0.6, yanki=0.3)
        elif tur == "top":
            for j, d in enumerate((-0.42, -0.2, 0.0)):
                M.ekle(top_atisi(rng, 1.0, 2.4), t0 + d, pan=np.clip(pan + (j - 1) * 0.35, -1, 1),
                       kazanc=0.38 + 0.18 * (j == 2), yanki=0.35)
            M.ekle(zil(rng, 2.4), t0, pan=pan, kazanc=0.18, yanki=0.35)
            M.ekle(davul_dum(rng, 1.3), t0, pan=pan, kazanc=0.5, yanki=0.3)
        elif tur == "deniz":
            M.ekle(dalga(rng, 2.2), t0 - 0.6, pan=pan - 0.2, kazanc=0.35, yanki=0.3)
            for d in (-0.25, 0.0):
                M.ekle(top_atisi(rng, 0.9, 2.6), t0 + d, pan=pan + d, kazanc=0.4, yanki=0.5)
            M.ekle(dalga(rng, 1.4), t0 + 0.05, pan=pan + 0.2, kazanc=0.3, yanki=0.3)
            M.ekle(davul_dum(rng, 1.2), t0, pan=pan, kazanc=0.45, yanki=0.3)
        elif tur == "final":
            M.ekle(riser(rng, 1.45, 1.0), t0 - 1.45, kazanc=0.32, yanki=0.3)
            M.ekle(top_atisi(rng, 1.3, 3.2), t0, kazanc=0.6, yanki=0.45)
            M.ekle(gong(rng, 73.4, 5.0, 1.0), t0, kazanc=0.6, yanki=0.5)
            M.ekle(zil(rng, 3.4), t0, pan=-0.3, kazanc=0.22, yanki=0.45)
            M.ekle(zil(rng, 3.4), t0 + 0.01, pan=0.3, kazanc=0.22, yanki=0.45)
            M.ekle(davul_dum(rng, 1.4), t0, kazanc=0.75, yanki=0.35)
            for d in (1.0, 1.25, 2.4):
                M.ekle(davul_dum(rng, 1.0), t0 + d, kazanc=0.32, yanki=0.35)

    # --- kamera hareketleri (buyuk uzaklasmalar)
    for tt, g in ((7.55, 0.45), (8.3, 0.35), (10.55, 0.35), (11.9, 0.25)):
        M.ekle(whoosh(rng, 1.1, 300, 2200, 1.0), tt, kazanc=g, yanki=0.2)

    # --- yil sayaci tikirtisi (yil degistikce, en fazla ~14/sn)
    if buyume is not None:
        ts, _, yillar = buyume
        son_t, son_y = -1.0, None
        for tt, y in zip(ts, yillar):
            yi = int(y)
            if son_y is not None and yi != son_y and tt - son_t > 0.07 and tt < final_t:
                M.ekle(tik(rng), tt, pan=-0.45, kazanc=0.035, yanki=0.05)
                son_t = tt
            son_y = yi

    # --- genisleme gurlemesi (dA/dt)
    if buyume is not None:
        ts, hiz, _ = buyume
        n = M.n
        zarf = np.interp(np.arange(n) / SR, ts, hiz)
        gur = _filtre(_filtre(_kahve(rng, sure), "lp", 150), "hp", 35) * 1.4 \
            + _filtre(_gurultu(rng, sure), "bp", (700, 1800)) * 0.05
        M.ekle(gur[:n] * zarf, 0.0, kazanc=0.08, yanki=0.15)

    # --- yanki + master
    ir = _oda_yankisi(rng)
    islak = np.stack([signal.fftconvolve(M.yanki[c], ir[c])[: M.n] for c in range(2)])
    mix = M.kuru + islak * 0.9
    mix = signal.sosfilt(_sos("hp", 28, 2), mix, axis=1)
    tepe = np.abs(mix).max() + 1e-9
    mix = mix / tepe * 1.4
    mix = np.tanh(mix) / np.tanh(1.4)               # yumusak sinirlayici
    son = int(0.02 * SR)
    mix[:, -son:] *= np.linspace(1, 0, son)
    mix *= 10 ** (-1.0 / 20)                        # -1 dBFS tepe
    _wav_yaz(yol, mix)
    return yol

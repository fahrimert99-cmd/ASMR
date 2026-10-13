"""
Video girisi icin kodla uretilen (telifsiz) foley / ses efekti katmani.

"The Food Almanac" girisinin (0-10 sn: ahsap ambar kapaginin kaldirilmasi,
bos ambara dokulen toz/saman, 10. sn'de baslik karti) sesini tamamen numpy
ile sentezler. Harici ornek dosya, servis veya scipy gerektirmez:

  - ambar oda tonu + hafif ruzgar           (renkli gurultu)
  - ele degen ahsap / kapak gicirtisi        (stick-slip darbe dizisi ->
                                              ahsap mod bankasi, FFT evrisim)
  - kapagin dayanmasi (tok ahsap vurus)      (modal sentez)
  - dokulen toz/saman + tane tikirtilari     (bant geciren gurultu + klikler)
  - bos ambarin oyuk rezonansi               (alcak drone)
  - basliga gecis "whoosh" + darbe + parsomen hisirtisi

Zaman cizelgesi `ZAMANLAMA` sozlugunden okunur; baska bir video icin yalnizca
bu degerler degistirilir.

Kullanim:
    from src import giris_sfx
    sfx = giris_sfx.uret(sr=44100)        # (n, 2) float32, [-1, 1]
"""
import numpy as np

# Saniye cinsinden olay zamanlari (frame analizine gore: 0.1 sn el kapakta,
# 0.5-1.9 sn kapak kalkar, ~1.0 sn toz kopar, 10.0 sn baslik karti).
ZAMANLAMA = {
    "el_temas": 0.12,
    "gicirti_bas": 0.42,
    "gicirti_bit": 1.92,
    "kapak_dayanma": 1.97,
    "toz_bas": 0.95,
    "toz_bit": 4.8,
    "oyuk_bas": 2.2,
    "oyuk_bit": 10.2,
    "whoosh_bas": 8.7,
    "baslik": 10.0,
    "toplam": 12.0,
}


def _db(x: float) -> float:
    return 10 ** (x / 20.0)


def _zarf(n: int, atak: int, salinim: int) -> np.ndarray:
    """Dogrusal atak + ustel olmayan (cosinus) salinim zarfi."""
    z = np.ones(n)
    atak = max(1, min(atak, n))
    salinim = max(1, min(salinim, n - atak))
    z[:atak] = np.linspace(0, 1, atak)
    z[n - salinim:] *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, salinim)))
    return z


def _bant(x: np.ndarray, sr: int, alt: float, ust: float, yumusak: float = 0.15) -> np.ndarray:
    """FFT maskesi ile bant geciren filtre (yumusak kenarli)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / sr)
    m = np.ones_like(f)
    if alt > 0:
        m *= 1 / (1 + np.exp(np.clip(-(f - alt) / (alt * yumusak + 1e-9), -60, 60)))
    if ust < sr / 2:
        m *= 1 / (1 + np.exp(np.clip((f - ust) / (ust * yumusak + 1e-9), -60, 60)))
    return np.fft.irfft(X * m, len(x))


def _renkli(n: int, beta: float, rng) -> np.ndarray:
    """beta=0 beyaz, 1 pembe, 2 kahverengi gurultu (normalize)."""
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n)
    f[0] = f[1]
    y = np.fft.irfft(X * f ** (-beta / 2), n)
    return y / (np.abs(y).max() + 1e-12)


def _modal_ir(sr: int, modlar, sure: float) -> np.ndarray:
    """(frekans, sonum_sn, kazanc) listesinden ahsap govde darbe tepkisi."""
    t = np.arange(int(sure * sr)) / sr
    ir = np.zeros_like(t)
    for f, tau, g in modlar:
        ir += g * np.exp(-t / tau) * np.sin(2 * np.pi * f * t)
    return ir / (np.abs(ir).max() + 1e-12)


def _evrisim(x: np.ndarray, ir: np.ndarray) -> np.ndarray:
    n = len(x) + len(ir) - 1
    N = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)]
    return y


def _yerlestir(hedef: np.ndarray, sinyal: np.ndarray, bas: float, sr: int,
               kazanc: float = 1.0, pan: float = 0.0):
    """Mono sinyali stereo hedefe (equal-power pan, -1 sol .. +1 sag) ekler."""
    i = int(bas * sr)
    if i >= len(hedef):
        return
    s = sinyal[: len(hedef) - i] * kazanc
    aci = (pan + 1) * np.pi / 4
    hedef[i:i + len(s), 0] += s * np.cos(aci)
    hedef[i:i + len(s), 1] += s * np.sin(aci)


# ---------------------------------------------------------------- katmanlar

def _oda_tonu(sr, sure, rng):
    n = int(sure * sr)
    kahve = _bant(_renkli(n, 2.0, rng), sr, 40, 400)
    t = np.arange(n) / sr
    # yavas ruzgar dalgalanmasi (ahsap aralarindan sizan hava)
    ruzgar = _bant(_renkli(n, 1.0, rng), sr, 350, 1600)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t + 1.3) * np.sin(2 * np.pi * 0.047 * t)
    y = kahve / (np.abs(kahve).max() + 1e-12) + 0.35 * ruzgar * lfo
    return y * _zarf(n, int(0.9 * sr), int(1.6 * sr))


def _el_temas(sr, rng):
    n = int(0.12 * sr)
    tik = _bant(rng.standard_normal(n), sr, 120, 900) * np.exp(-np.arange(n) / (0.018 * sr))
    ir = _modal_ir(sr, [(160, 0.05, 1.0), (340, 0.03, 0.6), (720, 0.015, 0.3)], 0.2)
    y = _evrisim(np.concatenate([tik, np.zeros(int(0.1 * sr))]), ir)
    return y / (np.abs(y).max() + 1e-12)


def _gicirti(sr, sure, rng):
    """Mentese/ahsap gicirtisi: degisken hizli stick-slip darbe dizisi,
    ahsap mod bankasindan gecirilir. Hiz egrisi kapagin hizlanip
    yavaslamasini taklit eder (perde once yukselir, sonra duser)."""
    n = int(sure * sr)
    t = np.arange(n) / sr
    u = t / sure
    hiz = 22 + 58 * np.sin(np.pi * u) ** 1.4 + 9 * np.sin(2 * np.pi * 2.3 * t)
    titreme = _bant(rng.standard_normal(n), sr, 1, 25)
    hiz *= 1 + 0.12 * titreme / (np.abs(titreme).max() + 1e-12)
    hiz = np.clip(hiz, 8, 140)
    faz = np.cumsum(hiz / sr)
    darbe = np.zeros(n)
    idx = np.nonzero(np.diff(np.floor(faz)) > 0)[0]
    darbe[idx] = 1 + 0.35 * rng.standard_normal(len(idx))
    ir = _modal_ir(sr, [
        (212, 0.035, 1.0), (437, 0.028, 0.9), (781, 0.020, 0.75),
        (1290, 0.012, 0.55), (2130, 0.008, 0.35), (3370, 0.005, 0.2),
    ], 0.25)
    y = _evrisim(darbe, ir)
    # surtunme hisirtisi
    y += 0.08 * _bant(rng.standard_normal(n), sr, 1500, 6000) * (hiz / hiz.max())
    zarf = _zarf(n, int(0.12 * sr), int(0.3 * sr)) * (0.55 + 0.45 * np.sin(np.pi * u))
    return y / (np.abs(y).max() + 1e-12) * zarf


def _kapak_dayanma(sr, rng):
    n = int(0.9 * sr)
    vur = np.zeros(n)
    vur[0] = 1.0
    vur[int(0.045 * sr)] = 0.35            # kucuk geri sekme
    vur[int(0.11 * sr)] = 0.12
    ir = _modal_ir(sr, [(92, 0.22, 1.0), (178, 0.14, 0.8), (311, 0.08, 0.5),
                        (590, 0.04, 0.3), (1150, 0.02, 0.15)], 0.8)
    y = _evrisim(vur, ir)
    y += 0.25 * _bant(rng.standard_normal(n), sr, 200, 2500) * np.exp(-np.arange(n) / (0.02 * sr))
    return y / (np.abs(y).max() + 1e-12)


def _toz(sr, sure, rng):
    """Dokulen toz bulutu (yumusak hisirti) + seyrek saman/tane tikirtilari, stereo."""
    n = int(sure * sr)
    t = np.arange(n) / sr
    zarf = (1 - np.exp(-t / 0.25)) * np.exp(-t / (sure * 0.38))
    out = np.zeros((n, 2))
    for k in range(2):
        h = _bant(rng.standard_normal(n), sr, 1800, 9000)
        h *= 0.7 + 0.3 * np.sin(2 * np.pi * (0.6 + 0.3 * k) * t + k)
        out[:, k] = 0.5 * h / (np.abs(h).max() + 1e-12) * zarf
    # tikirtilar: yogunlugu zamanla azalan Poisson sureci
    yogunluk = 70 * np.exp(-t / (sure * 0.3))
    olay = rng.random(n) < yogunluk / sr
    tik_ir = _bant(rng.standard_normal(int(0.004 * sr)), sr, 2500, 8000)
    tik_ir *= np.exp(-np.arange(len(tik_ir)) / (0.0008 * sr))
    for i in np.nonzero(olay)[0]:
        g = rng.uniform(0.15, 0.6)
        p = rng.uniform(-0.8, 0.8)
        aci = (p + 1) * np.pi / 4
        s = tik_ir[: n - i] * g
        out[i:i + len(s), 0] += s * np.cos(aci)
        out[i:i + len(s), 1] += s * np.sin(aci)
    return out


def _oyuk(sr, sure, rng):
    """Bos ambarin oyuk, hafif tedirgin rezonansi (alcak drone)."""
    n = int(sure * sr)
    t = np.arange(n) / sr
    y = (np.sin(2 * np.pi * 55 * t) + 0.55 * np.sin(2 * np.pi * 82.4 * t + 0.7)
         + 0.25 * np.sin(2 * np.pi * 110.6 * t))
    y *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.23 * t)
    y += 0.4 * _bant(_renkli(n, 1.0, rng), sr, 60, 240)
    return y / (np.abs(y).max() + 1e-12) * _zarf(n, int(2.0 * sr), int(1.4 * sr))


def _whoosh(sr, sure, rng):
    """Basliga gecis: merkez frekansi yukselen, sonda kesilen nefes/whoosh."""
    n = int(sure * sr)
    t = np.arange(n) / sr
    u = t / sure
    parca = 24
    out = np.zeros(n)
    gurultu = _renkli(n, 0.6, rng)
    for k in range(parca):
        a, b = k * n // parca, (k + 1) * n // parca
        fc = 250 * (14 ** (k / parca))
        seg = _bant(gurultu, sr, fc * 0.6, fc * 1.7)[a:b]
        out[a:b] = seg
    zarf = u ** 2.2 * (1 - np.exp(-(1 - u) * sure / 0.03))
    return out / (np.abs(out).max() + 1e-12) * zarf


def _baslik_darbe(sr, rng):
    """Derin darbe (perdesi dusen sinus) + parsomen hisirtisi."""
    n = int(2.6 * sr)
    t = np.arange(n) / sr
    f = 45 + 50 * np.exp(-t / 0.09)
    boom = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t / 0.65)
    boom += 0.3 * _bant(rng.standard_normal(n), sr, 30, 180) * np.exp(-t / 0.25)
    # parsomen: rastgele kapilanan kirispi yuksek frekans gurultu
    m = int(0.9 * sr)
    kapi = (_bant(rng.standard_normal(m), sr, 3, 40) > 0.01).astype(float)
    kapi = np.convolve(kapi, np.ones(int(0.004 * sr)) / int(0.004 * sr), "same")
    kagit = _bant(rng.standard_normal(m), sr, 1600, 7500) * kapi
    kagit *= np.exp(-np.arange(m) / (0.35 * sr))
    y = boom / (np.abs(boom).max() + 1e-12)
    y[:m] += 0.22 * kagit / (np.abs(kagit).max() + 1e-12)
    return y * _zarf(n, int(0.004 * sr), int(0.8 * sr))


def uret(sr: int = 44100, tohum: int = 1319, zaman: dict = None) -> np.ndarray:
    """Giris foley katmanini (n, 2) float32 olarak dondurur."""
    z = dict(ZAMANLAMA, **(zaman or {}))
    rng = np.random.default_rng(tohum)
    out = np.zeros((int(z["toplam"] * sr), 2))

    oda = _oda_tonu(sr, z["baslik"] + 0.6, rng)
    _yerlestir(out, oda, 0.0, sr, _db(-34), -0.15)
    _yerlestir(out, oda[::-1].copy(), 0.0, sr, _db(-36), 0.2)

    _yerlestir(out, _el_temas(sr, rng), z["el_temas"], sr, _db(-24), -0.25)
    _yerlestir(out, _gicirti(sr, z["gicirti_bit"] - z["gicirti_bas"], rng),
               z["gicirti_bas"], sr, _db(-9), -0.1)
    _yerlestir(out, _kapak_dayanma(sr, rng), z["kapak_dayanma"], sr, _db(-9), 0.1)

    toz = _toz(sr, z["toz_bit"] - z["toz_bas"], rng)
    i = int(z["toz_bas"] * sr)
    out[i:i + len(toz)] += toz[: len(out) - i] * _db(-19)

    _yerlestir(out, _oyuk(sr, z["oyuk_bit"] - z["oyuk_bas"], rng),
               z["oyuk_bas"], sr, _db(-27), 0.0)
    _yerlestir(out, _whoosh(sr, z["baslik"] - z["whoosh_bas"], rng),
               z["whoosh_bas"], sr, _db(-13), 0.0)
    _yerlestir(out, _baslik_darbe(sr, rng), z["baslik"], sr, _db(-8), 0.0)

    tepe = np.abs(out).max()
    if tepe > 0.95:
        out *= 0.95 / tepe
    return out.astype(np.float32)

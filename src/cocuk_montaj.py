"""
Cocuk animasyonu montaji: "Omer Asil" (dikey 9:16).

Tek avatar gorselinden kare kare canli bir cizgi film uretir:

  Omer (avatar):
    - konusma: anlatim sesinin zarfina gore agiz acilir/kapanir (ust dudak
      sabit, alt dudak ve cene asagi iner; agiz ici, dil ve disler cizilir)
    - goz kirpma, ifadeye gore goz kisma / uykulu goz
    - kas kaldirma (heyecan, sasirma), bas egme ve sallanma, nefes
    - kamera: bolume gore yakin/uzak cerceve, fisildarken yaklasma
  Sahne:
    - duvar, avatarin kendi duvari ayristirilarak (renk farki maskesi; sac
      telleri korunur) bolum ortamina gore degisir: oda, gunduz, aksam, gece,
      gece ormani, yagmur, gokkusagi, yildizlar, sakin gece
    - karakterler: minik yildiz Piril, Pamuk Bulut, Bilge Baykus
    - efektler: pirilti, kalpler, konfeti, kayan yildiz, atesbocekleri,
      yagmur, gokkusagi, buyuk sayi/renk yazilari
  Arayuz: karaoke altyazi, bolum kartlari, giris/kapanis kartlari.

Kareler isci sureclerde paralel uretilir; her surec kendi parcasini ffmpeg'e
kodlar, parcalar sonra kopyalanarak birlestirilip sesle muxlanir.
"""
import math
import os
import subprocess
from pathlib import Path

import numpy as np

from src.avatar_montaj import GozKirpma, _font, _bindir, _yumusat, _ffmpeg

AGIRLIK = np.array([0.299, 0.587, 0.114], dtype=np.float32)

ORTAM = {
    "oda":        dict(renk=(1.0, 1.0, 1.0)),
    "gunduz":     dict(ust=(96, 166, 236), alt=(196, 228, 250), gunes=True, bulut=3,
                       kus=True, renk=(1.03, 1.01, 0.98)),
    "aksam":      dict(ust=(70, 58, 128), orta=(236, 128, 112), alt=(255, 196, 128),
                       aksam_gunesi=True, bulut=2, bulut_renk=(255, 196, 200), yildiz=18,
                       renk=(1.05, 0.92, 0.86)),
    "gece":       dict(ust=(8, 14, 42), alt=(40, 46, 100), yildiz=140, ay=True,
                       renk=(0.80, 0.84, 0.98)),
    "gece_orman": dict(ust=(6, 16, 34), alt=(24, 50, 62), yildiz=70, ay=True, agac=True,
                       atesbocegi=12, renk=(0.76, 0.84, 0.92)),
    "yagmur":     dict(ust=(44, 54, 76), alt=(98, 112, 136), koyu_bulut=True, yagmur=True,
                       renk=(0.82, 0.86, 0.94)),
    "gokkusagi":  dict(ust=(30, 28, 84), alt=(128, 98, 168), yildiz=80, ay=True,
                       gokkusagi=True, renk=(0.90, 0.88, 1.0)),
    "yildizlar":  dict(ust=(14, 8, 40), alt=(68, 34, 106), yildiz=260, nebula=True,
                       anne_yildiz=True, renk=(0.82, 0.80, 1.0)),
    "gece_sakin": dict(ust=(6, 10, 32), alt=(30, 34, 80), yildiz=150, ay=True,
                       renk=(0.76, 0.80, 0.96)),
}

# ifade -> (kas, goz_kis, uyku, zoom_ek, egim_derece, bas_dy, sallanma)
IFADE_HEDEF = {
    "normal":  (0.00, 0.00, 0.00, 0.000, 0.0, 0.0, 1.0),
    "heyecan": (0.75, 0.00, 0.00, 0.020, 0.0, -2.0, 1.4),
    "sasirma": (1.00, 0.00, 0.00, 0.030, 0.0, -3.0, 0.8),
    "gulme":   (0.25, 0.42, 0.00, 0.010, 1.2, 0.0, 1.5),
    "fisilti": (0.15, 0.00, 0.00, 0.060, -1.0, 2.0, 0.6),
    "uzgun":   (0.00, 0.18, 0.00, 0.020, -1.8, 5.0, 0.6),
    "dusunme": (0.55, 0.00, 0.00, 0.010, 2.4, 0.0, 0.8),
    "uykulu":  (0.00, 0.00, 0.55, 0.035, 1.5, 3.0, 0.5),
}


# ------------------------------------------------------------------ yardimcilar

def _kutu_bulanik(x, r: int, tekrar: int = 3):
    """Ayrilabilir kutu bulaniklastirma (gauss yaklasimi), 2B ya da 3B dizi."""
    def tek(x, eksen):
        dolgu = [(r + 1, r) if e == eksen else (0, 0) for e in range(x.ndim)]
        c = np.cumsum(np.pad(x, dolgu, mode="edge"), axis=eksen, dtype=np.float64)
        n = x.shape[eksen]
        ust = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=eksen)
        alt = np.take(c, np.arange(0, n), axis=eksen)
        return ((ust - alt) / (2 * r + 1)).astype(np.float32)
    for _ in range(tekrar):
        x = tek(tek(x, 0), 1)
    return x


def _ss(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def _ease(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _gecis(t, bas, bit, giris=0.4, cikis=0.4) -> float:
    if t < bas or t > bit:
        return 0.0
    return min(_ease((t - bas) / giris), _ease((bit - t) / cikis))


def _ekle_rgb(kare, sprite, x: float, y: float, kazanc: float = 1.0):
    """RGB sprite'i (toplamali) kareye merkezden ekler; kenarlarda kirpar."""
    if kazanc <= 0.003:
        return
    h, w = sprite.shape[:2]
    H, W = kare.shape[:2]
    x0, y0 = int(round(x - w / 2)), int(round(y - h / 2))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x0 + w - sx0), min(H, y0 + h - sy0)
    if x1 > x0 and y1 > y0:
        kare[y0:y1, x0:x1] += sprite[sy0:sy0 + y1 - y0, sx0:sx0 + x1 - x0] * kazanc


def _rgba(img):
    """PIL RGBA -> (h, w, 4) float (rgb 0..255, alfa 0..1)."""
    a = np.asarray(img, dtype=np.float32)
    return np.dstack([a[..., :3], a[..., 3:] / 255.0])


def _parilti_sprite(r: float, renk=(255, 240, 200)):
    """Yumusak gauss nokta (toplamali RGB)."""
    yar = int(math.ceil(r * 3))
    yy, xx = np.mgrid[-yar:yar + 1, -yar:yar + 1].astype(np.float32)
    g = np.exp(-(xx ** 2 + yy ** 2) / (2 * r * r))
    return g[..., None] * np.array(renk, np.float32)


def _yildiz4_sprite(r: float, renk=(255, 246, 210)):
    """Dort kollu pirilti yildizi (toplamali RGB)."""
    yar = int(math.ceil(r))
    yy, xx = np.mgrid[-yar:yar + 1, -yar:yar + 1].astype(np.float32)
    kol = (np.exp(-(np.abs(xx) / (0.10 * r)) ** 1.2 - (np.abs(yy) / r) ** 2 * 3)
           + np.exp(-(np.abs(yy) / (0.10 * r)) ** 1.2 - (np.abs(xx) / r) ** 2 * 3))
    cekirdek = np.exp(-(xx ** 2 + yy ** 2) / (2 * (0.16 * r) ** 2))
    return np.clip(kol * 0.8 + cekirdek, 0, 1.4)[..., None] * np.array(renk, np.float32)


# ------------------------------------------------------------------ arka plan ayrimi

def duvar_ayir(img, duvar_alt):
    """Avatarin duvarini ayristirir.

    Donus: (alfa, temiz_duvar, on_plan) - on_plan = img - alfa * duvar
    (renk-farki ayrimi: yari saydam sac telleri dogru karisir:
     yeni = on_plan + alfa * yeni_arka_plan).
    """
    H, W = img.shape[:2]
    lum = img @ AGIRLIK
    doy = img.max(axis=2) - img.min(axis=2)
    xs = np.arange(W, dtype=np.float32)
    sinir = np.interp(xs, [p[0] for p in duvar_alt], [p[1] for p in duvar_alt]) - 2
    Y = np.arange(H, dtype=np.float32)[:, None]
    aday = (lum > 50) & (doy < 26) & (Y < sinir[None, :])

    bolge = np.zeros_like(aday)
    bolge[12] = aday[12]
    for _ in range(4000):
        p = np.pad(bolge, 1)
        yeni = (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:] | bolge) & aday
        if (yeni == bolge).all():
            break
        bolge = yeni

    w = bolge.astype(np.float32)
    for _ in range(4):
        p = np.pad(w, 1)
        w = np.minimum.reduce([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:], w])
    pay = _kutu_bulanik(img * w[..., None], 12)
    payda = _kutu_bulanik(w, 12)[..., None]
    gecerli = payda > 0.01
    duvar = np.where(gecerli, pay / np.maximum(payda, 1e-4), img[w > 0].mean(axis=0))
    for r in (30, 60, 120):
        m = gecerli[..., 0].astype(np.float32)
        p2 = _kutu_bulanik(duvar * m[..., None], r)
        q2 = _kutu_bulanik(m, r)[..., None]
        duvar = np.where(gecerli, duvar, p2 / np.maximum(q2, 1e-4))
        gecerli = gecerli | (q2 > 0.02)
    duvar_l = duvar @ AGIRLIK

    genis = bolge.copy()
    for _ in range(4):
        p = np.pad(genis, 1)
        genis = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:] | genis
    genis &= (Y < sinir[None, :] + 2)
    alfa = (np.clip((lum - 14) / np.maximum(duvar_l - 14, 10), 0, 1)
            * np.clip((34 - doy) / 14, 0, 1) * genis)
    alfa = np.where(bolge, np.maximum(alfa, 0.85), alfa).astype(np.float32)
    on = (img - alfa[..., None] * duvar).astype(np.float32)
    return alfa, duvar.astype(np.float32), on


# ------------------------------------------------------------------ yuz parcalari

class Agiz:
    """Gulumseme cizgisini acarak konusan agiz (ust dudak sabit, cene iner)."""

    def __init__(self, gorsel, p: dict):
        cizgi = np.array(p["cizgi"], dtype=np.float32)
        self.xl, self.xr = float(p["acilma_sol"]), float(p["acilma_sag"])
        self.xp = float(p["tepe_x"])
        self.acik_max = float(p.get("acik_max", 15))
        self.cene = float(p["cene_y"])
        self.x0 = int(cizgi[0, 0]) - 60
        self.x1 = int(cizgi[-1, 0]) + 40
        self.y0 = int(cizgi[:, 1].min()) - 10
        self.y1 = int(self.cene + 70)
        xs = np.arange(self.x0, self.x1, dtype=np.float32)
        self.Y = _yumusat(np.interp(xs, cizgi[:, 0], cizgi[:, 1]), 9)[None, :]
        u = np.where(xs < self.xp, (xs - self.xl) / (self.xp - self.xl),
                     (self.xr - xs) / (self.xr - self.xp))
        self.profil = (np.sin(math.pi / 2 * np.clip(u, 0, 1)) ** 0.85)[None, :]
        cene = np.minimum(_ss((xs - (self.xl - 70)) / 90.0), _ss((self.xr + 50 - xs) / 70.0))
        self.cene_profil = cene[None, :]
        self.ys = np.arange(self.y0, self.y1, dtype=np.float32)[:, None]
        self.xs = xs[None, :]
        self.kolon = np.arange(self.x1 - self.x0)[None, :]
        self.yama = gorsel[self.y0:self.y1, self.x0:self.x1].astype(np.float32).copy()

    def uygula(self, img, acik: float):
        """img (kopya) uzerinde agzi `acik` (0..1) kadar acar (yerinde)."""
        if acik < 0.03:
            return
        ys, Y = self.ys, self.Y
        Hm = acik * self.acik_max * self.profil
        J = 0.5 * acik * self.acik_max * self.cene_profil
        k0, s0 = Y + Hm, Y
        k1, s1 = self.cene + J, self.cene
        k2 = s2 = float(self.y1 - 1)
        alt1 = s0 + (ys - k0) * (s1 - s0) / np.maximum(k1 - k0, 1.0)
        alt2 = s1 + (ys - k1) * (s2 - s1) / np.maximum(k2 - k1, 1.0)
        kaynak = np.where(ys <= Y, ys, np.where(ys < k0, Y, np.where(ys < k1, alt1, alt2)))
        r = np.clip(kaynak - self.y0, 0, self.yama.shape[0] - 1.001)
        r0 = np.floor(r).astype(np.int32)
        f = (r - r0)[..., None]
        cikti = self.yama[r0, self.kolon] * (1 - f) + self.yama[r0 + 1, self.kolon] * f

        # Agiz ici: koyu gradyan + dil + ust disler.
        ic = np.clip(ys - Y + 0.5, 0, 1) * np.clip(k0 - ys + 0.5, 0, 1) * (Hm > 0.6)
        if ic.max() > 0:
            derin = np.clip((ys - Y) / np.maximum(Hm, 1.0), 0, 1)[..., None]
            renk = np.array([38, 8, 14], np.float32) * (1 - derin) + np.array([92, 24, 34], np.float32) * derin
            hmax = float(Hm.max())
            genislik = 0.24 * (self.xr - self.xl)
            dil = np.clip((1.0 - ((self.xs - self.xp - 4) / genislik) ** 2
                           - ((ys - (Y + Hm * 1.02)) / max(1.0, 0.48 * hmax)) ** 2) * 3.0, 0, 1) * 0.9
            renk = renk * (1 - dil[..., None]) + np.array([200, 86, 98], np.float32) * dil[..., None]
            if acik > 0.35:
                dis = (np.clip(Y + 0.20 * Hm - ys + 0.5, 0, 1) * _ss((self.profil - 0.45) * 6)
                       * min(1.0, (acik - 0.35) * 4))
                renk = renk * (1 - dis[..., None] * 0.92) + np.array([240, 236, 228], np.float32) * dis[..., None] * 0.92
            cikti = cikti * (1 - ic[..., None]) + renk * ic[..., None]
        img[self.y0:self.y1, self.x0:self.x1] = cikti


class Kaslar:
    """Kaslari (ve uzerindeki alni) yukari kaldiran yerel bukme."""

    def __init__(self, gorsel, kaslar):
        self.parcalar = []
        H, W = gorsel.shape[:2]
        for cx, cy, rx, ry in kaslar:
            x0, x1 = max(0, int(cx - 1.9 * rx)), min(W, int(cx + 1.9 * rx))
            y0, y1 = max(0, int(cy - 3.4 * ry)), min(H, int(cy + 1.8 * ry))
            ys = np.arange(y0, y1, dtype=np.float32)[:, None]
            xs = np.arange(x0, x1, dtype=np.float32)[None, :]
            yatay = np.exp(-((xs - cx) / rx) ** 2)
            dikey = np.where(ys < cy, np.exp(-((ys - cy) / (2.6 * ry)) ** 2),
                             np.exp(-((ys - cy) / (0.9 * ry)) ** 2))
            pencere = _ss((ys - y0) / (1.2 * ry)) * _ss((y1 - 1 - ys) / (0.5 * ry))
            self.parcalar.append(dict(x0=x0, x1=x1, y0=y0, y1=y1, ys=ys,
                                      agirlik=(yatay * dikey * pencere).astype(np.float32),
                                      kolon=np.arange(x1 - x0)[None, :],
                                      yama=gorsel[y0:y1, x0:x1].astype(np.float32).copy()))

    def uygula(self, img, kas: float, px: float = 5.0):
        if abs(kas) < 0.02:
            return
        for p in self.parcalar:
            r = np.clip(p["ys"] + kas * px * p["agirlik"] - p["y0"], 0, p["yama"].shape[0] - 1.001)
            r0 = np.floor(r).astype(np.int32)
            f = (r - r0)[..., None]
            img[p["y0"]:p["y1"], p["x0"]:p["x1"]] = (p["yama"][r0, p["kolon"]] * (1 - f)
                                                     + p["yama"][r0 + 1, p["kolon"]] * f)


# ------------------------------------------------------------------ karakter cizimleri

def _yildiz_noktalari(cx, cy, R, r, kol=5, aci0=-90):
    pts = []
    for i in range(kol * 2):
        a = math.radians(aci0 + i * 180 / kol)
        rr = R if i % 2 == 0 else r
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def piril_sprite(R: int, mutlu: bool):
    """Minik yildiz Piril: yuzlu, yuvarlak koseli bes kollu yildiz (RGBA)."""
    from PIL import Image, ImageDraw, ImageFilter

    k = 4
    boyut = int(R * 2.6)
    S = boyut * k
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = S / 2
    Rk = R * k
    pts = _yildiz_noktalari(c, c + 0.05 * Rk, Rk, Rk * 0.5)
    d.polygon(pts, fill=(255, 206, 60, 255))
    d.line(pts + [pts[0]], fill=(255, 206, 60, 255), width=int(0.28 * Rk), joint="curve")
    ic = _yildiz_noktalari(c - 0.06 * Rk, c - 0.02 * Rk, Rk * 0.7, Rk * 0.36)
    parlak = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(parlak).polygon(ic, fill=(255, 240, 150, 200))
    img = Image.alpha_composite(img, parlak.filter(ImageFilter.GaussianBlur(0.08 * Rk)))
    d = ImageDraw.Draw(img)
    gz, gy = 0.27 * Rk, c - 0.02 * Rk
    for sx in (-1, 1):
        ex = c + sx * gz
        if mutlu:
            d.ellipse([ex - 0.12 * Rk, gy - 0.16 * Rk, ex + 0.12 * Rk, gy + 0.16 * Rk], fill=(70, 42, 28, 255))
        else:
            d.ellipse([ex - 0.11 * Rk, gy - 0.12 * Rk, ex + 0.11 * Rk, gy + 0.14 * Rk], fill=(70, 42, 28, 255))
        d.ellipse([ex - 0.05 * Rk, gy - 0.11 * Rk, ex + 0.03 * Rk, gy - 0.03 * Rk], fill=(255, 255, 255, 255))
        d.ellipse([ex + sx * 0.10 * Rk - 0.10 * Rk, gy + 0.14 * Rk, ex + sx * 0.10 * Rk + 0.10 * Rk,
                   gy + 0.24 * Rk], fill=(255, 140, 120, 150))
    my = c + 0.20 * Rk
    if mutlu:
        d.arc([c - 0.2 * Rk, my - 0.2 * Rk, c + 0.2 * Rk, my + 0.12 * Rk], 20, 160,
              fill=(110, 50, 30, 255), width=int(0.06 * Rk))
    else:
        d.arc([c - 0.15 * Rk, my + 0.02 * Rk, c + 0.15 * Rk, my + 0.24 * Rk], 200, 340,
              fill=(110, 50, 30, 255), width=int(0.055 * Rk))
        tx = c + gz + 0.02 * Rk
        d.ellipse([tx - 0.06 * Rk, gy + 0.16 * Rk, tx + 0.06 * Rk, gy + 0.32 * Rk], fill=(150, 210, 255, 230))
    img = img.resize((boyut, boyut), Image.LANCZOS)
    return _rgba(img)


def bulut_sprite(en: int, mutlu: bool, renk=(250, 250, 255)):
    """Pamuk Bulut: yuzlu, pofuduk bulut (RGBA)."""
    from PIL import Image, ImageDraw, ImageFilter

    k = 3
    W, H = en * k, int(en * 0.66) * k
    maske = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(maske)
    for cx, cy, r in ((0.30, 0.62, 0.20), (0.50, 0.45, 0.27), (0.72, 0.58, 0.21),
                      (0.20, 0.72, 0.14), (0.84, 0.72, 0.13), (0.50, 0.72, 0.22)):
        d.ellipse([(cx - r) * W, cy * H - r * W, (cx + r) * W, cy * H + r * W], fill=255)
    maske = maske.filter(ImageFilter.GaussianBlur(2 * k))
    a = np.asarray(maske, dtype=np.float32) / 255.0
    yy = np.linspace(0, 1, H)[:, None]
    golge = 1.0 - 0.16 * np.clip((yy - 0.45) / 0.5, 0, 1)
    rgb = np.ones((H, W, 3), np.float32) * np.array(renk, np.float32) * golge[..., None]
    img = Image.fromarray(np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)
    cx, gy = 0.5 * W, 0.56 * H
    for sx in (-1, 1):
        ex = cx + sx * 0.12 * W
        if mutlu:
            d.arc([ex - 0.045 * W, gy - 0.05 * W, ex + 0.045 * W, gy + 0.03 * W], 200, 340,
                  fill=(60, 64, 96, 255), width=int(0.012 * W))
        else:
            d.arc([ex - 0.04 * W, gy - 0.03 * W, ex + 0.04 * W, gy + 0.03 * W], 20, 160,
                  fill=(60, 64, 96, 255), width=int(0.011 * W))
            d.ellipse([ex - 0.012 * W, gy + 0.04 * W, ex + 0.012 * W, gy + 0.075 * W],
                      fill=(130, 190, 255, 230))
        d.ellipse([ex + sx * 0.05 * W - 0.035 * W, gy + 0.045 * W, ex + sx * 0.05 * W + 0.035 * W,
                   gy + 0.075 * W], fill=(255, 160, 170, 140))
    my = gy + 0.09 * W
    if mutlu:
        d.chord([cx - 0.06 * W, my - 0.04 * W, cx + 0.06 * W, my + 0.06 * W], 0, 180,
                fill=(120, 50, 70, 255))
    else:
        d.arc([cx - 0.05 * W, my, cx + 0.05 * W, my + 0.06 * W], 200, 340,
              fill=(60, 64, 96, 255), width=int(0.01 * W))
    return _rgba(img.resize((en, int(en * 0.66)), Image.LANCZOS))


def baykus_sprite(boy: int):
    """Bilge Baykus silueti + dal (RGBA). Gozler ayrica cizilir."""
    from PIL import Image, ImageDraw

    k = 3
    W, H = int(boy * 1.9) * k, int(boy * 1.25) * k
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([(0, 0.86 * H), (0.45 * W, 0.80 * H), (0.80 * W, 0.84 * H), (W, 0.78 * H)],
           fill=(18, 14, 18, 255), width=int(0.05 * H), joint="curve")
    for lx, ly in ((0.70, 0.74), (0.86, 0.70), (0.58, 0.88)):
        d.ellipse([(lx - 0.05) * W, (ly - 0.035) * H, (lx + 0.05) * W, (ly + 0.035) * H], fill=(14, 26, 22, 255))
    cx = 0.36 * W
    govde, kanat, gogus, yuz = (78, 66, 84, 255), (52, 44, 60, 255), (128, 112, 124, 255), (150, 134, 140, 255)
    d.ellipse([cx - 0.17 * W, 0.30 * H, cx + 0.17 * W, 0.84 * H], fill=govde)
    d.ellipse([cx - 0.20 * W, 0.40 * H, cx - 0.06 * W, 0.80 * H], fill=kanat)
    d.ellipse([cx + 0.06 * W, 0.40 * H, cx + 0.20 * W, 0.80 * H], fill=kanat)
    d.ellipse([cx - 0.10 * W, 0.48 * H, cx + 0.10 * W, 0.80 * H], fill=gogus)
    d.ellipse([cx - 0.15 * W, 0.12 * H, cx + 0.15 * W, 0.50 * H], fill=govde)
    d.polygon([(cx - 0.14 * W, 0.22 * H), (cx - 0.12 * W, 0.04 * H), (cx - 0.04 * W, 0.17 * H)], fill=govde)
    d.polygon([(cx + 0.14 * W, 0.22 * H), (cx + 0.12 * W, 0.04 * H), (cx + 0.04 * W, 0.17 * H)], fill=govde)
    for sx in (-1, 1):
        d.ellipse([cx + sx * 0.068 * W - 0.065 * W, 0.20 * H, cx + sx * 0.068 * W + 0.065 * W, 0.40 * H], fill=yuz)
    d.polygon([(cx - 0.02 * W, 0.36 * H), (cx + 0.02 * W, 0.36 * H), (cx, 0.43 * H)], fill=(232, 160, 60, 255))
    for i in range(3):
        d.line([(cx - 0.06 * W + i * 0.06 * W, 0.83 * H), (cx - 0.07 * W + i * 0.06 * W, 0.88 * H)],
               fill=(200, 150, 60, 255), width=max(2, int(0.012 * W)))
    return _rgba(img.resize((W // k, H // k), Image.LANCZOS))


def kalp_sprite(r: int):
    from PIL import Image, ImageDraw

    k = 4
    S = int(r * 2.4) * k
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    R = r * k
    c = S / 2
    d.ellipse([c - R, c - R * 0.7, c, c + R * 0.3], fill=(255, 92, 140, 255))
    d.ellipse([c, c - R * 0.7, c + R, c + R * 0.3], fill=(255, 92, 140, 255))
    d.polygon([(c - R * 0.96, c - R * 0.1), (c + R * 0.96, c - R * 0.1), (c, c + R * 1.05)],
              fill=(255, 92, 140, 255))
    d.ellipse([c - R * 0.62, c - R * 0.45, c - R * 0.3, c - R * 0.15], fill=(255, 210, 225, 230))
    return _rgba(img.resize((S // k, S // k), Image.LANCZOS))


# ------------------------------------------------------------------ yazilar

def _metin_sprite(satirlar, font, renk=(255, 255, 255), kontur=(24, 26, 56), kalinlik=3,
                  golge=0.55, satir_arasi=1.15):
    """Konturlu, golgeli, ortali cok satirli yazi (RGBA float)."""
    from PIL import Image, ImageDraw, ImageFilter

    asc, desc = font.getmetrics()
    sh = int((asc + desc) * satir_arasi)
    pay = 16 + kalinlik
    en = int(max(font.getlength(s) for s in satirlar)) + 2 * pay
    boy = sh * len(satirlar) + 2 * pay
    img = Image.new("RGBA", (en, boy), (0, 0, 0, 0))
    gol = Image.new("L", (en, boy), 0)
    d, dg = ImageDraw.Draw(img), ImageDraw.Draw(gol)
    for i, s in enumerate(satirlar):
        x = (en - font.getlength(s)) / 2
        y = pay + i * sh
        dg.text((x, y + 3), s, font=font, fill=255, stroke_width=kalinlik + 1)
        d.text((x, y), s, font=font, fill=tuple(renk) + (255,), stroke_width=kalinlik,
               stroke_fill=tuple(kontur) + (255,))
    a = _rgba(img)
    g = np.asarray(gol.filter(ImageFilter.GaussianBlur(5)), np.float32) / 255.0 * golge
    toplam = a[..., 3] + g * (1 - a[..., 3])
    rgb = a[..., :3] * (a[..., 3] / np.maximum(toplam, 1e-6))[..., None]
    return np.dstack([rgb, toplam])


class Altyazi:
    """Karaoke altyazi: soylenen kelimeler sariya boyanir."""

    def __init__(self, satir, font, max_en: int, k: float):
        from PIL import Image, ImageDraw, ImageFilter

        kelimeler = satir.metin.split()
        bosluk = font.getlength(" ")
        satirlar, mevcut, en_ = [], [], 0.0
        for i, kel in enumerate(kelimeler):
            w = font.getlength(kel)
            if mevcut and en_ + bosluk + w > max_en:
                satirlar.append(mevcut)
                mevcut, en_ = [], 0.0
            mevcut.append((i, kel, w))
            en_ += (bosluk if len(mevcut) > 1 else 0) + w
        if mevcut:
            satirlar.append(mevcut)
        asc, desc = font.getmetrics()
        sh = int((asc + desc) * 1.12)
        kal = max(2, int(3 * k))
        pay = 14 + kal
        genislikler = [sum(w for _, _, w in s) + bosluk * (len(s) - 1) for s in satirlar]
        en = int(max(genislikler)) + 2 * pay
        boy = sh * len(satirlar) + 2 * pay
        beyaz = Image.new("RGBA", (en, boy), (0, 0, 0, 0))
        sari = Image.new("RGBA", (en, boy), (0, 0, 0, 0))
        gol = Image.new("L", (en, boy), 0)
        db, ds, dg = ImageDraw.Draw(beyaz), ImageDraw.Draw(sari), ImageDraw.Draw(gol)
        self.kutular = [None] * len(kelimeler)
        for li, s in enumerate(satirlar):
            x = (en - genislikler[li]) / 2
            y = pay + li * sh
            for i, kel, w in s:
                for dr, renk in ((db, (255, 255, 255)), (ds, (255, 214, 64))):
                    dr.text((x, y), kel, font=font, fill=renk + (255,), stroke_width=kal,
                            stroke_fill=(22, 24, 52, 255))
                dg.text((x, y + 3), kel, font=font, fill=255, stroke_width=kal + 1)
                self.kutular[i] = (int(x - kal), int(x + w + kal), y - kal, y + sh)
                x += w + bosluk
        g = np.asarray(gol.filter(ImageFilter.GaussianBlur(5)), np.float32) / 255.0 * 0.6
        self.beyaz = self._golgeli(_rgba(beyaz), g)
        self.sari = _rgba(sari)
        self.kelime_zaman = [(satir.bas + b, satir.bas + e) for b, e, _ in satir.kelimeler]

    @staticmethod
    def _golgeli(a, g):
        toplam = a[..., 3] + g * (1 - a[..., 3])
        rgb = a[..., :3] * (a[..., 3] / np.maximum(toplam, 1e-6))[..., None]
        return np.dstack([rgb, toplam])

    def ciz(self, kare, t, x, y, opaklik):
        _bindir(kare, self.beyaz, x, y, opaklik)
        maske = np.zeros(self.sari.shape[:2], np.float32)
        for (b, e), kutu in zip(self.kelime_zaman, self.kutular):
            if kutu is None or t < b:
                continue
            x0, x1, y0, y1 = kutu
            oran = 1.0 if t >= e else (t - b) / max(1e-3, e - b)
            xs = int(x0 + (x1 - x0) * oran)
            maske[max(0, y0):y1, max(0, x0):xs] = 1.0
        if maske.any():
            sp = self.sari.copy()
            sp[..., 3] *= maske
            _bindir(kare, sp, x, y, opaklik)


# ------------------------------------------------------------------ sahne

class Sahne:
    """Bir isci surecinde kareleri ureten sahne (tum on hesaplar burada)."""

    def __init__(self, c, profil: dict, ayrim: dict, parametreler: dict, en: int, boy: int,
                 fps: int, tohum: int = 5):
        self.c, self.W, self.H, self.fps = c, en, boy, fps
        self.P = parametreler
        self.rng = np.random.default_rng(tohum)
        self.k = en / 720.0

        img = ayrim["gorsel"]
        self.alfa = ayrim["alfa"]
        self.on = ayrim["on"]
        self.duvar = ayrim["duvar"]
        self.odak = profil.get("odak", [en / 2, boy * 0.44])
        self.gogus_y = float(profil.get("gogus_y", boy * 0.68))
        self.goz = GozKirpma(img, profil.get("gozler", []))
        self.agiz = Agiz(img, profil["agiz"]) if profil.get("agiz") else None
        self.kaslar = Kaslar(img, profil.get("kaslar", []))
        self.kirpmalar = parametreler["kirpmalar"]

        Y, X = np.mgrid[0:boy, 0:en].astype(np.float32)
        self.X, self.Y = X, Y
        r = np.sqrt(((X - en * 0.5) / en) ** 2 + ((Y - boy * 0.45) / boy) ** 2)
        vinyet = 1.0 - 0.42 * np.clip(r / 0.65, 0, 1) ** 2.6
        alt = 1.0 - 0.55 * _ss((Y - boy * 0.70) / (boy * 0.30))
        self.carpan = (vinyet * alt)[..., None].astype(np.float32)

        self._tabanlar = {}
        self._hazirla_varliklar()
        self._yazi_onbellek = {}
        self.f_alt = _font("yari", int(34 * self.k))
        self.f_bolum = _font("baslik", int(46 * self.k))
        self.f_kucuk = _font("yari", int(24 * self.k))
        self.f_dev = _font("baslik", int(112 * self.k))
        self.f_baslik = _font("baslik", int(92 * self.k))
        self.f_alt_baslik = _font("baslik", int(52 * self.k))

    # -------------------------------------------------- varliklar
    def _hazirla_varliklar(self):
        W, H, k, rng = self.W, self.H, self.k, self.rng
        self.yildizlar = dict(x=rng.uniform(0, W, 300), y=rng.uniform(0, H * 0.8, 300) ** 1.0,
                              r=rng.uniform(0.7, 1.9, 300), faz=rng.uniform(0, 6.3, 300),
                              hiz=rng.uniform(0.8, 2.6, 300), a=rng.uniform(0.45, 1.0, 300))
        self.y_sprite = [_parilti_sprite(r * k) for r in (0.8, 1.2, 1.7)]
        self.y4 = [_yildiz4_sprite(r * k) for r in (9, 14, 22, 32)]
        self.piril = {True: piril_sprite(int(50 * k), True), False: piril_sprite(int(50 * k), False)}
        self.piril_hale = _parilti_sprite(36 * k, (255, 200, 90))
        self.bulut_kar = {True: bulut_sprite(int(250 * k), True), False: bulut_sprite(int(250 * k), False)}
        self.baykus = np.ascontiguousarray(baykus_sprite(int(120 * k))[:, ::-1])  # dal saga uzanir
        self.kalp = [kalp_sprite(int(r * k)) for r in (20, 27, 34)]
        self.bulutlar = [bulut_sprite(int(w * k), True)[..., [0, 1, 2, 3]] for w in (240, 300, 200)]
        for b in self.bulutlar:                         # suz bulutlar: yuzsuz versiyon
            b[...] = self._yuzsuz_bulut(b)
        self.ates_x = rng.uniform(0, W, 40)
        self.ates_y = rng.uniform(H * 0.15, H * 0.75, 40)
        self.ates_f = rng.uniform(0, 6.3, (40, 3))
        self.ates_sp = _parilti_sprite(3.2 * k, (210, 255, 120))
        self.ates_hale = _parilti_sprite(9 * k, (120, 200, 60))
        self.goz_hale = _parilti_sprite(9 * k, (255, 196, 80))
        self.yagmur_doku = self._yagmur_dokusu()
        self.gokkusagi = self._gokkusagi()
        self.ay_sp = self._ay()
        self.konfeti = dict(x=rng.uniform(0, W, 90), v=rng.uniform(160, 320, 90),
                            faz=rng.uniform(0, 6.3, 90), w=rng.uniform(6, 12, 90) * k,
                            renk=rng.choice(np.array([[255, 90, 90], [255, 200, 60], [90, 200, 120],
                                                      [80, 160, 255], [200, 110, 240], [255, 140, 200]],
                                                     np.float32), 90))

    @staticmethod
    def _yuzsuz_bulut(sp):
        a = sp[..., 3]
        rgb = np.ones_like(sp[..., :3]) * 252.0
        yy = np.linspace(0, 1, sp.shape[0])[:, None]
        rgb *= (1.0 - 0.15 * np.clip((yy - 0.45) / 0.5, 0, 1))[..., None]
        return np.dstack([rgb, a])

    def _yagmur_dokusu(self):
        W, H, rng = self.W, self.H, self.rng
        doku = np.zeros((2 * H, W), np.float32)
        for _ in range(int(900 * self.k)):
            x, y = rng.uniform(0, W), rng.uniform(0, 2 * H)
            boy = rng.uniform(18, 38) * self.k
            for j in range(int(boy)):
                yy, xx = int(y + j) % (2 * H), int(x - j * 0.18) % W
                doku[yy, xx] = max(doku[yy, xx], 0.5 + 0.5 * j / boy)
        return _kutu_bulanik(doku, 1, 1)

    def _gokkusagi(self):
        W, H = self.W, self.H
        cx, cy = W * 0.5, H * 0.60
        d = np.sqrt((self.X - cx) ** 2 + (self.Y - cy) ** 2)
        renkler = np.array([[236, 64, 64], [255, 150, 40], [255, 220, 50], [80, 200, 90],
                            [70, 140, 240], [80, 90, 200], [170, 90, 220]], np.float32)
        r_ic, r_dis = 330 * self.k, 470 * self.k
        u = (r_dis - d) / (r_dis - r_ic) * 7
        i = np.clip(np.floor(u), 0, 6).astype(np.int32)
        rgb = renkler[i]
        a = (np.clip(u * 2, 0, 1) * np.clip((7 - u) * 2, 0, 1) * (self.Y < cy)).astype(np.float32) * 0.62
        aci = np.arctan2(cy - self.Y, self.X - cx)          # pi (sol) -> 0 (sag)
        ilerleme = (math.pi - np.clip(aci, 0, math.pi)) / math.pi
        return dict(rgb=rgb.astype(np.float32), a=a, ilerleme=ilerleme.astype(np.float32))

    def _ay(self):
        r = 50 * self.k
        yar = int(r * 3.2)
        yy, xx = np.mgrid[-yar:yar + 1, -yar:yar + 1].astype(np.float32)
        d = np.sqrt(xx ** 2 + yy ** 2)
        disk = np.clip(r - d + 0.5, 0, 1)
        kraterler = np.ones_like(d)
        for kx, ky, kr in ((-0.3, -0.2, 0.22), (0.25, 0.15, 0.16), (-0.05, 0.4, 0.12), (0.35, -0.35, 0.1)):
            kraterler -= 0.10 * np.clip(kr * r - np.sqrt((xx - kx * r) ** 2 + (yy - ky * r) ** 2), 0, 1.5)
        rgb = np.array([246, 240, 214], np.float32) * (disk * kraterler)[..., None]
        hale = np.exp(-(d / (1.25 * r)) ** 2)[..., None] * np.array([120, 130, 170], np.float32) * 0.6
        return dict(disk=rgb, a=disk, hale=hale)

    # -------------------------------------------------- arka plan tabanlari
    def _taban(self, ortam: str):
        if ortam in self._tabanlar:
            return self._tabanlar[ortam]
        W, H, k = self.W, self.H, self.k
        o = ORTAM[ortam]
        if ortam == "oda":
            taban = self.duvar.copy()
        else:
            u = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
            ust, alt = np.array(o["ust"], np.float32), np.array(o["alt"], np.float32)
            if "orta" in o:
                orta = np.array(o["orta"], np.float32)
                renk = np.where(u < 0.55, ust + (orta - ust) * (u / 0.55),
                                orta + (alt - orta) * ((u - 0.55) / 0.45))
            else:
                renk = ust + (alt - ust) * u
            taban = np.broadcast_to(renk, (H, W, 3)).astype(np.float32).copy()
        if o.get("nebula"):
            for cx, cy, r, rnk in ((0.2, 0.25, 260, (120, 60, 180)), (0.8, 0.15, 220, (40, 90, 170)),
                                   (0.75, 0.55, 280, (170, 70, 140)), (0.3, 0.6, 200, (60, 50, 150))):
                g = np.exp(-(((self.X - cx * W) ** 2 + (self.Y - cy * H) ** 2) / (2 * (r * k) ** 2)))
                taban += g[..., None] * np.array(rnk, np.float32) * 0.45
        if o.get("aksam_gunesi"):
            g = np.exp(-(((self.X - 90 * k) ** 2 + (self.Y - 620 * k) ** 2) / (2 * (170 * k) ** 2)))
            taban += g[..., None] * np.array([255, 170, 90], np.float32) * 0.55
            disk = np.clip(70 * k - np.sqrt((self.X - 90 * k) ** 2 + (self.Y - 620 * k) ** 2), 0, 1)
            taban = taban * (1 - disk[..., None]) + np.array([255, 214, 120], np.float32) * disk[..., None]
        if o.get("koyu_bulut"):
            for cx, cy, w in ((0.1, 0.06, 360), (0.45, 0.02, 420), (0.85, 0.07, 380), (0.25, 0.16, 300),
                              (0.7, 0.18, 320)):
                sp = self._yuzsuz_bulut(bulut_sprite(int(w * k), True))
                sp[..., :3] *= np.array([0.42, 0.46, 0.55], np.float32)
                _bindir(taban, sp, cx * W, cy * H, 0.95)
        if o.get("agac"):
            from PIL import Image, ImageDraw
            maske = Image.new("L", (W, H), 0)
            d = ImageDraw.Draw(maske)
            for kx, ky, r in ((0.0, 0.22, 150), (0.08, 0.34, 120), (-0.04, 0.45, 140), (1.0, 0.18, 150),
                              (0.94, 0.30, 115), (1.04, 0.42, 150)):
                d.ellipse([kx * W - r * k, ky * H - r * k, kx * W + r * k, ky * H + r * k], fill=255)
            d.rectangle([0, 0.3 * H, 34 * k, H], fill=255)
            d.rectangle([W - 30 * k, 0.25 * H, W, H], fill=255)
            m = _kutu_bulanik(np.asarray(maske, np.float32) / 255.0, 2, 2)[..., None]
            taban = taban * (1 - m) + np.array([6, 14, 20], np.float32) * m
        self._tabanlar[ortam] = taban
        return taban

    # -------------------------------------------------- karakter durumlari
    def _olay_t(self, olay):
        return self.c.olay_zamani(olay)

    def _durum(self, gel, git, t, gecis_in=1.6, gecis_out=1.8):
        """(gorunurluk_asamasi, ilerleme) : 'yok' | 'giris' | 'var' | 'cikis'."""
        g = [x for x in self._olay_t(gel) if x <= t]
        if not g:
            return "yok", 0.0
        t0 = g[-1]
        c = [x for x in self._olay_t(git) if x >= t0] if git else []
        if c and t >= c[0]:
            u = (t - c[0]) / gecis_out
            return ("cikis", u) if u < 1 else ("gitti", 1.0)
        u = (t - t0) / gecis_in
        return ("giris", u) if u < 1 else ("var", 1.0)

    def _ciz_piril(self, bg, t):
        asama, u = self._durum("piril_gel", "piril_git", t, 1.6, 1.9)
        if asama == "yok":
            return
        k, W = self.k, self.W
        mutlu = bool([x for x in self._olay_t("piril_mutlu") if x <= t])
        yer = np.array([640 * k, 335 * k])
        hedef = np.array([548 * k, 74 * k])
        sal = np.array([4 * k * math.sin(1.3 * t), 9 * k * math.sin(2.1 * t)])
        olcek = 1.0
        if asama == "giris":
            e = 1 - (1 - u) ** 3
            konum = np.array([W + 40 * k, -60 * k]) * (1 - e) + yer * e
        elif asama == "var":
            konum = yer + sal
        elif asama == "cikis":
            e = u * u * (3 - 2 * u)
            konum = (yer + sal) * (1 - e) + hedef * e
            olcek = 1.0 - 0.55 * e
            for j in range(6):                         # pirilti izi
                v = max(0.0, e - j * 0.07)
                p = (yer + sal) * (1 - v) + hedef * v
                _ekle_rgb(bg, self.y4[0], p[0], p[1], 0.5 * (1 - j / 6))
        else:
            konum, olcek = hedef, 0.45
        nabiz = 0.85 + 0.15 * math.sin(3.0 * t)
        _ekle_rgb(bg, self.piril_hale, konum[0], konum[1], 0.55 * nabiz * olcek)
        sp = self.piril[mutlu or asama in ("cikis", "gitti")]
        if abs(olcek - 1) > 0.02:
            sp = self._olcekle(sp, olcek)
        _bindir(bg, sp, konum[0], konum[1], 1.0)

    def _olcekle(self, sp, olcek):
        from PIL import Image
        h, w = sp.shape[:2]
        nw, nh = max(2, int(w * olcek)), max(2, int(h * olcek))
        rgba = np.dstack([sp[..., :3], sp[..., 3:] * 255]).clip(0, 255).astype(np.uint8)
        return _rgba(Image.fromarray(rgba, "RGBA").resize((nw, nh), Image.BILINEAR))

    def _ciz_bulut(self, bg, t):
        asama, u = self._durum("bulut_gel", "bulut_git", t, 2.2, 2.2)
        if asama in ("yok", "gitti"):
            return
        k = self.k
        mutlu = bool([x for x in self._olay_t("bulut_mutlu") if x <= t])
        yer = np.array([612 * k, 182 * k + 6 * k * math.sin(1.1 * t)])
        if asama == "giris":
            e = 1 - (1 - u) ** 3
            konum = np.array([self.W + 200 * k, 182 * k]) * (1 - e) + yer * e
        elif asama == "cikis":
            e = u * u
            konum = yer * (1 - e) + np.array([self.W + 220 * k, 130 * k]) * e
        else:
            konum = yer
        sp = self.bulut_kar[mutlu]
        _bindir(bg, sp, konum[0], konum[1], 1.0)
        # Uzgunken bulutun altindan yagmur damlalari.
        if not mutlu:
            for j in range(10):
                x = konum[0] + (j - 4.5) * 18 * k
                y = konum[1] + 70 * k + ((t * 260 * k + j * 37 * k) % (240 * k))
                _ekle_rgb(bg, self.y_sprite[2], x, y, 0.6)

    def _ciz_baykus(self, bg, t):
        asama, u = self._durum("baykus_gel", "baykus_git", t, 1.4, 1.6)
        if asama in ("yok", "gitti"):
            return
        op = u if asama == "giris" else (1 - u if asama == "cikis" else 1.0)
        k = self.k
        sp = self.baykus
        x, y = self.W - sp.shape[1] / 2, 182 * k
        _bindir(bg, sp, x, y, op)
        cx = x - sp.shape[1] / 2 + 0.64 * sp.shape[1]
        gy = y - sp.shape[0] / 2 + 0.30 * sp.shape[0]
        kirp = (t % 4.3) < 0.15
        for sx in (-1, 1):
            if not kirp:
                ex = cx + sx * 0.068 * sp.shape[1]
                _ekle_rgb(bg, self.goz_hale, ex, gy, 0.7 * op)
                _ekle_rgb(bg, _parilti_sprite(4.0 * k, (255, 220, 90)), ex, gy, 1.3 * op)

    # -------------------------------------------------- ortam katmanlari
    def _katmanlar(self, bg, ortam, t, w):
        """Bir ortamin hareketli katmanlarini agirlik `w` ile bg'ye ekler."""
        o = ORTAM[ortam]
        W, H, k = self.W, self.H, self.k
        n = o.get("yildiz", 0)
        if n:
            Y = self.yildizlar
            for i in range(n):
                a = Y["a"][i] * (0.55 + 0.45 * math.sin(Y["hiz"][i] * t + Y["faz"][i]))
                sp = self.y_sprite[min(2, int(Y["r"][i] / 0.7) - 1)]
                _ekle_rgb(bg, sp, Y["x"][i], Y["y"][i], a * w)
            for i in range(0, n // 25):
                a = 0.5 + 0.5 * math.sin(0.9 * t + i * 1.7)
                _ekle_rgb(bg, self.y4[i % 2], Y["x"][i * 7], Y["y"][i * 7], a * 0.6 * w)
        if o.get("ay"):
            ax, ay = 104 * k, 178 * k
            _ekle_rgb(bg, self.ay_sp["hale"], ax, ay, w)
            m = self.ay_sp["a"]
            h2 = m.shape[0] // 2
            y0, x0 = int(ay) - h2, int(ax) - h2
            yy0, xx0 = max(0, y0), max(0, x0)
            parca = bg[yy0:y0 + m.shape[0], xx0:x0 + m.shape[1]]
            mm = m[yy0 - y0:yy0 - y0 + parca.shape[0], xx0 - x0:xx0 - x0 + parca.shape[1]][..., None] * w
            parca[...] = parca * (1 - mm) + self.ay_sp["disk"][yy0 - y0:yy0 - y0 + parca.shape[0],
                                                               xx0 - x0:xx0 - x0 + parca.shape[1]] * w
        if o.get("gunes"):
            gx, gy = 600 * k, 150 * k
            r0 = int(260 * k)
            y0, y1 = max(0, int(gy) - r0), min(H, int(gy) + r0)
            x0, x1 = max(0, int(gx) - r0), min(W, int(gx) + r0)
            dx, dy = self.X[y0:y1, x0:x1] - gx, self.Y[y0:y1, x0:x1] - gy
            d = np.sqrt(dx ** 2 + dy ** 2)
            aci = np.arctan2(dy, dx)
            isin = (0.5 + 0.5 * np.cos(10 * (aci - 0.12 * t))) * np.exp(-d / (150 * k)) * 0.35
            disk = np.clip(56 * k - d + 0.5, 0, 1)
            hale = np.exp(-(d / (95 * k)) ** 2) * 0.7
            yama = bg[y0:y1, x0:x1]
            yama += ((isin + hale) * w)[..., None] * np.array([255, 236, 170], np.float32)
            yama[...] = yama * (1 - disk[..., None] * w) + np.array([255, 228, 120], np.float32) * (disk * w)[..., None]
        nb = o.get("bulut", 0)
        if nb:
            renk = np.array(o.get("bulut_renk", (255, 255, 255)), np.float32) / 255.0
            for i in range(nb):
                sp = self.bulutlar[i % 3]
                hiz = (7 + 4 * i) * k
                x = (i * 310 * k + hiz * t) % (W + sp.shape[1]) - sp.shape[1] / 2
                y = (140 + 150 * i) * k
                sp2 = sp.copy()
                sp2[..., :3] *= renk
                _bindir(bg, sp2, x, y, 0.9 * w)
        if o.get("kus"):
            for i in range(3):
                x = (i * 260 * k + 30 * k * t) % (W + 120 * k) - 60 * k
                y = (210 + 55 * i) * k + 8 * k * math.sin(0.8 * t + i)
                kanat = 6 * k * math.sin(9 * t + i * 2)
                for sx in (-1, 1):
                    for j in range(10):
                        u = j / 9
                        px = x + sx * u * 14 * k
                        py = y - kanat * u + 4 * k * u * u
                        bg[int(py) % H, int(px) % W] = bg[int(py) % H, int(px) % W] * (1 - 0.8 * w) + 40 * 0.8 * w
        if o.get("agac") or o.get("atesbocegi"):
            fazla = bool([x for x in self._olay_t("atesbocegi_cok") if x <= t])
            sayi = 34 if fazla else o.get("atesbocegi", 0)
            for i in range(sayi):
                f = self.ates_f[i]
                x = self.ates_x[i] + 40 * k * math.sin(0.31 * t + f[0])
                y = self.ates_y[i] + 30 * k * math.sin(0.23 * t + f[1])
                a = max(0.0, math.sin(1.7 * t + f[2])) ** 2
                _ekle_rgb(bg, self.ates_hale, x, y, 0.35 * a * w)
                _ekle_rgb(bg, self.ates_sp, x, y, a * w)
        if o.get("yagmur"):
            dur = [x for x in self._olay_t("yagmur_dur") if x <= t]
            siddet = 1.0 if not dur else max(0.0, 1 - (t - dur[-1]) / 2.0)
            if siddet > 0:
                kay = int((t * 900 * k) % H)
                doku = self.yagmur_doku[kay:kay + H]
                bg += (doku * 0.5 * siddet * w)[..., None] * np.array([210, 220, 240], np.float32)
        if o.get("gokkusagi"):
            cik = [x for x in self._olay_t("gokkusagi_cik") if x <= t]
            if cik:
                g = self.gokkusagi
                acilma = min(1.0, (t - cik[-1]) / 2.6)
                m = g["a"] * np.clip((acilma * 1.1 - g["ilerleme"]) * 8, 0, 1) * w
                bg[...] = bg * (1 - m[..., None]) + g["rgb"] * m[..., None]
        if o.get("anne_yildiz"):
            nabiz = 0.8 + 0.2 * math.sin(2.2 * t)
            _ekle_rgb(bg, self.piril_hale, 610 * k, 58 * k, 0.8 * nabiz * w)
            _ekle_rgb(bg, self.y4[3], 610 * k, 58 * k, 0.9 * nabiz * w)

    def _kayan_yildiz(self, bg, t):
        for t0 in self._olay_t("kayan_yildiz"):
            u = (t - t0) / 1.4
            if 0 <= u <= 1:
                bas, son = np.array([700, 40]) * self.k, np.array([200, 470]) * self.k
                for j in range(26):
                    v = max(0.0, u - j * 0.012)
                    p = bas * (1 - v) + son * v
                    _ekle_rgb(bg, self.y_sprite[2], p[0], p[1], (1 - j / 26) * 1.6)
                p = bas * (1 - u) + son * u
                _ekle_rgb(bg, self.y4[1], p[0], p[1], 1.0)

    # -------------------------------------------------- on plan efektleri
    def _efektler(self, kare, t):
        k, W, H = self.k, self.W, self.H
        for t0 in self._olay_t("pirilti"):
            u = (t - t0) / 1.5
            if 0 <= u <= 1:
                rng = np.random.default_rng(int(t0 * 1000))
                for i in range(12):
                    gecik = rng.uniform(0, 0.45)
                    v = (u - gecik) / 0.55
                    if 0 <= v <= 1:
                        aci = rng.uniform(0, 2 * math.pi)
                        rr = rng.uniform(170, 300) * k
                        x = 350 * k + rr * math.cos(aci)
                        y = 500 * k + rr * math.sin(aci) * 1.2
                        _ekle_rgb(kare, self.y4[int(rng.integers(0, 3))], x, y, math.sin(math.pi * v) * 1.2)
        for t0 in self._olay_t("kalpler"):
            u = (t - t0) / 2.8
            if 0 <= u <= 1:
                rng = np.random.default_rng(int(t0 * 997))
                for i in range(8):
                    gecik = rng.uniform(0, 0.35)
                    v = (u - gecik) / 0.65
                    if 0 <= v <= 1:
                        x = rng.uniform(90, 630) * k + 26 * k * math.sin(6 * v + i)
                        y = (1180 - 620 * v) * k
                        _bindir(kare, self.kalp[i % 3], x, y, min(1.0, 4 * v) * min(1.0, (1 - v) * 3))
        for t0 in self._olay_t("konfeti"):
            u = t - t0
            if 0 <= u <= 3.4:
                K = self.konfeti
                op = min(1.0, (3.4 - u) * 1.5)
                for i in range(len(K["x"])):
                    y = int(-30 * k + K["v"][i] * u * k - (i % 7) * 40 * k)
                    if y < 0 or y >= H - 12:
                        continue
                    x = int(K["x"][i] + 30 * k * math.sin(3 * u + K["faz"][i])) % (W - 14)
                    w = max(2, int(K["w"][i]))
                    h = max(1, int(K["w"][i] * abs(math.cos(5 * u + K["faz"][i])) * 0.6) + 1)
                    kare[y:y + h, x:x + w] = kare[y:y + h, x:x + w] * (1 - op) + K["renk"][i] * op
        # On plan atesbocekleri (derinlik icin buyuk ve az).
        b = self.c.bolum_at(t)
        if ORTAM[b.ortam].get("atesbocegi"):
            for i in range(6):
                f = self.ates_f[i + 34] if i + 34 < len(self.ates_f) else self.ates_f[i]
                x = (self.ates_x[i] * 1.3 + 25 * k * t * (0.5 + i * 0.1)) % W
                y = self.ates_y[i] + 60 * k * math.sin(0.4 * t + f[1])
                a = max(0.0, math.sin(1.3 * t + f[2])) ** 2
                _ekle_rgb(kare, self.ates_hale, x, y, 0.5 * a)
                _ekle_rgb(kare, _parilti_sprite(5 * k, (230, 255, 150)), x, y, 0.8 * a)

    # -------------------------------------------------- yazi onbellegi
    def _yazi(self, anahtar, uret):
        if anahtar not in self._yazi_onbellek:
            if len(self._yazi_onbellek) > 40:
                self._yazi_onbellek.pop(next(iter(self._yazi_onbellek)))
            self._yazi_onbellek[anahtar] = uret()
        return self._yazi_onbellek[anahtar]

    def _arayuz(self, kare, t):
        c, W, H, k = self.c, self.W, self.H, self.k
        # Giris karti.
        op = _gecis(t, 0.3, c.giris - 0.4, 0.8, 0.8)
        if op > 0:
            kay = 18 * k * (1 - op)
            _bindir(kare, self._yazi("baslik", lambda: _metin_sprite([c.baslik], self.f_baslik, kalinlik=5)),
                    W / 2, H * 0.76 + kay, op)
            _bindir(kare, self._yazi("alt_baslik", lambda: _metin_sprite(
                [c.alt_baslik], self.f_alt_baslik, renk=(255, 214, 64), kalinlik=4)),
                W / 2, H * 0.835 + kay, op)
        # Kapanis karti.
        op = _gecis(t, c.kapanis_bas + 0.5, c.toplam + 1, 1.0, 0.1)
        if op > 0:
            _bindir(kare, self._yazi("kapanis1", lambda: _metin_sprite(["İyi geceler!"], self.f_baslik, kalinlik=5)),
                    W / 2, H * 0.74, op)
            _bindir(kare, self._yazi("kapanis2", lambda: _metin_sprite(
                ["Bir sonraki macerada", "görüşmek üzere"], self.f_alt, renk=(255, 214, 64))), W / 2, H * 0.83, op)
            _bindir(kare, self._yazi("kapanis3", lambda: _metin_sprite([c.baslik], self.f_kucuk)),
                    W / 2, H * 0.90, op)
        # Bolum karti.
        b = c.bolum_at(t)
        op = _gecis(t, b.bas + 0.2, b.bas + 4.6, 0.5, 0.7)
        if op > 0 and t < c.kapanis_bas:
            _bindir(kare, self._yazi(("bno", b.no), lambda: _metin_sprite(
                [f"BÖLÜM {b.no}"], self.f_kucuk, renk=(255, 214, 64), kalinlik=2)),
                W / 2, 72 * k + 10 * k * (1 - op), op)
            _bindir(kare, self._yazi(("bad", b.no), lambda: _metin_sprite(
                [b.ad], self.f_bolum, kalinlik=4)), W / 2, 122 * k + 10 * k * (1 - op), op)
        # Ekran yazisi (sayilar, renkler) ve altyazi.
        for s in c.satirlar:
            if s.bas - 0.2 > t:
                break
            if s.ekran and s.bas - 0.05 <= t <= s.bit + 0.7:
                u = (t - s.bas + 0.05) / 0.28
                olcek = 0.6 + 0.48 * _ease(u) - 0.08 * _ease((u - 1) * 1.5) if u < 2.5 else 1.0
                renk = tuple(s.ekran.get("renk", (255, 214, 64)))
                sp = self._yazi(("ekran", s.id), lambda: _metin_sprite(
                    [s.ekran["yazi"]], self.f_dev, renk=renk, kalinlik=6))
                if abs(olcek - 1) > 0.02:
                    sp = self._olcekle(sp, olcek)
                _bindir(kare, sp, W / 2, 262 * k, min(1.0, (s.bit + 0.7 - t) * 3))
            if s.bas - 0.1 <= t <= s.bit + 0.45:
                alt = self._yazi(("alt", s.id), lambda: Altyazi(s, self.f_alt, int(W * 0.86), k))
                alt.ciz(kare, t, W / 2, H * 0.885, _gecis(t, s.bas - 0.1, s.bit + 0.45, 0.15, 0.25))

    # -------------------------------------------------- kare
    def kare(self, n: int):
        c, W, H, k, P = self.c, self.W, self.H, self.k, self.P
        t = n / self.fps

        # 1) Yuz animasyonu (kaynak on plan uzerinde).
        kaynak = self.on.copy()
        self.kaslar.uygula(kaynak, float(P["kas"][n]))
        kirp = _kirpma(t, self.kirpmalar)
        kapanma = max(kirp, float(P["kis"][n]), float(P["uyku"][n]))
        kaynak = self.goz.uygula(kaynak, kapanma)
        if self.agiz is not None:
            self.agiz.uygula(kaynak, float(P["agiz"][n]))

        # 2) Kamera: zoom + egim + bas sallanmasi + nefes; ters esleme ile ornekleme.
        z = float(P["zoom"][n])
        aci = math.radians(float(P["egim"][n]))
        px, py = self.odak
        dx = 3.0 * k * math.sin(2 * math.pi * t / 13.0)
        dy = float(P["bas_dy"][n]) * k
        u = (self.X - px - dx) / z
        v = (self.Y - py - dy) / z
        ca, sa = math.cos(aci), math.sin(aci)
        sx = px + u * ca + v * sa
        sy = py - u * sa + v * ca
        nefes = 0.5 - 0.5 * math.cos(2 * math.pi * t / 4.2)
        sy += 0.003 * H * nefes * (1.0 - _ss((sy - self.gogus_y) / (H - self.gogus_y)))
        x0 = np.floor(sx)
        y0 = np.floor(sy)
        fx = (sx - x0)[..., None]
        fy = (sy - y0)[..., None]
        x0 = np.clip(x0.astype(np.int32), 0, W - 2)
        y0 = np.clip(y0.astype(np.int32), 0, H - 2)
        i = y0 * W + x0
        duz = kaynak.reshape(-1, 3)
        a, b, cc, d = duz[i], duz[i + 1], duz[i + W], duz[i + W + 1]
        on = (a + (b - a) * fx) * (1 - fy) + (cc + (d - cc) * fx) * fy
        al = self.alfa.reshape(-1)
        a1, b1, c1, d1 = al[i], al[i + 1], al[i + W], al[i + W + 1]
        alfa = (a1 + (b1 - a1) * fx[..., 0]) * (1 - fy[..., 0]) + (c1 + (d1 - c1) * fx[..., 0]) * fy[..., 0]

        # 3) Arka plan (ortam gecisli) + karakterler.
        o1, o2, m = c.ortam_at(t)
        bg = self._taban(o2).copy() if m >= 1 else (self._taban(o1) * (1 - m) + self._taban(o2) * m)
        if m < 1:
            self._katmanlar(bg, o1, t, 1 - m)
        self._katmanlar(bg, o2, t, m)
        self._kayan_yildiz(bg, t)
        self._ciz_baykus(bg, t)
        self._ciz_bulut(bg, t)

        renk = (np.array(ORTAM[o1]["renk"], np.float32) * (1 - m)
                + np.array(ORTAM[o2]["renk"], np.float32) * m)
        kare = on * renk + alfa[..., None] * bg

        # 4) On plan: Piril, efektler, vinyet, arayuz.
        self._ciz_piril(kare, t)
        self._efektler(kare, t)
        if ORTAM[o2].get("yagmur") and m > 0.5:
            dur = [x for x in self._olay_t("yagmur_dur") if x <= t]
            siddet = 1.0 if not dur else max(0.0, 1 - (t - dur[-1]) / 2.0)
            if siddet > 0:
                kay = int((t * 1300 * k + H // 2) % H)
                kare += (self.yagmur_doku[kay:kay + H] * 0.22 * siddet)[..., None] * np.array(
                    [220, 228, 245], np.float32)
        kare *= self.carpan
        self._arayuz(kare, t)

        acilis = min(1.0, t / 0.8) * min(1.0, (c.toplam - t) / 1.5)
        if acilis < 1.0:
            kare *= max(0.0, acilis)
        return np.clip(kare, 0, 255).astype(np.uint8)


def _kirpma(t: float, kirpmalar) -> float:
    """Goz kirpma kapanma miktari (0..1); kirpmalar sirali zaman listesi."""
    import bisect
    i = bisect.bisect_right(kirpmalar, t) - 1
    if i < 0:
        return 0.0
    d = t - kirpmalar[i]
    if d >= 0.3:
        return 0.0
    if d < 0.08:
        return (d / 0.08) ** 1.5
    if d < 0.13:
        return 1.0
    return 1.0 - _ease((d - 0.13) / 0.17)


# ------------------------------------------------------------------ kare parametreleri

def kare_parametreleri(c, agiz, konusma, fps: int, tohum: int = 5) -> dict:
    """Tum video icin kare basina animasyon parametreleri (ana surecte, bir kez)."""
    n = len(agiz)
    t = np.arange(n) / fps
    hedef = np.zeros((n, 7), np.float32)
    hedef[:, 6] = 1.0
    for s in c.satirlar:
        i0, i1 = int(s.bas * fps), int((s.bit + 0.5) * fps)
        hedef[i0:i1] = IFADE_HEDEF[s.ifade]
    # Ileri-geri ustel yumusatma (sifir fazli).
    alfa = 1 - math.exp(-1 / (0.28 * fps))
    yum = hedef.copy()
    for k in range(1, n):
        yum[k] = yum[k - 1] + (hedef[k] - yum[k - 1]) * alfa
    for k in range(n - 2, -1, -1):
        yum[k] = yum[k + 1] + (yum[k] - yum[k + 1]) * (1 - alfa)
    kas, kis, uyku, zoom_ek, egim, bas_dy, sallanma = yum.T

    # Bolume gore kamera cercevesi (yakin / orta / genis), yumusak gecis.
    cerceve = np.ones(n, np.float32) * 1.05
    secenek = [1.04, 1.10, 1.06, 1.12, 1.03, 1.08]
    for b in c.bolumler:
        cerceve[int(b.bas * fps):] = secenek[(b.no - 1) % len(secenek)]
    pencere = int(2.5 * fps)
    cerceve = np.convolve(np.pad(cerceve, pencere, mode="edge"), np.ones(2 * pencere + 1) / (2 * pencere + 1),
                          mode="valid")
    yavas = np.convolve(agiz, np.ones(9) / 9, mode="same")
    konus = np.clip(konusma, 0, 1)
    egim_top = (egim + 0.6 * np.sin(2 * math.pi * t / 7.3)
                + 1.1 * konus * sallanma * np.sin(2 * math.pi * t / 2.9))
    bas_top = bas_dy - 2.4 * (agiz - yavas) * sallanma - 1.2 * konus * np.sin(2 * math.pi * t / 1.7)
    zoom = cerceve + zoom_ek + 0.004 * np.sin(2 * math.pi * t / 9.0)

    rng = np.random.default_rng(tohum)
    kirpmalar, x = [], 1.8
    while x < c.toplam:
        kirpmalar.append(round(x, 3))
        x += float(rng.uniform(2.4, 5.2))
    return dict(agiz=agiz.astype(np.float32), kas=kas, kis=kis, uyku=uyku,
                zoom=zoom.astype(np.float32), egim=egim_top.astype(np.float32),
                bas_dy=bas_top.astype(np.float32), kirpmalar=kirpmalar)


# ------------------------------------------------------------------ paralel render

def _isci(argumanlar):
    (no, bas, bit, c, profil, ayrim_yolu, P, en, boy, fps, parca_yolu, kod_ayar) = argumanlar
    veri = np.load(ayrim_yolu)
    ayrim = {k: veri[k] for k in veri.files}
    sahne = Sahne(c, profil, ayrim, P, en, boy, fps)
    komut = [_ffmpeg(), "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{en}x{boy}", "-r", str(fps), "-i", "-",
             "-c:v", "libx264", "-preset", kod_ayar["preset"], "-crf", str(kod_ayar["crf"]),
             "-pix_fmt", "yuv420p", "-threads", "2", str(parca_yolu)]
    islem = subprocess.Popen(komut, stdin=subprocess.PIPE)
    try:
        for n in range(bas, bit):
            islem.stdin.write(sahne.kare(n).tobytes())
            if (n - bas) % (fps * 30) == 0:
                print(f"     [isci {no}] {n - bas}/{bit - bas} kare", flush=True)
    finally:
        islem.stdin.close()
        kod = islem.wait()
    if kod != 0:
        raise RuntimeError(f"isci {no}: ffmpeg hatasi ({kod})")
    return str(parca_yolu)


def render(c, profil, ayrim_yolu, P, ses_wav, hedef, ayar: dict, aralik=None, kapak=None) -> Path:
    """Kareleri paralel uretir, parcalari birlestirip sesle muxlar."""
    import multiprocessing

    a = ayar.get("cocuk", {})
    en, boy = a.get("cozunurluk", [720, 1280])
    fps = int(a.get("fps", 24))
    kod = {"preset": a.get("preset", "medium"), "crf": int(a.get("crf", 22))}
    toplam = len(P["agiz"])
    bas, bit = (0, toplam) if aralik is None else (int(aralik[0] * fps), min(toplam, int(aralik[1] * fps)))
    isci_sayisi = max(1, min(int(a.get("isci", os.cpu_count() or 2)), bit - bas))
    hedef = Path(hedef)
    klasor = hedef.parent / "parcalar"
    klasor.mkdir(parents=True, exist_ok=True)
    sinirlar = np.linspace(bas, bit, isci_sayisi + 1).astype(int)
    isler = [(i, int(sinirlar[i]), int(sinirlar[i + 1]), c, profil, str(ayrim_yolu), P, en, boy, fps,
              klasor / f"parca_{i:02d}.mp4", kod) for i in range(isci_sayisi)]
    print(f"     {bit - bas} kare, {isci_sayisi} paralel isci", flush=True)
    with multiprocessing.get_context("fork").Pool(isci_sayisi) as havuz:
        parcalar = havuz.map(_isci, isler)

    liste = klasor / "liste.txt"
    liste.write_text("".join(f"file '{Path(p).resolve()}'\n" for p in parcalar), encoding="utf-8")
    ses_ofset = ["-ss", f"{bas / fps:.3f}", "-t", f"{(bit - bas) / fps:.3f}"]
    subprocess.run([_ffmpeg(), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(liste),
                    *ses_ofset, "-i", str(ses_wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(hedef)],
                   check=True)
    if kapak is not None:
        veri = np.load(ayrim_yolu)
        sahne = Sahne(c, profil, {k: veri[k] for k in veri.files}, P, en, boy, fps)
        from PIL import Image
        kn = min(toplam - 1, int(float(a.get("kapak_sn", 4.0)) * fps))
        Image.fromarray(sahne.kare(kn)).save(kapak, quality=92)
    return hedef

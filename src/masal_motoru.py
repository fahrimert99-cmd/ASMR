"""
Masal videosu motoru — resimli kitap (storybook) üslubunda, tamamen kodla
çizilen ve canlandırılan masal videoları.

Görsel dil
  * Kağıt     : sıcak krem kağıt; lif, gren ve lekelenme dokusu (prosedürel).
  * Boya      : sulu boya/guaş taklidi — hafif titrek kenar, nesneye yapışık
                pigment dokusu, kenarda koyulaşan pigment, yumuşak iç gölge.
  * Mürekkep  : el çizimi titrek sepya çizgiler (skia DiscretePathEffect).
  * Karakter  : eklemli kukla; her karede vektörle yeniden çizilir.
  * Sayfa     : altta kağıt kart üzerinde metin (süslü ilk harf), cümle cümle
                belirir; sayfalar arasında silindir kıvrımlı sayfa çevirme.

Bir masal, masallar/<kimlik>.py dosyasında SAYFALAR listesiyle tanımlanır;
her sayfanın bir sahnesi (arka: bir kez çizilen resim, on: her karede çizilen
hareketli katman), metni, kamerası ve müzik ruh hali vardır.
"""
import math
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia
from scipy import ndimage

KOK = Path(__file__).resolve().parent.parent
FONT_DIR = KOK / "veri" / "fontlar"

W, H = 1920, 1080
R = 1.25                                    # arka plan resminin cozunurluk carpani
KAGIT = (0.957, 0.925, 0.852)
MUREKKEP = (0.20, 0.14, 0.10)
CEVIRME = 1.25                              # sayfa cevirme suresi (sn)


# ================================================================ yardimcilar
def _ss(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def yumusak(x):
    """0..1 -> 0..1, yumusak giris/cikis (dizi de kabul eder)."""
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def renk4(r, a=1.0):
    return skia.Color4f(float(r[0]), float(r[1]), float(r[2]), float(a))


def koyu(r, k=0.75):
    return tuple(float(v) * k for v in r)


def acik(r, k=0.3):
    return tuple(float(v) + (1 - float(v)) * k for v in r)


def karistir(a, b, u):
    return tuple(float(x) + (float(y) - float(x)) * u for x, y in zip(a, b))


# ================================================================ yollar
def egri(noktalar, kapali=True, gerginlik=0.5):
    """Noktalardan gecen yumusak (Catmull-Rom) skia yolu."""
    p = [tuple(map(float, q)) for q in noktalar]
    yol = skia.Path()
    n = len(p)
    if n < 2:
        return yol
    yol.moveTo(*p[0])
    son = n if kapali else n - 1
    for i in range(son):
        p0 = p[(i - 1) % n] if (kapali or i > 0) else p[i]
        p1, p2 = p[i], p[(i + 1) % n]
        p3 = p[(i + 2) % n] if (kapali or i + 2 < n) else p2
        k = gerginlik / 3.0
        c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        yol.cubicTo(*c1, *c2, *p2)
    if kapali:
        yol.close()
    return yol


def cokgen(noktalar, kapali=True):
    yol = skia.Path()
    yol.moveTo(*map(float, noktalar[0]))
    for q in noktalar[1:]:
        yol.lineTo(*map(float, q))
    if kapali:
        yol.close()
    return yol


def leke(cx, cy, rx, ry, tohum=0, puruz=0.08, n=14, aci=0.0):
    """Hafif duzensiz, organik elips (bulut, cali, tas...)."""
    rng = np.random.default_rng(tohum)
    faz = rng.uniform(0, 2 * np.pi, 3)
    ca, sa = math.cos(aci), math.sin(aci)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + puruz * (math.sin(2 * a + faz[0]) + 0.6 * math.sin(3 * a + faz[1]) + 0.4 * math.sin(5 * a + faz[2]))
        x, y = math.cos(a) * rx * r, math.sin(a) * ry * r
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return egri(pts)


def elips(cx, cy, rx, ry):
    yol = skia.Path()
    yol.addOval(skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry))
    return yol


def daire(cx, cy, r):
    return elips(cx, cy, r, r)


def kapsul(x0, y0, x1, y1, r0, r1=None):
    """Iki uc arasinda konik, yuvarlak uclu kol/bacak yolu."""
    r1 = r0 if r1 is None else r1
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    a = math.atan2(dy, dx)
    yol = skia.Path()
    yol.moveTo(x0 + nx * r0, y0 + ny * r0)
    yol.lineTo(x1 + nx * r1, y1 + ny * r1)
    yol.arcTo(skia.Rect(x1 - r1, y1 - r1, x1 + r1, y1 + r1), math.degrees(a) + 90, -180, False)
    yol.lineTo(x0 - nx * r0, y0 - ny * r0)
    yol.arcTo(skia.Rect(x0 - r0, y0 - r0, x0 + r0, y0 + r0), math.degrees(a) - 90, -180, False)
    yol.close()
    return yol


def dikdortgen(x0, y0, x1, y1, r=0.0):
    yol = skia.Path()
    if r:
        yol.addRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), r, r))
    else:
        yol.addRect(skia.Rect(x0, y0, x1, y1))
    return yol


# ================================================================ dokular
def _gurultu_karo(n, sigmalar, agirliklar, tohum):
    rng = np.random.default_rng(tohum)
    top = np.zeros((n, n), np.float32)
    for s, w in zip(sigmalar, agirliklar):
        g = ndimage.gaussian_filter(rng.standard_normal((n, n)).astype(np.float32), s, mode="wrap")
        top += w * g / (g.std() + 1e-6)
    top -= top.min()
    return top / (top.max() + 1e-6)


@lru_cache(maxsize=1)
def _doku_resimleri():
    """Nesneye yapisan pigment dokusu (carpma icin, 1 = degisim yok)."""
    d = _gurultu_karo(512, (1.2, 5.0, 22.0, 60.0), (0.25, 0.45, 0.7, 0.6), 11)
    pig = (0.66 + 0.34 * d ** 0.8)
    g = _gurultu_karo(512, (0.7,), (1.0,), 12)
    gran = (0.86 + 0.14 * g)

    def img(a):
        u8 = (np.clip(a, 0, 1) * 255).astype(np.uint8)
        rgba = np.dstack([u8, u8, u8, np.full_like(u8, 255)])
        return skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)
    return img(pig), img(gran)


@lru_cache(maxsize=1)
def kagit_dokusu():
    """Ekran uzayinda kagit carpani (H, W, 1) ~ 1.0 civari + vinyet + kitap sirti golgesi."""
    rng = np.random.default_rng(5)
    kucuk = rng.standard_normal((H // 6, W // 6)).astype(np.float32)
    kucuk = ndimage.gaussian_filter(kucuk, 3.0)
    lek = np.asarray(skia.Image.fromarray(np.dstack([((kucuk - kucuk.min()) / (np.ptp(kucuk) + 1e-6) * 255).astype(np.uint8)] * 3
                                                    + [np.full(kucuk.shape, 255, np.uint8)]),
                                          colorType=skia.kRGBA_8888_ColorType)
                     .resize(W, H, skia.SamplingOptions(skia.FilterMode.kLinear))
                     .toarray(colorType=skia.kRGBA_8888_ColorType)[..., 0], np.float32) / 255.0
    gren = ndimage.gaussian_filter(rng.standard_normal((H, W)).astype(np.float32), 0.6)
    gren /= gren.std() + 1e-6
    lif = np.zeros((H, W), np.float32)
    for _ in range(900):                                    # kagit lifleri
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        a, L = rng.uniform(0, np.pi), rng.uniform(8, 40)
        for s in np.linspace(0, 1, int(L)):
            xi = int(x + math.cos(a) * L * s + 3 * math.sin(s * 6 + a))
            yi = int(y + math.sin(a) * L * s)
            if 0 <= xi < W and 0 <= yi < H:
                lif[yi, xi] += 1
    lif = ndimage.gaussian_filter(lif, 0.5)
    carpan = 1.0 + 0.035 * (lek - 0.5) * 2 + 0.018 * gren - 0.05 * np.clip(lif, 0, 1)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rv = np.hypot((xx / W - 0.5) * 1.1, (yy / H - 0.5) * 1.25)
    vinyet = 1.0 - 0.32 * np.clip((rv - 0.38) / 0.45, 0, 1) ** 1.7
    sirt = 1.0 - 0.22 * np.exp(-xx / 26.0) - 0.08 * np.exp(-xx / 140.0)     # kitap sirti
    return (carpan * vinyet * sirt).astype(np.float32)[..., None]


# ================================================================ firca
class Firca:
    """Sulu boya / guas taklidi cizim yardimcisi (skia)."""

    def __init__(self):
        pig, gran = _doku_resimleri()
        so = skia.SamplingOptions(skia.FilterMode.kLinear)
        self._pig = pig.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, so)
        self._gran = gran.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, so)

    @staticmethod
    def _titret(yol, titrek, tohum):
        if titrek <= 0:
            return yol
        p = skia.Paint(PathEffect=skia.DiscretePathEffect.Make(titrek * 5, titrek, tohum))
        out = skia.Path()
        p.getFillPath(yol, out)
        return out

    def boya(self, c, yol, renk, alfa=1.0, doku=0.6, kenar=0.6, kenar_gen=9.0, titrek=0.8,
             murekkep=0.0, cizgi=2.4, golge=0.0, golge_yon=(8, 6), parlak=0.0, tohum=1,
             doku_olcek=1.0, leke_sayi=None):
        """Tek bir boya lekesi: dolgu + pigment dokusu + ic lekeler + kenar koyulugu + golge + murekkep."""
        p = self._titret(yol, titrek, tohum)
        c.drawPath(p, skia.Paint(AntiAlias=True, Color4f=renk4(renk, alfa)))
        b = p.computeTightBounds()
        boyut = max(b.width(), b.height())
        if leke_sayi is None:
            leke_sayi = 0 if boyut < 60 else (2 if boyut < 300 else 4)
        if leke_sayi:                                      # islak-islak lekeler (bloom)
            rng = np.random.default_rng(tohum * 7919 + 13)
            c.save()
            c.clipPath(p, doAntiAlias=True)
            for _ in range(leke_sayi):
                cx = b.left() + rng.uniform(0.1, 0.9) * b.width()
                cy = b.top() + rng.uniform(0.1, 0.9) * b.height()
                r = boyut * rng.uniform(0.12, 0.3)
                ton = acik(renk, 0.28) if rng.uniform() < 0.55 else koyu(renk, 0.84)
                c.drawPath(leke(cx, cy, r, r * rng.uniform(0.6, 1.0), int(rng.integers(1e6)), 0.2),
                           skia.Paint(AntiAlias=True, Color4f=renk4(ton, 0.32 * alfa),
                                      MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.45)))
            c.restore()
        if doku:
            c.save()
            if doku_olcek != 1.0:
                c.scale(doku_olcek, doku_olcek)
                ters = skia.Matrix.Scale(1 / doku_olcek, 1 / doku_olcek)
                p2 = skia.Path(p)
                p2.transform(ters)
            else:
                p2 = p
            c.drawPath(p2, skia.Paint(AntiAlias=True, Shader=self._pig, BlendMode=skia.BlendMode.kMultiply,
                                      Alphaf=min(1.0, doku * alfa)))
            c.restore()
        if kenar or golge or parlak:
            c.save()
            c.clipPath(p, doAntiAlias=True)
            if golge:
                q = skia.Path(p)
                q.offset(*golge_yon)
                q.setFillType(skia.PathFillType.kInverseWinding)
                c.drawPath(q, skia.Paint(AntiAlias=True, Color4f=renk4(koyu(renk, 0.45), golge * alfa),
                                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle,
                                                                             max(2.0, math.hypot(*golge_yon) * 0.9))))
            if parlak:
                q = skia.Path(p)
                q.offset(-golge_yon[0], -golge_yon[1])
                q.setFillType(skia.PathFillType.kInverseWinding)
                c.drawPath(q, skia.Paint(AntiAlias=True, Color4f=renk4(acik(renk, 0.6), parlak * alfa),
                                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle,
                                                                             max(2.0, math.hypot(*golge_yon) * 0.9))))
            if kenar:
                c.drawPath(p, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=kenar_gen,
                                         Color4f=renk4(koyu(renk, 0.55), min(1.0, kenar * 0.9) * alfa),
                                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, kenar_gen * 0.22)))
            c.restore()
        if murekkep:
            self.cizgi(c, yol, cizgi, murekkep * alfa, tohum=tohum + 3, titrek=cizgi * 0.38)
        return p

    def cizgi(self, c, yol, gen=2.4, alfa=0.85, renk=MUREKKEP, tohum=3, titrek=None):
        """El cizimi murekkep cizgisi; titreme ve parca boyu cizgi kalinligiyla olceklenir."""
        titrek = gen * 0.38 if titrek is None else titrek
        c.drawPath(yol, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=gen,
                                   StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join,
                                   Color4f=renk4(renk, alfa),
                                   PathEffect=skia.DiscretePathEffect.Make(gen * 3.0, titrek, tohum) if titrek else None))

    def yumusak(self, c, yol, renk, alfa=0.5, bulanik=12.0, mod=None):
        """Bulanik leke: isik, golge, yanak pembesi, sis, parlti."""
        p = skia.Paint(AntiAlias=True, Color4f=renk4(renk, alfa),
                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, bulanik))
        if mod:
            p.setBlendMode(mod)
        c.drawPath(yol, p)

    def degrade(self, c, yol, ust, alt, y0, y1, alfa=1.0, doku=0.4, doku_olcek=3.0):
        """Dikey renk gecisli yikama (gok, su, toprak)."""
        sh = skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)],
                                            [renk4(ust, alfa).toColor(), renk4(alt, alfa).toColor()])
        c.drawPath(yol, skia.Paint(AntiAlias=True, Shader=sh))
        if doku:
            c.save()
            c.scale(doku_olcek, doku_olcek)
            p2 = skia.Path(yol)
            p2.transform(skia.Matrix.Scale(1 / doku_olcek, 1 / doku_olcek))
            c.drawPath(p2, skia.Paint(AntiAlias=True, Shader=self._pig, BlendMode=skia.BlendMode.kMultiply, Alphaf=doku))
            c.restore()

    def gren(self, c, yol, alfa=0.35):
        """Ince pigment granulasyonu."""
        c.drawPath(yol, skia.Paint(AntiAlias=True, Shader=self._gran, BlendMode=skia.BlendMode.kMultiply, Alphaf=alfa))


# ================================================================ yazi
@lru_cache(maxsize=16)
def yazi_tipi(ad):
    return skia.Typeface.MakeFromFile(str(FONT_DIR / ad))


def font(ad, boy):
    f = skia.Font(yazi_tipi(ad), boy)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def cumlelere_bol(metin):
    """Metni cumlelere boler (tirnak icindeki konusmalar ayri cumle sayilir)."""
    parca = re.findall(r'[^.!?…”]+(?:[.!?…]+[”"]?|”|$)', metin)
    cumleler = [p.strip() for p in parca if p.strip()]
    birlesik = []
    for c in cumleler:                                      # tek basina kalan kapanis tirnagi/kisa parca
        if birlesik and (len(c) < 3 or c[0] in "”\"" or c[0].islower()):
            birlesik[-1] += " " + c
        else:
            birlesik.append(c)
    return birlesik


class MetinKarti:
    """Sayfanin altindaki kagit kart: metin yerlesimi + cumle cumle belirme."""
    BOY = 39
    SATIR = 1.36

    def __init__(self, metin, sure, konusanlar=None, gen=1580, suslu=True):
        self.metin = metin
        self.suslu = suslu
        self.cumleler = cumlelere_bol(metin)
        self.konusanlar = list(konusanlar or [])
        self.f = font("EBGaramond.ttf", self.BOY)
        self.fi = font("EBGaramond-Italic.ttf", self.BOY)
        self.fd = font("Cinzel.ttf", self.BOY * 2.25)
        self.gen = gen
        self._yerlestir()
        # zamanlama: okuma hizi ~2.7 kelime/sn
        t = 0.7
        self.zaman = []
        for cm in self.cumleler:
            self.zaman.append(t)
            t += 0.55 + len(cm.split()) / 2.7
        self.okuma_bitis = t
        self.sure = sure

    def _yerlestir(self):
        pad = 46
        bas = self.metin.strip()[0]
        self.ilk = bas
        dg = self.fd.measureText(bas) + 14
        satir_h = self.BOY * self.SATIR
        icerik_gen = self.gen - 2 * pad
        kelimeler = []                                     # (kelime, cumle_no, italik)
        tirnak = False
        for i, cm in enumerate(self.cumleler):
            for k in cm.split():
                if "“" in k:
                    tirnak = True
                kelimeler.append((k, i, tirnak))
                if "”" in k:
                    tirnak = False
        if not self.suslu:
            dg = 0
        elif kelimeler:                                    # ilk harf suslu harfle cizilir
            k, i, it = kelimeler[0]
            kelimeler[0] = (k[1:], i, it)
        bosluk = self.f.measureText(" ")
        satirlar, satir, x = [], [], 0.0
        for k, i, it in kelimeler:
            ff = self.fi if it else self.f
            w = ff.measureText(k)
            sinir = icerik_gen - (dg if len(satirlar) < 2 else 0)
            if satir and x + w > sinir:
                satirlar.append(satir)
                satir, x = [], 0.0
            satir.append((k, i, it, x, w))
            x += w + bosluk
        if satir:
            satirlar.append(satir)
        self.satirlar = satirlar
        self.dg = dg
        n = max(len(satirlar), 2)
        self.yuk = int(pad * 0.75 * 2 + satir_h * n)
        self.x0 = (W - self.gen) // 2
        self.y0 = H - 34 - self.yuk
        self.pad = pad
        self.satir_h = satir_h
        self._kart = self._kart_resmi()

    def _kart_resmi(self):
        """Tirtikli kenarli, hafif golgeli kagit kart (bir kez)."""
        gw, gh = self.gen + 60, self.yuk + 60
        s = skia.Surface(gw, gh)
        c = s.getCanvas()
        c.clear(skia.ColorTRANSPARENT)
        rng = np.random.default_rng(len(self.metin))
        pts = []
        x0, y0, x1, y1 = 30, 30, 30 + self.gen, 30 + self.yuk
        for x in np.linspace(x0, x1, 80):
            pts.append((x, y0 + rng.uniform(-1.6, 1.6)))
        for y in np.linspace(y0, y1, 16)[1:]:
            pts.append((x1 + rng.uniform(-1.6, 1.6), y))
        for x in np.linspace(x1, x0, 80)[1:]:
            pts.append((x, y1 + rng.uniform(-1.6, 1.6)))
        for y in np.linspace(y1, y0, 16)[1:-1]:
            pts.append((x0 + rng.uniform(-1.6, 1.6), y))
        yol = cokgen(pts)
        g = skia.Path(yol)
        g.offset(4, 7)
        c.drawPath(g, skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.18, 0.12, 0.08, 0.28),
                                 MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9)))
        f = Firca()
        f.boya(c, yol, (0.975, 0.955, 0.905), doku=0.18, kenar=0.25, kenar_gen=14, titrek=0, tohum=4)
        # ince suslu cerceve
        ic = dikdortgen(x0 + 12, y0 + 12, x1 - 12, y1 - 12, 6)
        f.cizgi(c, ic, 1.3, 0.35, renk=(0.55, 0.30, 0.18), titrek=0.4)
        return s.makeImageSnapshot()

    def alfa(self, t, i):
        return _ss((t - self.zaman[i]) / 0.65)

    def konusan(self, t):
        """t aninda konusan karakter (cumlesi yeni beliriyorsa)."""
        for i in range(len(self.cumleler) - 1, -1, -1):
            if t >= self.zaman[i]:
                if i < len(self.konusanlar) and self.konusanlar[i]:
                    sure = 0.4 + len(self.cumleler[i].split()) / 3.2
                    if t < self.zaman[i] + sure:
                        return self.konusanlar[i]
                return None
        return None

    def ciz(self, c, t, alfa=1.0):
        c.drawImage(self._kart, self.x0 - 30, self.y0 - 30, skia.SamplingOptions(), skia.Paint(Alphaf=alfa))
        mur = (0.17, 0.11, 0.07)
        bx = self.x0 + self.pad
        by = self.y0 + self.pad * 0.75 + self.BOY * 0.98
        # suslu ilk harf
        a0 = self.alfa(t, 0) * alfa
        if self.suslu:
            c.drawString(self.ilk, bx - 2, by + self.satir_h * 0.93, self.fd,
                         skia.Paint(AntiAlias=True, Color4f=skia.Color4f(0.58, 0.16, 0.10, a0)))
        for j, satir in enumerate(self.satirlar):
            ox = bx + (self.dg if j < 2 else 0)
            yy = by + j * self.satir_h
            for k, i, it, x, w in satir:
                a = self.alfa(t, i) * alfa
                if a <= 0.004:
                    continue
                dy = (1 - a) * 6
                c.drawString(k, ox + x, yy + dy, self.fi if it else self.f,
                             skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*mur, a)))


# ================================================================ kamera
class Kamera:
    """Sayfa ici yavas yaklasma/kaydirma (Ken Burns). Anahtarlar: (t, zoom, cx, cy)."""

    def __init__(self, anahtarlar=None):
        self.k = sorted(anahtarlar or [(0.0, 1.0, W / 2, H / 2), (1.0, 1.05, W / 2, H / 2)])

    def __call__(self, u):
        """u: sayfanin 0..1 ilerlemesi."""
        k = self.k
        if u <= k[0][0]:
            return k[0][1:]
        for a, b in zip(k, k[1:]):
            if u <= b[0]:
                s = yumusak((u - a[0]) / max(b[0] - a[0], 1e-6))
                return tuple(a[i] + (b[i] - a[i]) * s for i in (1, 2, 3))
        return k[-1][1:]

    @staticmethod
    def matris(z, cx, cy, sars=(0.0, 0.0)):
        m = skia.Matrix()
        m.setTranslate(W / 2 + sars[0], H / 2 + sars[1])
        m.preScale(z, z)
        m.preTranslate(-cx, -cy)
        return m


# ================================================================ sayfa cevirme
@lru_cache(maxsize=2)
def _cevirme_izgarasi(aci):
    th = math.radians(aci)
    ca, sa = math.cos(th), math.sin(th)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H / 2
    xr = (xx - cx) * ca + (yy - cy) * sa                      # kivrima dik eksen
    yr = -(xx - cx) * sa + (yy - cy) * ca
    kose = np.array([[0, 0], [W, 0], [0, H], [W, H]], np.float32)
    kr = (kose[:, 0] - cx) * ca + (kose[:, 1] - cy) * sa
    return xr, yr, float(kr.max()), float(kr.min())


def sayfa_cevir(A, B, u, aci=13.0):
    """A sayfasi (kalkan) ile B sayfasi (alttaki) arasinda silindir kivrimli cevirme.

    A, B: (H, W, 3) uint8. u: 0..1 ilerleme. Donus: (H, W, 3) uint8.
    """
    Rr = 115.0
    th = math.radians(aci)
    ca, sa = math.cos(th), math.sin(th)
    cx, cy = W / 2, H / 2
    xr, yr, sag, sol = _cevirme_izgarasi(aci)
    e = yumusak(u) if u < 1 else 1.0
    xf = sag + 8 + (sol - math.pi * Rr / 2 - 30 - sag - 8) * e
    d = xr - xf

    Af = A.astype(np.float32) / 255.0
    Bf = B.astype(np.float32) / 255.0

    def ornekle(img, xo):                                   # ornek: dondurulmus eksende xo, ayni yr
        px = cx + xo * ca - yr * sa
        py = cy + xo * sa + yr * ca
        ix = np.clip(np.round(px).astype(np.int32), 0, W - 1)
        iy = np.clip(np.round(py).astype(np.int32), 0, H - 1)
        return img[iy, ix], (px >= 0) & (px < W) & (py >= 0) & (py < H)

    out = Bf.copy()
    # alttaki sayfaya kivrimin dusurdugu golge
    golge = np.where(d > 0, 1 - 0.38 * np.exp(-np.maximum(d - Rr, 0) / 55.0), 1.0)
    out *= golge[..., None]
    kagit_arka = np.array([0.955, 0.93, 0.87], np.float32)

    # 1) duz bolge (kivrimin solu): A ya da A'nin ters yuzu (katlanmis duz kisim)
    sol_mask = d < 0
    u3 = math.pi * Rr - d
    xo3 = xf + u3
    arka3, ic3 = ornekle(Af, xo3)
    kat3 = sol_mask & ic3
    duz_A = sol_mask & ~ic3
    out[duz_A] = Af[duz_A]
    if kat3.any():
        # katlanan kismin A uzerine dusurdugu yumusak golge (dusuk cozunurlukte bulaniklastirilir)
        kucuk = kat3[::4, ::4].astype(np.float32)
        kucuk = ndimage.gaussian_filter(ndimage.shift(kucuk, (2, -3), order=0), 7)
        bulanik = np.repeat(np.repeat(kucuk, 4, 0), 4, 1)[:H, :W]
        out[duz_A] *= (1 - 0.42 * bulanik[duz_A])[..., None]
        arka = kagit_arka * 0.94 + 0.06 * arka3[kat3]
        out[kat3] = arka * (0.985 - 0.09 * np.clip(-d[kat3] / 700, 0, 1))[..., None]

    # 2) kivrim bolgesi
    kv = (d >= 0) & (d <= Rr)
    if kv.any():
        s = np.clip(d / Rr, 0, 1)
        u1 = Rr * np.arcsin(s)
        u2 = Rr * (math.pi - np.arcsin(s))
        arka2, ic2 = ornekle(Af, xf + u2)
        on1, ic1 = ornekle(Af, xf + u1)
        m2 = kv & ic2
        m1 = kv & ~ic2 & ic1
        isik2 = 0.80 + 0.2 * np.cos(np.arcsin(s))
        out[m2] = (kagit_arka * 0.94 + 0.06 * arka2[m2]) * isik2[m2][..., None]
        isik1 = 0.55 + 0.45 * np.cos(np.arcsin(s))
        out[m1] = on1[m1] * isik1[m1][..., None]
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


# ================================================================ sayfa / masal
class Sayfa:
    def __init__(self, tanim, firca):
        self.t = tanim
        self.sahne = tanim["sahne"]
        self.metin = tanim.get("metin")
        self.kart = None
        sure = tanim.get("sure")
        if self.metin:
            self.kart = MetinKarti(self.metin, sure or 0, tanim.get("konusanlar"), suslu=tanim.get("suslu_harf", True))
            if not sure:
                sure = max(8.0, min(17.0, self.kart.okuma_bitis + 2.6))
            self.kart.sure = sure
        self.sure = float(sure or 6.0)
        self.kamera = Kamera(tanim.get("kamera"))
        self.firca = firca
        self._arka = None

    def arka_resmi(self):
        if self._arka is None:
            aw, ah = int(W * R), int(H * R)
            s = skia.Surface(aw, ah)
            c = s.getCanvas()
            c.clear(renk4(KAGIT).toColor())
            c.scale(R, R)
            self.sahne.arka(c, self.firca)
            self._arka = s.makeImageSnapshot()
        return self._arka

    def kare(self, t):
        """Sayfanin t anindaki karesi -> (H, W, 3) uint8."""
        s = skia.Surface(W, H)
        c = s.getCanvas()
        c.clear(renk4(KAGIT).toColor())
        u = t / self.sure
        z, kx, ky = self.kamera(u)
        sars = getattr(self.sahne, "sarsinti", lambda t: (0.0, 0.0))(t)
        c.save()
        c.concat(Kamera.matris(z, kx, ky, sars))
        c.save()
        c.scale(1 / R, 1 / R)
        c.drawImage(self.arka_resmi(), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
        c.restore()
        durum = dict(konusan=self.kart.konusan(t) if self.kart else None, sure=self.sure, u=u,
                     cumle_t=list(self.kart.zaman) if self.kart else [])
        self.sahne.on(c, self.firca, t, durum)
        c.restore()
        if hasattr(self.sahne, "ust"):                          # kameradan bagimsiz ust katman
            self.sahne.ust(c, self.firca, t, durum)
        if self.kart:
            self.kart.ciz(c, t)
        a = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3].astype(np.float32)
        a *= kagit_dokusu()
        return (np.clip(a, 0, 255) + 0.5).astype(np.uint8)


def tam_ekran(c, renk, alfa=1.0, mod=None):
    """Kamera donusumu altinda da tum gorunur alani kaplayan dolgu (gece tonu, isik)."""
    p = skia.Paint(AntiAlias=False, Color4f=renk4(renk, alfa))
    if mod is not None:
        p.setBlendMode(mod)
    c.drawRect(skia.Rect(-800, -800, W + 800, H + 800), p)


def isik(c, x, y, r, renk, alfa=0.5, mod=skia.BlendMode.kScreen):
    """Radyal isik (ates, fener, gunes)."""
    c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, BlendMode=mod, Shader=skia.GradientShader.MakeRadial(
        skia.Point(x, y), r, [renk4(renk, alfa).toColor(), renk4(renk, 0.0).toColor()])))


class Masal:
    """Bir masal modulunu yukler, zaman cizelgesini kurar, kare uretir."""

    def __init__(self, kimlik):
        import importlib
        self.kimlik = kimlik
        self.mod = importlib.import_module(f"masallar.{kimlik}")
        self.firca = Firca()
        self.sayfalar = [Sayfa(t, self.firca) for t in self.mod.SAYFALAR]
        # zaman cizelgesi: sayfa_i [bas, bit), aralarda CEVIRME
        self.bas = []
        t = 0.0
        for i, s in enumerate(self.sayfalar):
            self.bas.append(t)
            t += s.sure + (CEVIRME if i < len(self.sayfalar) - 1 else 0.0)
        self.SURE = t
        self.BASLIK = getattr(self.mod, "BASLIK", kimlik)

    def nerede(self, t):
        """t -> ('sayfa', i, yerel_t) ya da ('cevir', i, u) (i -> i+1)."""
        for i, s in enumerate(self.sayfalar):
            b = self.bas[i]
            if t < b + s.sure or i == len(self.sayfalar) - 1:
                return ("sayfa", i, min(max(t - b, 0.0), s.sure))
            if t < b + s.sure + CEVIRME:
                return ("cevir", i, (t - b - s.sure) / CEVIRME)
        return ("sayfa", len(self.sayfalar) - 1, self.sayfalar[-1].sure)

    def kare(self, t):
        tur, i, x = self.nerede(t)
        if tur == "sayfa":
            img = self.sayfalar[i].kare(x)
            if i == 0 and x < 0.8:                                  # giris kararmasi
                img = (img.astype(np.float32) * _ss(x / 0.8)).astype(np.uint8)
            son = self.sayfalar[-1]
            if i == len(self.sayfalar) - 1 and x > son.sure - 1.2:
                img = (img.astype(np.float32) * _ss((son.sure - x) / 1.2)).astype(np.uint8)
            return img
        if getattr(self, "_cevir_onbellek", (None,))[0] != i:            # gecis boyunca A ve B sabit
            self._cevir_onbellek = (i, self.sayfalar[i].kare(self.sayfalar[i].sure), self.sayfalar[i + 1].kare(0.0))
        _, A, B = self._cevir_onbellek
        return sayfa_cevir(A, B, x)

    def hazirla(self):
        """Arka plan resimlerini (pahali) once ana surecte cizer."""
        for s in self.sayfalar:
            s.arka_resmi()

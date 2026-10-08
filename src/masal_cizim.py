"""
Masal çizim kütüphanesi — karakterler (eklemli kukla) ve dekorlar.

Karakterler 100 birimlik tasarım boyunda çizilir (ayak tabanı y=0, baş üstü
y≈-100); `boy` parametresi sahnedeki yüksekliği (piksel) belirler. Açılar
derece cinsindendir: 0 = aşağı sarkık, pozitif = yüzün baktığı yöne doğru.

Poz sözlüğü (hepsi isteğe bağlı):
    govde   : gövde eğimi            bas     : baş eğimi
    kol_on  : (omuz, dirsek) öndeki kol      kol_arka: (omuz, dirsek)
    bacak_on: (kalça, diz)           bacak_arka: (kalça, diz)
    zipla   : dikey kayma (birim)    goz     : açıklık 0..1
    agiz    : 0 kapalı (gülümser) .. 1 açık   ifade : gul|sasir|zor|kork|sus|kiz
    bakis   : göz bebeği kayması (-1..1)
"""
import math

import numpy as np
import skia

from src.masal_motoru import (acik, daire, egri, elips, kapsul, koyu, leke, renk4, cokgen,
                              dikdortgen, yumusak, font, MUREKKEP)

TEN = (0.95, 0.79, 0.63)
TEN_ANA = (0.93, 0.76, 0.60)
TEN_KOYU = (0.80, 0.60, 0.45)


# ================================================================ temel
class Boyaci:
    """Olcekli tasarim uzayinda firca kisayollari (cizgi kalinligi ekranda sabit kalir)."""

    def __init__(self, c, f, k):
        self.c, self.f, self.k = c, f, k

    def __call__(self, yol, renk, murekkep=0.9, golge=0.28, kenar=0.55, tohum=1, **kw):
        k = self.k
        kw.setdefault("cizgi", 2.3 * k)
        kw.setdefault("kenar_gen", 6.5 * k)
        kw.setdefault("golge_yon", (3.2 * k, 2.6 * k))
        kw.setdefault("titrek", 0.55 * k)
        kw.setdefault("doku_olcek", k)
        kw.setdefault("leke_sayi", 1)
        return self.f.boya(self.c, yol, renk, murekkep=murekkep, golge=golge, kenar=kenar, tohum=tohum, **kw)

    def cizgi(self, yol, gen=2.0, alfa=0.85, renk=MUREKKEP, tohum=3):
        self.f.cizgi(self.c, yol, gen * self.k, alfa, renk=renk, tohum=tohum)

    def yumusak(self, yol, renk, alfa=0.5, bulanik=4.0):
        self.f.yumusak(self.c, yol, renk, alfa, bulanik * self.k)

    def dolgu(self, yol, renk, alfa=1.0):
        self.c.drawPath(yol, skia.Paint(AntiAlias=True, Color4f=renk4(renk, alfa)))


def _uc(p, aci, L):
    a = math.radians(aci)
    return (p[0] + math.sin(a) * L, p[1] + math.cos(a) * L)


def uzuv(B, kok, a1, a2, L1, L2, r1, r2, renk, el_renk=None, el_r=0.0, tohum=1, ayak=None, ayak_renk=None):
    """Iki parcali uzuv (kol/bacak); dirsek/diz noktasini ve ucu dondurur."""
    orta = _uc(kok, a1, L1)
    uc = _uc(orta, a1 + a2, L2)
    ust = kapsul(*kok, *orta, r1, r1 * 0.92)
    alt = kapsul(*orta, *uc, r1 * 0.9, r2)
    yol = skia.Path()
    yol.addPath(ust)
    yol.addPath(alt)
    yol = skia.Op(ust, alt, skia.PathOp.kUnion_PathOp) or yol
    B(yol, renk, tohum=tohum)
    if ayak:
        ayak(B, uc, a1 + a2)
    elif el_renk and el_r:
        B(daire(uc[0], uc[1], el_r), el_renk, tohum=tohum + 1, golge=0.15)
    return orta, uc


def _carik(renk):
    def ciz(B, uc, aci):
        x, y = uc
        yol = egri([(x - 4.5, y - 2.5), (x + 3, y - 3.2), (x + 9.5, y - 1.5), (x + 11.5, y - 4.2),
                    (x + 10.5, y + 0.6), (x + 2, y + 1.6), (x - 4.8, y + 1.0)])
        B(yol, renk, golge=0.25, tohum=31)
    return ciz


def _cizme(renk):
    def ciz(B, uc, aci):
        x, y = uc
        yol = egri([(x - 4.5, y - 5), (x + 3.5, y - 5.2), (x + 6, y - 2.5), (x + 9.5, y - 1.8),
                    (x + 9.5, y + 1.2), (x - 4.8, y + 1.2)])
        B(yol, renk, golge=0.25, tohum=37)
    return ciz


def _poz(poz, **varsayilan):
    p = dict(govde=0.0, bas=0.0, kol_on=(10, -10), kol_arka=(-8, -12), bacak_on=(4, 0), bacak_arka=(-4, 0),
             zipla=0.0, goz=1.0, agiz=0.0, ifade="gul", bakis=0.0)
    p.update(varsayilan)
    p.update(poz or {})
    return p


def goz_kirp(t, tohum=0, aralik=3.4):
    """Ara sira goz kirpma: 1 acik, 0 kapali."""
    faz = (t + tohum * 1.37) % aralik
    if faz < 0.13:
        return abs(faz - 0.065) / 0.065
    return 1.0


def konus_agiz(t, aktif):
    if not aktif:
        return 0.0
    return 0.25 + 0.75 * abs(math.sin(t * 13.0 + math.sin(t * 5.3) * 1.4))


def yuru(faz, adim=1.0):
    """Yurume dongusu pozu (faz radyan)."""
    s = math.sin(faz)
    return dict(bacak_on=(26 * adim * s, max(0.0, 34 * adim * math.sin(faz + 1.6))),
                bacak_arka=(-26 * adim * s, max(0.0, 34 * adim * math.sin(faz + 1.6 + math.pi))),
                kol_on=(-22 * adim * s, -14), kol_arka=(22 * adim * s, -14),
                zipla=-1.6 * adim * abs(math.cos(faz)), govde=3 * adim)


def kos(faz, adim=1.0):
    s = math.sin(faz)
    return dict(bacak_on=(42 * adim * s, max(0.0, 70 * adim * math.sin(faz + 1.4))),
                bacak_arka=(-42 * adim * s, max(0.0, 70 * adim * math.sin(faz + 1.4 + math.pi))),
                kol_on=(-50 * adim * s + 20, -70), kol_arka=(50 * adim * s + 20, -70),
                zipla=-4.0 * adim * abs(math.cos(faz)), govde=14 * adim)


def golge_zemin(c, f, x, y, gen, alfa=0.22):
    f.yumusak(c, elips(x, y, gen, gen * 0.16), (0.25, 0.18, 0.12), alfa, gen * 0.18)


# ================================================================ yuz
def yuz(B, cx, cy, p, olcek=1.0, ten=TEN, kas=(0.30, 0.18, 0.12), yas=0.0, kirpik=False, yanak=0.42):
    """Gozler, kaslar, burun, agiz, yanaklar. (cx, cy) yuz merkezi."""
    s = olcek
    goz = max(0.06, p["goz"])
    ifade = p["ifade"]
    bx = p["bakis"] * 0.9 * s
    gozler = [(cx - 6.2 * s, cy - 2.0 * s), (cx + 6.0 * s, cy - 2.0 * s)]
    ry = 3.0 * s * goz
    if ifade == "sasir":
        ry *= 1.25
    for i, (gx, gy) in enumerate(gozler):
        if ifade == "gul" and p.get("mutlu_goz"):
            B.cizgi(egri([(gx - 2.6 * s, gy + 0.6 * s), (gx, gy - 1.6 * s), (gx + 2.6 * s, gy + 0.6 * s)], False), 1.6)
            continue
        B.dolgu(elips(gx + bx, gy, 2.2 * s, ry), (0.10, 0.07, 0.06))
        if goz > 0.4:
            B.dolgu(daire(gx + bx + 0.7 * s, gy - 1.0 * s * goz, 0.75 * s), (1, 1, 1), 0.95)
        if kirpik:
            B.cizgi(egri([(gx - 2.4 * s, gy - ry + 0.2), (gx + 2.6 * s, gy - ry - 0.4 * s)], False), 1.2)
    # kaslar
    kd = {"gul": (0.0, -0.4), "sasir": (-1.8, 0.0), "zor": (1.2, 1.4), "kork": (-1.4, 1.6),
          "sus": (0.6, 0.6), "kiz": (1.6, -1.8)}.get(ifade, (0.0, 0.0))
    for i, (gx, gy) in enumerate(gozler):
        yon = -1 if i == 0 else 1
        ic_y = gy - 5.0 * s + kd[0] * s + kd[1] * s * 0.5          # kasin buruna yakin ucu
        dis_y = gy - 5.6 * s + kd[0] * s - kd[1] * s * 0.5
        p1 = (gx - 3.0 * s, (dis_y if yon < 0 else ic_y))
        p2 = (gx + 3.0 * s, (ic_y if yon < 0 else dis_y))
        B.cizgi(egri([p1, ((p1[0] + p2[0]) / 2, min(p1[1], p2[1]) - 0.8 * s), p2], False), 1.9, renk=kas)
    # burun
    B(egri([(cx + 0.4 * s, cy + 1.5 * s), (cx + 2.4 * s, cy + 4.6 * s), (cx + 0.2 * s, cy + 5.6 * s),
            (cx - 1.4 * s, cy + 4.8 * s)]), koyu(ten, 0.93), murekkep=0.55, golge=0.1, kenar=0.3,
      cizgi=1.4 * B.k, leke_sayi=0)
    # yanaklar
    if yanak:
        for gx, gy in gozler:
            B.yumusak(daire(gx + 0.5 * s, gy + 5.5 * s, 2.8 * s), (0.95, 0.45, 0.42), yanak, 2.2 * s)
    # yas cizgileri
    if yas:
        for gx, gy in gozler:
            d = 1 if gx > cx else -1
            B.cizgi(egri([(gx + d * 3.6 * s, gy - 0.6 * s), (gx + d * 5.0 * s, gy + 0.6 * s)], False), 1.0, alfa=0.5 * yas)
    # agiz
    a = p["agiz"]
    my = cy + 9.2 * s
    if ifade == "sus":
        B.cizgi(egri([(cx - 2.2 * s, my), (cx + 2.2 * s, my)], False), 1.6)
    elif a > 0.05 or ifade in ("sasir", "kork"):
        ac = max(a, 0.55 if ifade in ("sasir", "kork") else 0.0)
        gen = (3.2 if ifade in ("sasir", "kork") else 4.2) * s
        yol = egri([(cx - gen, my - 0.6 * s), (cx, my - 1.2 * s), (cx + gen, my - 0.6 * s),
                    (cx + gen * 0.7, my + 3.8 * s * ac), (cx, my + 5.0 * s * ac), (cx - gen * 0.7, my + 3.8 * s * ac)])
        B(yol, (0.45, 0.12, 0.12), murekkep=0.7, golge=0.0, kenar=0.2, cizgi=1.4 * B.k, leke_sayi=0)
        if ac > 0.35:
            B.dolgu(elips(cx, my + 3.3 * s * ac, gen * 0.45, 1.4 * s * ac), (0.88, 0.45, 0.45), 0.9)
    elif ifade == "zor":
        B.cizgi(egri([(cx - 3.6 * s, my + 0.8 * s), (cx - 1.2 * s, my - 0.4 * s), (cx + 1.2 * s, my + 0.8 * s),
                      (cx + 3.6 * s, my - 0.4 * s)], False), 1.6)
    elif ifade == "kiz":
        B.cizgi(egri([(cx - 3.6 * s, my + 1.2 * s), (cx, my - 0.6 * s), (cx + 3.6 * s, my + 1.2 * s)], False), 1.7)
    else:
        B.cizgi(egri([(cx - 4.2 * s, my - 0.8 * s), (cx, my + 2.0 * s), (cx + 4.2 * s, my - 0.8 * s)], False), 1.7)


# ================================================================ Keloglan
KEL = dict(ten=TEN, gomlek=(0.95, 0.91, 0.80), yelek=(0.74, 0.20, 0.16), yama1=(0.88, 0.66, 0.26),
           yama2=(0.40, 0.55, 0.32), kusak=(0.90, 0.63, 0.17), salvar=(0.29, 0.38, 0.55), carik=(0.47, 0.29, 0.16))


def keloglan(c, f, x, y, boy, poz=None, yon=1, sirtta=None):
    """Keloglan: kel, yamali kirmizi yelek, sari kusak, mavi salvar, carik.

    sirtta: (c, f) alan bir cizim fonksiyonu — sirta yuklenen yuk (ornegin kapi),
    gövdeden once (arkada) cizilir; tasarim birimlerinde, sirt noktasi (−6, −52).
    """
    p = _poz(poz)
    k = 100.0 / boy
    B = Boyaci(c, f, k)
    R = KEL
    c.save()
    c.translate(x, y)
    c.scale(yon / k, 1 / k)
    c.translate(0, p["zipla"])
    golge_zemin(c, f, 0, 0.5, 20, 0.25)
    kalca = (0.0, -36.0)
    c.save()
    c.rotate(p["govde"], kalca[0], kalca[1])
    omuz_on, omuz_arka = (5.5, -56.5), (-7.5, -56.5)
    # arkadaki uzuvlar
    uzuv(B, (-2.5, -37), *p["bacak_arka"], 16.5, 16.5, 6.6, 3.8, koyu(R["salvar"], 0.85), tohum=11,
         ayak=_carik(koyu(R["carik"], 0.85)))
    if sirtta:
        c.save()
        c.translate(-6, -52)
        sirtta(c, f, k)
        c.restore()
    uzuv(B, omuz_arka, *p["kol_arka"], 13, 12, 3.9, 3.2, koyu(R["gomlek"], 0.88), koyu(R["ten"], 0.92), 3.4, tohum=13)
    # salvar (kalca/oturak)
    B(egri([(-11, -42), (11, -42), (12.5, -33), (6, -27), (-6, -27), (-12.5, -33)]), R["salvar"], tohum=15)
    uzuv(B, (2.5, -37), *p["bacak_on"], 16.5, 16.5, 6.6, 3.8, R["salvar"], tohum=17, ayak=_carik(R["carik"]))
    # gomlek + yelek
    govde = egri([(-11.5, -58), (-4, -60.5), (5, -60.5), (11.5, -58), (12.5, -46), (11, -38.5), (-11, -38.5), (-12.5, -46)])
    B(govde, R["gomlek"], tohum=19)
    yel_arka = egri([(-12, -57.5), (-3.5, -60), (-1.5, -50), (-3, -38.5), (-11.5, -38.5), (-13, -47)])
    yel_on = egri([(12, -57.5), (4.5, -60), (3.0, -50), (4.5, -38.5), (11.5, -38.5), (13, -47)])
    B(yel_arka, koyu(R["yelek"], 0.9), tohum=21)
    B(yel_on, R["yelek"], tohum=23)
    B(dikdortgen(6.2, -49, 10.4, -44.5, 0.6), R["yama1"], murekkep=0.7, golge=0.1, leke_sayi=0, tohum=25)
    B(dikdortgen(-10.8, -54, -6.6, -50.2, 0.6), R["yama2"], murekkep=0.7, golge=0.1, leke_sayi=0, tohum=27)
    for (x0, y0, x1, y1) in ((6.2, -49, 10.4, -44.5), (-10.8, -54, -6.6, -50.2)):
        for xx in np.linspace(x0 + 0.8, x1 - 0.8, 4):
            B.cizgi(egri([(xx, y0 - 0.6), (xx, y0 + 0.6)], False), 0.8, alfa=0.6)
    # kusak
    B(egri([(-12, -42.5), (12, -42.5), (12.3, -37.5), (-12.3, -37.5)]), R["kusak"], golge=0.2, tohum=29)
    B(egri([(7.5, -40), (11, -39), (12.5, -31.5), (10, -31), (8.8, -36)]), koyu(R["kusak"], 0.92), golge=0.15, tohum=30)
    # boyun + bas
    B(dikdortgen(-3.2, -63, 3.2, -57.5, 1.5), koyu(R["ten"], 0.93), murekkep=0.6, golge=0.1, leke_sayi=0)
    c.save()
    c.rotate(p["bas"], 0, -62)
    hb = (0.5, -77.0)
    B(elips(-16.0, -75.5, 3.6, 5.0), koyu(R["ten"], 0.95), golge=0.15, leke_sayi=0, tohum=33)
    B(elips(hb[0], hb[1], 17.2, 16.6), R["ten"], golge=0.32, golge_yon=(3.5 * k * 0 + 3.0, 2.6), tohum=35)
    B.yumusak(elips(-6.5, -88.5, 5.6, 3.2), (1, 0.98, 0.94), 0.75, 1.8)              # kel parlamasi
    B.yumusak(daire(-1.5, -90.5, 1.6), (1, 1, 1), 0.85, 0.8)
    B(elips(15.8, -74.5, 2.6, 4.2), koyu(R["ten"], 0.96), golge=0.1, leke_sayi=0, tohum=36)   # on kulak
    yuz(B, 5.0, -76.0, p, 1.0, R["ten"])
    c.restore()
    # ondeki kol
    uzuv(B, omuz_on, *p["kol_on"], 13, 12, 3.9, 3.2, R["gomlek"], R["ten"], 3.4, tohum=37)
    c.restore()
    c.restore()


# ================================================================ Ana
ANA = dict(ten=TEN_ANA, yazma=(0.97, 0.95, 0.89), oya=(0.82, 0.25, 0.22), entari=(0.46, 0.30, 0.50),
           onluk=(0.86, 0.55, 0.30), kusak=(0.30, 0.48, 0.36), carik=(0.42, 0.26, 0.15))


def ana(c, f, x, y, boy, poz=None, yon=1, elde=None, yuru_faz=None):
    """Keloglan'in anasi: beyaz oyali yazma, mor entari, turuncu onluk.

    elde: ondeki elde tasinan nesne cizimi (c, f, k) — el noktasina tasinir.
    """
    p = _poz(poz, kol_on=(18, -40), kol_arka=(-6, -18))
    k = 100.0 / boy
    B = Boyaci(c, f, k)
    R = ANA
    c.save()
    c.translate(x, y)
    c.scale(yon / k, 1 / k)
    c.translate(0, p["zipla"])
    golge_zemin(c, f, 0, 0.5, 22, 0.25)
    c.save()
    c.rotate(p["govde"] + 4, 0, -30)
    sal = math.sin(yuru_faz) * 2.5 if yuru_faz is not None else 0.0
    # ayaklar (etek altindan)
    if yuru_faz is not None:
        on_ayak = 5 + 6 * math.sin(yuru_faz)
        arka_ayak = -5 - 6 * math.sin(yuru_faz)
    else:
        on_ayak, arka_ayak = 5, -6
    _carik(koyu(R["carik"], 0.85))(B, (arka_ayak - 2, -1.2), 0)
    _carik(R["carik"])(B, (on_ayak - 2, -1.2), 0)
    omuz_on, omuz_arka = (6.0, -55.5), (-7.0, -55.5)
    uzuv(B, omuz_arka, *p["kol_arka"], 12.5, 12, 4.0, 3.2, koyu(R["entari"], 0.85), koyu(R["ten"], 0.92), 3.2, tohum=41)
    # entari (A kesim)
    entari = egri([(-11, -57), (-3, -59.5), (4, -59.5), (11, -57), (13, -44), (16 + sal, -20), (18.5 + sal, -5),
                   (8 + sal, -2.6), (-4 + sal, -2.4), (-17 + sal, -4.5), (-14.5 + sal, -22), (-12.5, -44)])
    B(entari, R["entari"], tohum=43, golge=0.3)
    rng = np.random.default_rng(3)
    for _ in range(26):                                    # cicek desenleri
        px, py = rng.uniform(-13, 15), rng.uniform(-52, -6)
        if abs(px) > 11 + (-(py) < 40) * 3:
            continue
        B.dolgu(daire(px + sal * (-py < 25), py, 0.95), (0.95, 0.80, 0.42), 0.75)
    # onluk
    onluk = egri([(-7, -42), (8.5, -42), (11 + sal, -12), (9 + sal, -7.5), (-6 + sal, -7.5), (-8.5 + sal, -12)])
    B(onluk, R["onluk"], tohum=45, golge=0.2)
    for yy in np.linspace(-36, -12, 5):
        B.cizgi(egri([(-7.6, yy), (9.6, yy)], False), 1.0, alfa=0.35, renk=koyu(R["onluk"], 0.6))
    B(egri([(-12.5, -46), (12.5, -46), (12.8, -41), (-12.8, -41)]), R["kusak"], golge=0.2, tohum=47)
    # bas + yazma
    c.save()
    c.rotate(p["bas"], 0, -60)
    yazma_arka = egri([(-14.5, -86), (-3, -95), (11, -92), (15, -78), (13, -62), (6, -56), (-12, -54), (-17, -66)])
    B(yazma_arka, R["yazma"], tohum=49, golge=0.25)
    hb = (2.5, -76.5)
    B(elips(hb[0] + 1.0, hb[1], 12.0, 13.2), R["ten"], tohum=51, golge=0.22)
    yuz(B, hb[0] + 1.6, hb[1] - 1.0, p, 0.82, R["ten"], kas=(0.45, 0.40, 0.36), yas=1.0, yanak=0.38)
    # yazma on kenari ve oya
    on_kenar = egri([(-9.5, -87), (0, -91.5), (11, -88.5), (15.5, -80), (13.8, -82.5), (9.5, -86.5),
                     (1, -88.5), (-7.5, -84.5), (-11.5, -76), (-11, -66), (-14, -70), (-13.5, -80)])
    B(on_kenar, R["yazma"], tohum=53, golge=0.18)
    for a in np.linspace(-2.6, -0.2, 11):
        px, py = hb[0] + math.cos(a) * 14.2, hb[1] - 1 + math.sin(a) * 14.0
        B.dolgu(daire(px, py, 0.95), R["oya"], 0.95)
    for _ in range(12):
        px, py = rng.uniform(-14, 12), rng.uniform(-90, -60)
        if (px - hb[0]) ** 2 / 150 + (py - hb[1]) ** 2 / 190 > 1.15:
            B.dolgu(daire(px, py, 0.8), R["oya"], 0.7)
    c.restore()
    p_el = uzuv(B, omuz_on, *p["kol_on"], 12.5, 12, 4.0, 3.2, R["entari"], R["ten"], 3.2, tohum=55)[1]
    if elde:
        c.save()
        c.translate(*p_el)
        elde(c, f, k)
        c.restore()
    c.restore()
    c.restore()


# ================================================================ Harami
HARAMI_TIPLERI = {
    "sisman": dict(sarik=(0.72, 0.22, 0.18), yelek=(0.22, 0.17, 0.14), gomlek=(0.86, 0.78, 0.62),
                   salvar=(0.20, 0.20, 0.24), kusak=(0.62, 0.16, 0.14), gen=1.32, boy=0.96, biyik=1.3),
    "uzun": dict(sarik=(0.30, 0.45, 0.32), yelek=(0.33, 0.22, 0.15), gomlek=(0.80, 0.74, 0.62),
                 salvar=(0.26, 0.22, 0.20), kusak=(0.80, 0.55, 0.15), gen=0.86, boy=1.08, biyik=1.0),
    "orta": dict(sarik=(0.85, 0.62, 0.22), yelek=(0.17, 0.15, 0.20), gomlek=(0.70, 0.60, 0.50),
                 salvar=(0.30, 0.20, 0.18), kusak=(0.36, 0.30, 0.55), gen=1.05, boy=1.0, biyik=1.15, bant=True),
}


def harami(c, f, x, y, boy, tip="orta", poz=None, yon=1, oturuyor=False):
    """Uc haramiden biri: sarik, kocaman burma biyik, kalin kaslar, kusakta hancer."""
    T = HARAMI_TIPLERI[tip]
    p = _poz(poz, ifade="kiz")
    k = 100.0 / boy
    B = Boyaci(c, f, k)
    g = T["gen"]
    c.save()
    c.translate(x, y)
    c.scale(yon / k, 1 / k)
    c.translate(0, p["zipla"])
    golge_zemin(c, f, 0, 0.5, 24 * g, 0.28)
    kal_y = -33.0 if not oturuyor else -12.0
    c.save()
    c.rotate(p["govde"], 0, kal_y)
    omuz_on, omuz_arka = (7.0 * g, -59.0 + (kal_y + 33)), (-8.0 * g, -59.0 + (kal_y + 33))
    dy = kal_y + 33
    if oturuyor:                                           # bagdas
        B(egri([(-20 * g, -2), (-6 * g, -13), (8 * g, -13), (21 * g, -2), (10 * g, 1.5), (-10 * g, 1.5)]),
          T["salvar"], tohum=61)
        _cizme((0.12, 0.10, 0.09))(B, (-14 * g, -1), 0)
        _cizme((0.12, 0.10, 0.09))(B, (9 * g, -1), 0)
    else:
        uzuv(B, (-3 * g, -33), *p["bacak_arka"], 16, 16.5, 7.2, 4.0, koyu(T["salvar"], 0.85), tohum=63,
             ayak=_cizme((0.10, 0.08, 0.07)))
    uzuv(B, omuz_arka, *p["kol_arka"], 14, 13, 4.4, 3.6, koyu(T["gomlek"], 0.85), koyu(TEN_KOYU, 0.95), 3.8, tohum=65)
    if not oturuyor:
        B(egri([(-12 * g, -40), (12 * g, -40), (13 * g, -30), (6, -24), (-6, -24), (-13 * g, -30)]), T["salvar"], tohum=67)
        uzuv(B, (3 * g, -33), *p["bacak_on"], 16, 16.5, 7.2, 4.0, T["salvar"], tohum=69, ayak=_cizme((0.13, 0.11, 0.10)))
    # govde
    gb = 6 if tip == "sisman" else 0
    govde = egri([(-12 * g, -61 + dy), (0, -63.5 + dy), (12 * g, -61 + dy), (13 * g + gb, -48 + dy),
                  (12 * g + gb * 0.6, -36 + dy), (-12 * g, -36 + dy), (-13.5 * g, -48 + dy)])
    B(govde, T["gomlek"], tohum=71)
    B(egri([(-12.8 * g, -60.5 + dy), (-3, -62.5 + dy), (-1, -48 + dy), (-2.5, -36 + dy), (-12 * g, -36 + dy), (-14 * g, -48 + dy)]),
      T["yelek"], tohum=73)
    B(egri([(12.8 * g, -60.5 + dy), (4, -62.5 + dy), (2.5, -48 + dy), (4, -36 + dy), (12 * g + gb * 0.6, -36 + dy),
            (13.5 * g + gb, -48 + dy)]), T["yelek"], tohum=75)
    for xx in (-1.5, 3.2):                                 # sirma kenar
        B.cizgi(egri([(xx, -61 + dy), (xx + 0.6, -48 + dy), (xx, -37 + dy)], False), 1.0, alfa=0.7, renk=(0.85, 0.65, 0.25))
    B(egri([(-13 * g, -42 + dy), (13 * g + gb * 0.6, -42 + dy), (13.2 * g + gb * 0.6, -35 + dy), (-13.2 * g, -35 + dy)]),
      T["kusak"], tohum=77, golge=0.2)
    # hancer
    B(cokgen([(-4, -42 + dy), (-1, -42 + dy), (-0.5, -49 + dy), (-4.6, -49 + dy)]), (0.45, 0.32, 0.16), golge=0.1, tohum=78)
    B(daire(-2.6, -49.5 + dy, 1.6), (0.88, 0.70, 0.30), golge=0.1, leke_sayi=0, tohum=79)
    # bas
    c.save()
    c.rotate(p["bas"], 0, -64 + dy)
    hb = (1.0, -77.0 + dy)
    B(dikdortgen(-3.5, -68 + dy, 3.5, -61 + dy, 1.5), koyu(TEN_KOYU, 0.97), murekkep=0.5, golge=0.1, leke_sayi=0)
    B(elips(hb[0], hb[1], 11.8, 12.6), TEN_KOYU, tohum=81, golge=0.3)
    B.yumusak(egri([(-9, -74 + dy), (10, -74 + dy), (8, -66 + dy), (0, -63.5 + dy), (-8, -66 + dy)]),
              (0.32, 0.30, 0.36), 0.35, 1.6)                # sakal golgesi
    yuz(B, hb[0] + 2.0, hb[1] - 1.5, p, 0.78, TEN_KOYU, kas=(0.10, 0.08, 0.07), yanak=0.15)
    # burma biyik
    bs = T["biyik"]
    by_ = hb[1] + 4.6
    for d in (-1, 1):
        B(egri([(hb[0] + 2.0, by_ - 0.5), (hb[0] + 2.0 + d * 5.5 * bs, by_ - 1.4), (hb[0] + 2.0 + d * 10 * bs, by_ - 4.8),
                (hb[0] + 2.0 + d * 11.5 * bs, by_ - 7.5), (hb[0] + 2.0 + d * 9.4 * bs, by_ - 5.6),
                (hb[0] + 2.0 + d * 6.2 * bs, by_ + 1.8), (hb[0] + 2.0, by_ + 1.6)]),
          (0.09, 0.07, 0.06), murekkep=0.6, golge=0.0, kenar=0.2, leke_sayi=0, tohum=83 + d)
    if T.get("bant"):
        B(elips(hb[0] - 3.8, hb[1] - 3.2, 3.0, 2.6), (0.08, 0.07, 0.06), murekkep=0.5, golge=0, leke_sayi=0)
        B.cizgi(egri([(-10.5, hb[1] - 7.5), (hb[0] - 3.8, hb[1] - 3.2), (11.5, hb[1] - 9)], False), 1.2, alfa=0.9,
                renk=(0.08, 0.07, 0.06))
    # sarik
    sr = T["sarik"]
    B(egri([(-13.5, hb[1] - 5), (-12, hb[1] - 15), (-2, hb[1] - 20), (10, hb[1] - 17), (14, hb[1] - 7),
            (6, hb[1] - 8.5), (-4, hb[1] - 7.5)]), sr, tohum=85, golge=0.3)
    for i in range(3):
        yy = hb[1] - 9.5 - i * 3.2
        B.cizgi(egri([(-12.5 + i, yy + 1.5), (0, yy - 1.2), (12.5 - i, yy + 1.0)], False), 1.0, alfa=0.55, renk=koyu(sr, 0.55))
    B(daire(1.5, hb[1] - 16.5, 2.4), (0.88, 0.72, 0.32), murekkep=0.6, golge=0.1, leke_sayi=0, tohum=87)
    c.restore()
    uzuv(B, omuz_on, *p["kol_on"], 14, 13, 4.4, 3.6, T["gomlek"], TEN_KOYU, 3.8, tohum=89)
    c.restore()
    c.restore()


# ================================================================ koylu
def koylu(c, f, x, y, boy, kadin=False, renkler=None, poz=None, yon=1, tohum=0, sapka="kasket", biyik=True):
    """Dugun kalabaligi icin sade koylu (erkek: kasket/fes, yelek, salvar; kadin: yazma, entari)."""
    rng = np.random.default_rng(tohum)
    r = renkler or {}
    p = _poz(poz)
    k = 100.0 / boy
    B = Boyaci(c, f, k)
    ten = r.get("ten", karisik_ten(rng))
    ust = r.get("ust", tuple(rng.uniform(0.25, 0.8, 3)))
    alt = r.get("alt", tuple(rng.uniform(0.2, 0.55, 3)))
    bas_renk = r.get("bas", tuple(rng.uniform(0.3, 0.9, 3)))
    c.save()
    c.translate(x, y)
    c.scale(yon / k, 1 / k)
    c.translate(0, p["zipla"])
    golge_zemin(c, f, 0, 0.5, 19, 0.22)
    c.save()
    c.rotate(p["govde"], 0, -36)
    omuz_on, omuz_arka = (6.0, -57), (-7.0, -57)
    if not kadin:
        uzuv(B, (-2.5, -36), *p["bacak_arka"], 16.5, 16.5, 6.0, 3.6, koyu(alt, 0.85), tohum=tohum + 1,
             ayak=_carik((0.30, 0.22, 0.15)))
    uzuv(B, omuz_arka, *p["kol_arka"], 13, 12, 3.8, 3.1, koyu(ust, 0.85), koyu(ten, 0.92), 3.2, tohum=tohum + 2)
    if kadin:
        _carik((0.35, 0.22, 0.14))(B, (-6, -1.2), 0)
        _carik((0.35, 0.22, 0.14))(B, (3, -1.2), 0)
        B(egri([(-11, -58), (0, -60.5), (11, -58), (13, -40), (17, -4), (-16, -4), (-13, -40)]), ust, tohum=tohum + 3)
        rr = np.random.default_rng(tohum + 9)
        for _ in range(16):
            B.dolgu(daire(rr.uniform(-12, 14), rr.uniform(-52, -8), 0.9), acik(ust, 0.6), 0.7)
    else:
        B(egri([(-11, -41), (11, -41), (12, -32), (6, -26), (-6, -26), (-12, -32)]), alt, tohum=tohum + 4)
        uzuv(B, (2.5, -36), *p["bacak_on"], 16.5, 16.5, 6.0, 3.6, alt, tohum=tohum + 5, ayak=_carik((0.32, 0.23, 0.15)))
        B(egri([(-11, -58), (0, -60.5), (11, -58), (12, -46), (11, -38), (-11, -38), (-12, -46)]), (0.93, 0.90, 0.82),
          tohum=tohum + 6)
        B(egri([(-11.5, -57.5), (-3, -60), (-1.5, -38), (-11, -38), (-12.5, -47)]), ust, tohum=tohum + 7)
        B(egri([(11.5, -57.5), (3.5, -60), (2.5, -38), (11, -38), (12.5, -47)]), ust, tohum=tohum + 8)
    c.save()
    c.rotate(p["bas"], 0, -61)
    hb = (0.5, -75.5)
    B(elips(hb[0], hb[1], 12.5, 13.2), ten, tohum=tohum + 10, golge=0.25)
    yuz(B, hb[0] + 2.2, hb[1], p, 0.8, ten, yanak=0.35)
    if kadin:
        B(egri([(-13.5, -78), (-5, -90.5), (8, -90), (14.5, -80), (12, -70), (14, -60), (-12, -58), (-15, -68)]),
          bas_renk, tohum=tohum + 11, golge=0.2, alfa=1.0)
        B(elips(hb[0] + 1.6, hb[1] + 1.6, 9.6, 10.6), ten, murekkep=0.5, golge=0.1, leke_sayi=0, tohum=tohum + 12)
        yuz(B, hb[0] + 2.2, hb[1] + 0.5, p, 0.72, ten, yanak=0.35)
    else:
        if biyik:
            B(egri([(hb[0] - 4, hb[1] + 6.5), (hb[0] + 2.2, hb[1] + 5), (hb[0] + 8.5, hb[1] + 6.5), (hb[0] + 2.2, hb[1] + 8.4)]),
              (0.22, 0.15, 0.10), murekkep=0.4, golge=0, leke_sayi=0, tohum=tohum + 13)
        if sapka == "fes":
            B(cokgen([(-8, hb[1] - 9), (9, hb[1] - 9), (7, hb[1] - 20), (-6, hb[1] - 20)]), (0.72, 0.14, 0.12),
              tohum=tohum + 14, golge=0.25)
            B.cizgi(egri([(0, hb[1] - 20), (-3, hb[1] - 16), (-5, hb[1] - 10)], False), 1.2, renk=(0.12, 0.08, 0.06))
        else:
            B(egri([(-13, hb[1] - 6), (-10, hb[1] - 14.5), (4, hb[1] - 16), (13, hb[1] - 10), (17, hb[1] - 6.5),
                    (4, hb[1] - 7.5)]), bas_renk, tohum=tohum + 15, golge=0.25)
    c.restore()
    uzuv(B, omuz_on, *p["kol_on"], 13, 12, 3.8, 3.1, ust if not kadin else acik(ust, 0.05), ten, 3.2, tohum=tohum + 16)
    c.restore()
    c.restore()


def karisik_ten(rng):
    return tuple(np.array(TEN) * rng.uniform(0.88, 1.0) + np.array([0, -0.02, -0.03]) * rng.uniform(0, 1))


# ================================================================ esyalar
AHSAP = (0.62, 0.42, 0.25)


def kapi(c, f, x, y, gen, yuk, aci=0.0, k=1.0, pivot=None, tohum=7):
    """Ahsap kapi: uc tahta, iki kusak, demir mentese ve halka. (x, y) sol ust kose."""
    B = Boyaci(c, f, k)
    c.save()
    if aci:
        px, py = pivot or (x + gen / 2, y + yuk / 2)
        c.rotate(aci, px, py)
    tg = gen / 3.0
    for i in range(3):
        ton = koyu(AHSAP, 0.92 + 0.08 * ((i * 7 + tohum) % 3) / 2)
        B(dikdortgen(x + i * tg, y, x + (i + 1) * tg, y + yuk, 1.5 * k), ton, golge=0.25, tohum=tohum + i)
        rng = np.random.default_rng(tohum + i)
        for _ in range(3):                                  # damar
            xx = x + i * tg + rng.uniform(0.2, 0.8) * tg
            B.cizgi(egri([(xx, y + yuk * 0.06), (xx + rng.uniform(-2, 2) * k, y + yuk * 0.5), (xx, y + yuk * 0.94)], False),
                    0.9, alfa=0.35)
    for yy in (0.18, 0.78):
        B(dikdortgen(x - 1.5 * k, y + yuk * yy, x + gen + 1.5 * k, y + yuk * yy + yuk * 0.07, 1.2 * k),
          koyu(AHSAP, 0.8), golge=0.3, tohum=tohum + 9)
        B(dikdortgen(x - 2 * k, y + yuk * yy + yuk * 0.015, x + gen * 0.38, y + yuk * yy + yuk * 0.055, 0.8 * k),
          (0.20, 0.18, 0.17), golge=0.1, tohum=tohum + 10)
        for xx in (x + gen * 0.08, x + gen * 0.22, x + gen * 0.33):
            B.dolgu(daire(xx, y + yuk * yy + yuk * 0.035, 1.1 * k), (0.55, 0.52, 0.48), 0.9)
    hx, hy = x + gen * 0.82, y + yuk * 0.5
    B.cizgi(daire(hx, hy + 3 * k, 3.6 * k), 1.6, alfa=0.95, renk=(0.18, 0.16, 0.15))
    B.dolgu(daire(hx, hy - 1.0 * k, 1.6 * k), (0.25, 0.22, 0.20), 1.0)
    c.restore()


def kapi_sirtta(gen=42, yuk=78, aci=-10):
    """Keloglan'in sirtindaki kapi (sirtta= icin): basindan yuksek, komik derecede buyuk."""
    def ciz(c, f, k):
        kapi(c, f, -gen * 0.65, -yuk * 0.62, gen, yuk, aci=aci, k=k, tohum=7)
    return ciz


TASI = dict(kol_on=(18, 128), kol_arka=(8, 132), govde=7)        # kapiyi sirtta tasirken kollar


def bohca(renk=(0.80, 0.28, 0.22), boyut=9.0):
    def ciz(c, f, k):
        B = Boyaci(c, f, k)
        s = boyut
        B(egri([(-s, s * 0.4), (-s * 0.8, s * 1.6), (s * 0.8, s * 1.7), (s * 1.05, s * 0.5), (0, s * 0.1)]),
          renk, golge=0.3, tohum=91)
        B(egri([(-s * 0.4, s * 0.25), (-s * 0.55, -s * 0.25), (0, s * 0.05), (s * 0.5, -s * 0.3), (s * 0.4, s * 0.3)]),
          koyu(renk, 0.85), golge=0.1, tohum=92)
        rng = np.random.default_rng(5)
        for _ in range(9):
            B.dolgu(daire(rng.uniform(-s * 0.7, s * 0.8), rng.uniform(s * 0.6, s * 1.5), s * 0.09), (0.98, 0.85, 0.40), 0.85)
    return ciz


def heybe(c, f, x, y, s=1.0, k=1.0, tohum=3):
    B = Boyaci(c, f, k)
    renkler = [(0.70, 0.18, 0.15), (0.20, 0.30, 0.50), (0.88, 0.66, 0.25), (0.25, 0.45, 0.30)]
    for d in (-1, 1):
        yol = egri([(x + d * 4 * s, y), (x + d * 22 * s, y + 2 * s), (x + d * 24 * s, y + 24 * s),
                    (x + d * 13 * s, y + 29 * s), (x + d * 3 * s, y + 24 * s)])
        B(yol, renkler[0], tohum=tohum + d)
        for i in range(3):
            yy = y + (8 + i * 6) * s
            B.cizgi(egri([(x + d * 5 * s, yy), (x + d * 22 * s, yy + 1 * s)], False), 2.2 * s, alfa=0.8,
                    renk=renkler[1 + i % 3])
    B(dikdortgen(x - 5 * s, y - 2 * s, x + 5 * s, y + 4 * s, 1.5 * s), (0.55, 0.38, 0.22), tohum=tohum + 5)


def altin_yigini(c, f, x, y, s=1.0, n=26, t=0.0, tohum=4, k=1.0, parilti=True):
    """Altin sikke yigini + ara sira parlayan yildizciklar."""
    rng = np.random.default_rng(tohum)
    B = Boyaci(c, f, k)
    sikkeler = []
    sira = 0
    while len(sikkeler) < n:                               # tabandan tepeye daralan siralar
        gen = 26 * s * (1 - sira / 6.0)
        if gen <= 3 * s:
            break
        adet = max(1, int(gen / (6.5 * s)))
        for j in range(adet):
            px = x + (j - (adet - 1) / 2) * (2 * gen / max(adet, 1)) * 0.95 + rng.uniform(-2, 2) * s
            py = y - sira * 4.2 * s + rng.uniform(-1.2, 1.2) * s + abs(px - x) / max(gen, 1) * 2.5 * s
            sikkeler.append((py, px))
        sira += 1
    for py, px in sorted(sikkeler):
        B(elips(px, py, 5.2 * s, 2.6 * s), (0.93, 0.74, 0.22), murekkep=0.6, golge=0.15, kenar=0.5,
          leke_sayi=0, tohum=int(px * 7) % 97, cizgi=1.2 * k)
        B.dolgu(elips(px - 1.2 * s, py - 0.6 * s, 2.0 * s, 0.7 * s), (1.0, 0.95, 0.70), 0.7)
    if parilti:
        for i in range(4):
            ph = (t * 0.9 + i * 0.37 + tohum * 0.11) % 1.0
            a = max(0.0, math.sin(ph * math.pi)) ** 3
            if a > 0.02:
                px = x + (rng.uniform(-0.8, 0.8)) * 22 * s
                py = y - rng.uniform(0, 1) * 10 * s
                yildizcik(c, px, py, 7 * s * (0.6 + a * 0.6), a)


def sikke(c, f, x, y, s=1.0, aci=0.0, k=1.0):
    B = Boyaci(c, f, k)
    c.save()
    c.rotate(aci, x, y)
    B(elips(x, y, 5.2 * s, 5.2 * s * max(0.12, abs(math.cos(math.radians(aci * 3))))), (0.93, 0.74, 0.22),
      murekkep=0.6, golge=0.15, leke_sayi=0, cizgi=1.2 * k)
    c.restore()


def yildizcik(c, x, y, r, alfa=1.0, renk=(1.0, 0.97, 0.80)):
    """Dort kollu parilti."""
    yol = skia.Path()
    for i in range(8):
        a = i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.18
        px, py = x + math.cos(a) * rr, y + math.sin(a) * rr
        (yol.moveTo if i == 0 else yol.lineTo)(px, py)
    yol.close()
    c.drawPath(yol, skia.Paint(AntiAlias=True, Color4f=renk4(renk, alfa)))
    c.drawCircle(x, y, r * 0.55, skia.Paint(AntiAlias=True, Color4f=renk4(renk, 0.35 * alfa),
                                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.5)))


def ates(c, f, x, y, s=1.0, t=0.0, guc=1.0):
    """Kamp atesi: tas halka, capraz kutukler, titreyen alevler, kivilcim, isilti."""
    B = Boyaci(c, f, 1.0)
    # isilti (zemin)
    c.drawPath(elips(x, y, 190 * s, 70 * s), skia.Paint(
        AntiAlias=True, Shader=skia.GradientShader.MakeRadial(skia.Point(x, y), 190 * s,
                                                               [renk4((1.0, 0.62, 0.25), 0.38 * guc).toColor(),
                                                                renk4((1.0, 0.5, 0.2), 0.0).toColor()]),
        BlendMode=skia.BlendMode.kScreen))
    for i in range(7):
        a = math.pi * (0.05 + 0.9 * i / 6)
        B(leke(x + math.cos(a) * 34 * s, y + 6 * s - math.sin(a) * 6 * s, 8 * s, 6 * s, i, 0.15),
          (0.50, 0.48, 0.45), golge=0.3, tohum=100 + i, cizgi=1.8)
    for d in (-1, 1):
        B(kapsul(x - 30 * s * d, y + 4 * s, x + 26 * s * d, y - 6 * s, 5.5 * s), (0.42, 0.27, 0.15), golge=0.35,
          tohum=110 + d, cizgi=1.8)
    # alevler
    katman = [((0.92, 0.26, 0.10), 1.0, 0.0), ((1.0, 0.55, 0.12), 0.75, 1.3), ((1.0, 0.86, 0.35), 0.48, 2.6)]
    for renk, olc, faz in katman:
        pts = []
        n = 9
        for i in range(n + 1):
            u = i / n
            bx = x + (u - 0.5) * 50 * s * olc
            yuk = (1 - abs(u - 0.5) * 2) ** 0.7
            tit = math.sin(t * 9 + u * 7 + faz) * 0.18 + math.sin(t * 15.3 + u * 13 + faz * 2) * 0.1
            pts.append((bx + tit * 10 * s, y - 4 * s - yuk * (78 * s * olc) * (1 + tit) * guc))
        pts.append((x + 25 * s * olc, y))
        pts.append((x - 25 * s * olc, y))
        yol = egri(pts)
        c.drawPath(yol, skia.Paint(AntiAlias=True, Color4f=renk4(renk, 0.92),
                                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.6 * s)))
    # kivilcimlar
    rng = np.random.default_rng(9)
    for i in range(10):
        ph = (t * 0.6 + rng.uniform()) % 1.0
        px = x + rng.uniform(-25, 25) * s + math.sin(t * 3 + i) * 10 * s * ph
        py = y - 60 * s - ph * 160 * s
        c.drawCircle(px, py, 2.0 * s * (1 - ph) + 0.6, skia.Paint(AntiAlias=True, Color4f=renk4((1.0, 0.8, 0.4), (1 - ph) * 0.9)))
    # parlama
    c.drawCircle(x, y - 30 * s, 120 * s, skia.Paint(
        AntiAlias=True, Shader=skia.GradientShader.MakeRadial(skia.Point(x, y - 30 * s), 120 * s,
                                                               [renk4((1.0, 0.7, 0.3), 0.30 * guc).toColor(),
                                                                renk4((1.0, 0.6, 0.2), 0.0).toColor()]),
        BlendMode=skia.BlendMode.kScreen))


def duman(c, f, x, y, t, s=1.0, n=7, renk=(0.92, 0.92, 0.94), alfa=0.55, ruzgar=18.0):
    for i in range(n):
        ph = (t * 0.22 + i / n) % 1.0
        px = x + ruzgar * ph * 3 * s + math.sin(ph * 6 + i) * 6 * s
        py = y - ph * 170 * s
        r = (8 + ph * 26) * s
        f.yumusak(c, leke(px, py, r, r * 0.85, i, 0.2), renk, alfa * (1 - ph) ** 1.2 * min(1, ph * 6), r * 0.35)


def toz_bulutu(c, f, x, y, u, s=1.0):
    """u: 0..1 patlamanin ilerlemesi."""
    if u <= 0 or u >= 1:
        return
    rng = np.random.default_rng(21)
    for i in range(14):
        a = rng.uniform(math.pi * 1.0, math.pi * 2.0)
        sp = rng.uniform(0.5, 1.0)
        px = x + math.cos(a) * 170 * s * sp * u ** 0.6
        py = y + math.sin(a) * 60 * s * sp * u ** 0.6 - 10 * s
        r = (14 + 40 * u) * s * rng.uniform(0.7, 1.2)
        f.yumusak(c, leke(px, py, r, r * 0.8, i, 0.2), (0.80, 0.72, 0.60), 0.7 * (1 - u) ** 1.3, r * 0.3)


def kuslar(c, f, x, y, t, n=3, s=1.0, hiz=60.0, tohum=1):
    rng = np.random.default_rng(tohum)
    for i in range(n):
        ox, oy = rng.uniform(-80, 80) * s, rng.uniform(-30, 30) * s
        px = x + ox + t * hiz
        py = y + oy + math.sin(t * 1.3 + i) * 6 * s
        kanat = math.sin(t * 9 + i * 1.7) * 7 * s
        yol = egri([(px - 11 * s, py - kanat), (px - 4 * s, py - 2 * s), (px, py + 1.5 * s), (px + 4 * s, py - 2 * s),
                    (px + 11 * s, py - kanat)], False)
        f.cizgi(c, yol, 2.2 * s, 0.75, tohum=i + 4)


def ay(c, f, x, y, r=60.0):
    c.drawCircle(x, y, r * 3.2, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        skia.Point(x, y), r * 3.2, [renk4((1.0, 0.96, 0.80), 0.30).toColor(), renk4((1.0, 0.96, 0.8), 0.0).toColor()])))
    f.boya(c, daire(x, y, r), (0.99, 0.95, 0.80), doku=0.45, kenar=0.35, kenar_gen=10, titrek=0.6, tohum=5)
    for (dx, dy, rr) in ((-0.3, -0.2, 0.18), (0.25, 0.15, 0.12), (-0.05, 0.35, 0.1)):
        f.yumusak(c, daire(x + dx * r, y + dy * r, rr * r), (0.85, 0.80, 0.66), 0.5, rr * r * 0.5)


def yildizlar(c, f, t, kutu=(0, 0, 1920, 560), n=80, tohum=3):
    rng = np.random.default_rng(tohum)
    for i in range(n):
        x = rng.uniform(kutu[0], kutu[2])
        y = rng.uniform(kutu[1], kutu[3])
        r = rng.uniform(1.2, 3.4)
        a = 0.55 + 0.45 * math.sin(t * rng.uniform(1.0, 3.0) + rng.uniform(0, 6))
        if r > 2.8:
            yildizcik(c, x, y, r * 2.6, a * 0.9, (1.0, 0.97, 0.85))
        else:
            c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Color4f=renk4((1.0, 0.97, 0.85), a * 0.9)))


def elma(c, f, x, y, s=1.0, aci=0.0, renk=(0.85, 0.16, 0.12)):
    c.save()
    c.rotate(aci, x, y)
    f.boya(c, egri([(x, y - 9 * s), (x + 10 * s, y - 12 * s), (x + 14 * s, y), (x + 8 * s, y + 13 * s), (x, y + 11 * s),
                    (x - 8 * s, y + 13 * s), (x - 14 * s, y), (x - 10 * s, y - 12 * s)]), renk, murekkep=0.9, golge=0.35,
           golge_yon=(3, 3), cizgi=2.0, kenar_gen=6, tohum=7)
    f.yumusak(c, elips(x - 5 * s, y - 4 * s, 3.5 * s, 2.5 * s), (1, 1, 1), 0.6, 2 * s)
    f.cizgi(c, egri([(x, y - 9 * s), (x + 1 * s, y - 16 * s)], False), 2.0)
    f.boya(c, egri([(x + 1 * s, y - 14 * s), (x + 8 * s, y - 19 * s), (x + 12 * s, y - 15 * s), (x + 6 * s, y - 12 * s)]),
           (0.40, 0.62, 0.28), murekkep=0.8, golge=0.2, cizgi=1.6, kenar_gen=4, tohum=8)
    c.restore()


def dusunce_balonu(c, f, x, y, gen, yuk, kaynak, alfa=1.0, icerik=None):
    """Bulut seklinde dusunce balonu; kaynak: karakterin basi (x, y)."""
    if alfa <= 0.01:
        return
    c.saveLayerAlpha(None, int(255 * alfa))
    for i, u in enumerate((0.25, 0.5)):
        px = kaynak[0] + (x - kaynak[0]) * u * 0.9
        py = kaynak[1] + (y + yuk * 0.4 - kaynak[1]) * u * 0.9
        f.boya(c, daire(px, py, 6 + 6 * i), (0.99, 0.98, 0.95), murekkep=0.9, golge=0.1, cizgi=2.0, kenar_gen=4, tohum=i)
    pts = []
    for i in range(12):
        a = 2 * math.pi * i / 12
        rr = 1 + 0.12 * math.sin(i * 2.3)
        pts.append((x + math.cos(a) * gen / 2 * rr, y + math.sin(a) * yuk / 2 * rr))
    yol = skia.Path()
    for i in range(12):
        a0 = 2 * math.pi * i / 12
        yol.addCircle(x + math.cos(a0) * gen * 0.4, y + math.sin(a0) * yuk * 0.38, min(gen, yuk) * 0.22)
    yol.addOval(skia.Rect(x - gen * 0.42, y - yuk * 0.4, x + gen * 0.42, y + yuk * 0.4))
    yol = skia.Op(yol, skia.Path(), skia.PathOp.kUnion_PathOp) or yol
    f.boya(c, yol, (0.99, 0.98, 0.95), murekkep=0.9, golge=0.12, cizgi=2.2, kenar_gen=8, kenar=0.25, tohum=9)
    if icerik:
        icerik(c, f)
    c.restore()


def davul(c, f, x, y, s=1.0, k=1.0, tohum=5):
    B = Boyaci(c, f, k)
    B(dikdortgen(x - 9 * s, y - 17 * s, x + 9 * s, y + 17 * s, 2 * s), (0.70, 0.18, 0.14), tohum=tohum + 1)
    for i in range(6):                                     # ip ortgusu
        yy = y - 15 * s + i * 6 * s
        B.cizgi(egri([(x - 8 * s, yy), (x + 8 * s, yy + 3 * s)], False), 1.0, alfa=0.85, renk=(0.97, 0.88, 0.60))
        B.cizgi(egri([(x - 8 * s, yy + 3 * s), (x + 8 * s, yy)], False), 1.0, alfa=0.85, renk=(0.97, 0.88, 0.60))
    for d in (-1, 1):
        B(elips(x + d * 9 * s, y, 4 * s, 17.5 * s), (0.90, 0.85, 0.72), tohum=tohum + 2 + d, golge=0.2)


def zurna(c, f, x, y, aci=-20, s=1.0, k=1.0):
    B = Boyaci(c, f, k)
    c.save()
    c.rotate(aci, x, y)
    B(cokgen([(x, y - 1.6 * s), (x + 22 * s, y - 2.6 * s), (x + 30 * s, y - 6.5 * s), (x + 30 * s, y + 6.5 * s),
              (x + 22 * s, y + 2.6 * s), (x, y + 1.6 * s)]), (0.55, 0.34, 0.18), tohum=3, golge=0.2)
    for xx in (8, 13, 18):
        B.dolgu(daire(x + xx * s, y, 0.9 * s), (0.15, 0.1, 0.08))
    c.restore()


def fener(c, f, x, y, t, s=1.0, renk=(0.95, 0.40, 0.20), i=0):
    salla = math.sin(t * 1.6 + i) * 4
    c.save()
    c.rotate(salla, x, y - 14 * s)
    c.drawCircle(x, y, 46 * s, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        skia.Point(x, y), 46 * s, [renk4((1.0, 0.85, 0.5), 0.5).toColor(), renk4((1.0, 0.8, 0.5), 0.0).toColor()]),
        BlendMode=skia.BlendMode.kScreen))
    f.boya(c, elips(x, y, 9 * s, 12 * s), renk, murekkep=0.8, golge=0.2, cizgi=1.6, kenar_gen=4, tohum=i)
    f.yumusak(c, elips(x, y, 5 * s, 8 * s), (1.0, 0.95, 0.6), 0.75, 3 * s)
    f.cizgi(c, egri([(x, y - 12 * s), (x, y - 20 * s)], False), 1.4)
    c.restore()


def bayraklar(c, f, x0, y0, x1, y1, sarkma=40, n=12, t=0.0, tohum=2):
    renkler = [(0.80, 0.20, 0.16), (0.95, 0.75, 0.25), (0.25, 0.45, 0.65), (0.30, 0.55, 0.30), (0.95, 0.95, 0.88)]
    ip = []
    for i in range(41):
        u = i / 40
        ip.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + sarkma * 4 * u * (1 - u)))
    f.cizgi(c, egri(ip, False), 1.6, 0.8)
    for i in range(n):
        u = (i + 0.5) / n
        px = x0 + (x1 - x0) * u
        py = y0 + (y1 - y0) * u + sarkma * 4 * u * (1 - u)
        sal = math.sin(t * 2.2 + i) * 2.5
        f.boya(c, cokgen([(px - 13, py), (px + 13, py), (px + sal, py + 30)]), renkler[(i + tohum) % 5],
               murekkep=0.7, golge=0.1, cizgi=1.4, kenar_gen=4, leke_sayi=0, tohum=i)


def gum_yazisi(c, x, y, u, metin="GÜM!"):
    """Patlama yildizi icinde cizgi roman yansima sesi."""
    if u <= 0:
        return
    s = 0.6 + 0.6 * yumusak(min(1.0, u * 3)) - 0.15 * max(0.0, u - 0.6)
    a = 1.0 if u < 0.75 else max(0.0, 1 - (u - 0.75) / 0.25)
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.rotate(-8)
    yol = skia.Path()
    for i in range(24):
        aa = i * math.pi / 12
        rr = 170 if i % 2 == 0 else 105
        (yol.moveTo if i == 0 else yol.lineTo)(math.cos(aa) * rr * 1.2, math.sin(aa) * rr * 0.75)
    yol.close()
    c.drawPath(yol, skia.Paint(AntiAlias=True, Color4f=renk4((1.0, 0.86, 0.30), 0.95 * a)))
    c.drawPath(yol, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4,
                               Color4f=renk4(MUREKKEP, 0.9 * a)))
    ft = font("Cinzel.ttf", 120)
    gen = ft.measureText(metin)
    c.drawString(metin, -gen / 2 + 5, 46, ft, skia.Paint(AntiAlias=True, Color4f=renk4((0.25, 0.08, 0.05), 0.5 * a)))
    c.drawString(metin, -gen / 2, 40, ft, skia.Paint(AntiAlias=True, Color4f=renk4((0.80, 0.14, 0.10), a)))
    c.drawString(metin, -gen / 2, 40, ft, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                                                     Color4f=renk4(MUREKKEP, a)))
    c.restore()


def ter_damlasi(c, f, x, y, t, i=0):
    ph = (t * 1.2 + i * 0.5) % 1.0
    yy = y + ph * 26
    a = 1 - ph
    f.boya(c, egri([(x, yy - 6), (x + 3.5, yy + 1), (x, yy + 4), (x - 3.5, yy + 1)]), (0.70, 0.85, 0.98), alfa=a,
           murekkep=0.6 * a, golge=0.0, cizgi=1.2, kenar_gen=2, leke_sayi=0)


# ================================================================ dekor (statik resim)
def cimen_tutamlari(c, f, kutu, n=120, renk=(0.30, 0.45, 0.20), tohum=1, boy=(10, 22), alfa=0.6):
    rng = np.random.default_rng(tohum)
    x0, y0, x1, y1 = kutu
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        h = rng.uniform(*boy) * (0.6 + 0.4 * (y - y0) / max(1, y1 - y0))
        for j in range(3):
            a = rng.uniform(-0.5, 0.5)
            f.cizgi(c, egri([(x + j * 3, y), (x + j * 3 + a * h * 0.5, y - h * 0.6), (x + j * 3 + a * h, y - h)], False),
                    1.6, alfa, renk=koyu(renk, rng.uniform(0.7, 1.1)), tohum=int(rng.integers(1000)), titrek=0.3)


def cicekler(c, f, kutu, n=40, renkler=((0.95, 0.85, 0.30), (0.95, 0.95, 0.92), (0.88, 0.35, 0.40)), tohum=2):
    rng = np.random.default_rng(tohum)
    x0, y0, x1, y1 = kutu
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.uniform(2.5, 4.5)
        rk = renkler[int(rng.integers(len(renkler)))]
        for j in range(5):
            a = j * 2 * math.pi / 5
            c.drawCircle(x + math.cos(a) * r, y + math.sin(a) * r, r * 0.8,
                         skia.Paint(AntiAlias=True, Color4f=renk4(rk, 0.9)))
        c.drawCircle(x, y, r * 0.6, skia.Paint(AntiAlias=True, Color4f=renk4((0.95, 0.65, 0.20), 0.95)))


def agac_yuvarlak(c, f, x, y, s=1.0, yesil=(0.36, 0.52, 0.26), tohum=1, gece=0.0, govde_renk=(0.42, 0.29, 0.18)):
    """Yuvarlak tepeli agac: govde + ust uste binen yaprak kumeleri."""
    rng = np.random.default_rng(tohum)
    f.boya(c, egri([(x - 9 * s, y), (x - 7 * s, y - 70 * s), (x - 14 * s, y - 110 * s), (x - 4 * s, y - 100 * s),
                    (x + 2 * s, y - 120 * s), (x + 8 * s, y - 98 * s), (x + 16 * s, y - 112 * s), (x + 8 * s, y - 70 * s),
                    (x + 11 * s, y)]), govde_renk, murekkep=0.85, golge=0.35, tohum=tohum, cizgi=2.2)
    kumeler = []
    for i in range(9):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0, 1) ** 0.5
        kumeler.append((x + math.cos(a) * 52 * s * r, y - 150 * s + math.sin(a) * 42 * s * r, rng.uniform(30, 46) * s))
    kumeler.sort(key=lambda q: q[1])
    for i, (kx, ky, kr) in enumerate(kumeler):
        ton = karistir_renk(yesil, rng.uniform(0.82, 1.12), gece)
        f.boya(c, leke(kx, ky, kr, kr * 0.85, tohum * 31 + i, 0.14), ton, murekkep=0.75, golge=0.35, golge_yon=(6, 8),
               parlak=0.25 * (1 - gece), tohum=tohum * 17 + i, cizgi=2.0, kenar_gen=10)


def karistir_renk(r, k, gece=0.0):
    out = tuple(min(1.0, v * k) for v in r)
    if gece:
        gc = (0.10, 0.14, 0.24)
        out = tuple(o * (1 - 0.6 * gece) + g * 0.6 * gece for o, g in zip(out, gc))
    return out


def kavak(c, f, x, y, s=1.0, yesil=(0.40, 0.55, 0.28), tohum=1, gece=0.0):
    f.boya(c, dikdortgen(x - 3 * s, y - 40 * s, x + 3 * s, y, 2), (0.40, 0.30, 0.20), murekkep=0.8, cizgi=1.8, tohum=tohum)
    f.boya(c, egri([(x, y - 230 * s), (x + 18 * s, y - 160 * s), (x + 20 * s, y - 80 * s), (x + 10 * s, y - 36 * s),
                    (x - 10 * s, y - 36 * s), (x - 20 * s, y - 80 * s), (x - 17 * s, y - 160 * s)]),
           karistir_renk(yesil, 1.0, gece), murekkep=0.75, golge=0.35, golge_yon=(5, 6), cizgi=2.0, tohum=tohum + 1)


def cinar(c, f, x, y, s=1.0, gece=0.0, tohum=5):
    """Koca cinar: kalin, kokleri yayilan govde, genis dallar, kat kat yaprak kumeleri."""
    gr = karistir_renk((0.45, 0.33, 0.22), 1.0, gece * 0.7)
    govde = egri([(x - 70 * s, y + 6 * s), (x - 42 * s, y - 20 * s), (x - 34 * s, y - 160 * s), (x - 60 * s, y - 250 * s),
                  (x - 150 * s, y - 330 * s), (x - 130 * s, y - 345 * s), (x - 40 * s, y - 280 * s), (x - 10 * s, y - 330 * s),
                  (x + 20 * s, y - 400 * s), (x + 38 * s, y - 390 * s), (x + 22 * s, y - 300 * s), (x + 60 * s, y - 270 * s),
                  (x + 170 * s, y - 320 * s), (x + 180 * s, y - 300 * s), (x + 50 * s, y - 230 * s), (x + 34 * s, y - 150 * s),
                  (x + 44 * s, y - 20 * s), (x + 78 * s, y + 6 * s)])
    f.boya(c, govde, gr, murekkep=0.9, golge=0.4, golge_yon=(10, 6), tohum=tohum, cizgi=2.6, kenar_gen=14)
    rng = np.random.default_rng(tohum)
    for i in range(14):                                    # kabuk lekeleri
        px, py = x + rng.uniform(-28, 30) * s, y - rng.uniform(20, 230) * s
        f.yumusak(c, leke(px, py, rng.uniform(6, 12) * s, rng.uniform(10, 20) * s, i, 0.2),
                  (0.75, 0.68, 0.55) if rng.uniform() < 0.5 else koyu(gr, 0.7), 0.35, 3 * s)
    kumeler = []
    for i in range(26):
        a = rng.uniform(math.pi * 1.0, math.pi * 2.0)
        r = rng.uniform(0.15, 1.0) ** 0.6
        kumeler.append((x + math.cos(a) * 300 * s * r, y - 330 * s + math.sin(a) * 160 * s * r + rng.uniform(-20, 40) * s,
                        rng.uniform(60, 100) * s))
    kumeler.sort(key=lambda q: q[1])
    yesil = (0.34, 0.50, 0.24)
    for i, (kx, ky, kr) in enumerate(kumeler):
        ton = karistir_renk(yesil, rng.uniform(0.8, 1.15), gece)
        f.boya(c, leke(kx, ky, kr, kr * 0.75, tohum * 13 + i, 0.16), ton, murekkep=0.7, golge=0.38, golge_yon=(10, 12),
               parlak=0.22 * (1 - gece), tohum=tohum * 19 + i, cizgi=2.1, kenar_gen=14)


def ev(c, f, x, y, s=1.0, gece=0.0, kapi_bosluk=True, tohum=3):
    """Anadolu koy evi: tas temel, badanali duvar, kiremit cati, ahsap pencere, baca.

    (x, y) zemin hizasinda duvarin sol alt kosesi; genislik ~360*s.
    Kapi boslugu: (x+150*s, y-150*s)..(x+222*s, y) — kapinin kendisi ayri cizilir.
    """
    def g(r):
        return karistir_renk(r, 1.0, gece)
    gw = 360 * s
    # cati altindaki golge ve duvar
    f.boya(c, cokgen([(x, y), (x, y - 220 * s), (x + gw, y - 220 * s), (x + gw, y)]), g((0.93, 0.88, 0.78)),
           murekkep=0.9, golge=0.3, golge_yon=(0, 26), tohum=tohum, cizgi=2.4, kenar_gen=16)
    # tas temel
    for i in range(16):
        px = x + (i % 8) * gw / 8 + (gw / 16 if i >= 8 else 0)
        py = y - (12 if i < 8 else 34) * s
        f.boya(c, leke(px + gw / 16, py, gw / 17, 11 * s, i, 0.18), g((0.66, 0.62, 0.56)), murekkep=0.6, golge=0.25,
               tohum=tohum + 10 + i, cizgi=1.6, kenar_gen=6, leke_sayi=0)
    # ahsap hatil
    f.boya(c, dikdortgen(x - 6 * s, y - 112 * s, x + gw + 6 * s, y - 102 * s, 2), g(koyu(AHSAP, 0.85)), murekkep=0.8,
           golge=0.2, tohum=tohum + 30, cizgi=1.8)
    # kapi boslugu
    if kapi_bosluk:
        f.boya(c, dikdortgen(x + 150 * s, y - 152 * s, x + 222 * s, y, 3), g((0.20, 0.14, 0.10)), murekkep=0.9,
               golge=0.0, tohum=tohum + 31)
        f.boya(c, dikdortgen(x + 144 * s, y - 160 * s, x + 228 * s, y - 150 * s, 2), g(koyu(AHSAP, 0.8)), murekkep=0.8,
               golge=0.2, tohum=tohum + 32)
    # pencere
    f.boya(c, dikdortgen(x + 40 * s, y - 175 * s, x + 110 * s, y - 120 * s, 3), g((0.25, 0.30, 0.38)) if not gece else (0.95, 0.75, 0.40),
           murekkep=0.9, golge=0.1, tohum=tohum + 33)
    f.cizgi(c, egri([(x + 75 * s, y - 175 * s), (x + 75 * s, y - 120 * s)], False), 3.0)
    f.cizgi(c, egri([(x + 40 * s, y - 148 * s), (x + 110 * s, y - 148 * s)], False), 2.4)
    for d in (-1, 1):
        bx = x + 75 * s + d * 52 * s
        f.boya(c, dikdortgen(bx - 17 * s, y - 178 * s, bx + 17 * s, y - 117 * s, 2), g((0.30, 0.48, 0.55)), murekkep=0.85,
               golge=0.2, tohum=tohum + 34 + d)
    # saksilar (sardunya)
    for i, px in enumerate((x + 262 * s, x + 300 * s)):
        f.boya(c, cokgen([(px - 12 * s, y - 30 * s), (px + 12 * s, y - 30 * s), (px + 9 * s, y), (px - 9 * s, y)]),
               g((0.75, 0.40, 0.25)), murekkep=0.8, golge=0.25, tohum=tohum + 40 + i, cizgi=1.8)
        f.boya(c, leke(px, y - 44 * s, 18 * s, 14 * s, i, 0.2), g((0.30, 0.50, 0.25)), murekkep=0.7, golge=0.3,
               tohum=tohum + 42 + i, cizgi=1.6)
        for j in range(4):
            c.drawCircle(px + (j - 1.5) * 8 * s, y - (50 + (j % 2) * 8) * s, 4.5 * s,
                         skia.Paint(AntiAlias=True, Color4f=renk4(g((0.90, 0.20, 0.25)), 0.95)))
    # baca
    f.boya(c, dikdortgen(x + 270 * s, y - 330 * s, x + 305 * s, y - 250 * s, 2), g((0.78, 0.72, 0.66)), murekkep=0.9,
           golge=0.3, tohum=tohum + 50)
    # cati
    cati = cokgen([(x - 34 * s, y - 214 * s), (x + gw / 2, y - 330 * s), (x + gw + 34 * s, y - 214 * s)])
    f.boya(c, cati, g((0.72, 0.32, 0.20)), murekkep=0.95, golge=0.35, golge_yon=(0, 14), tohum=tohum + 51, cizgi=2.6,
           kenar_gen=16)
    for i in range(1, 6):                                  # kiremit siralari
        u = i / 6
        y_ = y - 214 * s - (116 * s) * (1 - u)
        xa = x - 34 * s + (gw / 2 + 34 * s) * (1 - u)
        xb = x + gw + 34 * s - (gw / 2 + 34 * s) * (1 - u)
        pts = []
        for j, xx in enumerate(np.linspace(xa, xb, max(4, int((xb - xa) / (22 * s))))):
            pts.append((xx, y_ + (3 * s if j % 2 else 0)))
        f.cizgi(c, egri(pts, False), 1.4, 0.45, renk=(0.40, 0.14, 0.08))


def cit(c, f, x0, x1, y, s=1.0, gece=0.0, tohum=4):
    r = karistir_renk((0.60, 0.44, 0.28), 1.0, gece)
    for i, xx in enumerate(np.arange(x0, x1, 26 * s)):
        f.boya(c, cokgen([(xx - 5 * s, y), (xx - 5 * s, y - 60 * s), (xx, y - 68 * s), (xx + 5 * s, y - 60 * s), (xx + 5 * s, y)]),
               r, murekkep=0.8, golge=0.2, cizgi=1.8, tohum=tohum + i, kenar_gen=4, leke_sayi=0)
    for yy in (y - 45 * s, y - 20 * s):
        f.boya(c, dikdortgen(x0 - 6 * s, yy - 4 * s, x1, yy + 4 * s, 2), koyu(r, 0.9), murekkep=0.7, golge=0.15, cizgi=1.6,
               tohum=tohum + 99, kenar_gen=4)


def tepeler(c, f, katmanlar, gece=0.0):
    """katmanlar: [(noktalar, renk, tohum), ...] arkadan one."""
    for pts, renk, tohum in katmanlar:
        yol = egri(pts + [(2000, 1200), (-80, 1200)])
        f.boya(c, yol, karistir_renk(renk, 1.0, gece), murekkep=0.0, golge=0.25, golge_yon=(0, 18), kenar=0.55,
               kenar_gen=16, tohum=tohum, titrek=1.2)


def gokyuzu(c, f, ust, alt, y1=760, bulutlar=(), gece=0.0):
    f.degrade(c, dikdortgen(-20, -20, 1940, y1), ust, alt, 0, y1, doku=0.35, doku_olcek=3.5)
    for i, (x, y, rx, ry) in enumerate(bulutlar):
        renk = (1.0, 0.99, 0.96) if not gece else (0.55, 0.60, 0.72)
        for j in range(3):
            f.yumusak(c, leke(x + (j - 1) * rx * 0.45, y - (j == 1) * ry * 0.4, rx * (0.55 + 0.1 * j), ry, i * 7 + j, 0.2),
                      renk, 0.6 if not gece else 0.35, ry * 0.45)

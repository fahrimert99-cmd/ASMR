"""
Masallar için ortak sahne yardımcıları: manzara paletleri, küçük hayvanlar,
gece/ateş ışığı, kapak çerçevesi ve zaman yardımcıları.

    from masallar._ortak import ZEMIN, ara, lerp, manzara, tavuk, gece_tonu, ...
"""
import math

import numpy as np
import skia

from src import masal_cizim as C
from src.masal_motoru import H, W, daire, egri, isik, koyu, renk4, tam_ekran, cokgen

__all__ = ["ZEMIN", "ara", "lerp", "PALET", "manzara", "tavuk", "kurt", "baykus", "ates_feneri", "gece_tonu",
           "cerceve", "np", "math", "H", "W"]


ZEMIN = 785.0


# ================================================================ yardimcilar
def ara(t, a, b):
    return min(max((t - a) / max(b - a, 1e-6), 0.0), 1.0)


def lerp(a, b, u):
    return a + (b - a) * u


PALET = {
    "sabah": dict(gok=((0.58, 0.77, 0.88), (0.98, 0.93, 0.82)), uzak=(0.66, 0.74, 0.72), orta=(0.60, 0.70, 0.45),
                  yakin=(0.52, 0.64, 0.33), yol=(0.88, 0.78, 0.60)),
    "ikindi": dict(gok=((0.60, 0.72, 0.86), (0.99, 0.86, 0.66)), uzak=(0.72, 0.70, 0.64), orta=(0.64, 0.66, 0.42),
                   yakin=(0.58, 0.60, 0.32), yol=(0.88, 0.74, 0.54)),
    "aksam": dict(gok=((0.30, 0.25, 0.47), (0.98, 0.62, 0.36)), uzak=(0.50, 0.38, 0.52), orta=(0.38, 0.36, 0.42),
                  yakin=(0.28, 0.32, 0.28), yol=(0.62, 0.50, 0.44)),
    "gece": dict(gok=((0.10, 0.12, 0.26), (0.26, 0.30, 0.46)), uzak=(0.22, 0.26, 0.38), orta=(0.18, 0.25, 0.30),
                 yakin=(0.16, 0.24, 0.22), yol=(0.36, 0.34, 0.36)),
    "safak": dict(gok=((0.54, 0.62, 0.86), (1.00, 0.80, 0.62)), uzak=(0.72, 0.66, 0.74), orta=(0.62, 0.67, 0.48),
                  yakin=(0.52, 0.63, 0.34), yol=(0.90, 0.77, 0.60)),
    "gunbatimi": dict(gok=((0.50, 0.50, 0.72), (1.00, 0.74, 0.44)), uzak=(0.66, 0.54, 0.58), orta=(0.60, 0.60, 0.40),
                      yakin=(0.50, 0.57, 0.31), yol=(0.88, 0.70, 0.52)),
}


def manzara(c, f, palet, ufuk=560, bulutlar=None, yol=None, cimen=True, tohum=1):
    P = PALET[palet]
    if bulutlar is None:
        bulutlar = [(300, 150, 170, 42), (1250, 110, 230, 50), (1700, 230, 130, 32)]
    gece = 1.0 if palet == "gece" else 0.0
    C.gokyuzu(c, f, *P["gok"], y1=ufuk + 260, bulutlar=bulutlar, gece=gece)
    C.tepeler(c, f, [
        ([(-80, ufuk - 30), (240, ufuk - 95), (520, ufuk - 40), (860, ufuk - 110), (1180, ufuk - 50), (1500, ufuk - 120),
          (1800, ufuk - 60), (2000, ufuk - 80)], P["uzak"], tohum),
        ([(-80, ufuk + 40), (300, ufuk - 10), (700, ufuk + 50), (1100, ufuk), (1500, ufuk + 60), (2000, ufuk + 10)],
         P["orta"], tohum + 1),
        ([(-80, ZEMIN - 70), (500, ZEMIN - 110), (1000, ZEMIN - 80), (1500, ZEMIN - 120), (2000, ZEMIN - 90)],
         P["yakin"], tohum + 2),
    ])
    if yol:
        f.boya(c, egri(yol), P["yol"], murekkep=0.0, golge=0.2, golge_yon=(0, 10), kenar=0.45, kenar_gen=12,
               tohum=tohum + 5, titrek=1.0)
    if cimen:
        C.cimen_tutamlari(c, f, (-40, ZEMIN - 90, 1960, ZEMIN + 30), n=160, renk=koyu(P["yakin"], 0.7),
                          tohum=tohum + 3, alfa=0.5 if not gece else 0.35)
    if palet in ("sabah", "ikindi", "safak", "gunbatimi"):
        C.cicekler(c, f, (-40, ZEMIN - 70, 1960, ZEMIN + 20), n=45, tohum=tohum + 4)


def tavuk(c, f, x, y, t, s=1.0, yon=1, tohum=0):
    gaga = max(0.0, math.sin(t * 2.6 + tohum * 1.9)) ** 6         # ara sira yem gagalama
    c.save()
    c.translate(x, y)
    c.scale(yon * s, s)
    C.golge_zemin(c, f, 0, 1, 22, 0.2)
    f.boya(c, egri([(-22, -18), (-6, -30), (14, -26), (20, -14), (12, -2), (-14, -2), (-26, -12)]), (0.96, 0.94, 0.88),
           murekkep=0.85, golge=0.25, golge_yon=(3, 3), cizgi=2.0, kenar_gen=5, tohum=tohum)
    f.boya(c, egri([(-24, -16), (-34, -30), (-30, -12)]), (0.90, 0.86, 0.78), murekkep=0.8, golge=0.1, cizgi=1.8,
           kenar_gen=4, tohum=tohum + 1)
    c.save()
    c.rotate(gaga * 55, 10, -24)
    f.boya(c, daire(16, -34, 8), (0.96, 0.94, 0.88), murekkep=0.85, golge=0.2, cizgi=2.0, kenar_gen=4, tohum=tohum + 2)
    f.boya(c, egri([(12, -42), (15, -48), (18, -43), (21, -47), (22, -40)]), (0.86, 0.18, 0.15), murekkep=0.7,
           golge=0.0, cizgi=1.6, kenar_gen=3, leke_sayi=0, tohum=tohum + 3)
    f.boya(c, cokgen([(23, -35), (30, -33), (23, -30)]), (0.95, 0.70, 0.20), murekkep=0.7, golge=0, cizgi=1.4,
           kenar_gen=2, leke_sayi=0)
    c.drawCircle(18, -36, 1.6, skia.Paint(AntiAlias=True, Color4f=renk4((0.1, 0.07, 0.05))))
    c.restore()
    for d in (-5, 5):
        f.cizgi(c, egri([(d, -3), (d + 1, 6)], False), 2.0, 0.9, renk=(0.85, 0.60, 0.20))
    c.restore()


def kurt(c, f, x, y, s=1.0, ulu=0.0):
    """Uzak tepede uluyan kurt silueti."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    b = -ulu * 10
    yol = egri([(-40, 0), (-38, -26), (-20, -34), (10, -34), (22, -40), (30, -56 + b), (34, -66 + b), (40, -60 + b),
                (38, -46), (30, -32), (32, 0), (26, 0), (22, -20), (-18, -20), (-24, 0), (-30, 0), (-34, -18), (-48, -14)])
    c.drawPath(yol, skia.Paint(AntiAlias=True, Color4f=renk4((0.16, 0.12, 0.20), 0.92)))
    c.restore()


def baykus(c, f, x, y, t, s=1.0):
    goz = C.goz_kirp(t, 3, 4.1)
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    f.boya(c, egri([(-18, 0), (-20, -30), (-12, -46), (0, -42), (12, -46), (20, -30), (18, 0)]), (0.50, 0.40, 0.32),
           murekkep=0.85, golge=0.3, cizgi=2.0, kenar_gen=5, tohum=3)
    for d in (-1, 1):
        f.boya(c, daire(d * 8, -30, 7), (0.95, 0.88, 0.62), murekkep=0.8, golge=0.1, cizgi=1.6, kenar_gen=3, leke_sayi=0)
        c.drawOval(skia.Rect(d * 8 - 3, -30 - 3.5 * goz, d * 8 + 3, -30 + 3.5 * goz),
                   skia.Paint(AntiAlias=True, Color4f=renk4((0.1, 0.07, 0.05))))
    f.boya(c, cokgen([(-3, -24), (3, -24), (0, -18)]), (0.90, 0.65, 0.25), murekkep=0.6, golge=0, cizgi=1.2, kenar_gen=2)
    c.restore()


def ates_feneri(c, x, y, r, t, guc=1.0):
    """Atesin cevreye vurdugu titrek sicak isik."""
    tit = 1.0 + 0.06 * math.sin(t * 11) + 0.04 * math.sin(t * 17.3)
    isik(c, x, y, r * tit, (1.0, 0.62, 0.28), 0.42 * guc)
    isik(c, x, y, r * 0.45 * tit, (1.0, 0.75, 0.40), 0.35 * guc, mod=skia.BlendMode.kPlus)


def gece_tonu(c, guc=1.0):
    tam_ekran(c, (0.50, 0.56, 0.86), guc, skia.BlendMode.kMultiply)


def cerceve(c):
    """Kapak ve son sayfadaki suslu cift cizgi cerceve."""
    cer = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                     Color4f=renk4((0.55, 0.16, 0.10), 0.75))
    c.drawRect(skia.Rect(26, 26, W - 26, H - 26), cer)
    cer.setStrokeWidth(1.4)
    c.drawRect(skia.Rect(38, 38, W - 38, H - 38), cer)
    for (kx, ky) in ((38, 38), (W - 38, 38), (38, H - 38), (W - 38, H - 38)):
        for r in (16, 9):
            c.drawCircle(kx, ky, r, skia.Paint(AntiAlias=True, Color4f=renk4((0.97, 0.93, 0.82))))
            c.drawCircle(kx, ky, r, cer)



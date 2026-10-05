"""
Keloğlan ile Kapı — Anadolu halk masalı (ATU 1009 + 1653: "kapıyı çek" ve
"ağaç altındaki haramiler"). Kamu malı; metin bu video için yeniden anlatıldı.

Keloğlan, anasının "kapıyı çek" sözünü harfiyen anlar: kapıyı menteşesinden
söküp sırtlar. Gece ormanda çınara tırmanırlar; kapı, ağacın dibinde altın
sayan üç haraminin tepesine düşer, haramiler altınları bırakıp kaçar.
"""
import math

import numpy as np
import skia

from src import masal_cizim as C
from src.masal_motoru import (H, W, daire, dikdortgen, egri, isik, koyu, leke, renk4,
                              tam_ekran, yumusak, cokgen, font)

BASLIK = "Keloğlan ile Kapı"
ALT_BASLIK = "Bir Anadolu masalı"
YOUTUBE = dict(
    baslik="Keloğlan ile Kapı | Resimli Masal (Anadolu Halk Masalı)",
    aciklama=("Anasının \"kapıyı çek\" sözünü harfiyen anlayan Keloğlan, kapıyı menteşesinden söküp sırtına "
              "vurur... Ormanda bir çınar, ağacın dibinde altın sayan üç harami ve tepelerine düşen bir kapı! "
              "Resimli kitap üslubunda, tamamen kodla çizilen ve canlandırılan bir Anadolu masalı."),
    etiketler=["Keloğlan", "masal", "Keloğlan masalları", "çocuk masalları", "resimli masal", "Anadolu masalları",
               "Türk masalları", "uyku masalı", "masal dinle"],
)

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


# ================================================================ sayfalar
class Kapak:
    """Kitap kapagi: tepedeki patikada kapisini sirtlamis Keloglan, ust kurdelede baslik."""

    def arka(self, c, f):
        manzara(c, f, "sabah", ufuk=520,
                yol=[(-60, 1100), (500, 900), (800, 800), (1000, 720), (1300, 640), (1600, 600), (1700, 610),
                     (1350, 670), (1080, 760), (900, 860), (700, 1000), (500, 1100)], tohum=11)
        for i, x in enumerate((1480, 1560, 1640)):                 # uzakta koy
            C.ev(c, f, x, 560 - i * 6, 0.2, kapi_bosluk=True, tohum=40 + i)
        for i, x in enumerate((120, 190, 1820, 1880)):
            C.kavak(c, f, x, 680 + (i % 2) * 10, 1.0, tohum=20 + i)
        C.agac_yuvarlak(c, f, 330, 800, 1.5, tohum=5)

    def on(self, c, f, t, d):
        C.kuslar(c, f, 820, 210, t, n=3, s=1.2, hiz=40, tohum=2)
        faz = t * 4.2
        x = lerp(820, 940, ara(t, 0.0, 6.5))
        y = 868 - (x - 820) * 0.42
        C.keloglan(c, f, x, y, 330, poz=dict(C.yuru(faz, 0.8), **C.TASI, goz=C.goz_kirp(t), mutlu_goz=False),
                   sirtta=C.kapi_sirtta())

    def ust(self, c, f, t, d):
        a = yumusak(ara(t, 0.5, 1.8))
        if a <= 0:
            return
        c.saveLayerAlpha(None, int(255 * a))
        # kurdele
        x0, x1, y0 = 470, 1450, 70
        for dd in (-1, 1):
            ux = x0 - 40 if dd < 0 else x1 + 40
            ic = x0 + 30 if dd < 0 else x1 - 30
            f.boya(c, cokgen([(ic, y0 + 40), (ux, y0 + 40), (ux + dd * -0 - dd * 50, y0 + 105), (ux, y0 + 170),
                              (ic, y0 + 170)]), (0.66, 0.16, 0.12), murekkep=0.9, golge=0.3, tohum=3 + dd, cizgi=2.4)
        f.boya(c, egri([(x0, y0 + 10), (960, y0 - 18), (x1, y0 + 10), (x1, y0 + 150), (960, y0 + 122), (x0, y0 + 150)]),
               (0.97, 0.93, 0.82), murekkep=0.95, golge=0.25, golge_yon=(0, 8), tohum=7, cizgi=2.6, kenar_gen=12)
        ft = font("Cinzel.ttf", 84)
        metin = "KELOĞLAN İLE KAPI"
        gen = ft.measureText(metin)
        c.drawString(metin, 960 - gen / 2 + 3, y0 + 98, ft, skia.Paint(AntiAlias=True, Color4f=renk4((0.3, 0.1, 0.05), 0.35)))
        c.drawString(metin, 960 - gen / 2, y0 + 95, ft, skia.Paint(AntiAlias=True, Color4f=renk4((0.58, 0.14, 0.09))))
        fi = font("EBGaramond-Italic.ttf", 44)
        alt = "Bir Anadolu masalı"
        g2 = fi.measureText(alt)
        c.drawString(alt, 960 - g2 / 2, y0 + 228, fi, skia.Paint(AntiAlias=True, Color4f=renk4((0.25, 0.16, 0.10), 0.9)))
        c.restore()
        cerceve(c)


class Ev:
    """Sayfa 1: koyun kiyisindaki ev; Keloglan el sallar, anasi tavuklara yem atar."""
    EVX = 980

    def arka(self, c, f):
        manzara(c, f, "sabah", ufuk=540, tohum=21)
        for i, x in enumerate((90, 160, 1760, 1840)):
            C.kavak(c, f, x, 640, 1.1, tohum=30 + i)
        C.agac_yuvarlak(c, f, 300, ZEMIN + 5, 1.35, tohum=9)
        C.cit(c, f, 520, 930, ZEMIN - 10, 1.0, tohum=12)
        C.ev(c, f, self.EVX, ZEMIN - 15, 1.0, tohum=3)
        C.cit(c, f, 1370, 1700, ZEMIN - 10, 1.0, tohum=14)

    def on(self, c, f, t, d):
        x = self.EVX
        C.duman(c, f, x + 287, ZEMIN - 15 - 335, t, 1.0)
        C.kapi(c, f, x + 150, ZEMIN - 15 - 152, 72, 152, k=1.0)
        C.kuslar(c, f, 300, 170, t, n=3, s=1.1, hiz=35, tohum=4)
        for i, (tx, ty, yon) in enumerate(((470, 800, 1), (560, 812, -1), (640, 798, 1))):
            tavuk(c, f, tx + math.sin(t * 0.7 + i) * 6, ty, t, 0.8, yon, tohum=i)
        # ana: yem serper
        kol = 40 + 50 * max(0.0, math.sin(t * 2.4))
        C.ana(c, f, 750, ZEMIN + 12, 262, poz=dict(kol_on=(kol, -40), goz=C.goz_kirp(t, 1), agiz=C.konus_agiz(t, False)))
        for j in range(6):                                          # yem taneleri
            ph = (t * 1.2 + j / 6) % 1.0
            c.drawCircle(700 - ph * 120 + j * 6, 690 + ph * 110 + (ph ** 2) * 20, 2.2,
                         skia.Paint(AntiAlias=True, Color4f=renk4((0.92, 0.80, 0.40), 1 - ph)))
        salla = 150 + 25 * math.sin(t * 6)
        C.keloglan(c, f, 905, ZEMIN + 16, 285, poz=dict(kol_on=(salla, -30), goz=C.goz_kirp(t), bas=4 * math.sin(t * 1.3)),
                   yon=-1)


class EvYakin:
    """Ev kapisinin onu (orta plan) — 2, 3 ve 4. sayfalarin ortak arka plani."""
    EVX, EVS = 470, 1.75

    def kapi_kutusu(self):
        x, s = self.EVX, self.EVS
        return x + 150 * s, ZEMIN - 152 * s, 72 * s, 152 * s

    def arka(self, c, f):
        manzara(c, f, "sabah", ufuk=520, yol=[(1150, 1100), (1300, 760), (1500, 620), (1700, 560), (1760, 565),
                                               (1560, 640), (1420, 780), (1330, 1100)], tohum=31)
        C.kavak(c, f, 1640, 600, 0.7, tohum=33)
        C.kavak(c, f, 1700, 590, 0.6, tohum=34)
        C.agac_yuvarlak(c, f, 1840, ZEMIN, 1.3, tohum=35)
        C.ev(c, f, self.EVX, ZEMIN, self.EVS, tohum=3)
        # esik tasi
        x, y, w, h = self.kapi_kutusu()
        f.boya(c, dikdortgen(x - 18, ZEMIN - 6, x + w + 18, ZEMIN + 12, 4), (0.70, 0.66, 0.60), murekkep=0.8, golge=0.25,
               tohum=36)


class Veda(EvYakin):
    """Sayfa 2: anasi bohcasiyla dugune gider, parmagini sallayarak tembihler."""

    def on(self, c, f, t, d):
        x, y, w, h = self.kapi_kutusu()
        C.kapi(c, f, x, y, w, h, k=1.0)
        konusan = d["konusan"]
        bitis = d["sure"] - 2.2
        git = ara(t, bitis, d["sure"])
        if konusan == "ana":
            kol = (150 + 12 * math.sin(t * 9), -50)
        else:
            kol = (30, -40)
        ax = 1240 + git * 260
        poz = dict(kol_on=kol, goz=C.goz_kirp(t, 2), agiz=C.konus_agiz(t, konusan == "ana"), ifade="gul",
                   bas=-3 + 3 * math.sin(t * 2))
        if git > 0:
            poz.update(kol_on=(20, -30))
        C.ana(c, f, ax, ZEMIN + 4, 300, poz=poz, yon=-1 if git < 0.15 else 1, elde=C.bohca() if git <= 0 else None,
              yuru_faz=t * 6 if git > 0 else None)
        if git > 0:                                                # bohca diger elde
            pass
        bas_sall = 6 * math.sin(t * 5) if konusan == "ana" else 2 * math.sin(t)
        C.keloglan(c, f, 1010, ZEMIN + 6, 320, poz=dict(goz=C.goz_kirp(t), bas=bas_sall, kol_on=(15, -20)), yon=1)


class CanSikintisi(EvYakin):
    """Sayfa 3: anasi uzaklasir; esikte oturan Keloglan davul-zurnayi hayal eder."""

    def on(self, c, f, t, d):
        x, y, w, h = self.kapi_kutusu()
        C.kapi(c, f, x, y, w, h, k=1.0)
        u = ara(t, 0, d["sure"])
        C.ana(c, f, lerp(1560, 1700, u), lerp(612, 575, u), lerp(70, 52, u), poz=dict(), yon=1, yuru_faz=t * 5)
        konusan = d["konusan"] == "kel"
        hayal = ara(t, d["cumle_t"][1] - 0.4, d["cumle_t"][1] + 0.4) if len(d["cumle_t"]) > 1 else 0
        ifade = "gul" if hayal > 0.5 else "kiz"
        C.keloglan(c, f, 1030, ZEMIN + 8, 320, poz=dict(zipla=17, bacak_on=(86, -84), bacak_arka=(80, -80),
                                                         kol_on=(40, -150) if hayal < 0.5 else (150 + 20 * math.sin(t * 7), -30),
                                                         kol_arka=(30, -60), govde=-4, bas=8 if hayal < 0.5 else -6,
                                                         goz=C.goz_kirp(t) * (0.6 if hayal < 0.5 else 1.0),
                                                         agiz=C.konus_agiz(t, konusan), ifade=ifade, bakis=0.6 * hayal))

        def icerik(c, f):
            C.davul(c, f, 1240, 300, 3.2)
            C.zurna(c, f, 1330, 300, -25, 3.2)
            for i in range(3):
                ph = (t * 0.8 + i / 3) % 1.0
                nx, ny = 1150 + i * 90, 260 - ph * 60
                c.drawCircle(nx, ny, 7, skia.Paint(AntiAlias=True, Color4f=renk4((0.2, 0.12, 0.08), 1 - ph)))
                f.cizgi(c, egri([(nx + 6, ny), (nx + 6, ny - 26), (nx + 16, ny - 20)], False), 2.4, 1 - ph)
        C.dusunce_balonu(c, f, 1260, 290, 330, 210, (1080, 470), alfa=hayal, icerik=icerik)


class KapiCekme(EvYakin):
    """Sayfa 4: Keloglan kapiyi ceker, ceker... kapi menteseden cikar; sirtlayip yola koyulur."""

    def on(self, c, f, t, d):
        x, y, w, h = self.kapi_kutusu()
        ct = d["cumle_t"] + [99, 99, 99]
        t_kop = ct[1]                       # "Kapi menteşesinden çıkıvermiş!"
        t_kalk = t_kop + 1.0
        t_sirt = t_kalk + 1.2
        t_yuru = max(ct[2] + 0.4, t_sirt + 0.2)
        kel_x = x + w + 95
        if t < t_kop:                                              # cekme
            cek = math.sin(t * 7.0)
            sars = 1.4 * cek if t > 0.5 else 0
            C.kapi(c, f, x, y, w, h, aci=sars, pivot=(x, y + h / 2), k=1.0)
            C.keloglan(c, f, kel_x + 6 * cek, ZEMIN + 6, 320,
                       poz=dict(kol_on=(92, -6), kol_arka=(86, -2), govde=-14 - 6 * cek, ifade="zor",
                                bacak_on=(22, 0), bacak_arka=(-18, 0), goz=1.0), yon=-1)
        elif t < t_kalk:                                           # kapi kopar, Keloglan popo ustu duser
            u = ara(t, t_kop, t_kop + 0.45)
            dx = 70 * yumusak(u)
            aci = -14 * yumusak(u)
            C.kapi(c, f, x + dx, y + 18 * u, w, h, aci=aci, pivot=(x + w, y + h), k=1.0)
            C.toz_bulutu(c, f, x + 20, y + h * 0.5, ara(t, t_kop, t_kop + 1.0), 0.6)
            C.keloglan(c, f, kel_x + 40 * yumusak(u), ZEMIN + 6, 320,
                       poz=dict(zipla=17 * yumusak(u), bacak_on=(80, -60), bacak_arka=(70, -55), govde=-24 * u,
                                kol_on=(120, 0), kol_arka=(110, 10), ifade="sasir"), yon=-1)
        elif t < t_sirt:                                           # kalkar, kapiyi kaldirir
            u = yumusak(ara(t, t_kalk, t_sirt))
            kx = kel_x + 40
            kapi_x = lerp(x + 70, kx - w * 0.62, u)
            kapi_y = lerp(y + 18, ZEMIN - 320 * 0.93 - 10, u)
            C.keloglan(c, f, kx, ZEMIN + 6, 320, poz=dict(kol_on=(lerp(60, 160, u), -10), kol_arka=(lerp(50, 150, u), -10),
                                                          ifade="gul", agiz=0.5), yon=-1)
            C.kapi(c, f, kapi_x, kapi_y, w, h, aci=lerp(-14, -6, u), k=1.0)
        else:                                                      # sirtta, yurur
            u = ara(t, t_yuru, d["sure"] + 1.0)
            kx = lerp(kel_x + 40, 1800, u)
            yuruyor = t > t_yuru
            poz = dict(C.TASI, goz=C.goz_kirp(t), agiz=C.konus_agiz(t, d["konusan"] == "kel"), ifade="gul")
            if yuruyor:
                poz.update(C.yuru(t * 6.5, 1.0))
                poz.update(kol_on=C.TASI["kol_on"], kol_arka=C.TASI["kol_arka"])
            C.keloglan(c, f, kx, ZEMIN + 6, 320, poz=poz, yon=1, sirtta=C.kapi_sirtta())


class Dugun:
    """Sayfa 5: dugun meydani — davul zurna, halay; anasi dizlerini dover, koy kahkahayla guler."""

    def arka(self, c, f):
        manzara(c, f, "ikindi", ufuk=500, bulutlar=[(400, 120, 180, 40), (1500, 150, 200, 44)], tohum=41)
        for i, (x, s) in enumerate(((60, 0.75), (1380, 0.8), (1700, 0.62))):
            C.ev(c, f, x, ZEMIN - 150 - i * 6, s, tohum=50 + i)
        C.agac_yuvarlak(c, f, 470, ZEMIN - 120, 1.6, tohum=55)
        f.boya(c, egri([(-60, ZEMIN - 60), (700, ZEMIN - 95), (1400, ZEMIN - 75), (1980, ZEMIN - 90), (1980, 1120),
                        (-60, 1120)]), (0.86, 0.76, 0.58), murekkep=0.0, golge=0.2, golge_yon=(0, 12), tohum=56,
               kenar_gen=14)

    def on(self, c, f, t, d):
        ct = d["cumle_t"] + [99, 99, 99]
        gul = ara(t, ct[2], ct[2] + 0.5)
        C.bayraklar(c, f, -20, 150, 980, 170, 70, 13, t, tohum=1)
        C.bayraklar(c, f, 940, 170, 1960, 140, 80, 13, t, tohum=3)
        for i, (fx, fy) in enumerate(((300, 250), (720, 268), (1210, 262), (1640, 240))):
            C.fener(c, f, fx, fy, t, 1.6, i=i)
        vurus = abs(math.sin(t * 2 * math.pi * 1.6))
        # muzisyenler (sol)
        C.koylu(c, f, 150, ZEMIN - 30, 250, tohum=61, sapka="fes",
                poz=dict(kol_on=(60 + 50 * vurus, -60), kol_arka=(70, -90), agiz=0.0, goz=C.goz_kirp(t, 4)))
        C.davul(c, f, 175, ZEMIN - 165, 3.0)
        C.koylu(c, f, 290, ZEMIN - 30, 245, tohum=62, poz=dict(kol_on=(120, -50), kol_arka=(115, -45), goz=0.6,
                                                               bas=-6 + 3 * math.sin(t * 3)))
        C.zurna(c, f, 318, ZEMIN - 205, -8 + 4 * math.sin(t * 3), 3.4)
        # halay
        for i in range(5):
            hx = 640 + i * 130
            adim = math.sin(t * 2 * math.pi * 0.8 + i * 0.3)
            poz = dict(kol_on=(80, -20), kol_arka=(-80, 20), bacak_on=(22 * max(0, adim), 0),
                       bacak_arka=(-10 * max(0, -adim), 0), zipla=-3 * max(0, adim), goz=C.goz_kirp(t, i))
            if gul > 0:
                poz.update(agiz=0.7 + 0.3 * math.sin(t * 16 + i), ifade="gul", mutlu_goz=True,
                           zipla=-4 * abs(math.sin(t * 12 + i)), kol_on=(30, -10), kol_arka=(-20, 10))
            C.koylu(c, f, hx, ZEMIN - 70, 200, kadin=(i % 2 == 1), tohum=70 + i, poz=poz,
                    sapka="fes" if i == 2 else "kasket")
        # ana: dizlerini dover
        dov = ct[0] <= t < ct[1]
        kol = (40 + 30 * abs(math.sin(t * 8)), -10) if dov else (30, -30)
        C.ana(c, f, 900, ZEMIN + 8, 300, poz=dict(kol_on=kol, kol_arka=kol, ifade="sasir" if t < ct[2] else "gul",
                                                   agiz=C.konus_agiz(t, d["konusan"] == "ana"),
                                                   govde=8 if dov else 0, goz=C.goz_kirp(t, 2)), yon=1)
        # keloglan gelir
        gel = ara(t, 0.0, max(ct[0] - 0.1, 0.5))
        kx = lerp(1700, 1220, yumusak(gel))
        poz = dict(C.TASI, ifade="gul", agiz=C.konus_agiz(t, d["konusan"] == "kel"), goz=C.goz_kirp(t))
        if gel < 1:
            poz.update(C.yuru(t * 6.5, 1.0))
            poz.update(kol_on=C.TASI["kol_on"], kol_arka=C.TASI["kol_arka"])
        if gul > 0:
            poz.update(zipla=-3 * abs(math.sin(t * 12)), mutlu_goz=True)
        C.keloglan(c, f, kx, ZEMIN + 8, 320, poz=poz, yon=-1, sirtta=C.kapi_sirtta())
        if gul > 0:                                                # sagda gulen iki koylu
            for i, hx in enumerate((1550, 1700)):
                C.koylu(c, f, hx, ZEMIN + 10, 285, kadin=i == 1, tohum=90 + i,
                        poz=dict(agiz=0.8, mutlu_goz=True, kol_on=(120, -40), zipla=-4 * abs(math.sin(t * 13 + i)),
                                 govde=-6), yon=-1)


class AksamOrman:
    """Sayfa 6: aksam, ormana dogru yuruyus; uzakta uluyan kurt; koca cinara tirmanis."""
    CX = 1380

    def arka(self, c, f):
        manzara(c, f, "aksam", ufuk=560, bulutlar=[(500, 200, 200, 30), (1300, 130, 260, 36)], cimen=True,
                yol=[(-60, 830), (500, 790), (1000, 805), (1400, 800), (1980, 820), (1980, 870), (1400, 850), (1000, 860),
                     (500, 845), (-60, 880)], tohum=61)
        isik(c, 640, 520, 260, (1.0, 0.75, 0.45), 0.55)
        f.boya(c, daire(640, 520, 62), (1.0, 0.82, 0.52), murekkep=0.0, golge=0, kenar=0.3, tohum=62)
        for i in range(14):                                        # orman silueti (kurdun tepesi bos)
            x = 60 + i * 140 + (i % 3) * 25
            if 150 < x < 420:
                continue
            C.agac_yuvarlak(c, f, x, 640 + (i % 2) * 12, 0.75 + 0.1 * (i % 3), yesil=(0.24, 0.26, 0.30), tohum=70 + i,
                            gece=0.4, govde_renk=(0.25, 0.20, 0.22))
        f.boya(c, egri([(120, 660), (220, 585), (300, 560), (380, 590), (470, 660)]), (0.30, 0.26, 0.34), murekkep=0.0,
               golge=0.2, tohum=63)
        C.cinar(c, f, self.CX, ZEMIN + 10, 0.95, gece=0.5, tohum=5)

    def dal(self):
        return self.CX - 150, ZEMIN - 245

    def on(self, c, f, t, d):
        ct = d["cumle_t"] + [99, 99]
        karar = ara(t, 0, d["sure"])
        kurt(c, f, 300, 566, 0.95, ulu=ara(t, 1.5, 2.2) * (1 - ara(t, 4.2, 4.8)))
        t_tir = ct[1] + 1.2
        t_bit = t_tir + 2.4
        yuru = ara(t, 0, t_tir)
        dx, dy = self.dal()
        if t < t_tir:
            kx = lerp(-80, self.CX - 220, yuru)
            C.ana(c, f, kx - 120, ZEMIN + 18, 215, poz=dict(goz=C.goz_kirp(t, 1)), yon=1, yuru_faz=t * 6)
            poz = dict(C.yuru(t * 6.5, 1.0), goz=C.goz_kirp(t), ifade="gul")
            poz.update(kol_on=C.TASI["kol_on"], kol_arka=C.TASI["kol_arka"])
            C.keloglan(c, f, kx, ZEMIN + 20, 235, poz=poz, yon=1, sirtta=C.kapi_sirtta())
        else:
            u = yumusak(ara(t, t_tir, t_bit))
            tir = dict(kol_on=(170 + 10 * math.sin(t * 8), -20), kol_arka=(160 - 10 * math.sin(t * 8), -20),
                       bacak_on=(30 * max(0, math.sin(t * 8)), 20), bacak_arka=(30 * max(0, -math.sin(t * 8)), 20))
            if u >= 1:
                tir = dict(zipla=17, bacak_on=(86, -84), bacak_arka=(80, -80), kol_on=(20, -10), goz=C.goz_kirp(t))
            C.kapi(c, f, dx - 130, dy - 26, 60, 125, aci=-78, pivot=(dx - 100, dy), k=1.0) if u >= 1 else None
            C.ana(c, f, lerp(self.CX - 340, dx - 20, u), lerp(ZEMIN + 18, dy + 8, u), lerp(215, 150, u),
                  poz=dict(goz=C.goz_kirp(t, 1), kol_on=(160, -20)) if u < 1 else dict(goz=C.goz_kirp(t, 1), zipla=12),
                  yon=1)
            C.keloglan(c, f, lerp(self.CX - 220, dx + 60, u), lerp(ZEMIN + 20, dy + 2, u), lerp(235, 160, u),
                       poz=dict(tir, ifade="gul"), yon=1, sirtta=C.kapi_sirtta() if u < 1 else None)
        tam_ekran(c, (0.42, 0.40, 0.66), 0.55 * karar, skia.BlendMode.kMultiply)
        if karar > 0.6:
            for i in range(8):                                     # atesbocekleri
                ph = (t * 0.3 + i * 0.13) % 1.0
                px = 300 + i * 190 + math.sin(t * 1.3 + i) * 30
                py = 700 - ph * 120 + math.cos(t * 1.7 + i) * 15
                isik(c, px, py, 14, (0.95, 1.0, 0.6), 0.8 * (karar - 0.6) / 0.4 * math.sin(ph * math.pi),
                     mod=skia.BlendMode.kPlus)


class GeceHaramiler:
    """Sayfa 7: gece yarisi cinarin dibine uc harami gelir, ates yakip altin sayar."""
    CX = 1380
    ATES = (880, 770)

    def arka(self, c, f):
        manzara(c, f, "gece", ufuk=560, bulutlar=[(600, 160, 220, 26), (1500, 230, 160, 22)], tohum=81)
        C.ay(c, f, 300, 170, 62)
        for i in range(14):
            x = 60 + i * 140 + (i % 3) * 25
            C.agac_yuvarlak(c, f, x, 640 + (i % 2) * 12, 0.75 + 0.1 * (i % 3), yesil=(0.16, 0.22, 0.30), tohum=70 + i,
                            gece=0.8, govde_renk=(0.14, 0.13, 0.18))
        C.cinar(c, f, self.CX, ZEMIN + 10, 0.95, gece=0.85, tohum=5)

    def on(self, c, f, t, d):
        ct = d["cumle_t"] + [99, 99]
        C.yildizlar(c, f, t, (0, 0, 1920, 480), n=70)
        dx, dy = self.CX - 150, ZEMIN - 245
        # agactakiler
        C.kapi(c, f, dx - 130, dy - 26, 60, 125, aci=-78, pivot=(dx - 100, dy), k=1.0)
        C.ana(c, f, dx - 20, dy + 8, 150, poz=dict(zipla=12, goz=C.goz_kirp(t, 1), bakis=-0.8, ifade="sasir"), yon=-1)
        C.keloglan(c, f, dx + 60, dy + 2, 160, poz=dict(zipla=17, bacak_on=(86, -84), bacak_arka=(80, -80),
                                                        goz=C.goz_kirp(t), bakis=-0.8, ifade="sasir"), yon=-1)
        baykus(c, f, self.CX + 250, ZEMIN - 330, t, 1.2)
        # haramiler
        gel = ara(t, ct[0], ct[0] + 3.0)
        ates_g = ara(t, ct[1], ct[1] + 1.6)
        sayim = t > ct[1] + 1.4
        ax, ay = self.ATES
        hedefler = [("sisman", ax - 170, 1), ("orta", ax + 175, -1), ("uzun", ax + 330, -1)]
        for i, (tip, hx, yon) in enumerate(hedefler):
            gx = lerp(-200 - i * 150, hx, yumusak(ara(gel, i * 0.12, 1.0)))
            oturdu = gel >= 1.0 and t > ct[1] - 0.3
            if not oturdu:
                poz = dict(C.yuru(t * 6 + i, 1.0), ifade="kiz")
                C.harami(c, f, gx, ZEMIN + 8, 300, tip, poz=poz, yon=1)
            else:
                kol = (70 + 25 * math.sin(t * 5 + i), -60) if sayim else (30, -20)
                C.harami(c, f, hx, ZEMIN + 8, 300, tip, oturuyor=True, yon=yon,
                         poz=dict(kol_on=kol, agiz=0.6 * abs(math.sin(t * 6 + i)) if sayim else 0.0,
                                  ifade="gul" if sayim else "kiz", goz=C.goz_kirp(t, 5 + i)))
        if ates_g > 0:
            C.ates(c, f, ax, ay, 1.1, t, guc=ates_g)
        if sayim:
            C.heybe(c, f, ax + 70, ZEMIN - 30, 1.6)
            C.altin_yigini(c, f, ax + 20, ZEMIN + 18, 1.6, n=30, t=t, tohum=4)
            ph = (t * 1.3) % 1.0                                     # havaya atilan sikke
            C.sikke(c, f, ax - 120, ZEMIN - 120 - math.sin(ph * math.pi) * 60, 1.4, aci=ph * 360)
        gece_tonu(c, 0.85)
        if ates_g > 0:
            ates_feneri(c, ax, ay - 40, 520, t, ates_g)


class Agacta:
    """Sayfa 8: agacta yakin cekim — Keloglan'in kollari uyusur, anasi susturur, kapi kayar."""
    DAL_Y = 640

    def arka(self, c, f):
        C.gokyuzu(c, f, (0.08, 0.10, 0.24), (0.20, 0.24, 0.40), y1=1100, bulutlar=[], gece=1.0)
        C.ay(c, f, 1650, 170, 70)
        rng = np.random.default_rng(3)
        for i in range(30):                                        # yaprak kumeleri cerceve
            a = rng.uniform(0, 2 * math.pi)
            if 0.2 < math.sin(a) < 0.9 and math.cos(a) > 0.3:
                continue
            r = rng.uniform(0.8, 1.05)
            x = 960 + math.cos(a) * 1150 * r
            y = 480 + math.sin(a) * 700 * r
            f.boya(c, leke(x, y, rng.uniform(150, 260), rng.uniform(110, 190), i, 0.15),
                   C.karistir_renk((0.22, 0.34, 0.22), rng.uniform(0.8, 1.1), 0.75), murekkep=0.6, golge=0.35,
                   golge_yon=(10, 12), tohum=100 + i, cizgi=2.2, kenar_gen=16)
        dal = egri([(-80, self.DAL_Y + 40), (500, self.DAL_Y + 10), (1100, self.DAL_Y + 30), (1700, self.DAL_Y - 10),
                    (2000, self.DAL_Y - 30), (2000, self.DAL_Y + 80), (1700, self.DAL_Y + 70), (1100, self.DAL_Y + 100),
                    (500, self.DAL_Y + 95), (-80, self.DAL_Y + 130)])
        f.boya(c, dal, (0.34, 0.27, 0.24), murekkep=0.9, golge=0.45, golge_yon=(0, 16), tohum=7, cizgi=2.6, kenar_gen=16)

    def on(self, c, f, t, d):
        ct = d["cumle_t"] + [99, 99, 99, 99]
        t_kay = ct[3]
        kay = ara(t, t_kay, t_kay + 1.3)
        yorgun = ara(t, 0.0, t_kay)
        tit = (3 + 6 * yorgun) * math.sin(t * 31) * (1 - kay)
        konusan = d["konusan"]
        # ana: susturur
        sus = konusan == "ana"
        C.ana(c, f, 430, self.DAL_Y + 26, 400,
              poz=dict(kol_on=(150, -128) if sus else (30, -30), ifade="sus" if sus else ("sasir" if kay > 0 else "gul"),
                       agiz=C.konus_agiz(t, sus) * 0.6, goz=C.goz_kirp(t, 2), bakis=0.6), yon=1)
        # keloglan: dik duran kapiyi tutmaya calisir
        kel_ifade = "sasir" if kay > 0 else "zor"
        taban = self.DAL_Y + 24
        kw, kh = 170, 380
        kx0 = 1030
        aci = tit * 0.35 + 72 * yumusak(kay)
        dus = max(0.0, kay - 0.35) / 0.65
        C.kapi(c, f, kx0, taban - kh + dus ** 2 * 900, kw, kh, aci=aci, pivot=(kx0 + kw * 0.5, taban + dus ** 2 * 900), k=1.0)
        uzan = 92 + tit * 0.8 if kay <= 0 else 92 + 40 * kay
        C.keloglan(c, f, 900, taban - 2, 450,
                   poz=dict(kol_on=(uzan, -8), kol_arka=(uzan + 8, -14), ifade=kel_ifade, govde=-6 + tit * 0.2,
                            agiz=C.konus_agiz(t, konusan == "kel"), goz=1.0 if kay > 0 else C.goz_kirp(t),
                            bacak_on=(14, 0), bacak_arka=(-12, 0)), yon=1)
        for i in range(3):
            if yorgun > 0.3 and kay < 0.2:
                C.ter_damlasi(c, f, 850 + i * 38, 240 + i * 10, t, i)
        isik(c, 960, 1180, 900, (1.0, 0.60, 0.30), 0.30)
        gece_tonu(c, 0.6)


class Gum:
    """Sayfa 9: GUM! Kapi haramilerin tepesine iner; haramiler altinlari birakip kacar."""
    ATES = (900, 760)
    DUS = 0.72

    def arka(self, c, f):
        C.gokyuzu(c, f, (0.10, 0.12, 0.26), (0.24, 0.28, 0.42), y1=900, bulutlar=[(500, 150, 240, 28)], gece=1.0)
        for i in range(10):
            x = 40 + i * 200
            C.agac_yuvarlak(c, f, x, 600 + (i % 2) * 20, 0.9, yesil=(0.16, 0.22, 0.30), tohum=170 + i, gece=0.8,
                            govde_renk=(0.14, 0.13, 0.18))
        f.boya(c, egri([(-60, 640), (600, 610), (1200, 640), (1980, 600), (1980, 1120), (-60, 1120)]), (0.18, 0.25, 0.22),
               murekkep=0.0, golge=0.2, tohum=171, kenar_gen=16)
        f.boya(c, egri([(1640, 1100), (1690, 700), (1660, 300), (1700, -50), (2000, -50), (2000, 1100)]),
               (0.26, 0.21, 0.20), murekkep=0.9, golge=0.4, golge_yon=(14, 0), tohum=172, cizgi=2.6)
        C.cimen_tutamlari(c, f, (-40, 660, 1960, ZEMIN + 30), n=150, renk=(0.12, 0.18, 0.16), tohum=173, alfa=0.4)

    def sarsinti(self, t):
        u = ara(t, self.DUS, self.DUS + 0.7)
        if u <= 0 or u >= 1:
            return (0.0, 0.0)
        g = (1 - u) ** 2 * 26
        return (g * math.sin(t * 71), g * math.cos(t * 53))

    def on(self, c, f, t, d):
        ct = d["cumle_t"] + [99, 99, 99]
        C.yildizlar(c, f, t, (0, 0, 1920, 420), n=50, tohum=8)
        ax, ay = self.ATES
        dus = ara(t, 0.0, self.DUS)
        carpti = t >= self.DUS
        kac = ara(t, ct[2] - 0.4, d["sure"])
        # haramiler
        hedef = [("sisman", ax - 230, 1), ("orta", ax + 230, -1), ("uzun", ax + 420, -1)]
        for i, (tip, hx, yon) in enumerate(hedef):
            if not carpti:
                C.harami(c, f, hx, ZEMIN + 8, 340, tip, oturuyor=True, yon=yon,
                         poz=dict(kol_on=(70 + 25 * math.sin(t * 5 + i), -60), ifade="gul", agiz=0.4,
                                  goz=C.goz_kirp(t, i)))
            elif kac <= 0:
                zp = -40 * math.sin(ara(t, self.DUS, self.DUS + 0.5) * math.pi)
                C.harami(c, f, hx, ZEMIN + 8 + zp, 340, tip, yon=yon,
                         poz=dict(ifade="kork", kol_on=(160, -20), kol_arka=(150, -30), agiz=1.0))
            else:
                hiz = 1.0 + 0.25 * i
                gx = hx - kac * (1600 + 300 * i) * hiz
                C.harami(c, f, gx, ZEMIN + 8, 340, tip, yon=-1,
                         poz=dict(C.kos(t * 11 + i, 1.0), ifade="kork", agiz=1.0))
        if carpti:
            C.altin_yigini(c, f, ax + 40, ZEMIN + 22, 1.8, n=34, t=t, tohum=4)
            C.heybe(c, f, ax + 130, ZEMIN - 26, 1.7)
        C.ates(c, f, ax, ay, 1.2, t, guc=1.0 if not carpti else 0.85)
        # kapi yuzu gorunerek donup duser
        kw, kh = 170, 330
        if not carpti:
            cy = lerp(-320, ay - 75, dus ** 2)
            aci = lerp(-20, 84, dus)
        else:
            cy, aci = ay - 75, 84
        C.kapi(c, f, ax - kw / 2, cy - kh / 2, kw, kh, aci=aci, pivot=(ax, cy), k=1.0)
        if carpti:
            C.toz_bulutu(c, f, ax, ay - 20, ara(t, self.DUS, self.DUS + 1.6), 1.2)
        gece_tonu(c, 0.8)
        ates_feneri(c, ax, ay - 40, 560, t, 1.0)

    def ust(self, c, f, t, d):
        C.gum_yazisi(c, 980, 330, ara(t, self.DUS - 0.02, self.DUS + 1.6))


class Sabah:
    """Sayfa 10: safak; altinlari toplayip kapiyi yine sirtlayarak eve donus."""

    def arka(self, c, f):
        P = PALET["safak"]
        C.gokyuzu(c, f, *P["gok"], y1=820, bulutlar=[(400, 160, 200, 40), (1200, 120, 240, 44)])
        isik(c, 1500, 560, 380, (1.0, 0.84, 0.55), 0.6)
        f.boya(c, daire(1500, 560, 70), (1.0, 0.86, 0.55), murekkep=0.0, golge=0, kenar=0.3, tohum=3)
        manzara_tepeler = [
            ([(-80, 560), (300, 500), (700, 560), (1100, 520), (1500, 575), (2000, 530)], P["uzak"], 91),
            ([(-80, 640), (400, 600), (900, 650), (1400, 610), (2000, 650)], P["orta"], 92),
            ([(-80, ZEMIN - 60), (600, ZEMIN - 100), (1200, ZEMIN - 70), (2000, ZEMIN - 110)], P["yakin"], 93),
        ]
        C.tepeler(c, f, manzara_tepeler)
        f.boya(c, egri([(-60, 870), (400, 820), (900, 800), (1400, 760), (1800, 700), (1980, 690), (1980, 720), (1800, 735),
                        (1400, 800), (900, 850), (400, 880), (-60, 930)]), P["yol"], murekkep=0.0, golge=0.2, tohum=94)
        C.ev(c, f, 1760, 640, 0.22, tohum=95)
        for i, x in enumerate((140, 220, 1650, 1880)):
            C.kavak(c, f, x, 700, 1.0, tohum=96 + i)
        C.cimen_tutamlari(c, f, (-40, ZEMIN - 90, 1960, ZEMIN + 40), n=160, renk=(0.30, 0.42, 0.20), tohum=97)
        C.cicekler(c, f, (-40, ZEMIN - 80, 1960, ZEMIN + 30), n=60, tohum=98)

    def on(self, c, f, t, d):
        u = ara(t, 0, d["sure"] + 1.0)
        C.kuslar(c, f, 200, 220, t, n=4, s=1.1, hiz=55, tohum=7)
        for i in range(3):                                          # sabah sisi
            x = (200 + i * 600 + t * 20) % 2200 - 140
            f.yumusak(c, leke(x, 640 + i * 20, 260, 30, i, 0.2), (1, 1, 1), 0.35, 26)
        kx = lerp(380, 1300, u)
        ky = 830 - (kx - 380) * 0.07
        C.ana(c, f, kx - 170, ky + 6, 225, poz=dict(goz=C.goz_kirp(t, 1), mutlu_goz=True, kol_on=(25, -40)), yon=1,
              elde=C.bohca((0.95, 0.75, 0.25), 9.5), yuru_faz=t * 6)
        poz = dict(C.yuru(t * 6.5, 1.0), goz=C.goz_kirp(t), ifade="gul", mutlu_goz=True)
        poz.update(kol_on=C.TASI["kol_on"], kol_arka=C.TASI["kol_arka"])
        C.keloglan(c, f, kx, ky, 245, poz=poz, yon=1, sirtta=C.kapi_sirtta())
        tam_ekran(c, (1.0, 0.90, 0.75), 0.10, skia.BlendMode.kMultiply)


class SonEv(Ev):
    """Sayfa 11: kapi yerinde; gun batiminda mutlu son."""

    def arka(self, c, f):
        manzara(c, f, "gunbatimi", ufuk=540, tohum=111)
        isik(c, 1650, 520, 420, (1.0, 0.75, 0.45), 0.55)
        f.boya(c, daire(1650, 545, 72), (1.0, 0.80, 0.50), murekkep=0.0, golge=0, kenar=0.3, tohum=112)
        C.tepeler(c, f, [([(-80, 600), (500, 560), (1000, 590), (1500, 575), (2000, 600)], (0.62, 0.62, 0.42), 113),
                         ([(-80, ZEMIN - 70), (500, ZEMIN - 110), (1000, ZEMIN - 80), (1500, ZEMIN - 120),
                           (2000, ZEMIN - 90)], (0.50, 0.57, 0.31), 114)])
        C.cimen_tutamlari(c, f, (-40, ZEMIN - 90, 1960, ZEMIN + 30), n=160, renk=(0.30, 0.40, 0.18), tohum=115)
        C.cicekler(c, f, (-40, ZEMIN - 70, 1960, ZEMIN + 20), n=80, tohum=116)
        for i, x in enumerate((90, 160)):
            C.kavak(c, f, x, 640, 1.1, tohum=30 + i)
        C.agac_yuvarlak(c, f, 300, ZEMIN + 5, 1.35, tohum=9)
        C.cit(c, f, 520, 930, ZEMIN - 10, 1.0, tohum=12)
        C.ev(c, f, self.EVX, ZEMIN - 15, 1.0, tohum=3)
        C.cit(c, f, 1370, 1700, ZEMIN - 10, 1.0, tohum=14)

    def on(self, c, f, t, d):
        x = self.EVX
        C.duman(c, f, x + 287, ZEMIN - 15 - 335, t, 1.0, renk=(0.95, 0.90, 0.88))
        C.kapi(c, f, x + 150, ZEMIN - 15 - 152, 72, 152, k=1.0)
        C.kuslar(c, f, 1300, 200, t, n=3, s=1.0, hiz=-40, tohum=9)
        for i, (tx, ty, yon) in enumerate(((470, 800, 1), (560, 812, -1))):
            tavuk(c, f, tx + math.sin(t * 0.7 + i) * 6, ty, t, 0.8, yon, tohum=i)
        salla = 150 + 25 * math.sin(t * 5)
        C.ana(c, f, 760, ZEMIN + 10, 225, poz=dict(kol_on=(salla, -30), goz=C.goz_kirp(t, 1), mutlu_goz=True), yon=1)
        C.keloglan(c, f, 900, ZEMIN + 14, 245, poz=dict(kol_on=(150 + 25 * math.sin(t * 5 + 1), -30), goz=C.goz_kirp(t),
                                                        mutlu_goz=True, agiz=0.4), yon=-1)
        C.altin_yigini(c, f, 1095, ZEMIN + 20, 0.8, n=14, t=t, tohum=6)
        isik(c, 1650, 520, 900, (1.0, 0.70, 0.40), 0.18 + 0.12 * ara(t, d["cumle_t"][1] if len(d["cumle_t"]) > 1 else 5, d["sure"]))


class Elmalar:
    """Sayfa 12: Gokten uc elma dusmus... + SON."""
    ZAMAN = (1.0, 2.3, 3.6)

    def arka(self, c, f):
        C.gokyuzu(c, f, (0.66, 0.78, 0.90), (0.99, 0.94, 0.84), y1=900,
                  bulutlar=[(300, 200, 200, 46), (1550, 160, 240, 52), (950, 90, 150, 32)])
        C.tepeler(c, f, [([(-80, 680), (500, 620), (960, 600), (1400, 625), (2000, 680)], (0.56, 0.68, 0.38), 121)])
        C.cimen_tutamlari(c, f, (-40, 640, 1960, 830), n=200, renk=(0.30, 0.45, 0.20), tohum=122)
        C.cicekler(c, f, (-40, 650, 1960, 830), n=70, tohum=123)

    def on(self, c, f, t, d):
        for i, (x, t0) in enumerate(zip((620, 960, 1300), self.ZAMAN)):
            u = (t - t0) / 0.75
            if u < 0:
                continue
            if u < 1:
                y = lerp(-80, 660, u ** 2)
            else:
                b = (t - t0 - 0.75)
                y = 660 - 60 * abs(math.sin(min(b, 0.9) * math.pi / 0.45)) * math.exp(-b * 3.0)
            C.elma(c, f, x, y, 2.4, aci=12 * math.sin(t * 2 + i))
            if 0 < t - t0 - 0.75 < 0.6:
                C.yildizcik(c, x + 30, y - 40, 22, 1 - (t - t0 - 0.75) / 0.6)

    def ust(self, c, f, t, d):
        a = yumusak(ara(t, 4.6, 5.6))
        if a <= 0:
            return
        c.saveLayerAlpha(None, int(255 * a))
        ft = font("Cinzel.ttf", 130)
        gen = ft.measureText("SON")
        f.boya(c, egri([(960 - 230, 250), (960, 205), (960 + 230, 250), (960 + 230, 420), (960, 465), (960 - 230, 420)]),
               (0.97, 0.93, 0.82), murekkep=0.95, golge=0.25, tohum=9, cizgi=2.6, kenar_gen=12)
        c.drawString("SON", 960 - gen / 2, 388, ft, skia.Paint(AntiAlias=True, Color4f=renk4((0.58, 0.14, 0.09))))
        cerceve(c)
        c.restore()


# ================================================================ sayfa listesi
SAYFALAR = [
    dict(kimlik="kapak", sesler=[("cinlama", 1.2), ("kuslar", 0.5, dict(sure=6))], sahne=Kapak(), sure=6.5, muzik="giris",
         kamera=[(0.0, 1.06, 960, 560), (1.0, 1.0, 960, 540)]),
    dict(kimlik="ev", sesler=[("kuslar", 0.3, dict(sure=10)), ("tavuk", 2.2), ("tavuk", 6.8)], sahne=Ev(), muzik="koy",
         metin="Evvel zaman içinde, kalbur saman içinde, bir köyün kıyısında Keloğlan ile anası yaşarmış. "
               "Evleri küçük, gönülleri kocamanmış.",
         kamera=[(0.0, 1.0, 960, 540), (1.0, 1.06, 900, 520)]),
    dict(kimlik="veda", sesler=[("kuslar", 0.3, dict(sure=6)), ("adimlar", -2.2, dict(sure=2.2))], sahne=Veda(), muzik="koy",
         metin="Bir gün anası komşu köydeki düğüne gidecek olmuş. “Oğlum, sakın evden ayrılma,” demiş. "
               "“Çıkarsan da kapıyı çekmeyi unutma!”",
         konusanlar=[None, "ana", "ana"],
         kamera=[(0.0, 1.0, 960, 540), (1.0, 1.05, 1000, 520)]),
    dict(kimlik="can_sikintisi", sesler=[("hayal", "c1-0.3")], sahne=CanSikintisi(), muzik="merak",
         metin="Anası gözden kaybolur kaybolmaz Keloğlan’ın canı sıkılmış. "
               "“Ben de düğüne gideyim, davul zurna dinleyeyim!” demiş.",
         konusanlar=[None, "kel"],
         kamera=[(0.0, 1.04, 1000, 540), (1.0, 1.0, 960, 540)]),
    dict(kimlik="kapi_cekme", sesler=[("gicirti", 0.6, dict(sure=1.7)), ("kopma", "c1"), ("dusme", "c1+0.3"), ("adimlar", "c2+0.4", dict(sure=6))], sahne=KapiCekme(), muzik="komik",
         metin="Kapıyı çekmiş, çekmiş… Kapı menteşesinden çıkıvermiş! "
               "“Anam kapıyı çek dedi,” demiş Keloğlan, kapıyı sırtladığı gibi yola koyulmuş.",
         konusanlar=[None, None, "kel"],
         kamera=[(0.0, 1.0, 960, 540), (1.0, 1.04, 1040, 540)]),
    dict(kimlik="dugun", sesler=[("gulme", "c2")], sahne=Dugun(), muzik="dugun",
         metin="Düğün yerinde anası onu görünce dizlerini dövmüş: “Aman oğlum, bu ne hâl?” "
               "“Kapıyı çektim ya ana!” Bütün köy kahkahalarla gülmüş.",
         konusanlar=["ana", "kel", None],
         kamera=[(0.0, 1.0, 960, 540), (1.0, 1.05, 1000, 540)]),
    dict(kimlik="aksam", sesler=[("kurt", 1.4), ("adimlar", 0.2, dict(sure="c1+1.2")), ("tirmanma", "c1+1.2", dict(sure=2.4)), ("circir", 5.5, dict(sure=5))], sahne=AksamOrman(), muzik="aksam",
         metin="Akşam olmuş, yola düşmüşler. Ormanda karanlık basınca kurtlardan korkup "
               "kapıyla birlikte koca bir çınara tırmanmışlar.",
         kamera=[(0.0, 1.0, 960, 540), (1.0, 1.06, 1150, 500)]),
    dict(kimlik="haramiler", sesler=[("circir", 0.0, dict(sure=10)), ("agir_adimlar", "c0", dict(sure=3)), ("baykus", 2.2), ("ates", "c1", dict(sure=6.5)), ("altin", "c1+1.5", dict(sure=4.5))], sahne=GeceHaramiler(), muzik="gece",
         metin="Gece yarısı ağacın dibine üç harami gelmiş. Ateşi yakmışlar, heybelerdeki altınları "
               "döküp saymaya koyulmuşlar.",
         kamera=[(0.0, 1.0, 960, 540), (1.0, 1.06, 900, 560)]),
    dict(kimlik="agacta", sesler=[("circir", 0.0, dict(sure=10)), ("ates_uzak", 0.0, dict(sure=10)), ("kalp", 0.8, dict(sure="c3")), ("kayma", "c3"), ("whoosh", "c3+0.6", dict(sure=1.4))], sahne=Agacta(), muzik="gerilim",
         metin="Keloğlan’ın kolları uyuşmuş. “Ana, kapıyı tutamıyorum!” “Sus oğlum, duyacaklar!” "
               "Derken kapı elinden kayıvermiş…",
         konusanlar=[None, "kel", "ana", None],
         kamera=[(0.0, 1.0, 960, 540), (1.0, 1.07, 900, 500)]),
    dict(kimlik="gum", sesler=[("gum", 0.72), ("altin_sacilma", 0.8), ("kosma", "c2-0.3", dict(sure=4)), ("ates", 0.0, dict(sure=10)), ("circir", 4.0, dict(sure=6))], sahne=Gum(), muzik="kacis", suslu_harf=False,
         metin="GÜM! Kapı haramilerin tepesine inmiş. “Gök yıkılıyor, kaçın!” diye bağrışarak "
               "altınları bırakıp tabanları yağlamışlar.",
         konusanlar=[None, None, "harami"],
         kamera=[(0.0, 1.0, 960, 540), (1.0, 1.03, 900, 540)]),
    dict(kimlik="sabah", sesler=[("horoz", 0.5), ("kuslar", 0.2, dict(sure=10)), ("adimlar", 0.2, dict(sure=9.5))], sahne=Sabah(), muzik="sabah",
         metin="Sabah olunca Keloğlan ile anası altınları toplamış. Keloğlan kapıyı yine sırtına vurmuş, "
               "birlikte evlerine dönmüşler.",
         kamera=[(0.0, 1.0, 900, 540), (1.0, 1.05, 1050, 520)]),
    dict(kimlik="son_ev", sesler=[("kuslar", 0.2, dict(sure=10)), ("tavuk", 3.0)], sahne=SonEv(), muzik="final",
         metin="Kapıyı yerine takmışlar, bir daha da yoksulluk yüzü görmemişler. "
               "Onlar ermiş muradına, biz çıkalım kerevetine.",
         kamera=[(0.0, 1.05, 1000, 520), (1.0, 1.0, 960, 540)]),
    dict(kimlik="elmalar", sesler=[("elma", 1.75), ("elma", 3.05), ("elma", 4.35), ("cinlama", 4.6)], sahne=Elmalar(), muzik="son", sure=9.0,
         metin="Gökten üç elma düşmüş: biri bana, biri anlatana, biri de dinleyenlere.",
         kamera=[(0.0, 1.0, 960, 540), (1.0, 1.02, 960, 530)]),
]

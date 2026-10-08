"""
Masaldan dikey (9:16) Shorts tanıtımı.

Masal modülündeki SHORTS = dict(sayfalar=("kapi_cekme", "dugun")) sayfaları
(ardışık aralık) yatay masaldan alınır ve dikey bir sayfaya yerleştirilir:

    ┌───────────────┐  üstte başlık (masal adı) + alt başlık
    │   BAŞLIK      │
    │ ┌───────────┐ │  ortada resim (yatay kare, kitap sayfası gibi çerçeveli)
    │ │  resim    │ │
    │ └───────────┘ │
    │  metin kartı  │  altta büyük puntolu metin, anlatıcı okurken cümle cümle
    │  ▶ devamı     │  sonda "Masalın tamamı kanalımızda" çağrısı
    └───────────────┘

Ses: tam masal izinin aynı aralığı + kısa kapanış ezgisi (masal.py keser).
"""
import numpy as np
import skia
from PIL import Image, ImageFilter

from src.masal_motoru import (KAGIT, MUREKKEP, MetinKarti, _ss, font, kagit_dokusu, renk4)

SW, SH = 1080, 1920
KAPANIS = 3.2                                       # sondaki cagri suresi (sn)
RESIM_Y = 560
RESIM_H = int(SW * 9 / 16)


class ShortsKurgu:
    def __init__(self, masal):
        self.m = masal
        ids = [s.t["kimlik"] for s in masal.sayfalar]
        spec = getattr(masal.mod, "SHORTS", None) or {}
        adlar = spec.get("sayfalar")
        if adlar:
            bilinmeyen = [a for a in adlar if a not in ids]
            if bilinmeyen:
                raise ValueError(f"SHORTS sayfalari bulunamadi: {bilinmeyen}")
            sira = sorted(ids.index(a) for a in adlar)
        else:                                       # varsayilan: ortadaki iki sayfa
            orta = len(ids) // 2
            sira = [orta - 1, orta]
        self.i0, self.i1 = sira[0], sira[-1]
        self.T0 = masal.bas[self.i0]
        self.T1 = masal.bas[self.i1] + masal.sayfalar[self.i1].sure
        self.SURE = (self.T1 - self.T0) + KAPANIS
        self.baslik = tr_buyuk(getattr(masal.mod, "BASLIK", masal.kimlik))
        self.alt = spec.get("alt_baslik") or getattr(masal.mod, "ALT_BASLIK", "")
        self.cagri = spec.get("cagri") or "Masalın tamamı kanalımızda ▶"
        self.kartlar = {}
        for i in range(self.i0, self.i1 + 1):
            s = masal.sayfalar[i]
            if not s.kart:
                continue
            k = MetinKarti(s.metin, s.sure, s.kart.konusanlar, gen=1000, suslu=s.kart.suslu, boy=48)
            k.zaman = list(s.kart.zaman)
            k.sureler = s.kart.sureler
            k.x0 = (SW - k.gen) // 2
            k.y0 = RESIM_Y + RESIM_H + 70
            self.kartlar[i] = k
        self._ust = None

    # ---------------------------------------------------------- sabit katman
    def _ust_katman(self):
        """Baslik, resim cercevesi golgesi ve kagit zemini (bir kez)."""
        if self._ust is None:
            s = skia.Surface(SW, SH)
            c = s.getCanvas()
            c.clear(skia.ColorTRANSPARENT)
            ft = font("Cinzel.ttf", 82)
            gen = ft.measureText(self.baslik)
            while gen > SW - 90 and ft.getSize() > 40:
                ft = font("Cinzel.ttf", ft.getSize() - 4)
                gen = ft.measureText(self.baslik)
            y = 300
            c.drawString(self.baslik, SW / 2 - gen / 2 + 3, y + 4, ft,
                         skia.Paint(AntiAlias=True, Color4f=renk4((0.3, 0.1, 0.05), 0.35)))
            c.drawString(self.baslik, SW / 2 - gen / 2, y, ft, skia.Paint(AntiAlias=True, Color4f=renk4((0.58, 0.14, 0.09))))
            if self.alt:
                fi = font("EBGaramond-Italic.ttf", 46)
                g2 = fi.measureText(self.alt)
                c.drawString(self.alt, SW / 2 - g2 / 2, y + 80, fi,
                             skia.Paint(AntiAlias=True, Color4f=renk4((0.25, 0.16, 0.10), 0.9)))
            cizgi = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.4,
                               Color4f=renk4((0.55, 0.16, 0.10), 0.7))
            c.drawLine(SW / 2 - 220, y + 112, SW / 2 + 220, y + 112, cizgi)
            # resim golgesi ve cercevesi
            r = skia.Rect(24, RESIM_Y - 12, SW - 24, RESIM_Y + RESIM_H + 12)
            c.drawRect(r.makeOffset(6, 10), skia.Paint(AntiAlias=True, Color4f=renk4((0.15, 0.1, 0.06), 0.35),
                                                       MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12)))
            c.drawRect(r, skia.Paint(AntiAlias=True, Color4f=renk4((0.98, 0.96, 0.91))))
            self._ust = s.makeImageSnapshot()
        return self._ust

    # ---------------------------------------------------------- kare
    def kare(self, s):
        """Shorts zamani s -> (1920, 1080, 3) uint8."""
        m = self.m
        hikaye = self.T1 - self.T0
        t = self.T0 + min(s, hikaye - 1e-3)
        yatay = m.kare(t, kart=False)
        # zemin: resmin cok bulanik, buyutulmus kopyasi + kagit
        kucuk = Image.fromarray(yatay).resize((96, 54), Image.BILINEAR)
        orta = kucuk.crop((48 - 15, 0, 48 + 15, 54)).filter(ImageFilter.GaussianBlur(4))
        zemin = np.asarray(orta.resize((SW, SH), Image.BILINEAR), np.float32)
        kagit = np.array(KAGIT, np.float32) * 255
        zemin = zemin * 0.28 + kagit * 0.72
        resim = Image.fromarray(yatay).resize((SW - 60, int((SW - 60) * 9 / 16)), Image.LANCZOS)

        yuz = skia.Surface(SW, SH)
        c = yuz.getCanvas()
        z = np.dstack([np.clip(zemin, 0, 255).astype(np.uint8), np.full((SH, SW), 255, np.uint8)])
        c.drawImage(skia.Image.fromarray(z, colorType=skia.kRGBA_8888_ColorType), 0, 0)
        c.drawImage(self._ust_katman(), 0, 0)
        r = np.dstack([np.asarray(resim), np.full((resim.height, resim.width), 255, np.uint8)])
        c.drawImage(skia.Image.fromarray(np.ascontiguousarray(r), colorType=skia.kRGBA_8888_ColorType), 30, RESIM_Y)
        c.drawRect(skia.Rect(30, RESIM_Y, 30 + resim.width, RESIM_Y + resim.height),
                   skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2,
                              Color4f=renk4(MUREKKEP, 0.75)))
        # metin karti
        tur, i, x = m.nerede(t)
        if tur == "sayfa" and i in self.kartlar:
            self.kartlar[i].ciz(c, x)
        elif tur == "cevir" and i in self.kartlar and x < 0.5:
            self.kartlar[i].ciz(c, m.sayfalar[i].sure, alfa=1 - _ss(x / 0.5))
        # giris basligi vurgusu ve kapanis cagrisi
        a = _ss((s - (hikaye - 0.8)) / 0.8)
        if a > 0:
            fc = font("EBGaramond-Italic.ttf", 58)
            gen = fc.measureText(self.cagri)
            y = SH - 210
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(SW / 2 - gen / 2 - 40, y - 64, SW / 2 + gen / 2 + 40, y + 30), 40, 40),
                        skia.Paint(AntiAlias=True, Color4f=renk4((0.58, 0.14, 0.09), 0.92 * a)))
            c.drawString(self.cagri, SW / 2 - gen / 2, y, fc,
                         skia.Paint(AntiAlias=True, Color4f=renk4((0.99, 0.96, 0.88), a)))
        img = yuz.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3].astype(np.float32)
        img *= kagit_dokusu(SW, SH, False)
        if s < 0.35:
            img *= _ss(s / 0.35)
        if s > self.SURE - 0.6:
            img *= _ss((self.SURE - s) / 0.6)
        return (np.clip(img, 0, 255) + 0.5).astype(np.uint8)

    def hazirla(self):
        self._ust_katman()
        kagit_dokusu(SW, SH, False)


def tr_buyuk(metin):
    """Turkce buyuk harf: i -> İ, ı -> I."""
    return metin.replace("i", "İ").replace("ı", "I").upper()

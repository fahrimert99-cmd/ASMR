"""
Tarihi harita animasyonu motoru — bir imparatorlugun kurulustan en genis
sinirlarina buyumesini ~20 saniyelik sesli bir videoya donusturur.

Her konu `senaryolar/<kimlik>.py` icinde VERI olarak tanimlanir (olaylar,
bolgeler, sehirler, kamera, muzik). Motor bu veriyi okur:

  1. Projeksiyon : Lambert Konik Konform (senaryo kendi merkezini secer).
  2. Alanlar     : Her bolge, "fethedildigi video aninin" yazili oldugu bir zaman
                   alanina (raster, ~1.25 km/piksel) donusturulur. Bolge, verilen
                   yil araliginda mevcut sinirdan ya da tohum sehirden mesafeye
                   gore disa dogru yayilir (organik cephe icin hafif gurultu).
                   Bir karede "devletin mi?" sorusu yalnizca  alan <= t  olur.
  3. Cizer       : Her kare icin kamera (PCHIP), vektor kara/goller/nehirler
                   (2x supersample), zaman alanindan sinir maskesi, HUD
                   (yil sayaci, olay basligi, yuzolcumu, zaman cizelgesi).

Disaridan yalnizca numpy, scipy, Pillow kullanir; veri dosyalari repoda
(veri/harita/harita.json, veri/fontlar/) bulunur, internet gerekmez.
"""
import importlib
import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

KOK = Path(__file__).resolve().parent.parent
HARITA_JSON = KOK / "veri" / "harita" / "harita.json"
FONT_DIR = KOK / "veri" / "fontlar"

SONSUZ = np.float32(1e9)
R_DUNYA = 6371.0

# Senaryo vermezse kullanilan deniz adlari: (metin, boylam, enlem, cografi aci, boy_km)
# aci: yerel dogu yonune gore derece (projeksiyon donmesi otomatik eklenir);
# boy_km: yazi yuksekligi ~ boy_km * (piksel/km) — yakin cekimde buyur, uzakta kaybolur.
VARSAYILAN_DENIZLER = [
    ("KARADENİZ", 34.6, 43.4, 0, 95),
    ("AKDENİZ", 18.5, 34.6, 0, 95),
    ("EGE", 25.1, 38.0, 0, 40),
    ("MARMARA", 28.15, 40.72, 0, 40),
    ("ADRİYATİK", 15.6, 42.9, -38, 45),
    ("KIZILDENİZ", 38.4, 20.6, -66, 95),
    ("HAZAR DENİZİ", 50.6, 42.2, -95, 95),
    ("BASRA KÖRFEZİ", 50.4, 27.6, -50, 70),
    ("ARAL", 59.6, 45.0, 0, 40),
    ("ARAP DENİZİ", 63.0, 17.0, 0, 120),
    ("ATLAS OKYANUSU", -19.0, 37.0, 0, 140),
    ("HİNT OKYANUSU", 72.0, 6.0, 0, 150),
    ("BENGAL KÖRFEZİ", 89.0, 15.0, 0, 95),
    ("KUZEY DENİZİ", 3.5, 56.0, 0, 80),
    ("BALTIK DENİZİ", 19.5, 57.5, 0, 70),
    ("JAPON DENİZİ", 134.5, 40.5, 35, 90),
    ("SARI DENİZ", 123.5, 35.8, 0, 60),
    ("DOĞU ÇİN DENİZİ", 125.5, 29.0, 0, 85),
    ("GÜNEY ÇİN DENİZİ", 114.0, 14.0, 0, 110),
]


# ================================================================ projeksiyon
class Projeksiyon:
    """Kuresel Lambert Konik Konform. Cikti: km."""

    def __init__(self, lon0=24.0, lat0=35.0, lat1=25.0, lat2=47.0):
        r = math.radians
        f0, f1, f2 = r(lat0), r(lat1), r(lat2)
        t = lambda f: math.tan(math.pi / 4 + f / 2)
        self.lon0_d = lon0
        self.lon0 = r(lon0)
        self.n = math.log(math.cos(f1) / math.cos(f2)) / math.log(t(f2) / t(f1))
        self.F = math.cos(f1) * t(f1) ** self.n / self.n
        self.rho0 = R_DUNYA * self.F / t(f0) ** self.n

    def ileri(self, lon, lat):
        lon = np.radians(np.asarray(lon, dtype=np.float64))
        lat = np.radians(np.asarray(lat, dtype=np.float64))
        rho = R_DUNYA * self.F / np.tan(np.pi / 4 + lat / 2) ** self.n
        th = self.n * (lon - self.lon0)
        return rho * np.sin(th), self.rho0 - rho * np.cos(th)

    def donme(self, lon):
        """Boylamdaki yerel dogu yonunun ekrandaki acisi (derece, saat yonu tersine)."""
        return math.degrees(self.n * math.radians(lon - self.lon0_d))

    def olcek_xy(self, x, y):
        """(x, y) noktasindaki dogrusal olcek carpani k (alan carpani k^2)."""
        rho = np.hypot(x, self.rho0 - y)
        lat = 2 * np.arctan((R_DUNYA * self.F / rho) ** (1 / self.n)) - np.pi / 2
        return rho * self.n / (R_DUNYA * np.cos(lat))


def _kolaylik(u):
    # Olay aninda kisa bir duraklama, sonra hizlanip bir sonrakine yavaslama.
    v = np.clip((u - 0.12) / 0.88, 0.0, 1.0)
    return 0.35 * v + 0.65 * v * v * (3 - 2 * v)


# ================================================================ senaryo
class Senaryo:
    """`senaryolar/<kimlik>.py` modulunu okur; zaman <-> yil donusumlerini saglar."""

    def __init__(self, kimlik):
        mod = importlib.import_module(f"senaryolar.{kimlik}")
        g = lambda ad, vars_=None: getattr(mod, ad, vars_)
        self.kimlik = kimlik
        self.mod = mod
        self.SURE = float(g("SURE", 20.0))
        self.BASLIK = g("BASLIK")
        self.ALT_BASLIK = g("ALT_BASLIK", "")
        self.OLAYLAR = g("OLAYLAR")
        self.BOLGELER = g("BOLGELER")
        self.SEHIRLER = g("SEHIRLER", [])
        self.BASKENTLER = g("BASKENTLER", [])
        self.KAMERA = g("KAMERA")
        self.KITALAR = g("KITALAR", [])
        self.DENIZLER = list(g("DENIZLER", None) or VARSAYILAN_DENIZLER) + list(g("EK_DENIZLER", []))
        self.RENK = tuple(g("RENK", (176, 22, 30)))
        self.VASAL_RENK = g("VASAL_RENK", None)          # ((acik), (koyu)) ya da RENK'ten turetilir
        self.LEJANT = tuple(g("LEJANT", ("Doğrudan yönetim", "Vasal / bağlı devlet")))
        self.MUZIK = dict(g("MUZIK", {}))
        self.BARUT = bool(g("BARUT", True))
        self.YOUTUBE = dict(g("YOUTUBE", {}))
        self.PROJ = Projeksiyon(**g("PROJEKSIYON", {}))

        self._OT = np.array([o["t"] for o in self.OLAYLAR], dtype=np.float64)
        self._OY = np.array([o["yil"] for o in self.OLAYLAR], dtype=np.float64)
        self.ilk_yil, self.son_yil = int(self._OY[0]), int(self._OY[-1])
        self.mo = self.ilk_yil < 0                       # MO/MS gosterimi gerekli mi
        self._TT = np.linspace(0.0, self.SURE, 40001)
        self._YY = self.yil(self._TT)
        self._isler = None

    # -- zaman cizelgesi
    def yil(self, t):
        """Videonun t. saniyesinde sayacin gosterdigi (kesirli) yil."""
        _OT, _OY = self._OT, self._OY
        t = np.asarray(t, dtype=np.float64)
        i = np.clip(np.searchsorted(_OT, t, side="right") - 1, 0, len(_OT) - 2)
        u = (t - _OT[i]) / (_OT[i + 1] - _OT[i])
        y = _OY[i] + (_OY[i + 1] - _OY[i]) * _kolaylik(u)
        y = np.where(t <= _OT[0], _OY[0], y)
        return np.where(t >= _OT[-1], _OY[-1], y)

    def zaman(self, y):
        """Sayacin ilk kez y yilina ulastigi video ani (sn)."""
        i = int(np.searchsorted(self._YY, y, side="left"))
        return float(self._TT[min(i, len(self._TT) - 1)])

    def aktif_olay(self, t):
        i = int(np.searchsorted(self._OT, t, side="right")) - 1
        return max(i, -1)

    def belirme(self, y):
        """Sehir/baskent icin belirme ani (kurulus yilindakiler girisle birlikte)."""
        return self.zaman(y) if y > self.ilk_yil else min(1.0, self._OT[0] - 0.6)

    # -- yil metinleri
    def yil_parca(self, y):
        """(onek, sayi): 1453 -> ('', '1453'); -264 -> ('MÖ', '264')."""
        y = int(y)
        if not self.mo:
            return "", str(y)
        return ("MÖ", str(-y)) if y < 0 else ("MS", str(max(y, 1)))

    def yil_metni(self, y):
        on, sayi = self.yil_parca(y)
        return f"{on} {sayi}".strip()

    def yil_araligi(self):
        a, b = self.yil_metni(self.ilk_yil), self.yil_metni(self.son_yil)
        if self.mo and self.ilk_yil < 0 and self.son_yil < 0:
            a = a.replace("MÖ ", "")                      # "MÖ 336 – 323" yerine "336 – MÖ 323" olmasin
            return f"MÖ {a} – {b.replace('MÖ ', '')}"
        return f"{a} – {b}"

    # -- bolgeler
    def bolge_isleri(self):
        if self._isler is None:
            self._isler = _bolge_isleri(self)
        return self._isler


# ================================================================ cografya
@lru_cache(maxsize=1)
def harita_verisi():
    return json.loads(HARITA_JSON.read_text(encoding="utf-8"))


def _proj_halka(proj, halka):
    a = np.asarray(halka, dtype=np.float64)
    x, y = proj.ileri(a[:, 0], a[:, 1])
    return np.stack([x, y], axis=1)


class Katman:
    """Projekte edilmis halkalar: tek dizi + ofsetler + kutu (hizli culling)."""

    def __init__(self, proj, poligonlar=None, cizgiler=None):
        halkalar, tip = [], []           # tip: 1 = dis halka, 0 = delik
        for p in poligonlar or []:
            for i, h in enumerate(p):
                halkalar.append(_proj_halka(proj, h))
                tip.append(1 if i == 0 else 0)
        for c in cizgiler or []:
            halkalar.append(_proj_halka(proj, c))
            tip.append(2)
        self.tip = tip
        self.ofset = np.cumsum([0] + [len(h) for h in halkalar])
        self.xy = np.concatenate(halkalar) if halkalar else np.zeros((0, 2))
        self.kutu = np.array([[h[:, 0].min(), h[:, 1].min(), h[:, 0].max(), h[:, 1].max()]
                              for h in halkalar]) if halkalar else np.zeros((0, 4))

    def ekran(self, kam, carpan, gorus):
        """Gorunen halkalari ekran koordinatina cevirir: [(tip, duz_liste)]."""
        s, cx, cy, ox, oy = kam
        x0, y0, x1, y1 = gorus
        g = ((self.kutu[:, 2] >= x0) & (self.kutu[:, 0] <= x1) &
             (self.kutu[:, 3] >= y0) & (self.kutu[:, 1] <= y1))
        idx = np.nonzero(g)[0]
        if not len(idx):
            return []
        px = ((self.xy[:, 0] - cx) * s + ox) * carpan
        py = (oy - (self.xy[:, 1] - cy) * s) * carpan
        pts = np.stack([px, py], axis=1)
        cikis = []
        for i in idx:
            a, b = self.ofset[i], self.ofset[i + 1]
            if b - a >= 2:
                cikis.append((self.tip[i], pts[a:b].ravel().tolist()))
        return cikis


# ================================================================ bolgeler
# Elle cizilmis halkalarin duz kenarlari, tum bolgelerde ORTAK olan yumusak bir
# yer degistirme alaniyla dalgalandirilir: komsu kenarlar ayni sekilde kayar,
# sinirlar dogal (nehir/dag gibi) gorunur. Uclar sabit kalir (bogazlar korunur).
_DALGA = [(7.0, 0.012, -0.009, 0.3, 2.1), (5.0, 0.045, 0.030, 1.7, 4.0),
          (3.0, -0.020, 0.070, 5.2, 0.9), (1.6, 0.150, 0.110, 2.8, 3.3),
          (0.8, 0.310, -0.230, 4.4, 1.2)]


def _yer_degistir(x, y):
    dx = np.zeros_like(x)
    dy = np.zeros_like(x)
    for A, kx, ky, fx, fy in _DALGA:
        dx += A * np.sin(kx * x + ky * y + fx)
        dy += A * np.sin(ky * x - kx * y + fy)
    return dx, dy


def bolge_halkasi(proj, halka, adim=5.0):
    p = _proj_halka(proj, halka)
    parcalar = []
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        L = float(np.hypot(*(b - a)))
        n = max(1, int(math.ceil(L / adim)))
        u = np.arange(n) / n
        pts = a + (b - a) * u[:, None]
        sonum = np.sin(np.pi * u) * min(1.0, L / 80.0)
        dx, dy = _yer_degistir(pts[:, 0], pts[:, 1])
        pts = pts + np.stack([dx, dy], axis=1) * sonum[:, None]
        parcalar.append(pts)
    return np.concatenate(parcalar)


def _bolge_isleri(S):
    """[(ta, tb, tur, [halka_km], tohum)] — video zamanina gore sirali."""
    olay_t = sorted(o["t"] for o in S.OLAYLAR)

    def pencere(ta, tb):
        if tb - ta < 0.35:                    # cok kisa pencere -> gorunur yayilma
            ta = tb - 0.35
            onceki = max([e for e in olay_t if e < tb - 1e-6], default=0.0)
            ta = max(ta, min(onceki + 0.22, tb - 0.12))   # olay anini temiz birak
        return ta, tb

    isler = []
    for b in S.BOLGELER:
        halkalar = [bolge_halkasi(S.PROJ, h) for h in b["halkalar"]]
        if b.get("zaman"):
            ta, tb = b["zaman"]
        else:
            ta, tb = pencere(S.zaman(b["yil"][0]), S.zaman(b["yil"][1]))
        isler.append((ta, tb, b["tur"], halkalar, b.get("tohum")))
        if b.get("dogrudan"):
            ta2, tb2 = pencere(S.zaman(b["dogrudan"][0]), S.zaman(b["dogrudan"][1]))
            isler.append((ta2, tb2, "d", halkalar, None))
    isler.sort(key=lambda i: i[0])
    return isler


# ================================================================ zaman alanlari
class Alanlar:
    """Dogrudan (Fd) ve vasal (Fv) zaman alanlari + yuzolcumu egrileri."""

    def __init__(self, senaryo, tohum=7):
        from scipy import ndimage
        self._nd = ndimage
        self.S = senaryo
        self.PROJ = senaryo.PROJ
        rng = np.random.default_rng(tohum)

        tum = np.concatenate([h for i in senaryo.bolge_isleri() for h in i[3]])
        m = 60.0
        self.x0, self.y0 = tum[:, 0].min() - m, tum[:, 1].min() - m
        self.x1, self.y1 = tum[:, 0].max() + m, tum[:, 1].max() + m
        # buyuk imparatorluklarda (Mogol gibi) bellek icin cozunurluk uyarlanir
        self.COZ = max(1.25, max(self.x1 - self.x0, self.y1 - self.y0) / 5200.0)
        self.W = int(math.ceil((self.x1 - self.x0) / self.COZ))
        self.H = int(math.ceil((self.y1 - self.y0) / self.COZ))

        self.kara = self._kara_raster()
        # dusuk frekansli gurultu -> organik ilerleme cephesi
        kucuk = rng.standard_normal((self.H // 24 + 3, self.W // 24 + 3)).astype(np.float32)
        kucuk = ndimage.gaussian_filter(kucuk, 1.2)
        g = ndimage.zoom(kucuk, 24, order=3)[: self.H, : self.W]
        self.gurultu = ((g - g.mean()) / (g.std() + 1e-6)).astype(np.float32)

        self.Fd = np.full((self.H, self.W), SONSUZ, dtype=np.float32)
        self.Fv = np.full((self.H, self.W), SONSUZ, dtype=np.float32)
        for is_ in senaryo.bolge_isleri():
            self._yay(*is_)
        del self.gurultu
        self._alan_egrileri()

    # -- yardimcilar
    def grid(self, lon, lat):
        x, y = self.PROJ.ileri(lon, lat)
        return (x - self.x0) / self.COZ, (self.y1 - y) / self.COZ

    def _kara_raster(self):
        img = Image.new("L", (self.W, self.H), 0)
        d = ImageDraw.Draw(img)
        veri = harita_verisi()
        for poligon in veri["kara_ince"]:
            for i, h in enumerate(poligon):
                gx, gy = self.grid(*np.asarray(h).T)
                if i == 0 and (gx.max() < 0 or gx.min() > self.W or gy.max() < 0 or gy.min() > self.H):
                    break
                d.polygon(list(zip(gx.tolist(), gy.tolist())), fill=0 if i else 1)
        for poligon in veri["goller"]:
            gx, gy = self.grid(*np.asarray(poligon[0]).T)
            d.polygon(list(zip(gx.tolist(), gy.tolist())), fill=0)
        return np.asarray(img, dtype=bool)

    def _yay(self, ta, tb, tur, halkalar, tohum):
        nd = self._nd
        pg = [((h[:, 0] - self.x0) / self.COZ, (self.y1 - h[:, 1]) / self.COZ) for h in halkalar]
        allx = np.concatenate([p[0] for p in pg])
        ally = np.concatenate([p[1] for p in pg])
        pay = 260
        c0 = max(int(allx.min()) - pay, 0)
        c1 = min(int(allx.max()) + pay, self.W)
        r0 = max(int(ally.min()) - pay, 0)
        r1 = min(int(ally.max()) + pay, self.H)

        img = Image.new("L", (c1 - c0, r1 - r0), 0)
        d = ImageDraw.Draw(img)
        for gx, gy in pg:
            d.polygon(list(zip((gx - c0).tolist(), (gy - r0).tolist())), fill=1)
        M = np.asarray(img, dtype=bool)
        kara = self.kara[r0:r1, c0:c1]
        MK = M & kara
        if not MK.any():
            return

        hedef = self.Fd if tur == "d" else self.Fv
        kaynak = None
        if tohum:
            kaynak = np.zeros_like(M)
            for lon, lat in tohum:
                gx, gy = self.grid(lon, lat)
                ix, iy = int(gx) - c0, int(gy) - r0
                if 0 <= iy < kaynak.shape[0] and 0 <= ix < kaynak.shape[1]:
                    kaynak[max(iy - 1, 0):iy + 2, max(ix - 1, 0):ix + 2] = True
        else:
            mevcut = self.Fd[r0:r1, c0:c1] <= ta
            if tur == "v":
                mevcut |= self.Fv[r0:r1, c0:c1] <= ta
            if mevcut.any():
                kaynak = mevcut
        if kaynak is None or not kaynak.any():
            iy, ix = np.argwhere(MK).mean(axis=0).astype(int)
            kaynak = np.zeros_like(M)
            kaynak[iy, ix] = True

        mesafe = nd.distance_transform_edt(~kaynak).astype(np.float32)
        dmax = float(mesafe[MK].max()) or 1.0
        mesafe = np.maximum(mesafe + 0.08 * dmax * self.gurultu[r0:r1, c0:c1], 0.0)
        dmax = float(mesafe[MK].max()) or 1.0
        oran = np.clip(mesafe / dmax, 0.0, 1.0) ** 0.9
        tpix = (ta + (tb - ta) * oran).astype(np.float32)
        # raster, vektor sinirin 2 piksel disina tasar; karede vektor maske ile
        # kirpilir -> tamamlanan bolgelerin kenari pürüzsuz (merdivensiz) olur.
        Mg = nd.binary_dilation(M, iterations=2)
        alt = hedef[r0:r1, c0:c1]
        alt[Mg] = np.minimum(alt[Mg], tpix[Mg])

    def _alan_egrileri(self):
        ys, xs = np.nonzero(self.kara)
        X = self.x0 + (xs + 0.5) * self.COZ
        Y = self.y1 - (ys + 0.5) * self.COZ
        w = (self.COZ ** 2) / self.PROJ.olcek_xy(X, Y) ** 2
        for ad, F in (("toplam", np.minimum(self.Fd, self.Fv)), ("dogrudan", self.Fd)):
            v = F[ys, xs]
            sec = v < SONSUZ
            sira = np.argsort(v[sec])
            setattr(self, f"_t_{ad}", v[sec][sira].astype(np.float64))
            setattr(self, f"_a_{ad}", np.cumsum(w[sec][sira]))

    def alan(self, t, tur="toplam"):
        """t anindaki yuzolcumu (km2)."""
        ts, ac = getattr(self, f"_t_{tur}"), getattr(self, f"_a_{tur}")
        i = np.searchsorted(ts, t, side="right")
        return np.where(i > 0, ac[np.maximum(i - 1, 0)], 0.0)


# ================================================================ yazi / sprite
def _font(ad, boyut, agirlik=None):
    return _font_cache(ad, int(round(boyut)), agirlik)


@lru_cache(maxsize=256)
def _font_cache(ad, boyut, agirlik):
    try:
        f = ImageFont.truetype(str(FONT_DIR / ad), boyut)
        if agirlik is not None:
            try:
                f.set_variation_by_axes([agirlik])
            except Exception:
                pass
        return f
    except Exception:
        yedek = "DejaVuSerif-Bold.ttf" if (agirlik or 400) >= 600 else "DejaVuSerif.ttf"
        try:
            return ImageFont.truetype(yedek, boyut)
        except Exception:
            return ImageFont.load_default()


class Sprite:
    __slots__ = ("rgb", "a", "w", "h", "ax", "ay")

    def __init__(self, img, ax=0, ay=0):
        arr = np.asarray(img.convert("RGBA"), dtype=np.float32) / 255.0
        self.rgb = arr[..., :3]
        self.a = arr[..., 3]
        self.h, self.w = self.a.shape
        self.ax, self.ay = ax, ay          # yerlesim noktasinin sprite icindeki konumu


def _metin_genislik(f, metin, aralik):
    if not aralik:
        return f.getlength(metin)
    return sum(f.getlength(c) for c in metin) + aralik * (len(metin) - 1)


@lru_cache(maxsize=512)
def yazi(metin, font_ad, boyut, renk, agirlik=None, aralik=0, golge=0.7,
         hiza="sol", aci=0, kontur=0):
    """Metni golgeli bir sprite'a cizer. Yerlesim noktasi: hizaya gore ust kenar."""
    f = _font(font_ad, boyut, agirlik)
    gen = _metin_genislik(f, metin, aralik)
    asc, desc = f.getmetrics()
    pad = int(boyut * 0.35) + 4
    W, H = int(gen + 2 * pad), int(asc + desc + 2 * pad)
    katman = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(katman)
    x = pad
    kr = (12, 8, 6, 255)
    if aralik:
        for c in metin:
            d.text((x, pad), c, font=f, fill=renk, stroke_width=kontur, stroke_fill=kr)
            x += f.getlength(c) + aralik
    else:
        d.text((x, pad), metin, font=f, fill=renk, stroke_width=kontur, stroke_fill=kr)
    if golge:
        a = katman.getchannel("A").filter(ImageFilter.GaussianBlur(max(2, boyut * 0.08)))
        a = a.point(lambda v: int(v * golge))
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        g.putalpha(a)
        kaydir = max(1, int(boyut * 0.05))
        taban = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        taban.paste(g, (kaydir, kaydir))
        katman = Image.alpha_composite(taban, katman)
    ax = {"sol": pad, "orta": W / 2, "sag": W - pad}[hiza]
    ay = pad
    if aci:
        katman = katman.rotate(aci, resample=Image.BICUBIC, expand=True)
        return Sprite(katman, katman.width / 2, katman.height / 2)
    return Sprite(katman, ax, ay)


def yapistir(tuval, sp, x, y, alfa=1.0):
    """Sprite'i float RGB tuvale (H, W, 3) alfa ile karistirir."""
    if alfa <= 0.003:
        return
    H, W = tuval.shape[:2]
    x0, y0 = int(round(x - sp.ax)), int(round(y - sp.ay))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    sx1, sy1 = min(sp.w, W - x0), min(sp.h, H - y0)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    a = sp.a[sy0:sy1, sx0:sx1, None] * alfa
    bolge = tuval[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1]
    bolge += (sp.rgb[sy0:sy1, sx0:sx1] - bolge) * a


@lru_cache(maxsize=64)
def _ikon(tur, boyut):
    """Sehir noktasi / baskent yildizi / savas (capraz kilic) ikonlari."""
    S = 4
    n = int(boyut * 2 + 8)
    img = Image.new("RGBA", (n * S, n * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = n * S / 2
    r = boyut * S / 2
    if tur == "nokta":
        d.ellipse([c - r - 2 * S, c - r - 2 * S, c + r + 2 * S, c + r + 2 * S], fill=(25, 12, 8, 230))
        d.ellipse([c - r, c - r, c + r, c + r], fill=(250, 240, 215, 255))
    elif tur == "yildiz":
        pts = []
        for k in range(10):
            rr = r * 1.25 if k % 2 == 0 else r * 0.5
            a = -math.pi / 2 + k * math.pi / 5
            pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
        d.polygon(pts, fill=(255, 214, 102, 255), outline=(60, 25, 5, 255), width=2 * S)
    elif tur == "savas":
        w = max(2, int(boyut * 0.16)) * S
        for sgn in (1, -1):
            x0, y0 = c - sgn * r, c + r
            x1, y1 = c + sgn * r, c - r
            d.line([(x0, y0), (x1, y1)], fill=(20, 10, 6, 255), width=w + 3 * S)
            d.line([(x0, y0), (x1, y1)], fill=(245, 236, 210, 255), width=w)
            hx, hy = c - sgn * r * 0.55, c + r * 0.55
            q = r * 0.32
            d.line([(hx - q, hy - sgn * q * -1), (hx + q, hy + sgn * q * -1)],
                   fill=(255, 205, 90, 255), width=w)
    img = img.resize((n, n), Image.LANCZOS)
    return Sprite(img, n / 2, n / 2)


def _halka_ciz(tuval, x, y, r, kalinlik, renk, alfa):
    """Genisleyen nabiz halkasi (olay anlari)."""
    if alfa <= 0.01 or r <= 1:
        return
    H, W = tuval.shape[:2]
    m = int(r + kalinlik * 3 + 2)
    x0, x1 = max(int(x) - m, 0), min(int(x) + m, W)
    y0, y1 = max(int(y) - m, 0), min(int(y) + m, H)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dd = np.hypot(xx - x, yy - y)
    a = np.exp(-((dd - r) / kalinlik) ** 2) * alfa
    bolge = tuval[y0:y1, x0:x1]
    bolge += (np.asarray(renk, np.float32) / 255.0 - bolge) * a[..., None]


def _ss(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def _tr_sayi(x, ondalik=0):
    s = f"{x:,.{ondalik}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


# ================================================================ renkler
DENIZ_IC = np.array([34, 74, 92], np.float32) / 255
DENIZ_DIS = np.array([9, 26, 38], np.float32) / 255
KARA = np.array([214, 198, 160], np.float32) / 255
KARA_KOYU = np.array([180, 160, 120], np.float32) / 255
KIYI = np.array([62, 46, 30], np.float32) / 255
NEHIR = np.array([88, 132, 150], np.float32) / 255
ALTIN = np.array([255, 205, 92], np.float32) / 255

ALTIN_T = (236, 196, 110, 255)
KREM_T = (246, 237, 216, 255)
SOLUK_T = (214, 200, 170, 255)


# ================================================================ cizer
DUZENLER = {
    # guvenli: haritanin odak kutusunun sigdirildigi dikdortgen (x0, y0, x1, y1)
    "yatay": dict(en=1920, boy=1080, guvenli=(430, 70, 1880, 990)),
    "dikey": dict(en=1080, boy=1920, guvenli=(40, 540, 1040, 1560)),
}


class Cizer:
    def __init__(self, alanlar, duzen="yatay"):
        from scipy.interpolate import PchipInterpolator

        self.A = alanlar
        self.S = S = alanlar.S
        self.PROJ = PROJ = S.PROJ
        self.SURE = S.SURE
        self.t0 = S.OLAYLAR[0]["t"]                    # ilk olay: giris basligi biter
        self.tson = S.OLAYLAR[-1]["t"]                 # son olay: final
        self.renk = np.array(S.RENK, np.float32) / 255
        self.renk_sinir = self.renk * 0.45
        if S.VASAL_RENK:
            self.vasal_a = np.array(S.VASAL_RENK[0], np.float32) / 255
            self.vasal_k = np.array(S.VASAL_RENK[1], np.float32) / 255
        else:                                          # ana rengin acik tonu + koyu tarama
            self.vasal_a = self.renk * 0.55 + 0.45
            self.vasal_k = self.renk * 0.9
        self.parilti = np.clip(self.renk * 1.45 + 0.12, 0, 1)
        self.duzen = duzen
        cfg = DUZENLER[duzen]
        self.W, self.H = cfg["en"], cfg["boy"]
        gx0, gy0, gx1, gy1 = cfg["guvenli"]
        self.ox, self.oy = (gx0 + gx1) / 2, (gy0 + gy1) / 2
        gw, gh = gx1 - gx0, gy1 - gy0

        # kamera anahtar kareleri -> (log s, cx, cy)
        ts, ls, cxs, cys = [], [], [], []
        for t, (b, g, d, k) in S.KAMERA:
            lon = np.concatenate([np.linspace(b, d, 30), np.full(30, d), np.linspace(d, b, 30), np.full(30, b)])
            lat = np.concatenate([np.full(30, g), np.linspace(g, k, 30), np.full(30, k), np.linspace(k, g, 30)])
            x, y = PROJ.ileri(lon, lat)
            s = min(gw / (x.max() - x.min()), gh / (y.max() - y.min()))
            ts.append(t)
            ls.append(math.log(s))
            cxs.append((x.max() + x.min()) / 2)
            cys.append((y.max() + y.min()) / 2)
        self._kam = [PchipInterpolator(ts, v) for v in (ls, cxs, cys)]

        veri = harita_verisi()
        self.kara_ince = Katman(PROJ, veri["kara_ince"])
        self.kara_kaba = Katman(PROJ, veri["kara_kaba"])
        self.goller = Katman(PROJ, veri["goller"])
        self.nehirler = Katman(PROJ, cizgiler=veri["nehirler"])
        self.izgara = Katman(PROJ, cizgiler=self._izgara_cizgileri())

        self.Fd_img = Image.fromarray(alanlar.Fd, "F")
        self.Fv_img = Image.fromarray(alanlar.Fv, "F")

        self._statik()
        self.sehirler = []
        for ad, lon, lat, y, tur in S.SEHIRLER:
            x, yy = PROJ.ileri(lon, lat)
            self.sehirler.append((ad, float(x), float(yy), S.belirme(y), tur))
        self.olay_xy = [tuple(float(v) for v in PROJ.ileri(*o["yer"])) for o in S.OLAYLAR]
        self.baskent = []
        for y, ad in S.BASKENTLER:
            s = next(s for s in self.sehirler if s[0] == ad)
            self.baskent.append((S.belirme(y), s))
        self.toplam_alan = float(alanlar.alan(self.SURE))
        self.bolge_vektor = []
        for ta, tb, tur, halkalar, _ in S.bolge_isleri():
            hepsi = np.concatenate(halkalar)
            kutu = (hepsi[:, 0].min(), hepsi[:, 1].min(), hepsi[:, 0].max(), hepsi[:, 1].max())
            self.bolge_vektor.append((ta, tur, halkalar, kutu))
        self._etiket_plani()

    # ---------------------------------------------------------- hazirlik
    @staticmethod
    def _izgara_cizgileri():
        cizgiler = []
        for lon in range(-40, 171, 10):
            cizgiler.append([[lon, lat] for lat in np.linspace(-10, 80, 100)])
        for lat in range(-10, 81, 10):
            cizgiler.append([[lon, lat] for lon in np.linspace(-50, 180, 280)])
        return cizgiler

    def _statik(self):
        H, W = self.H, self.W
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        cx, cy = self.ox / W, self.oy / H
        r = np.hypot((xx / W - cx) * (W / max(W, H)) * 1.6, (yy / H - cy) * (H / max(W, H)) * 1.6)
        k = np.clip(r, 0, 1)[..., None]
        self.deniz = (DENIZ_IC * (1 - k) + DENIZ_DIS * k).astype(np.float32)
        rng = np.random.default_rng(3)
        from scipy import ndimage
        doku = ndimage.gaussian_filter(rng.standard_normal((H, W)).astype(np.float32), 1.1)
        doku2 = ndimage.gaussian_filter(rng.standard_normal((H // 8, W // 8)).astype(np.float32), 2.0)
        doku2 = np.asarray(Image.fromarray(doku2, "F").resize((W, H), Image.BICUBIC))
        self.doku = (1.0 + 0.035 * doku / (doku.std() + 1e-6) + 0.035 * doku2 / (doku2.std() + 1e-6)).astype(np.float32)
        # kenar karartma (vinyet)
        rv = np.hypot((xx / W - 0.5) * 1.15, (yy / H - 0.5) * 1.15 * H / W * (W / H if W > H else 1))
        self.vinyet = (1.0 - 0.45 * np.clip((rv - 0.35) / 0.5, 0, 1) ** 1.6).astype(np.float32)[..., None]
        # vasal tarama (ekran uzayinda capraz cizgiler)
        faz = (xx + yy) * (2 * math.pi / 13.0)
        self.tarama = (0.5 + 0.5 * np.clip(2.2 * np.sin(faz), -1, 1)).astype(np.float32)
        # HUD okunurluk golgeleri
        if self.duzen == "yatay":
            g = np.clip(1 - np.hypot(xx / 980, yy / 620), 0, 1) ** 1.3 * 0.62
            g = np.maximum(g, np.clip((yy - (H - 120)) / 120, 0, 1) ** 1.5 * 0.55)
        else:
            g = np.clip(1 - yy / 600, 0, 1) ** 1.2 * 0.72
            g = np.maximum(g, np.clip((yy - (H - 420)) / 420, 0, 1) ** 1.2 * 0.72)
        self.hud_golge = (1 - g).astype(np.float32)[..., None]

    # ---------------------------------------------------------- etiketler
    def _etiket_boyu(self, ad, tur, baskent):
        yatay = self.duzen == "yatay"
        buyuk = tur in ("buyuk", "savas")
        fs = (25 if buyuk else 19) if yatay else (31 if buyuk else 24)
        return fs + (3 if baskent else 0), buyuk

    def _baskent_ad(self, t):
        ad = None
        for tb, sh in self.baskent:
            if t >= tb:
                ad = sh[0]
        return ad

    def _etiket_plani(self, fps=30):
        """Etiket cakismalarini onceden coz: oncelikli, acgozlu yerlesim + zamanda yumusatma.

        Kareler paralel cizildigi icin durum tutulamaz; plan tum zaman cizelgesi
        icin bir kez hesaplanir, boylece etiketler kare kare titremez.
        """
        W, H = self.W, self.H
        if self.duzen == "yatay":
            sabit = [(0, 0, 610, 255), (0, 400, 440, 610), (0, H - 90, W, H)]
        else:
            sabit = [(0, 0, W, 530), (0, H - 380, W, H)]
        S, PROJ = self.S, self.PROJ
        ts = np.arange(0.0, self.SURE + 1e-9, 1.0 / fps)
        vis = np.zeros((len(ts), len(self.sehirler)), np.float32)
        for k, t in enumerate(ts):
            kam = self.kamera(t)
            bas = self._baskent_ad(t)
            i_olay = S.aktif_olay(t)
            olay_yer = S.OLAYLAR[i_olay]["yer"] if i_olay >= 0 else None
            adaylar = []
            for i, (ad, x, y, tb, tur) in enumerate(self.sehirler):
                if t < tb - 0.05:
                    continue
                sira = 4
                if ad == bas:
                    sira = 0
                elif olay_yer and abs(PROJ.ileri(*olay_yer)[0] - x) < 1 and abs(PROJ.ileri(*olay_yer)[1] - y) < 1:
                    sira = 1
                elif tur == "savas":
                    sira = 2
                elif tur == "buyuk":
                    sira = 3
                adaylar.append((sira, -tb, i))
            yerlesen = list(sabit)
            if self.duzen == "yatay" and i_olay >= 0:
                o = S.OLAYLAR[i_olay]
                bb = self._baslik_sprite(o["baslik"], 46, 820)
                f = _font("Cinzel.ttf", bb, 700)
                gen = max(_metin_genislik(f, o["baslik"], int(bb * 0.08)),
                          _font("EBGaramond-Italic.ttf", 34, 500).getlength(o["alt"]))
                yerlesen.append((0, 255, 64 + gen + 24, 400))
            for _, _, i in sorted(adaylar):
                ad, x, y, tb, tur = self.sehirler[i]
                px, py = self.ekran(kam, x, y)
                fs, buyuk = self._etiket_boyu(ad, tur, ad == bas)
                f = _font("EBGaramond.ttf", fs, 700 if buyuk else 600)
                w = f.getlength(ad)
                r = (px - 10, py - fs * 0.75, px + 16 + w, py + fs * 0.55)
                if any(r[0] < q[2] and r[2] > q[0] and r[1] < q[3] and r[3] > q[1] for q in yerlesen):
                    continue
                yerlesen.append(r)
                vis[k, i] = 1.0
        cekirdek = np.ones(9, np.float32) / 9
        for i in range(vis.shape[1]):
            v = np.pad(vis[:, i], 4, mode="edge")
            vis[:, i] = np.convolve(v, cekirdek, mode="valid")
        self._etiket_ts, self._etiket_vis = ts, vis

    def etiket_alfa(self, t, i):
        return float(np.interp(t, self._etiket_ts, self._etiket_vis[:, i]))

    # ---------------------------------------------------------- kamera
    def kamera(self, t):
        t = min(max(t, 0.0), self.SURE)
        s = math.exp(float(self._kam[0](t)))
        return (s, float(self._kam[1](t)), float(self._kam[2](t)), self.ox, self.oy)

    def ekran(self, kam, x, y):
        s, cx, cy, ox, oy = kam
        return ox + (x - cx) * s, oy - (y - cy) * s

    # ---------------------------------------------------------- kare
    def kare(self, t):
        W, H = self.W, self.H
        kam = self.kamera(t)
        s, cx, cy, ox, oy = kam
        gorus = (cx - ox / s, cy - (H - oy) / s, cx + (W - ox) / s, cy + oy / s)
        km_px = 1.0 / s

        # --- kara / goller (2x supersample)
        SS = 2
        katman = self.kara_ince if km_px < 1.6 else self.kara_kaba
        kimg = Image.new("L", (W * SS, H * SS), 0)
        kd = ImageDraw.Draw(kimg)
        kiyi = Image.new("L", (W * SS, H * SS), 0)
        cd = ImageDraw.Draw(kiyi)
        kw = 2 if km_px > 3 else 3
        kara_h = katman.ekran(kam, SS, gorus)
        gol_h = self.goller.ekran(kam, SS, gorus)
        for tip, pts in kara_h:
            kd.polygon(pts, fill=255 if tip == 1 else 0)
        for tip, pts in gol_h:
            kd.polygon(pts, fill=0)
        for tip, pts in kara_h + gol_h:
            cd.line(pts + pts[:2], fill=255, width=kw)
        kara_img = kimg.reduce(SS)
        kara = np.asarray(kara_img, np.float32) / 255.0
        kiyi_a = np.asarray(kiyi.reduce(SS), np.float32) / 255.0

        # nehirler + izgara
        nimg = Image.new("L", (W * SS, H * SS), 0)
        nd_ = ImageDraw.Draw(nimg)
        nw = 2 if km_px > 2.5 else 3
        for _, pts in self.nehirler.ekran(kam, SS, gorus):
            nd_.line(pts, fill=255, width=nw, joint="curve")
        nehir = np.asarray(nimg.reduce(SS), np.float32) / 255.0 * kara
        gimg = Image.new("L", (W, H), 0)
        gd = ImageDraw.Draw(gimg)
        for _, pts in self.izgara.ekran(kam, 1, gorus):
            gd.line(pts, fill=255, width=1)
        izgara = np.asarray(gimg, np.float32) / 255.0

        # kiyi parlamasi (denizde kiyiya yakin acik ton)
        parla = np.asarray(kara_img.filter(ImageFilter.GaussianBlur(9)), np.float32) / 255.0

        # --- zemin
        img = self.deniz * (1.0 + 0.55 * parla[..., None] * (1 - kara[..., None]))
        img = img * (1 - 0.10 * izgara[..., None]) + 0.10 * izgara[..., None] * np.float32(0.75)
        kara_renk = KARA * self.doku[..., None]
        img += (kara_renk - img) * kara[..., None]
        img += (NEHIR - img) * (nehir * 0.65)[..., None]

        # --- devletin alanlari
        a = 1.0 / (s * self.A.COZ)
        c = (cx - ox / s - self.A.x0) / self.A.COZ
        f = (self.A.y1 - cy - oy / s) / self.A.COZ
        tf = (a, 0.0, c, 0.0, a, f)
        Fd = np.asarray(self.Fd_img.transform((W, H), Image.AFFINE, tf, resample=Image.BILINEAR, fillcolor=float(SONSUZ)))
        Fv = np.asarray(self.Fv_img.transform((W, H), Image.AFFINE, tf, resample=Image.BILINEAR, fillcolor=float(SONSUZ)))
        vd = Image.new("L", (W * SS, H * SS), 0)
        vv = Image.new("L", (W * SS, H * SS), 0)
        dd, dv = ImageDraw.Draw(vd), ImageDraw.Draw(vv)
        x0g, y0g, x1g, y1g = gorus
        for ta, tur, halkalar, kutu in self.bolge_vektor:
            if ta > t or kutu[2] < x0g or kutu[0] > x1g or kutu[3] < y0g or kutu[1] > y1g:
                continue
            ciz = dd if tur == "d" else dv
            for h in halkalar:
                px = ((h[:, 0] - cx) * s + ox) * SS
                py = (oy - (h[:, 1] - cy) * s) * SS
                ciz.polygon(np.stack([px, py], 1).ravel().tolist(), fill=255)
        vek_d = np.asarray(vd.reduce(SS), np.float32) / 255.0
        vek_v = np.asarray(vv.reduce(SS), np.float32) / 255.0
        D = Fd <= t
        Vm = (Fv <= t) & ~D
        Dimg = Image.fromarray((D * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.75))
        Vimg = Image.fromarray((Vm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.75))
        Ad = np.asarray(Dimg, np.float32) / 255.0 * kara * vek_d
        Av = np.asarray(Vimg, np.float32) / 255.0 * kara * vek_v * (1 - Ad)

        if Av.any():
            vr = self.vasal_a + (self.vasal_k - self.vasal_a) * (self.tarama * 0.55)[..., None]
            img += (vr - img) * (Av * 0.72)[..., None]
            Av_img = Image.fromarray((Av * 255).astype(np.uint8))
            ve = Av - np.asarray(Av_img.filter(ImageFilter.MinFilter(3)), np.float32) / 255.0
            img += (self.vasal_k - img) * (np.clip(ve, 0, 1) * 0.8)[..., None]

        if Ad.any():
            Ad_img = Image.fromarray((Ad * 255).astype(np.uint8))
            parilti = np.asarray(Ad_img.filter(ImageFilter.GaussianBlur(7)), np.float32) / 255.0
            dis = np.clip(parilti - Ad, 0, 1)
            img += (self.parilti - img) * (dis * 0.45)[..., None]
            img += (self.renk * (0.92 + 0.08 * self.doku[..., None]) - img) * (Ad * 0.84)[..., None]
            taze = np.clip(1.0 - (t - Fd) / 0.5, 0.0, 1.0) * Ad
            img += (ALTIN - img) * (taze ** 1.6 * 0.5)[..., None]
            kenar = Ad - np.asarray(Ad_img.filter(ImageFilter.MinFilter(5)), np.float32) / 255.0
            img += (self.renk_sinir - img) * (np.clip(kenar, 0, 1) * 0.85)[..., None]

        # kiyi cizgisi en ustte (adalar okunur kalsin)
        img += (KIYI - img) * (kiyi_a * 0.55)[..., None]

        # --- etiketler, sehirler, nabizlar
        self._denizler(img, kam, t)
        self._sehirler(img, kam, t)
        self._nabizlar(img, kam, t)
        if t > self.tson + 0.2:
            self._kitalar(img, kam, t)

        img *= self.vinyet
        img *= self.hud_golge
        self._hud(img, t)

        # giris / cikis kararmasi
        k = min(_ss(t / 0.45), 1.0 - _ss((t - (self.SURE - 0.75)) / 0.75))
        img *= k
        return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)

    # ---------------------------------------------------------- katmanlar
    def _denizler(self, img, kam, t):
        for ad, lon, lat, aci, boy_km in self.S.DENIZLER:
            x, y = self.PROJ.ileri(lon, lat)
            px, py = self.ekran(kam, float(x), float(y))
            if not (-300 < px < self.W + 300 and -300 < py < self.H + 300):
                continue
            boy = kam[0] * boy_km
            if boy < 13 or boy > 46:
                continue
            alfa = min(1.0, (boy - 13) / 6) * min(1.0, (46 - boy) / 8) * 0.55
            ekran_aci = int(round(aci + self.PROJ.donme(lon))) if aci else 0
            sp = yazi(ad, "EBGaramond-Italic.ttf", int(boy), (190, 214, 222, 255),
                      agirlik=500, aralik=int(boy * 0.35), golge=0.0, hiza="orta", aci=ekran_aci)
            yapistir(img, sp, px, py, alfa * _ss(t / 0.8))

    def _kitalar(self, img, kam, t):
        alfa = _ss((t - self.tson - 0.2) / 0.9) * 0.82
        boy = 46 if self.duzen == "yatay" else 40
        for ad, lon, lat, _ in self.S.KITALAR:
            x, y = self.PROJ.ileri(lon, lat)
            px, py = self.ekran(kam, float(x), float(y))
            sp = yazi(ad, "Cinzel.ttf", boy, (248, 236, 205, 255), agirlik=700,
                      aralik=int(boy * 0.55), golge=0.85, hiza="orta")
            yapistir(img, sp, px, py - boy * 0.6, alfa)

    def _sehirler(self, img, kam, t):
        yatay = self.duzen == "yatay"
        bas_ad = self._baskent_ad(t)
        for i, (ad, x, y, tb, tur) in enumerate(self.sehirler):
            if t < tb - 0.05:
                continue
            px, py = self.ekran(kam, x, y)
            if not (-80 < px < self.W + 80 and -80 < py < self.H + 80):
                continue
            a = _ss((t - tb + 0.05) / 0.35)
            if tur == "savas":
                ik = _ikon("savas", 20 if yatay else 22)
            elif ad == bas_ad:
                ik = _ikon("yildiz", 17 if yatay else 19)
            else:
                ik = _ikon("nokta", 7 if tur == "buyuk" else 5)
            yapistir(img, ik, px, py, a)
            ea = a * self.etiket_alfa(t, i)
            if ea <= 0.01:
                continue
            fs, buyuk = self._etiket_boyu(ad, tur, ad == bas_ad)
            sp = yazi(ad, "EBGaramond.ttf", fs, KREM_T, agirlik=700 if buyuk else 600,
                      golge=0.95, kontur=1)
            yapistir(img, sp, px + 12, py - fs * 0.62, ea)

    def _nabizlar(self, img, kam, t):
        for o, (x, y) in zip(self.S.OLAYLAR, self.olay_xy):
            dt = t - o["t"]
            if not (-0.05 < dt < 1.6):
                continue
            px, py = self.ekran(kam, x, y)
            buyuk = o["ses"] in ("top", "final", "kurulus", "kusatma")
            for k, gecikme in enumerate((0.0, 0.22, 0.44) if buyuk else (0.0, 0.25)):
                u = (dt - gecikme) / 1.1
                if 0 < u < 1:
                    r = 8 + (150 if buyuk else 105) * (1 - (1 - u) ** 2.2)
                    _halka_ciz(img, px, py, r, 3.2, (255, 214, 120), (1 - u) ** 1.4 * 0.9)
            if dt < 0.35:
                _halka_ciz(img, px, py, 6, 10 * (1 - dt / 0.35) + 2, (255, 240, 200), (1 - dt / 0.35) * 0.8)

    # ---------------------------------------------------------- HUD
    def _yil_metni(self, img, t, x, y, boyut, hiza):
        S = self.S
        on, rakamlar = S.yil_parca(math.floor(float(S.yil(t)) + 1e-6))
        f = _font("Cinzel.ttf", boyut, 800)
        hucre = max(f.getlength(str(d)) for d in range(10)) * 0.96
        on_boy = int(boyut * 0.42)
        on_gen = (_font("Cinzel.ttf", on_boy, 700).getlength(on) + boyut * 0.12) if on else 0
        top = hucre * len(rakamlar) + on_gen
        bx = x if hiza == "sol" else x - top / 2
        # olay aninda altin parlama
        i = S.aktif_olay(t)
        flas = 0.0
        if i >= 0:
            flas = max(0.0, 1.0 - (t - S.OLAYLAR[i]["t"]) / 0.6)
        renk = tuple(int(KREM_T[k] + (ALTIN_T[k] - KREM_T[k]) * flas) for k in range(3)) + (255,)
        ha = self._hud_a(t)
        if on:
            sp = yazi(on, "Cinzel.ttf", on_boy, ALTIN_T, agirlik=700, golge=0.85)
            yapistir(img, sp, bx, y + boyut * 0.52, ha)
            bx += on_gen
        for j, ch in enumerate(rakamlar):
            sp = yazi(ch, "Cinzel.ttf", boyut, renk, agirlik=800, golge=0.85, hiza="orta")
            yapistir(img, sp, bx + hucre * (j + 0.5), y, ha)

    def _hud_a(self, t):
        return _ss((t - (self.t0 - 0.35)) / 0.45)

    def _sigdir(self, metin, font_ad, boyut, agirlik, aralik_oran, maks):
        while boyut > 14:
            if _metin_genislik(_font(font_ad, boyut, agirlik), metin, int(boyut * aralik_oran)) <= maks:
                break
            boyut -= 2
        return boyut

    def _baslik_sprite(self, metin, boyut, maks):
        while boyut > 18:
            f = _font("Cinzel.ttf", boyut, 700)
            if _metin_genislik(f, metin, int(boyut * 0.08)) <= maks:
                break
            boyut -= 2
        return boyut

    def _hud(self, img, t):
        yatay = self.duzen == "yatay"
        W, H = self.W, self.H
        ha = self._hud_a(t)

        S = self.S
        # --- giris basligi
        if t < self.t0 + 0.15:
            ga = _ss(t / 0.35) * (1 - _ss((t - (self.t0 - 0.45)) / 0.5))
            cy = H * (0.44 if yatay else 0.40)
            b1 = self._sigdir(S.BASLIK, "Cinzel.ttf", 92 if yatay else 74, 800, 0.065, W - 80)
            s1 = yazi(S.BASLIK, "Cinzel.ttf", b1, KREM_T,
                      agirlik=800, aralik=int(b1 * 0.065), golge=0.9, hiza="orta")
            b2 = self._sigdir(S.ALT_BASLIK, "EBGaramond-Italic.ttf", 44 if yatay else 46, 500, 0, W - 80)
            s2 = yazi(S.ALT_BASLIK, "EBGaramond-Italic.ttf", b2,
                      ALTIN_T, agirlik=500, golge=0.9, hiza="orta")
            s3 = yazi(S.yil_araligi(), "Cinzel.ttf", 40 if yatay else 44, SOLUK_T, agirlik=600,
                      aralik=8, golge=0.9, hiza="orta")
            yy = np.arange(H, dtype=np.float32)[:, None, None]
            bant = np.exp(-((yy - (cy + 20)) / (H * 0.2)) ** 2)
            img *= (1 - ga * (0.28 + 0.42 * bant))
            yapistir(img, s1, W / 2, cy - 70 + 10 * (1 - ga), ga)
            yapistir(img, s2, W / 2, cy + 50, ga)
            yapistir(img, s3, W / 2, cy + 112, ga)

        if ha <= 0:
            return

        # --- ust baslik + yil
        if yatay:
            bx, by = 64, 46
            ub = self._sigdir(S.BASLIK, "Cinzel.ttf", 28, 700, 0.18, 760)
            yapistir(img, yazi(S.BASLIK, "Cinzel.ttf", ub, ALTIN_T, agirlik=700,
                               aralik=int(ub * 0.18), golge=0.8), bx, by + (28 - ub) * 0.5, ha)
            img[by + 46:by + 48, bx:bx + 470] = img[by + 46:by + 48, bx:bx + 470] * (1 - 0.8 * ha) + \
                np.array(ALTIN_T[:3], np.float32) / 255 * 0.8 * ha
            self._yil_metni(img, t, bx - 4, by + 50, 132, "sol")
            tx, ty, maks, hz = bx, by + 228, 820, "sol"
            alt_boy, bas_boy = 34, 46
        else:
            ub = self._sigdir(S.BASLIK, "Cinzel.ttf", 38, 700, 0.16, W - 90)
            yapistir(img, yazi(S.BASLIK, "Cinzel.ttf", ub, ALTIN_T, agirlik=700,
                               aralik=int(ub * 0.16), golge=0.8, hiza="orta"), W / 2, 70 + (38 - ub) * 0.5, ha)
            img[124:126, W // 2 - 300:W // 2 + 300] = img[124:126, W // 2 - 300:W // 2 + 300] * (1 - 0.8 * ha) + \
                np.array(ALTIN_T[:3], np.float32) / 255 * 0.8 * ha
            self._yil_metni(img, t, W / 2, 128, 176, "orta")
            tx, ty, maks, hz = W / 2, 372, 1000, "orta"
            alt_boy, bas_boy = 40, 54

        # --- olay basligi (gecisli)
        i = S.aktif_olay(t)
        for j in (i - 1, i):
            if j < 0:
                continue
            o = S.OLAYLAR[j]
            giris = _ss((t - o["t"]) / 0.28)
            sonraki = S.OLAYLAR[j + 1]["t"] if j + 1 < len(S.OLAYLAR) else 99
            cikis = 1 - _ss((t - (sonraki - 0.2)) / 0.18)
            a = giris * cikis * ha
            if a <= 0.01:
                continue
            kay = 14 * (1 - giris)
            bb = self._baslik_sprite(o["baslik"], bas_boy, maks)
            sp = yazi(o["baslik"], "Cinzel.ttf", bb, ALTIN_T, agirlik=700,
                      aralik=int(bb * 0.08), golge=0.9, hiza=hz)
            yapistir(img, sp, tx, ty + kay, a)
            ab = self._sigdir(o["alt"], "EBGaramond-Italic.ttf", alt_boy, 500, 0, maks)
            sp2 = yazi(o["alt"], "EBGaramond-Italic.ttf", ab, KREM_T, agirlik=500,
                       golge=0.9, hiza=hz)
            yapistir(img, sp2, tx + (2 if hz == "sol" else 0), ty + bb * 1.22 + kay, a)

        # --- yuzolcumu + lejant
        alan = float(self.A.alan(t))
        if alan >= 1e6:
            am = f"≈ {_tr_sayi(alan / 1e6, 2)} milyon km²"
        else:
            am = f"≈ {_tr_sayi(round(alan / 1000) * 1000)} km²"
        if yatay:
            lx, ly, hz = 64, 420, "sol"
        else:
            lx, ly, hz = W / 2, 1600, "orta"
        yapistir(img, yazi("YÜZÖLÇÜMÜ", "Cinzel.ttf", 20 if yatay else 24, SOLUK_T, agirlik=600,
                           aralik=4, golge=0.8, hiza=hz), lx, ly, ha)
        yapistir(img, yazi(am, "EBGaramond.ttf", 40 if yatay else 50, KREM_T, agirlik=600,
                           golge=0.9, hiza=hz), lx, ly + (24 if yatay else 30), ha)
        self._lejant(img, lx, ly + (92 if yatay else 112), hz, ha, yatay)

        # --- zaman cizelgesi
        self._cizelge(img, t, ha, yatay)

    def _lejant(self, img, x, y, hz, a, yatay):
        boy = 22 if yatay else 28
        kare = 22 if yatay else 28
        ogeler = [(self.S.LEJANT[0], "d"), (self.S.LEJANT[1], "v")]
        sp = [yazi(m, "EBGaramond.ttf", boy, KREM_T, agirlik=500, golge=0.8) for m, _ in ogeler]
        if yatay:
            konum = [(x, y), (x, y + kare + 14)]
        else:
            genis = [kare + 12 + s_.w - 2 * s_.ax for s_ in sp]
            top = sum(genis) + 40
            x0 = x - top / 2
            konum = [(x0, y), (x0 + genis[0] + 40, y)]
        for (m, tur), s_, (px, py) in zip(ogeler, sp, konum):
            px, py = int(px), int(py)
            blok = img[py:py + kare, px:px + kare]
            if tur == "d":
                blok += (self.renk - blok) * a
            else:
                tar = self.tarama[py:py + kare, px:px + kare, None]
                renk = self.vasal_a + (self.vasal_k - self.vasal_a) * tar * 0.55
                blok += (renk - blok) * a
            img[py:py + 2, px:px + kare] *= 1 - 0.6 * a
            img[py + kare - 2:py + kare, px:px + kare] *= 1 - 0.6 * a
            yapistir(img, s_, px + kare + 12, py + kare / 2 - boy * 0.62, a)

    def _cizelge(self, img, t, a, yatay):
        W, H = self.W, self.H
        S = self.S
        if yatay:
            x0, x1, y = 64, W - 64, H - 46
        else:
            x0, x1, y = 90, W - 90, H - 120
        y0, y1 = float(S.ilk_yil), float(S.son_yil)
        X = lambda yy: x0 + (x1 - x0) * (yy - y0) / (y1 - y0)
        cur = float(S.yil(t))
        kalin = 2
        img[y - 1:y + 1, x0:x1] = img[y - 1:y + 1, x0:x1] * (1 - 0.45 * a) + 0.85 * 0.45 * a
        xc = int(X(cur))
        altin = np.array(ALTIN_T[:3], np.float32) / 255
        img[y - kalin:y + kalin, x0:xc] += (altin - img[y - kalin:y + kalin, x0:xc]) * a
        fs = 20 if yatay else 24
        for yy in cizelge_adimlari(y0, y1):
            xx = int(X(yy))
            img[y - 7:y - 2, xx - 1:xx + 1] += (0.85 - img[y - 7:y - 2, xx - 1:xx + 1]) * 0.6 * a
            sp = yazi(S.yil_metni(yy), "EBGaramond.ttf", fs, SOLUK_T, agirlik=500,
                      golge=0.8, hiza="orta")
            yapistir(img, sp, xx, y + 6, a * 0.9)
        sp = yazi(S.yil_metni(S.son_yil), "EBGaramond.ttf", fs, SOLUK_T, agirlik=700,
                  golge=0.8, hiza="orta")
        yapistir(img, sp, x1 - (sp.w / 2 - sp.ax - 10 if sp.w > 90 else 0), y + 6, a * 0.9)
        for o in S.OLAYLAR:
            xx = X(o["yil"])
            gecti = t >= o["t"] - 0.02
            ik = _ikon("nokta", 7 if gecti else 4)
            yapistir(img, ik, xx, y, a * (1.0 if gecti else 0.55))
        _halka_ciz(img, xc, y, 5, 3.5, (255, 225, 150), 0.9 * a)


def cizelge_adimlari(y0, y1):
    """Zaman cizelgesi icin yuvarlak yil isaretleri (en fazla ~6, sona cok yakin olan atlanir)."""
    aralik = y1 - y0
    adim = next((a for a in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000) if aralik / a <= 6), 1000)
    ilk = math.floor(y0 / adim) * adim + adim
    return [v for v in np.arange(ilk, y1, adim) if y1 - v > 0.45 * adim and v - y0 > 0.1 * adim]

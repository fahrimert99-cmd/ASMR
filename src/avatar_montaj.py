"""
Avatar videosu montaji (dikey 9:16, YouTube Shorts uyumlu).

Tek bir avatar gorselinden, kare kare numpy ile "canli" bir video uretir:

  - Nefes: gogus nefes egrisine gore yukselir/genisler, bas hafifce kalkar
    (gorsel, yumusak bir yer degistirme alaniyla bukulur).
  - Goz kirpma: profilde goz kapagi egrileri varsa avatar dogal araliklarla
    goz kirpar; son dongulerde nefes verirken gozlerini huzurla kapatir.
  - Kamera: cok yavas yaklasma (push-in), hafif salinim ve kayma.
  - Atmosfer: sicak isik huzmesi, nefesle yukselen toz/bokeh parcaciklari,
    vinyet ve alt bolumde okunabilirlik icin yumusak karartma.
  - Arayuz: nefes halkasi (AL'da buyur, TUT'ta durur, VER'de kuculur), geri
    sayim, dongu noktalari, faz etiketi, altyazi, baslik/kapanis kartlari ve
    ustte ilerleme cubugu.

Kareler dogrudan ffmpeg'e (rawvideo -> libx264) borulanir, ses ayni anda
muxlanir; ara PNG/klip dosyasi yazilmaz.
"""
import math
import shutil
import subprocess
from pathlib import Path

from src.avatar_senaryo import FAZ_ETIKET, Cizelge, nefes_seviyesi

FONTLAR = {
    "baslik": ["/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
    "yari": ["/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
    "metin": ["/usr/share/fonts/opentype/inter/Inter-Medium.otf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"],
}

# Faz renkleri: AL = gok mavisi, TUT = lavanta, VER = nane.
FAZ_RENK = {"al": (150, 214, 255), "tut": (198, 184, 255), "ver": (146, 236, 200),
            None: (230, 222, 255)}


def _ffmpeg() -> str:
    yol = shutil.which("ffmpeg")
    if yol:
        return yol
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _font(tur: str, boyut: int):
    from PIL import ImageFont
    for yol in FONTLAR[tur]:
        if Path(yol).exists():
            return ImageFont.truetype(yol, boyut)
    return ImageFont.load_default(size=boyut)


def _yumusak(x):
    """Skaler ya da dizi icin smoothstep (0..1)."""
    import numpy as np
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def _gecis(t: float, bas: float, bit: float, giris: float = 0.4, cikis: float = 0.4):
    """[bas, bit] araliginda yumusak giris/cikisli opaklik (0..1)."""
    if t < bas or t > bit:
        return 0.0
    return float(min(_yumusak((t - bas) / giris), _yumusak((bit - t) / cikis)))


# ------------------------------------------------------------------ yazilar

def _yazi_sprite(satirlar, font, renk=(255, 255, 255), aralik: int = 0,
                 satir_arasi: float = 1.25, golge: float = 0.6):
    """Cok satirli, ortali, golgeli yaziyi (h, w, 4) float dizi olarak cizer.

    RGB 0..255, alfa 0..1. aralik: harf araligi (px).
    """
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter

    def genislik(s):
        if not aralik:
            return font.getlength(s)
        return sum(font.getlength(ch) for ch in s) + aralik * (len(s) - 1)

    asc, desc = font.getmetrics()
    satir_h = int((asc + desc) * satir_arasi)
    pay = 14
    en = int(max(genislik(s) for s in satirlar)) + 2 * pay
    boy = satir_h * len(satirlar) + 2 * pay

    maske = Image.new("L", (en, boy), 0)
    d = ImageDraw.Draw(maske)
    for i, s in enumerate(satirlar):
        x = (en - genislik(s)) / 2
        y = pay + i * satir_h
        if not aralik:
            d.text((x, y), s, font=font, fill=255)
            continue
        for ch in s:
            d.text((x, y), ch, font=font, fill=255)
            x += font.getlength(ch) + aralik

    a = np.asarray(maske, dtype=np.float32) / 255.0
    golge_a = np.asarray(maske.filter(ImageFilter.GaussianBlur(5)), dtype=np.float32) / 255.0
    golge_a = np.roll(golge_a, 2, axis=0) * golge
    toplam_a = a + golge_a * (1.0 - a)
    rgb = np.zeros((boy, en, 3), dtype=np.float32)
    rgb[:] = renk
    rgb *= (a / np.maximum(toplam_a, 1e-6))[..., None]     # golge kismi siyah
    return np.dstack([rgb, toplam_a])


def _sar(metin: str, font, max_en: int):
    """Metni piksel genisligine gore satirlara boler."""
    satirlar, satir = [], ""
    for kelime in metin.split():
        deneme = f"{satir} {kelime}".strip()
        if font.getlength(deneme) <= max_en or not satir:
            satir = deneme
        else:
            satirlar.append(satir)
            satir = kelime
    if satir:
        satirlar.append(satir)
    return satirlar


def _bindir(kare, sprite, x_merkez: float, y_merkez: float, opaklik: float):
    """RGBA sprite'i karenin (x_merkez, y_merkez) noktasina alfa ile bindirir."""
    if opaklik <= 0.004:
        return
    h, w = sprite.shape[:2]
    H, W = kare.shape[:2]
    x0 = int(round(x_merkez - w / 2))
    y0 = int(round(y_merkez - h / 2))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x0 + w - sx0), min(H, y0 + h - sy0)
    if x1 <= x0 or y1 <= y0:
        return
    parca = sprite[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    a = parca[..., 3:4] * opaklik
    hedef = kare[y0:y1, x0:x1]
    hedef *= 1.0 - a
    hedef += parca[..., :3] * a


# ------------------------------------------------------------------ goz kirpma

def _yumusat(x, pencere: int = 7):
    """Egriyi hareketli ortalamayla yumusatir (uc noktalar korunur)."""
    import numpy as np
    x = np.asarray(x, dtype=np.float32)
    p = np.pad(x, pencere // 2, mode="edge")
    y = np.convolve(p, np.ones(pencere, dtype=np.float32) / pencere, mode="valid")
    y[0], y[-1] = x[0], x[-1]
    return y.astype(np.float32)


class GozKirpma:
    """Profildeki goz kapagi egrilerine gore gozleri kismen/tamamen kapatir.

    Her goz icin 'ust' (ust kirpik cizgisinin ust kenari) ve 'alt' (alt goz
    kapagi) noktalari verilir; iki egri goz koselerinde birlesir. Kapali goz:
    goz acikligi icten doldurulmus (inpaint) tenle ortulur ve kapanan kapagin
    kenarina koyu bir kirpik cizgisi cizilir.
    """

    def __init__(self, gorsel, gozler):
        import numpy as np
        from PIL import Image, ImageFilter

        self.gozler = []
        H, W = gorsel.shape[:2]
        for g in gozler:
            ust = np.array(g["ust"], dtype=np.float32)
            alt = np.array(g["alt"], dtype=np.float32)
            xl = float(min(ust[0, 0], alt[0, 0]))
            xr = float(max(ust[-1, 0], alt[-1, 0]))
            x0, x1 = max(0, int(xl) - 10), min(W, int(math.ceil(xr)) + 10)
            y0 = max(0, int(ust[:, 1].min()) - 12)
            y1 = min(H, int(math.ceil(alt[:, 1].max())) + 10)
            xs = np.arange(x0, x1, dtype=np.float32)
            U = _yumusat(np.interp(xs, ust[:, 0], ust[:, 1]), 11)
            L = _yumusat(np.interp(xs, alt[:, 0], alt[:, 1]), 11)
            ys = np.arange(y0, y1, dtype=np.float32)[:, None]
            ic_x = (np.clip((xs - xl) * 0.8, 0, 1) * np.clip((xr - xs) * 0.8, 0, 1))
            yama = gorsel[y0:y1, x0:x1].astype(np.float32)
            agirlik = np.array([0.299, 0.587, 0.114], dtype=np.float32)

            # Kapak teni: her sutunda gozun hemen ustundeki (ust kapak) ve
            # altindaki acik ten renginden dikey olarak doldurulur. Koyu kirpik /
            # kivrim pikselleri esikle disarida birakilir; sutunlar yatayda
            # yumusatilir (yan taraftaki isik/golge sinirlari gozun icine sizmaz).
            parlaklik = yama @ agirlik
            cevre = (ys < U - 4) | (ys > L + 2)
            bilinen = cevre & (parlaklik >= 0.80 * float(np.median(parlaklik[cevre])))

            def _sutun_rengi(bolge):
                m = (bolge & bilinen)[..., None]
                adet = m.sum(axis=0)[:, 0]
                renk = (yama * m).sum(axis=0) / np.maximum(adet, 1)[:, None]
                gecerli = adet > 0
                if not gecerli.any():
                    return np.repeat(yama[bilinen].mean(axis=0)[None], len(xs), 0)
                for k in range(3):
                    renk[:, k] = np.interp(xs, xs[gecerli], renk[gecerli, k])
                return np.stack([_yumusat(renk[:, k], 9) for k in range(3)], axis=1)

            ust_renk = _sutun_rengi((ys >= U - 11) & (ys <= U - 5))
            alt_renk = _sutun_rengi((ys >= L + 3) & (ys <= L + 9))
            dikey = np.clip((ys - U) / np.maximum(L - U, 1.0), 0, 1) ** 1.6 * 0.7
            ten = ust_renk[None] + (alt_renk - ust_renk)[None] * dikey[..., None]

            # Duz dolgu "yama" gibi durmasin: gozun hemen altindaki yanak
            # dokusunun yuksek frekansini (tarama cizgisi/gren) dolguya ekle.
            h = y1 - y0
            if y1 + 4 + h <= H:
                yanak = gorsel[y1 + 4:y1 + 4 + h, x0:x1].astype(np.float32)
                yanak_img = Image.fromarray(np.clip(yanak, 0, 255).astype(np.uint8))
                bulanik = np.asarray(yanak_img.filter(ImageFilter.GaussianBlur(2.5)),
                                     dtype=np.float32)
                ten = ten + (yanak - bulanik) * 0.9

            # Kirpik rengi: ust kirpik bandindaki en koyu piksellerin ortalamasi.
            bant = (ys >= U) & (ys <= U + 3) & (ic_x > 0.5)
            koyu = yama[bant]
            koyu = koyu[np.argsort(koyu @ agirlik)]
            kirpik = koyu[: max(1, len(koyu) // 3)].mean(axis=0) * 0.92

            oran = np.clip((xs - xl) / max(1.0, xr - xl), 0, 1)
            kalinlik = 1.3 + 2.2 * np.clip(np.sin(math.pi * oran), 0, 1) ** 0.6

            self.gozler.append(dict(x0=x0, x1=x1, y0=y0, y1=y1, U=U, L=L,
                                    ys=ys, ic_x=ic_x, ten=ten, kirpik=kirpik,
                                    kalinlik=kalinlik))

    def uygula(self, gorsel, kapanma: float):
        """kapanma 0 = acik, 1 = tamamen kapali. Yeni (kopya) gorsel dondurur."""
        import numpy as np

        if kapanma <= 0.01 or not self.gozler:
            return gorsel
        cikti = gorsel.copy()
        for g in self.gozler:
            U, L, ys, ic_x = g["U"], g["L"], g["ys"], g["ic_x"]
            # Ust kapak %85, alt kapak %15 yol alir; kapali gozde ikisi bulusur.
            E = U + kapanma * 0.85 * (L - U)                # ust kapagin kenari
            F = L - kapanma * 0.15 * (L - U)                # alt kapagin kenari
            ust_a = np.clip((ys - (U - 4.5)) / 3.0, 0, 1)
            ten_a = np.clip(E - ys + 0.5, 0, 1) * ust_a * ic_x
            alt_a = np.clip(ys - F + 0.5, 0, 1) * np.clip(L + 1.5 - ys, 0, 1) * ic_x
            # Kapanan kapagin kenarina dogru hafif golge.
            golge = 1.0 - 0.10 * np.clip(1.0 - (E - ys) / 6.0, 0, 1) * ten_a
            ten_a = np.maximum(ten_a, alt_a)
            cizgi_a = (np.clip(g["kalinlik"] / 2 + 0.7 - np.abs(ys - E), 0, 1)
                       * ic_x * min(1.0, kapanma * 5.0))
            yama = cikti[g["y0"]:g["y1"], g["x0"]:g["x1"]]
            yama[:] = yama * (1 - ten_a[..., None]) + g["ten"] * (ten_a * golge)[..., None]
            yama[:] = yama * (1 - cizgi_a[..., None]) + g["kirpik"] * cizgi_a[..., None]
        return cikti


def _kirpma_zamanlari(c: Cizelge, rng):
    """Dogal goz kirpma anlari (2.8-5.5 sn arayla) + kapali-goz araliklari."""
    kirpmalar, t = [], 2.2
    while t < c.toplam - 1.0:
        kirpmalar.append(t)
        t += float(rng.uniform(2.8, 5.5))
    # Son iki dongunun VER fazinda gozler huzurla kapanir.
    kapali = []
    verler = [f for f in c.fazlar if f.tur == "ver"]
    for f in verler[-2:]:
        kapali.append((f.bas + 0.6, f.bit - 0.7))
    # Kapali araliklarla cakisan kirpmalari at.
    kirpmalar = [k for k in kirpmalar
                 if all(not (a - 0.6 <= k <= b + 0.6) for a, b in kapali)]
    return kirpmalar, kapali


def _kapanma(t: float, kirpmalar, kapali) -> float:
    """t anindaki goz kapanma miktari (0..1)."""
    deger = 0.0
    for k in kirpmalar:
        d = t - k
        if 0 <= d < 0.3:
            if d < 0.08:
                deger = max(deger, (d / 0.08) ** 1.5)
            elif d < 0.13:
                deger = 1.0
            else:
                deger = max(deger, 1.0 - _yumusak((d - 0.13) / 0.17))
    for a, b in kapali:
        if a <= t <= b + 0.5:
            v = min(_yumusak((t - a) / 0.7), 1.0 - _yumusak((t - b) / 0.5))
            deger = max(deger, float(v))
    return float(deger)


# ------------------------------------------------------------------ sahne

class AvatarSahnesi:
    """Avatar gorseli + profilden, istenen t anindaki kareyi (RGB uint8) uretir."""

    def __init__(self, gorsel_yolu, profil: dict, c: Cizelge, en: int, boy: int,
                 tohum: int = 7):
        import numpy as np
        from PIL import Image

        self.c, self.W, self.H = c, en, boy
        self.rng = np.random.default_rng(tohum)

        # Gorseli 9:16 (en x boy) cerceveye "cover" ile oturt; profil
        # koordinatlarini da ayni olcek/kirpmaya tasi.
        img = Image.open(gorsel_yolu).convert("RGB")
        w, h = img.size
        s = max(en / w, boy / h)
        yw, yh = int(round(w * s)), int(round(h * s))
        odak = profil.get("odak") or [w / 2, h * 0.42]
        ox = int(np.clip(odak[0] * s - en / 2, 0, yw - en))
        oy = int(np.clip(odak[1] * s - boy * 0.42, 0, yh - boy))
        img = img.resize((yw, yh), Image.LANCZOS).crop((ox, oy, ox + en, oy + boy))
        self.taban = np.asarray(img, dtype=np.float32)

        def tasi(p):
            return [p[0] * s - ox, p[1] * s - oy]

        self.odak = tasi(odak)
        self.gogus_y = float(profil.get("gogus_y", h * 0.68)) * s - oy
        gozler = [{"ust": [tasi(p) for p in g["ust"]],
                   "alt": [tasi(p) for p in g["alt"]]}
                  for g in profil.get("gozler", [])]
        self.goz = GozKirpma(self.taban, gozler)
        self.kirpmalar, self.kapali = _kirpma_zamanlari(c, self.rng)
        if not gozler:
            self.kirpmalar, self.kapali = [], []

        # Sabit haritalar: cikis koordinat izgarasi, vinyet + alt karartma,
        # sicak isik huzmesi.
        Y, X = np.mgrid[0:boy, 0:en].astype(np.float32)
        self.X, self.Y = X, Y
        r = np.sqrt(((X - en * 0.5) / en) ** 2 + ((Y - boy * 0.45) / boy) ** 2)
        vinyet = 1.0 - 0.55 * np.clip(r / 0.62, 0, 1) ** 2.4
        alt = 1.0 - 0.58 * _yumusak((Y - boy * 0.60) / (boy * 0.40))
        self.carpan = (vinyet * alt)[..., None].astype(np.float32)
        isik = np.exp(-(((X - en * 1.0) ** 2) + ((Y + boy * 0.05) ** 2))
                      / (2 * (en * 0.75) ** 2))
        self.isik = (isik[..., None] * np.array([255, 214, 160], np.float32)).astype(np.float32)

        self._parcaciklar_hazirla()
        self._yazilar_hazirla()

    # -------------------------------------------------- parcaciklar
    def _parcaciklar_hazirla(self):
        import numpy as np

        n = 44
        rng = self.rng
        self.p_x = rng.uniform(0, self.W, n)
        self.p_y = rng.uniform(0, self.H, n)
        self.p_hiz = rng.uniform(7, 22, n)
        self.p_faz = rng.uniform(0, 2 * math.pi, n)
        self.p_a = rng.uniform(0.12, 0.40, n)
        boyutlar = rng.uniform(1.4, 4.8, n)
        self.p_sprite = []
        for b in boyutlar:
            yar = int(math.ceil(b * 3))
            yy, xx = np.mgrid[-yar:yar + 1, -yar:yar + 1].astype(np.float32)
            g = np.exp(-(xx ** 2 + yy ** 2) / (2 * (b * 0.9) ** 2))
            self.p_sprite.append((g[..., None] * np.array([255, 240, 214], np.float32)))

    def _parcaciklar(self, kare, t: float, nefes: float):
        H, W = self.H, self.W
        tau = t + 0.9 * nefes * 4.0          # AL'da hizlanir, VER'de yavaslar
        for i, sp in enumerate(self.p_sprite):
            yar = sp.shape[0] // 2
            y = (self.p_y[i] - self.p_hiz[i] * tau) % (H + 60) - 30
            x = self.p_x[i] + 14 * math.sin(0.23 * t + self.p_faz[i])
            a = self.p_a[i] * (0.6 + 0.4 * math.sin(1.3 * t + self.p_faz[i] * 3))
            x0, y0 = int(x) - yar, int(y) - yar
            x1, y1 = x0 + sp.shape[1], y0 + sp.shape[0]
            if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
                continue
            kare[y0:y1, x0:x1] += sp * a

    # -------------------------------------------------- yazilar
    def _yazilar_hazirla(self):
        W = self.W
        k = W / 720.0
        self.k = k
        f_ust = _font("yari", int(25 * k))
        f_baslik = _font("baslik", int(70 * k))
        f_kapanis = _font("baslik", int(58 * k))
        f_faz = _font("yari", int(30 * k))
        f_sayi = _font("baslik", int(56 * k))
        f_alt = _font("metin", int(31 * k))

        self.s_giris_ust = _yazi_sprite(["1 DAKİKALIK"], f_ust, aralik=int(5 * k))
        self.s_giris = _yazi_sprite(["Nefes Molası"], f_baslik)
        self.s_kapanis_ust = _yazi_sprite(["NEFES MOLASI · 1 DK"], f_ust, aralik=int(4 * k))
        self.s_kapanis = _yazi_sprite(["Kendine iyi bak."], f_kapanis)
        self.s_faz = {tur: _yazi_sprite([et], f_faz, aralik=int(6 * k))
                      for tur, et in FAZ_ETIKET.items()}
        self.s_sayi = {n: _yazi_sprite([str(n)], f_sayi, golge=0.35) for n in range(1, 10)}
        self.s_altyazi = [_yazi_sprite(_sar(r.metin, f_alt, int(W * 0.84)), f_alt,
                                       satir_arasi=1.18, golge=0.85)
                          for r in self.c.replikler]

    # -------------------------------------------------- nefes halkasi
    def _halka(self, kare, t: float, nefes: float, opaklik: float):
        import numpy as np

        if opaklik <= 0.004:
            return
        c, W, H, k = self.c, self.W, self.H, self.k
        cx, cy = W * 0.5, H * 0.707
        r_min, r_max = 58 * k, 100 * k
        r = r_min + (r_max - r_min) * nefes

        f = c.faz_bul(t)
        renk = np.array(FAZ_RENK[f.tur if f else None], np.float32)
        if f is not None and t - f.bas < 0.35:      # faz rengine yumusak gecis
            onceki = c.faz_bul(f.bas - 0.01)
            eski = np.array(FAZ_RENK[onceki.tur if onceki else None], np.float32)
            renk = eski + (renk - eski) * float(_yumusak((t - f.bas) / 0.35))

        yar = int(r_max + 40 * k)
        x0, y0 = int(cx) - yar, int(cy) - yar
        yama = kare[y0:y0 + 2 * yar, x0:x0 + 2 * yar]
        yy, xx = np.mgrid[0:2 * yar, 0:2 * yar].astype(np.float32)
        d = np.sqrt((xx - (cx - x0)) ** 2 + (yy - (cy - y0)) ** 2)

        dolgu = np.clip(r - d + 0.5, 0, 1) * 0.20
        rehber = np.clip(1.2 - np.abs(d - r_max), 0, 1) * 0.30
        halka = np.clip(1.8 - np.abs(d - r), 0, 1) * 0.95
        parilti = np.exp(-((d - r) / (15 * k)) ** 2) * (0.30 + 0.25 * nefes)

        for a, rgb in ((dolgu, renk), (rehber, np.array([255, 255, 255], np.float32)),
                       (halka, renk * 0.35 + 255 * 0.65)):
            a = (a * opaklik)[..., None]
            yama *= 1 - a
            yama += rgb * a
        yama += (parilti * opaklik)[..., None] * renk * 0.55

        # Halkanin icinde geri sayim + dongu noktalari; altinda faz etiketi.
        if f is not None:
            kalan = max(1, math.ceil(f.bit - t - 1e-6))
            nabiz = 0.75 + 0.25 * (1 - ((f.bit - t) % 1.0))
            _bindir(kare, self.s_sayi[min(9, kalan)], cx, cy - 8 * k, opaklik * nabiz)
            for i in range(c.dongu_sayisi):
                nx = cx + (i - (c.dongu_sayisi - 1) / 2) * 13 * k
                ny = cy + 30 * k
                dolu = i < f.dongu
                rr = 3.4 * k if dolu else 2.6 * k
                nokta = np.clip(rr - np.sqrt((xx - (nx - x0)) ** 2 + (yy - (ny - y0)) ** 2) + 0.5, 0, 1)
                a = (nokta * opaklik * (0.95 if dolu else 0.45))[..., None]
                yama *= 1 - a
                yama += 255 * a
            gecis = min(1.0, (t - f.bas) / 0.25)
            _bindir(kare, self.s_faz[f.tur], cx, cy + r_max + 34 * k, opaklik * gecis)

    # -------------------------------------------------- kare
    def kare(self, t: float):
        import numpy as np

        c, W, H = self.c, self.W, self.H
        nefes = nefes_seviyesi(c, t)
        ilerleme = t / c.toplam

        # 1) Goz kirpma (kaynak gorselde).
        kaynak = self.goz.uygula(self.taban, _kapanma(t, self.kirpmalar, self.kapali))

        # 2) Kamera + nefes bukulmesi: cikis pikselinin kaynak koordinati.
        z = 1.06 + 0.07 * (0.5 - 0.5 * math.cos(math.pi * ilerleme)) + 0.006 * nefes
        aci = math.radians(0.45) * math.sin(2 * math.pi * t / 11.0)
        dx = 4.0 * math.sin(2 * math.pi * t / 17.0)
        px, py = self.odak
        u = (self.X - px - dx) / z
        v = (self.Y - py) / z
        ca, sa = math.cos(aci), math.sin(aci)
        sx = px + u * ca + v * sa
        sy = py - u * sa + v * ca
        genlik = 0.0058 * H * nefes
        sy += genlik * (1.0 - _yumusak((sy - self.gogus_y) / (H - self.gogus_y)))
        omuz = _yumusak((sy - (self.gogus_y - 0.12 * H)) / (0.30 * H))
        sx = W * 0.5 + (sx - W * 0.5) / (1.0 + 0.014 * nefes * omuz)

        # Bilineer ornekleme.
        x0 = np.floor(sx)
        y0 = np.floor(sy)
        fx = (sx - x0)[..., None]
        fy = (sy - y0)[..., None]
        x0 = np.clip(x0.astype(np.int32), 0, W - 2)
        y0 = np.clip(y0.astype(np.int32), 0, H - 2)
        duz = kaynak.reshape(-1, 3)
        i = y0 * W + x0
        a, b = duz[i], duz[i + 1]
        cc, d = duz[i + W], duz[i + W + 1]
        kare = (a + (b - a) * fx) * (1 - fy) + (cc + (d - cc) * fx) * fy

        # 3) Atmosfer.
        kare *= 1.0 + 0.035 * nefes
        kare += self.isik * (0.07 + 0.05 * nefes)
        self._parcaciklar(kare, t, nefes)
        kare *= self.carpan

        # 4) Arayuz.
        T = c.toplam
        giris_op = _gecis(t, 0.5, c.giris - 0.3, 0.7, 0.6)
        ust_kay = 10 * self.k * (1 - giris_op)
        _bindir(kare, self.s_giris_ust, W / 2, H * 0.722 + ust_kay, giris_op)
        _bindir(kare, self.s_giris, W / 2, H * 0.775 + ust_kay, giris_op)

        halka_op = _gecis(t, c.giris - 0.5, c.kapanis_bas + 0.6, 0.6, 0.6)
        self._halka(kare, t, nefes, halka_op)

        kapanis_op = _gecis(t, c.kapanis_bas + 0.6, T + 1, 0.8, 0.1)
        _bindir(kare, self.s_kapanis_ust, W / 2, H * 0.705, kapanis_op)
        _bindir(kare, self.s_kapanis, W / 2, H * 0.755, kapanis_op)

        for r, sp in zip(c.replikler, self.s_altyazi):
            op = _gecis(t, r.bas - 0.1, r.bas + r.sure + 0.5, 0.25, 0.3)
            _bindir(kare, sp, W / 2, H * 0.868, op)

        # Ilerleme cubugu (ust kenar).
        cubuk_h = max(3, int(4 * self.k))
        kare[:cubuk_h] *= 0.75
        dolu = int(W * min(1.0, ilerleme))
        kare[:cubuk_h, :dolu] = kare[:cubuk_h, :dolu] * 0.25 + 255 * 0.75

        # 5) Basta/sonda siyahtan gecis.
        acilis = min(1.0, t / 0.8) * min(1.0, (T - t) / 1.0)
        if acilis < 1.0:
            kare *= max(0.0, acilis)
        return np.clip(kare, 0, 255).astype(np.uint8)


def render(gorsel_yolu, profil: dict, c: Cizelge, ses_wav, hedef, ayar: dict,
           kapak=None) -> Path:
    """Tum kareleri uretip ffmpeg ile sesle birlikte MP4'e kodlar."""
    from PIL import Image

    a = ayar.get("avatar", {})
    en, boy = a.get("cozunurluk", [720, 1280])
    fps = int(a.get("fps", 30))
    sahne = AvatarSahnesi(gorsel_yolu, profil, c, int(en), int(boy),
                          tohum=int(a.get("tohum", 7)))

    hedef = Path(hedef)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    komut = [_ffmpeg(), "-y", "-v", "error",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{en}x{boy}",
             "-r", str(fps), "-i", "-", "-i", str(ses_wav),
             "-map", "0:v", "-map", "1:a",
             "-c:v", "libx264", "-preset", a.get("preset", "medium"),
             "-crf", str(a.get("crf", 18)), "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
             "-shortest", str(hedef)]
    islem = subprocess.Popen(komut, stdin=subprocess.PIPE)
    toplam_kare = int(round(c.toplam * fps))
    kapak_t = float(a.get("kapak_sn", 8.6))
    try:
        for n in range(toplam_kare):
            t = n / fps
            kare = sahne.kare(t)
            if kapak is not None and abs(t - kapak_t) < 0.5 / fps:
                Image.fromarray(kare).save(kapak, quality=92)
            islem.stdin.write(kare.tobytes())
            if n % (fps * 5) == 0:
                print(f"     kare {n}/{toplam_kare}  ({t:.0f} sn)", flush=True)
    finally:
        islem.stdin.close()
        kod = islem.wait()
    if kod != 0:
        raise RuntimeError(f"ffmpeg kodlama hatasi (cikis kodu {kod})")
    return hedef

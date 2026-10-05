"""
Senaryo dogrulayici: yeni bir senaryo yayina girmeden once yapisal hatalari,
zamanlama sorunlarini, bolgeler arasindaki bosluklari (delikler) ve sinirdan
iceri giren acik bosluklari (girintiler) yakalar,
ayrica gozle kontrol icin bir kontak sayfasi (kontrol.png) uretir.

    python harita.py --senaryo roma --kontrol
"""
import math

import numpy as np

SES_TURLERI = {"kurulus", "fetih", "savas", "top", "kusatma", "ok", "deniz", "final"}
VERI_KUTUSU = (-30.0, -10.0, 160.0, 78.0)             # veri/harita/harita.json kapsami


def yapisal(S, MAKAMLAR):
    """(hatalar, uyarilar) listeleri."""
    H, U = [], []
    for ad in ("BASLIK", "OLAYLAR", "BOLGELER", "KAMERA"):
        if not getattr(S, ad, None):
            H.append(f"{ad} tanimli degil")
    if H:
        return H, U
    O = S.OLAYLAR
    if len(O) < 5:
        U.append(f"yalnizca {len(O)} olay var (onerilen 8-12)")
    for i, o in enumerate(O):
        for k in ("t", "yil", "baslik", "alt", "yer", "ses"):
            if k not in o:
                H.append(f"OLAYLAR[{i}] '{k}' alani eksik")
        if o.get("ses") not in SES_TURLERI:
            H.append(f"OLAYLAR[{i}] bilinmeyen ses turu: {o.get('ses')}")
        if o.get("ses") == "top" and not S.BARUT:
            U.append(f"OLAYLAR[{i}] 'top' barut oncesi cagda — otomatik 'kusatma' calinacak")
        if i and o["t"] - O[i - 1]["t"] < 0.9:
            U.append(f"OLAYLAR[{i}] bir oncekine cok yakin ({o['t'] - O[i - 1]['t']:.2f} sn) — baslik okunamaz")
        if i and o["yil"] <= O[i - 1]["yil"]:
            H.append(f"OLAYLAR[{i}] yili artmiyor ({O[i - 1]['yil']} -> {o['yil']})")
        if i and o["t"] <= O[i - 1]["t"]:
            H.append(f"OLAYLAR[{i}] zamani artmiyor")
    if O[0]["ses"] != "kurulus":
        U.append("ilk olayin sesi 'kurulus' degil")
    if O[-1]["ses"] != "final":
        H.append("son olayin sesi 'final' olmali (riser + buyuk vurus)")
    if not (1.0 <= O[0]["t"] <= 2.2):
        U.append(f"ilk olay {O[0]['t']} sn'de (giris basligi icin ~1.6 onerilir)")
    if not (S.SURE - 5.5 <= O[-1]["t"] <= S.SURE - 3.0):
        U.append(f"son olay {O[-1]['t']} sn'de (final icin ~{S.SURE - 4.3:.1f} onerilir)")

    ilk, son = S.ilk_yil, S.son_yil
    for b in S.BOLGELER:
        ad = b.get("ad", "?")
        if b["tur"] not in ("d", "v"):
            H.append(f"bolge '{ad}': tur 'd' ya da 'v' olmali")
        if not b.get("zaman"):
            a, z = b["yil"]
            if a >= z:
                H.append(f"bolge '{ad}': yil araligi ters ({a}, {z})")
            if z > son or a < ilk - 1:
                H.append(f"bolge '{ad}': yil araligi ({a}, {z}) zaman cizelgesi ({ilk}..{son}) disinda")
        if b.get("dogrudan") and b["dogrudan"][1] > son:
            H.append(f"bolge '{ad}': dogrudan gecisi {son} sonrasinda")
        for h in b["halkalar"]:
            if len(h) < 3:
                H.append(f"bolge '{ad}': halkada en az 3 nokta olmali")
            for lon, lat in h:
                if not (VERI_KUTUSU[0] <= lon <= VERI_KUTUSU[2] and VERI_KUTUSU[1] <= lat <= VERI_KUTUSU[3]):
                    H.append(f"bolge '{ad}': ({lon}, {lat}) harita verisi disinda")
                    break
    if not any(b.get("zaman") for b in S.BOLGELER):
        U.append("hicbir bolgede 'zaman' yok — kurulus bolgesi giris sirasinda (zaman=(0.85, 1.6)) buyumeli")

    K = S.KAMERA
    if K[0][0] != 0.0 or abs(K[-1][0] - S.SURE) > 1e-6:
        H.append("KAMERA ilk anahtar t=0, son anahtar t=SURE olmali")
    for t, (bb, g, d, k) in K:
        if not (bb < d and g < k):
            H.append(f"KAMERA t={t}: kutu (bati, guney, dogu, kuzey) sirasinda olmali")
        if bb < VERI_KUTUSU[0] or d > VERI_KUTUSU[2] or g < VERI_KUTUSU[1] or k > VERI_KUTUSU[3]:
            H.append(f"KAMERA t={t}: kutu harita verisi disina tasiyor")
    adlar = {s[0] for s in S.SEHIRLER}
    for _, ad in S.BASKENTLER:
        if ad not in adlar:
            H.append(f"BASKENTLER: '{ad}' SEHIRLER listesinde yok")
    mk = S.MUZIK.get("makam", "hicaz")
    if mk not in MAKAMLAR:
        H.append(f"MUZIK makam bilinmiyor: {mk} (secenekler: {', '.join(MAKAMLAR)})")
    yt = S.YOUTUBE
    if not yt.get("baslik"):
        U.append("YOUTUBE['baslik'] yok — otomatik baslik kullanilacak")
    elif len(yt["baslik"]) > 100:
        H.append("YOUTUBE['baslik'] 100 karakteri asiyor")
    return H, U


def _devlet_maskesi(A):
    """Son anda devlete ait kara pikselleri (bolge halkalari icinde ve fethedilmis)."""
    from PIL import Image, ImageDraw

    img = Image.new("L", (A.W, A.H), 0)
    d = ImageDraw.Draw(img)
    for _, _, _, hs, _ in A.S.bolge_isleri():
        for h in hs:
            gx = (h[:, 0] - A.x0) / A.COZ
            gy = (A.y1 - h[:, 1]) / A.COZ
            d.polygon(list(zip(gx.tolist(), gy.tolist())), fill=1)
    return np.asarray(img, bool) & A.kara & (np.minimum(A.Fd, A.Fv) < 1e8)


def _parcalar(A, maske, devlet, esik_km2, oran_esik):
    """maske'deki bagli parcalar -> [(alan_km2, boylam, enlem, oran)], buyukten kucuge.

    oran: parcanin cevresinin devlet topragi olan kesri; oran_esik altindakiler atlanir.
    """
    from scipy import ndimage as nd

    lab, _ = nd.label(maske)
    lon = np.linspace(VERI_KUTUSU[0], VERI_KUTUSU[2], 1521)
    lat = np.linspace(VERI_KUTUSU[1], VERI_KUTUSU[3], 705)
    LO, LA = np.meshgrid(lon, lat)
    PX, PY = A.S.PROJ.ileri(LO, LA)
    sonuc = []
    for i, sl in enumerate(nd.find_objects(lab), 1):
        m = lab[sl] == i
        alan = m.sum() * A.COZ ** 2
        if alan < esik_km2:
            continue
        pay = 2
        r0, r1 = max(sl[0].start - pay, 0), sl[0].stop + pay
        c0, c1 = max(sl[1].start - pay, 0), sl[1].stop + pay
        mm = lab[r0:r1, c0:c1] == i
        cevre = nd.binary_dilation(mm, iterations=1) & ~mm
        oran = (cevre & devlet[r0:r1, c0:c1]).sum() / max(1, cevre.sum())
        if oran < oran_esik:
            continue
        ys, xs = np.nonzero(m)
        X = A.x0 + (xs.mean() + sl[1].start + 0.5) * A.COZ
        Y = A.y1 - (ys.mean() + sl[0].start + 0.5) * A.COZ
        j = np.argmin((PX - X) ** 2 + (PY - Y) ** 2)
        sonuc.append((alan, float(LO.flat[j]), float(LA.flat[j]), oran))
    return sorted(sonuc, reverse=True)


def delikler(A, esik_km2=600.0):
    """Bolgelerin arasinda kalmis, ulasilmamis kara parcalari (adalar haric).

    Bir parca, cevresinin en az %30'u devlet topragiyla cevriliyse 'delik' sayilir;
    yalnizca denizle cevrili parcalar (adalar) raporlanmaz.
    """
    from scipy import ndimage as nd

    devlet = _devlet_maskesi(A)
    dolu = nd.binary_fill_holes(devlet | ~A.kara)
    return _parcalar(A, dolu & A.kara & ~devlet, devlet, esik_km2, 0.3)


def girintiler(A, yaricap_km=300.0, esik_km2=100000.0, oran_esik=0.6):
    """Sinirdan iceri derin giren, devlete ait olmayan kara parcalari (koy gibi acik bosluklar).

    delikler() yalnizca her yani kapali bosluklari bulur. Burada devlet topragi
    'yaricap_km' yaricapli bir diskle kapatilir (morfolojik kapanis); kapanisin
    icinde kalan ve cevresinin en az 'oran_esik' kadari devlet topragi olan kara
    parcalari raporlanir. Ornek: iki bolgenin arasinda unutulmus, kuzeye acik bir
    vadi. Coller ve tarihen gercek sinir boylari da cikabilir: kontrol.png'de bakin.
    """
    from scipy import ndimage as nd

    devlet = _devlet_maskesi(A)
    r = yaricap_km / A.COZ
    genis = nd.distance_transform_edt(~devlet) <= r
    kapanis = nd.distance_transform_edt(genis) > r
    delik = nd.binary_fill_holes(devlet | ~A.kara) & ~devlet       # delikler()'in buldugu
    return _parcalar(A, kapanis & A.kara & ~devlet & ~delik, devlet, esik_km2, oran_esik)


def kontak_sayfasi(C, yol, olcek=0.32):
    """Olay anlarindan kareleri tek bir PNG'de toplar (gozle kontrol icin)."""
    from PIL import Image

    S = C.S
    ts = [0.9] + [min(o["t"] + 0.45, S.SURE - 0.8) for o in S.OLAYLAR] + [S.SURE - 1.2]
    w, h = int(C.W * olcek), int(C.H * olcek)
    sut = 6 if C.W < C.H else 4
    satir = math.ceil(len(ts) / sut)
    sayfa = Image.new("RGB", (sut * w, satir * h), (0, 0, 0))
    for k, t in enumerate(ts):
        kare = Image.fromarray(C.kare(t)).resize((w, h), Image.LANCZOS)
        sayfa.paste(kare, ((k % sut) * w, (k // sut) * h))
    sayfa.save(yol)
    return yol

"""
Avatar videosu zaman cizelgesi: "1 Dakikalik Nefes Molasi".

Avatar, izleyiciyle birlikte nefes alir. Video uc bolumden olusur:

  giris  (~6 sn) : baslik karti + karsilama repligi, dogal sakin nefes
  donguler       : her biri  AL (4 sn) -> TUT (2 sn) -> VER (6 sn)  = 12 sn
  kapanis(~6 sn) : kapanis repligi + "Kendine iyi bak" karti

60 sn icin: 6 + 4 x 12 + 6 = 60. Farkli sure verilirse dongu sayisi sureye
gore hesaplanir, artan sure kapanisa eklenir.

Bu modul yalnizca VERI uretir (fazlar, replikler, nefes egrisi); ses ve
goruntu avatar_ses / avatar_montaj tarafinda bu cizelgeye gore kurulur.
"""
import math
from dataclasses import dataclass, field

# Ekranda gorunen faz etiketleri (Turkce buyuk harf: "i" -> "İ" elle yazildi).
FAZ_ETIKET = {"al": "NEFES AL", "tut": "TUT", "ver": "VER"}

GIRIS_REPLIK = "Merhaba. Bir dakikalığına her şeyi bırak, ve benimle nefes al."
KAPANIS_REPLIK = "Harikasın. Şimdi daha sakin, ve daha hafifsin."

# Her dongu icin (al, tut, ver) replikleri; son dongu her zaman SON_DONGU'dur.
DONGU_REPLIKLERI = [
    ("Burnundan yavaşça nefes al.", "Tut.", "Şimdi ağzından, yavaşça ver."),
    ("Derin bir nefes al.", "Tut.", "Bırak. Omuzların gevşesin."),
    ("Nefes al, göğsün genişlesin.", "Tut.", "Ver. Yorgunluğun uzaklaşsın."),
]
SON_DONGU = ("Son kez, derin bir nefes al.", "Tut.", "Ve yavaşça, bırak.")


@dataclass
class Faz:
    """Tek bir nefes fazi: tur = al | tut | ver | serbest."""
    tur: str
    bas: float
    bit: float
    dongu: int = 0          # 1..N (giris/kapanis icin 0)

    @property
    def sure(self) -> float:
        return self.bit - self.bas


@dataclass
class Replik:
    """Seslendirilecek ve altyazi olarak gosterilecek tek satir."""
    metin: str
    bas: float
    yuva: float             # replik bu sureyi asmamali (bir sonraki ipucuna kadar)
    sure: float = 0.0       # seslendirmeden sonra gercek sure ile doldurulur
    ses_yolu: str = ""


@dataclass
class Cizelge:
    toplam: float
    giris: float
    kapanis_bas: float
    dongu_sayisi: int
    fazlar: list = field(default_factory=list)
    replikler: list = field(default_factory=list)

    def faz_bul(self, t: float):
        """t anindaki fazi dondurur (giris/kapanis icin 'serbest')."""
        for f in self.fazlar:
            if f.bas <= t < f.bit:
                return f
        return None


def nefes_molasi(toplam: float = 60.0, al: float = 4.0, tut: float = 2.0,
                 ver: float = 6.0, giris: float = 6.0,
                 kapanis_min: float = 6.0) -> Cizelge:
    """Verilen toplam sureye gore nefes molasi cizelgesini kurar."""
    dongu_sn = al + tut + ver
    dongu_sayisi = max(1, int((toplam - giris - kapanis_min) // dongu_sn))
    kapanis_bas = giris + dongu_sayisi * dongu_sn

    c = Cizelge(toplam=float(toplam), giris=giris, kapanis_bas=kapanis_bas,
                dongu_sayisi=dongu_sayisi)
    c.replikler.append(Replik(GIRIS_REPLIK, 0.9, giris - 0.9))

    t = giris
    for i in range(dongu_sayisi):
        son = (i == dongu_sayisi - 1)
        satirlar = SON_DONGU if son else DONGU_REPLIKLERI[i % len(DONGU_REPLIKLERI)]
        for tur, sn, metin in zip(("al", "tut", "ver"), (al, tut, ver), satirlar):
            c.fazlar.append(Faz(tur, t, t + sn, i + 1))
            c.replikler.append(Replik(metin, t + 0.15, sn - 0.15))
            t += sn

    c.replikler.append(Replik(KAPANIS_REPLIK, kapanis_bas + 0.4,
                              toplam - kapanis_bas - 1.4))
    return c


def _yumusak(x: float) -> float:
    """0..1 araliginda yumusak (sinus) gecis."""
    x = min(1.0, max(0.0, x))
    return 0.5 - 0.5 * math.cos(math.pi * x)


def nefes_seviyesi(c: Cizelge, t: float) -> float:
    """Gogus doluluk seviyesi (0 = bos, 1 = dolu).

    AL fazinda 0 -> 1, TUT fazinda 1, VER fazinda 1 -> 0. Giris ve kapanista
    avatar dogal, kucuk genlikli ve sakin nefes alir.
    """
    f = c.faz_bul(t)
    if f is None:
        dogal = 0.22 * (0.5 - 0.5 * math.cos(2 * math.pi * t / 4.5))
        # Kapanista dogal nefese yumusak gecis (ani sicrama olmasin).
        if t >= c.kapanis_bas:
            return dogal * _yumusak((t - c.kapanis_bas) / 1.5)
        # Giristen ilk AL fazina: dogal nefes sona dogru sifira iner.
        return dogal * (1.0 - _yumusak((t - (c.giris - 1.2)) / 1.2))
    oran = (t - f.bas) / f.sure
    if f.tur == "al":
        return _yumusak(oran)
    if f.tur == "tut":
        return 1.0
    return 1.0 - _yumusak(oran)


def hava_akisi(c: Cizelge, t: float, dt: float = 1 / 60) -> float:
    """Nefes sesinin siddeti icin hava akisi (|d seviye / dt|, ~0..1)."""
    d = abs(nefes_seviyesi(c, t + dt) - nefes_seviyesi(c, t - dt)) / (2 * dt)
    return min(1.0, d / 0.4)

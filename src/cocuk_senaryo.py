"""
Cocuk animasyonu senaryosu ve zaman cizelgesi (Omer Asil).

Senaryo YAML'dan okunur (senaryolar/*.yaml): bolumler -> satirlar. Her satir
ayri seslendirilir; gercek ses sureleri belli olduktan sonra `zamanla` tum
satirlari, bolum kartlarini ve gecisleri hedef sureye (varsayilan 15 dk)
oturtacak sekilde zaman cizelgesine yerlestirir:

  giris karti -> [bolum karti -> satir, ara, satir, ...] x N -> kapanis karti

Hedef sureden kisa kalirsa once satir aralari (cocuklar icin daha sakin
tempo), sonra bolum aralarindaki muzik gecisleri, en son kapanis uzatilir;
uzun gelirse aralar kisaltilir.
"""
import hashlib
import math
from dataclasses import dataclass, field
from pathlib import Path

IFADELER = {"normal", "heyecan", "sasirma", "gulme", "fisilti", "uzgun",
            "dusunme", "uykulu"}
ORTAMLAR = {"oda", "gunduz", "aksam", "gece", "gece_orman", "yagmur",
            "gokkusagi", "yildizlar", "gece_sakin"}
OLAYLAR = {"kayan_yildiz", "pirilti", "konfeti", "kalpler", "piril_gel",
           "piril_mutlu", "piril_git", "bulut_gel", "bulut_mutlu", "bulut_git",
           "baykus_gel", "baykus_git", "yagmur_dur", "gokkusagi_cik",
           "atesbocegi_cok"}


@dataclass
class Satir:
    id: str
    metin: str
    bolum: int
    ifade: str = "normal"
    etiket: str = ""
    bekle: float = 0.0
    olaylar: list = field(default_factory=list)
    ekran: dict = None
    # seslendirmeden sonra doldurulur
    ses_yolu: str = ""
    sure: float = 0.0
    kelimeler: list = field(default_factory=list)   # [(bas, bit, kelime)] satira gore
    # zamanlamadan sonra doldurulur
    bas: float = 0.0

    @property
    def kisa(self) -> bool:
        """Sayma gibi tek kelimelik satirlar (daha kisa ara)."""
        return len(self.metin) <= 9

    @property
    def bit(self) -> float:
        return self.bas + self.sure


@dataclass
class Bolum:
    no: int
    ad: str
    ortam: str
    satirlar: list
    bas: float = 0.0
    bit: float = 0.0


@dataclass
class Cizelge:
    baslik: str
    alt_baslik: str
    hedef: float
    bolumler: list
    toplam: float = 0.0
    giris: float = 9.0
    kapanis_bas: float = 0.0
    satirlar: list = field(default_factory=list)
    olaylar: list = field(default_factory=list)     # [(t, olay, satir)]

    # -------------------------------------------------- sorgular
    def bolum_at(self, t: float):
        onceki = self.bolumler[0]
        for b in self.bolumler:
            if b.bas > t:
                break
            onceki = b
        return onceki

    def satir_at(self, t: float):
        for s in self.satirlar:
            if s.bas <= t < s.bit:
                return s
        return None

    def ortam_at(self, t: float, gecis: float = 2.5):
        """(onceki_ortam, ortam, karisim 0..1) - bolum basinda yumusak gecis."""
        b = self.bolum_at(t)
        i = b.no - 1
        if i == 0:
            return b.ortam, b.ortam, 1.0
        onceki = self.bolumler[i - 1].ortam
        x = (t - (b.bas - 0.8)) / gecis
        if x >= 1.0 or onceki == b.ortam:
            return b.ortam, b.ortam, 1.0
        x = max(0.0, x)
        return onceki, b.ortam, x * x * (3 - 2 * x)

    def olay_zamani(self, olay: str):
        return [t for t, o, _ in self.olaylar if o == olay]


def yukle(yol) -> Cizelge:
    """Senaryo YAML'ini okuyup (zamansiz) Cizelge dondurur."""
    import yaml

    veri = yaml.safe_load(Path(yol).read_text(encoding="utf-8"))
    bolumler, tum = [], []
    for bi, b in enumerate(veri["bolumler"], start=1):
        ortam = b.get("ortam", "oda")
        if ortam not in ORTAMLAR:
            raise ValueError(f"Bilinmeyen ortam '{ortam}' (bolum {bi})")
        satirlar = []
        for si, s in enumerate(b["satirlar"], start=1):
            if isinstance(s, str):
                s = {"metin": s}
            olaylar = s.get("olay") or []
            if isinstance(olaylar, str):
                olaylar = [olaylar]
            for o in olaylar:
                if o not in OLAYLAR:
                    raise ValueError(f"Bilinmeyen olay '{o}' (bolum {bi}, satir {si})")
            ifade = s.get("ifade", "normal")
            if ifade not in IFADELER:
                raise ValueError(f"Bilinmeyen ifade '{ifade}' (bolum {bi}, satir {si})")
            ekran = s.get("ekran")
            if isinstance(ekran, (str, int)):
                ekran = {"yazi": str(ekran)}
            satir = Satir(id=f"b{bi:02d}_s{si:02d}", metin=str(s["metin"]).strip(),
                          bolum=bi, ifade=ifade, etiket=s.get("etiket", ""),
                          bekle=float(s.get("bekle", 0.0)), olaylar=olaylar,
                          ekran=ekran)
            satirlar.append(satir)
            tum.append(satir)
        bolumler.append(Bolum(bi, b["ad"], ortam, satirlar))
    return Cizelge(baslik=veri.get("baslik", "Ömer Asil"),
                   alt_baslik=veri.get("alt_baslik", ""),
                   hedef=float(veri.get("hedef_sure", 900)),
                   bolumler=bolumler, satirlar=tum)


def metin_ozeti(c: Cizelge) -> str:
    """Seslendirme icin satir listesi (id <TAB> metin) - harici uretim icin."""
    return "\n".join(f"{s.id}\t{s.metin}" for s in c.satirlar) + "\n"


def parmak_izi(c: Cizelge) -> str:
    h = hashlib.sha1("\n".join(s.metin for s in c.satirlar).encode("utf-8"))
    return h.hexdigest()[:10]


def zamanla(c: Cizelge, hedef: float = None, giris: float = 9.0,
            kapanis: float = 12.0) -> Cizelge:
    """Seslendirilmis satirlari hedef sureye oturtarak zamanlar."""
    hedef = float(hedef or c.hedef)
    n_satir = len(c.satirlar)
    n_bolum = len(c.bolumler)
    konusma = sum(s.sure + s.bekle for s in c.satirlar)

    # Varsayilan aralar ve sinirlari.
    ara, ara_kisa = 0.60, 0.42
    bolum_basi, bolum_sonu = 3.2, 1.6

    def toplam(ara_ek=0.0, bolum_ek=0.0, kapanis_ek=0.0, olcek=1.0):
        aralar = sum((ara_kisa if s.kisa else ara) * olcek + ara_ek for s in c.satirlar)
        return (giris + konusma + aralar
                + n_bolum * (bolum_basi * min(1.0, olcek * 1.2) + bolum_sonu * olcek + bolum_ek)
                + kapanis + kapanis_ek)

    ara_ek = bolum_ek = kapanis_ek = 0.0
    olcek = 1.0
    eksik = hedef - toplam()
    uzun = eksik < 0
    if eksik > 0:
        ara_ek = min(0.38, eksik / n_satir)
        eksik = hedef - toplam(ara_ek)
        bolum_ek = min(9.0, max(0.0, eksik) / n_bolum)
        eksik = hedef - toplam(ara_ek, bolum_ek)
        kapanis_ek = max(0.0, eksik)
    elif eksik < 0:
        # Aralari en fazla %35 kisalt.
        for olcek in [1 - k * 0.05 for k in range(1, 8)]:
            if toplam(olcek=olcek) <= hedef:
                break

    t = giris
    for b in c.bolumler:
        b.bas = t
        t += bolum_basi * min(1.0, olcek * 1.2)
        for s in b.satirlar:
            s.bas = t
            t += s.sure + s.bekle + (ara_kisa if s.kisa else ara) * olcek + ara_ek
        t += bolum_sonu * olcek + bolum_ek
        b.bit = t
    c.giris = giris
    c.kapanis_bas = t
    c.toplam = t + kapanis if uzun else max(hedef, t + kapanis + kapanis_ek)
    c.toplam = float(math.ceil(c.toplam * 24 - 1e-6) / 24)

    c.olaylar = sorted(((s.bas + 0.05, o, s) for s in c.satirlar for o in s.olaylar),
                       key=lambda x: x[0])
    return c

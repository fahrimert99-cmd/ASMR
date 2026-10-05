"""Senaryo dosyalarinin ortak yardimcilari."""


def b(ad, tur, yil, halkalar, tohum=None, dogrudan=None, zaman=None):
    """Bir fetih/baglanma bolgesi.

    ad       : gorunmeyen aciklayici ad (kontrol raporlarinda kullanilir)
    tur      : "d" dogrudan yonetim | "v" vasal / bagli devlet
    yil      : (baslangic, bitis) — bolge bu yillar arasinda yayilir (MO icin negatif)
    halkalar : [(boylam, enlem), ...] tek halka ya da halka listesi (kiyida denize tasabilir)
    tohum    : [(boylam, enlem), ...] yayilmanin basladigi sehir(ler); yoksa mevcut sinirdan
    dogrudan : (a, b) vasal bolge bu yillarda dogrudan yonetime gecer
    zaman    : (t0, t1) yil yerine dogrudan video saniyesi (kurulus bolgesi icin)
    """
    if isinstance(halkalar[0][0], (int, float)):
        halkalar = [halkalar]
    return dict(ad=ad, tur=tur, yil=yil, halkalar=halkalar, tohum=tohum,
                dogrudan=dogrudan, zaman=zaman)

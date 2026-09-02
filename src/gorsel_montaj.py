"""
Gorsel montaj yardimcilari (ASMR / klip birlestirme icin ortak).

Tam ekran gorsele yavas "Ken Burns" hareketi veren ve klipler/sahneler arasi
yumusak crossfade uygulayan ince, surumler-arasi (moviepy 1.x/2.x) guvenli
yardimcilar. asmr_montaj ve klip_montaj bu iki fonksiyonu paylasir.
"""
from src.video_araci import sure_ver, konum_ver, boyutlandir


def _ken_burns(mp, gorsel: str, sure: float, en: int, boy: int,
               zoom: float = 0.06, iceri: bool = True):
    """Tam ekran (en x boy) gorseli, sure boyunca yavas zoom ile canlandirir.

    iceri=True  -> yavas yakinlasma (1.0 -> 1+zoom)
    iceri=False -> yavas uzaklasma (1+zoom -> 1.0)
    Zoom yapilamazsa sabit tam ekran gorsele duser.
    """
    taban = boyutlandir(mp.ImageClip(gorsel), (en, boy))
    if not zoom or zoom <= 0:
        return sure_ver(taban, sure)

    if iceri:
        olcek = lambda t: 1.0 + zoom * (t / max(sure, 0.1))
    else:
        olcek = lambda t: (1.0 + zoom) - zoom * (t / max(sure, 0.1))

    try:
        buyuyen = None
        for ad in ("resized", "resize"):
            m = getattr(taban, ad, None)
            if callable(m):
                buyuyen = m(olcek)
                break
        if buyuyen is None:
            return sure_ver(taban, sure)
        buyuyen = konum_ver(buyuyen, ("center", "center"))
        kare = mp.CompositeVideoClip([buyuyen], size=(en, boy))
        return sure_ver(kare, sure)
    except Exception:
        return sure_ver(taban, sure)


def _gecis_uygula(mp, klip, sure: float):
    """Klibe kisa bir crossfade-in uygular (surumler arasi guvenli). Olmazsa
    klibi aynen dondurur."""
    if sure <= 0:
        return klip
    # moviepy 2.x: with_effects([vfx.CrossFadeIn(sure)])
    try:
        from moviepy import vfx
        if hasattr(vfx, "CrossFadeIn") and hasattr(klip, "with_effects"):
            return klip.with_effects([vfx.CrossFadeIn(sure)])
    except Exception:
        pass
    # moviepy 1.x: crossfadein(sure)
    m = getattr(klip, "crossfadein", None)
    if callable(m):
        try:
            return m(sure)
        except Exception:
            pass
    return klip

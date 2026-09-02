"""
Seslendirme (ASMR opsiyonel yumusak anlatim).

edge-tts (Microsoft; bedava, anahtarsiz, Turkce sesler) ile tek akista hem mp3
sesini hem de kelime zamanlamasindan turetilen bir .srt altyazi uretir.
asmr.py bu modulun `_edge_seslendir` fonksiyonunu kullanir.
"""
import asyncio
import time
from pathlib import Path


def _srt_zaman(sn: float) -> str:
    """Saniyeyi SRT zaman damgasina cevirir (00:00:00,000)."""
    ms = max(0, int(round(sn * 1000)))
    saat, ms = divmod(ms, 3_600_000)
    dk, ms = divmod(ms, 60_000)
    san, ms = divmod(ms, 1000)
    return f"{saat:02d}:{dk:02d}:{san:02d},{ms:03d}"


def _srt_olustur(metin: str, kelimeler: list, max_kelime: int = 8) -> str:
    """edge-tts kelime sinirlarindan (offset/duration, 100ns tik) SRT metni uretir.

    Kelime zamanlamasi gelmezse tek bir cue'ye kaba sure tahminiyle tum metni yazar.
    """
    if not kelimeler:
        sure = max(1.5, len(metin.split()) * 0.4)
        return f"1\n{_srt_zaman(0)} --> {_srt_zaman(sure)}\n{metin.strip()}\n\n"

    gruplar, grup = [], []
    for off, dur, txt in kelimeler:
        grup.append((off, dur, txt))
        if len(grup) >= max_kelime or txt.strip().endswith((".", "!", "?", "…")):
            gruplar.append(grup)
            grup = []
    if grup:
        gruplar.append(grup)

    parcalar = []
    for i, g in enumerate(gruplar, start=1):
        bas = g[0][0] / 10_000_000
        bit = (g[-1][0] + g[-1][1]) / 10_000_000
        yazi = " ".join(w[2] for w in g).strip()
        parcalar.append(f"{i}\n{_srt_zaman(bas)} --> {_srt_zaman(bit)}\n{yazi}\n")
    return "\n".join(parcalar) + "\n"


def _edge_seslendir(metin, voice, rate, pitch, mp3_hedef, srt_hedef, deneme: int = 3):
    """edge-tts ile tek akista hem mp3 sesini hem kelime zamanlamasini alir;
    mp3 ve srt dosyalarini yazar. Ag/erisim hatasina karsi ustel bekleme ile
    en fazla `deneme` kez tekrar dener."""
    import edge_tts

    son_hata = None
    for i in range(max(1, deneme)):
        ses = bytearray()
        kelimeler = []

        async def _uret():
            iletisim = edge_tts.Communicate(metin, voice=voice, rate=rate, pitch=pitch)
            async for parca in iletisim.stream():
                if parca["type"] == "audio":
                    ses.extend(parca["data"])
                elif parca["type"] == "WordBoundary":
                    kelimeler.append(
                        (parca["offset"], parca["duration"], parca["text"]))

        try:
            asyncio.run(_uret())
            if not ses:
                raise RuntimeError("edge-tts bos ses dondurdu")
            Path(mp3_hedef).write_bytes(bytes(ses))
            Path(srt_hedef).write_text(
                _srt_olustur(metin, kelimeler), encoding="utf-8")
            return
        except Exception as e:  # ag/erisim hatasi vb. -> tekrar dene
            son_hata = e
            if i < max(1, deneme) - 1:
                time.sleep(2 ** i)  # 1s, 2s, ...

    raise RuntimeError(f"edge-tts {deneme} denemede basarisiz oldu: {son_hata}")

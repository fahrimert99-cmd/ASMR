"""
Cocuk animasyonu seslendirmesi (Omer Asil).

Her satir ayri seslendirilir; sessizlikleri kirpilip 44.1 kHz mono WAV olarak
cikti/<..>/ses/satirlar/<id>.wav altina yazilir. Altyazidaki kelime vurgusu
(karaoke) icin her satirin kelime zamanlari da cikarilir.

Motorlar (config cocuk.ses_motoru, "auto" = siradaki ilk calisan):
  dosya      : ses_klasoru altinda her satir icin <id>.mp3/.wav (ElevenLabs web
               arayuzunde ya da baska bir yerde uretip buraya koydugunuz sesler)
  elevenlabs : ElevenLabs API (ELEVENLABS_API_KEY). /with-timestamps ile kelime
               zamanlari da gelir. Yanitlar onbellege yazilir; ayni metin ikinci
               kez UCRETLENDIRILMEZ.
  edge       : edge-tts (bedava, internet ister) + cocuk tonu
  piper      : Piper/VITS (cevrimdisi) + rubberband ile cocuk tonu (onizleme)
"""
import base64
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from src import KOK
from src.avatar_ses import SR, _ffmpeg, _wav_oku, _wav_yaz, _piper_model

ELEVEN_URL = "https://api.elevenlabs.io/v1/text-to-speech/{ses}"

# ifade -> ElevenLabs v3 ses etiketi (config cocuk.eleven_etiketler ile degisir)
ETIKETLER = {"heyecan": "[excited]", "sasirma": "[surprised]", "gulme": "[happy]",
             "fisilti": "[whispers]", "uzgun": "[sad]", "dusunme": "[curious]",
             "uykulu": "[softly]"}


def _konusulan_metin(s, a: dict) -> str:
    """Seslendirilecek metin: v3/v4 modellerinde ifadeye gore ses etiketi eklenir."""
    model = a.get("eleven_model", "eleven_v3")
    if not any(k in model for k in ("v3", "v4")):
        return s.metin
    etiket = s.etiket or {**ETIKETLER, **a.get("eleven_etiketler", {})}.get(s.ifade, "")
    return f"{etiket} {s.metin}".strip()


# ------------------------------------------------------------------ yardimcilar

def _kirp(x, esik_db: float = -42.0, on: float = 0.04, son: float = 0.10):
    """Bas/son sessizligi kirpar; (kirpilmis, kirpilan_bas_sn) dondurur."""
    import numpy as np

    if len(x) == 0:
        return x, 0.0
    pencere = int(0.01 * SR)
    n = len(x) // pencere
    if n == 0:
        return x, 0.0
    rms = np.sqrt(np.mean(x[:n * pencere].reshape(n, pencere) ** 2, axis=1) + 1e-12)
    esik = np.max(rms) * 10 ** (esik_db / 20)
    aktif = np.where(rms > esik)[0]
    if len(aktif) == 0:
        return x, 0.0
    i0 = max(0, aktif[0] * pencere - int(on * SR))
    i1 = min(len(x), (aktif[-1] + 1) * pencere + int(son * SR))
    return x[i0:i1], i0 / SR


def _oransal_kelimeler(metin: str, sure: float):
    """Kelime zamanlarini harf sayisina gore orantili dagitir."""
    kelimeler = metin.split()
    agirlik = [len(k) + 1.5 for k in kelimeler]
    toplam = sum(agirlik) or 1.0
    t, sonuc = 0.0, []
    for k, w in zip(kelimeler, agirlik):
        d = sure * w / toplam
        sonuc.append((t, t + d, k))
        t += d
    return sonuc


def _hizalamadan_kelimeler(metin: str, hiz: dict, kayma: float):
    """ElevenLabs karakter hizalamasindan (etiketleri atlayarak) kelime zamanlari."""
    harfler = hiz.get("characters") or []
    baslar = hiz.get("character_start_times_seconds") or []
    bitler = hiz.get("character_end_times_seconds") or []
    kelimeler, kelime, k_bas, k_bit, etikette = [], "", None, None, False
    for ch, b, e in zip(harfler, baslar, bitler):
        if ch == "[":
            etikette = True
        if etikette:
            if ch == "]":
                etikette = False
            continue
        if ch.isspace():
            if kelime:
                kelimeler.append((k_bas, k_bit, kelime))
            kelime, k_bas = "", None
            continue
        kelime += ch
        k_bas = b if k_bas is None else k_bas
        k_bit = e
    if kelime:
        kelimeler.append((k_bas, k_bit, kelime))
    gosterilen = metin.split()
    if len(kelimeler) != len(gosterilen):
        return None
    return [(max(0.0, b - kayma), max(0.0, e - kayma), g)
            for (b, e, _), g in zip(kelimeler, gosterilen)]


def _kaydet(s, ham, klasor: Path, hizalama=None):
    """Ham sesi (float, 44.1k) kirpip satir WAV'ini yazar; sure/kelimeleri doldurur."""
    x, kayma = _kirp(ham)
    yol = klasor / "satirlar" / f"{s.id}.wav"
    _wav_yaz(yol, x)
    s.ses_yolu = str(yol)
    s.sure = len(x) / SR
    s.kelimeler = None
    if hizalama:
        s.kelimeler = _hizalamadan_kelimeler(s.metin, hizalama, kayma)
    if not s.kelimeler:
        s.kelimeler = _oransal_kelimeler(s.metin, s.sure)


def _cocuk_tonu(wav: Path, perde: float):
    """rubberband ile perdeyi (ve formantlari) yukseltir -> cocuksu ton."""
    if abs(perde - 1.0) < 0.01:
        return
    gecici = wav.with_suffix(".perde.wav")
    subprocess.run([_ffmpeg(), "-v", "error", "-y", "-i", str(wav), "-af",
                    f"rubberband=pitch={perde}:formant=shifted", str(gecici)], check=True)
    gecici.replace(wav)


# ------------------------------------------------------------------ motorlar

def _dosya(satirlar, a: dict, klasor: Path):
    kaynak = Path(a.get("ses_klasoru", "sesler/omer_asil"))
    if not kaynak.is_absolute():
        kaynak = KOK / kaynak
    eksik = []
    for s in satirlar:
        bulunan = next((kaynak / f"{s.id}{u}" for u in (".mp3", ".wav", ".m4a", ".ogg")
                        if (kaynak / f"{s.id}{u}").exists()), None)
        if bulunan is None:
            eksik.append(s.id)
            continue
        _kaydet(s, _wav_oku(bulunan), klasor)
    if eksik:
        raise FileNotFoundError(f"{kaynak} altinda {len(eksik)} satirin sesi yok "
                                f"(ilk: {eksik[0]})")


def _eleven_iste(metin: str, a: dict, anahtar: str):
    """ElevenLabs'ten (ses baytlari, hizalama) alir; 429/5xx'te bekleyip dener."""
    import requests

    ses = a.get("eleven_voice_id") or "AtCqglsS9sXaXLbu0Zco"
    govde = {"text": metin, "model_id": a.get("eleven_model", "eleven_v3"),
             "voice_settings": a.get("eleven_ayar") or {
                 "stability": 0.5, "similarity_boost": 0.8, "use_speaker_boost": True}}
    if a.get("eleven_dil", "tr"):
        govde["language_code"] = a.get("eleven_dil", "tr")
    basliklar = {"xi-api-key": anahtar, "Content-Type": "application/json"}
    zaman_damgali = True
    for deneme in range(6):
        url = ELEVEN_URL.format(ses=ses) + ("/with-timestamps" if zaman_damgali else "")
        y = requests.post(url, params={"output_format": "mp3_44100_128"},
                          headers=basliklar, json=govde, timeout=180)
        if y.status_code == 429 or y.status_code >= 500:
            time.sleep(min(30, 2 ** deneme))
            continue
        if y.status_code in (400, 422):
            hata = y.text.lower()
            if "language" in hata and "language_code" in govde:
                govde.pop("language_code")
                continue
            if zaman_damgali and ("timestamp" in hata or "alignment" in hata):
                zaman_damgali = False
                continue
        if y.status_code == 401:
            raise RuntimeError("ElevenLabs anahtari gecersiz (401)")
        y.raise_for_status()
        if not zaman_damgali:
            return y.content, None
        j = y.json()
        return (base64.b64decode(j["audio_base64"]),
                j.get("alignment") or j.get("normalized_alignment"))
    raise RuntimeError("ElevenLabs istekleri tekrar tekrar reddedildi (429/5xx)")


def _elevenlabs(satirlar, a: dict, klasor: Path):
    anahtar = (a.get("eleven_api_key") or os.environ.get("ELEVENLABS_API_KEY") or "").strip()
    if not anahtar:
        raise RuntimeError("ELEVENLABS_API_KEY tanimli degil")
    onbellek = klasor / "onbellek"
    onbellek.mkdir(parents=True, exist_ok=True)
    yeni = 0
    for i, s in enumerate(satirlar, start=1):
        metin = _konusulan_metin(s, a)
        anahtar_metin = json.dumps([a.get("eleven_voice_id"), a.get("eleven_model", "eleven_v3"),
                                    a.get("eleven_ayar"), a.get("eleven_dil", "tr"), metin],
                                   ensure_ascii=False)
        h = hashlib.sha1(anahtar_metin.encode("utf-8")).hexdigest()[:20]
        mp3, hiz_yol = onbellek / f"{h}.mp3", onbellek / f"{h}.json"
        if not mp3.exists():
            ses, hizalama = _eleven_iste(metin, a, anahtar)
            mp3.write_bytes(ses)
            hiz_yol.write_text(json.dumps(hizalama or {}), encoding="utf-8")
            yeni += 1
            if i % 10 == 0:
                print(f"     ElevenLabs: {i}/{len(satirlar)} satir", flush=True)
        hizalama = json.loads(hiz_yol.read_text(encoding="utf-8")) if hiz_yol.exists() else None
        _kaydet(s, _wav_oku(mp3), klasor, hizalama)
    print(f"     ElevenLabs: {yeni} yeni istek, {len(satirlar) - yeni} satir onbellekten")


def _edge(satirlar, a: dict, klasor: Path):
    from src.seslendirme import _edge_seslendir

    gecici = klasor / "gecici"
    gecici.mkdir(parents=True, exist_ok=True)
    for s in satirlar:
        mp3 = gecici / f"{s.id}.mp3"
        _edge_seslendir(s.metin, a.get("edge_ses", "tr-TR-EmelNeural"),
                        a.get("edge_hiz", "-6%"), a.get("edge_pitch", "+22Hz"),
                        mp3, mp3.with_suffix(".srt"))
        _kaydet(s, _wav_oku(mp3), klasor)


def _piper(satirlar, a: dict, klasor: Path):
    import numpy as np
    import sherpa_onnx

    ses = a.get("piper_ses", "tr_TR-dfki-medium")
    model = _piper_model(ses)
    tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=str(model / f"{ses}.onnx"), tokens=str(model / "tokens.txt"),
                data_dir=str(model / "espeak-ng-data")),
            num_threads=max(1, min(8, os.cpu_count() or 2)))))
    gecici = klasor / "gecici"
    gecici.mkdir(parents=True, exist_ok=True)
    hiz = float(a.get("piper_hiz", 0.92))
    perde = float(a.get("cocuk_perde", 1.24))
    for i, s in enumerate(satirlar, start=1):
        cikti = tts.generate(s.metin, sid=0, speed=hiz)
        wav = gecici / f"{s.id}.wav"
        _wav_yaz(wav, np.array(cikti.samples, dtype=np.float32), cikti.sample_rate)
        _cocuk_tonu(wav, perde)
        _kaydet(s, _wav_oku(wav), klasor)
        if i % 25 == 0:
            print(f"     Piper: {i}/{len(satirlar)} satir", flush=True)


MOTORLAR = {"dosya": _dosya, "elevenlabs": _elevenlabs, "edge": _edge, "piper": _piper}


def seslendir(c, ayar: dict, klasor: Path) -> str:
    """Tum satirlari seslendirir; kullanilan motorun adini dondurur."""
    a = dict(ayar.get("cocuk", {}))
    for ortam, alan in (("ELEVENLABS_VOICE_ID", "eleven_voice_id"), ("ELEVENLABS_MODEL", "eleven_model")):
        if os.environ.get(ortam, "").strip():
            a[alan] = os.environ[ortam].strip()
    istenen = a.get("ses_motoru", "auto")
    sira = (["dosya", "elevenlabs", "edge", "piper"] if istenen == "auto"
            else [istenen] + (["piper"] if istenen != "piper" and a.get("yedek", True) else []))
    klasor.mkdir(parents=True, exist_ok=True)
    for ad in sira:
        if ad == "dosya" and istenen == "auto":
            kaynak = Path(a.get("ses_klasoru", "sesler/omer_asil"))
            if not (kaynak if kaynak.is_absolute() else KOK / kaynak).exists():
                continue
        try:
            MOTORLAR[ad](c.satirlar, a, klasor)
            return ad
        except Exception as e:
            print(f"     [ses] {ad} kullanilamadi ({type(e).__name__}: {e})")
    raise RuntimeError("Hicbir seslendirme motoru calismadi")

"""
Masal seslendirmesi — ElevenLabs (zaman damgalı) ya da çevrimdışı test motoru.

Her sayfanın metni cümle cümle seslendirilir; ElevenLabs'in /with-timestamps uç
noktası harf düzeyinde zaman verir. Motor bu sürelere göre metin kartında
cümlelerin belireceği anları, sayfa sürelerini ve sahne animasyonlarını
(sahnelerin kullandığı cümle zamanlarını) yeniden hesaplar.

Ayarlar (öncelik sırasıyla):
    ortam değişkenleri : ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID (anlatıcı),
                         ELEVENLABS_MODEL, ELEVENLABS_SES_<KARAKTER> (ör. ELEVENLABS_SES_KELOGLAN)
    config/ayarlar.yaml: masal.eleven_api_key, eleven_voice_id, eleven_model,
                         eleven_ayar{stability, similarity_boost, style}, eleven_sesler{keloglan: ...}

Üretilen sesler `cikti/masal/<kimlik>/seslendirme/` altında önbelleğe alınır
(metin + ses + model + ayar özetine göre); aynı metin ikinci kez ücretlendirilmez.

Motorlar:
    elevenlabs : gerçek seslendirme (ücretli anahtar; api.elevenlabs.io erişimi gerekir)
    piper      : ücretsiz, anahtarsız, çevrimdışı sinir ağı sesi (piper-tts). Türkçe ses
                 modeli ilk çalıştırmada huggingface.co'dan indirilir (varsayılan:
                 tr_TR-fahrettin-medium; PIPER_SES ile değiştirilebilir).
    espeak     : yalnızca hattı denemek için mekanik çevrimdışı ses (espeak-ng)
"""
import base64
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parent.parent
API = "https://api.elevenlabs.io/v1"
SR = 48000
VARSAYILAN_AYAR = dict(stability=0.40, similarity_boost=0.85, style=0.35, use_speaker_boost=True)
PIPER_DEPO = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
PIPER_TERCIH = ("fahrettin", "fettah", "dfki")              # Turkce sesler icin tercih sirasi


class SeslendirmeHatasi(RuntimeError):
    pass


def _ffmpeg():
    return shutil.which("ffmpeg") or "ffmpeg"


def ayarlar():
    """config/ayarlar.yaml (varsa) + ortam degiskenleri -> seslendirme ayarlari."""
    cfg = {}
    yol = KOK / "config" / "ayarlar.yaml"
    if yol.exists():
        try:
            import yaml
            cfg = (yaml.safe_load(yol.read_text(encoding="utf-8")) or {}).get("masal", {}) or {}
        except Exception:
            cfg = {}
    sesler = {k.lower(): v for k, v in (cfg.get("eleven_sesler") or {}).items()}
    for k, v in os.environ.items():
        if k.startswith("ELEVENLABS_SES_") and v.strip():
            sesler[k[len("ELEVENLABS_SES_"):].lower()] = v.strip()
    return dict(
        anahtar=os.environ.get("ELEVENLABS_API_KEY", "").strip() or str(cfg.get("eleven_api_key") or "").strip(),
        anlatici=os.environ.get("ELEVENLABS_VOICE_ID", "").strip() or str(cfg.get("eleven_voice_id") or "").strip(),
        model=os.environ.get("ELEVENLABS_MODEL", "").strip() or cfg.get("eleven_model") or "eleven_multilingual_v2",
        ayar={**VARSAYILAN_AYAR, **(cfg.get("eleven_ayar") or {})},
        sesler=sesler,
        dil=cfg.get("eleven_dil"),
        piper_ses=os.environ.get("PIPER_SES", "").strip() or cfg.get("piper_ses") or "tr_TR-fahrettin-medium",
        piper_hiz=float(os.environ.get("PIPER_HIZ", "") or cfg.get("piper_hiz") or 1.12),
    )


def _mp3_coz(veri: bytes) -> np.ndarray:
    p = subprocess.run([_ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", "pipe:0", "-f", "f32le", "-ac", "1",
                        "-ar", str(SR), "pipe:1"], input=veri, capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


def _wav_coz(yol: Path) -> np.ndarray:
    p = subprocess.run([_ffmpeg(), "-hide_banner", "-loglevel", "error", "-i", str(yol), "-f", "f32le", "-ac", "1",
                        "-ar", str(SR), "pipe:1"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


def _sessizlik_kirp(x, esik=0.01, pay=0.04):
    """Bas/son sessizligi kirpar (hizalama zamanlarini kaydirmamak icin bastaki kirpma miktarini dondurur)."""
    i = np.nonzero(np.abs(x) > esik)[0]
    if len(i) == 0:
        return x, 0.0
    a = max(0, i[0] - int(pay * SR))
    b = min(len(x), i[-1] + int(pay * SR))
    return x[a:b], a / SR


class Klip:
    """Seslendirilmis tek cumle: ses (48 kHz mono), sure ve harf zamanlari."""

    def __init__(self, metin, ses, harfler=None, baslar=None):
        self.metin = metin
        self.ses = ses
        self.sure = len(ses) / SR
        self.harfler = harfler or list(metin)
        if baslar is None:                                # hizalama yoksa orantili tahmin
            baslar = list(np.linspace(0, self.sure * 0.95, len(self.harfler)))
        self.baslar = list(baslar)

    def kelime_zamani(self, kelime):
        """Kelimenin (kucuk/buyuk harf duyarsiz) ilk geciste baslama ani (klip icinde, sn)."""
        metin = "".join(self.harfler).lower()
        i = metin.find(kelime.lower())
        if i < 0:
            return None
        return float(self.baslar[min(i, len(self.baslar) - 1)])


class Seslendirici:
    def __init__(self, motor, onbellek: Path):
        self.motor = motor
        self.A = ayarlar()
        self.dizin = Path(onbellek)
        self.dizin.mkdir(parents=True, exist_ok=True)
        if motor == "elevenlabs":
            if not self.A["anahtar"]:
                raise SeslendirmeHatasi(
                    "ELEVENLABS_API_KEY tanimli degil. Anahtari ortam degiskeni (bulut ortaminda: ortam ayarlari; "
                    "GitHub Actions'ta: repo secret) olarak ekleyin.")
            if not self.A["anlatici"]:
                raise SeslendirmeHatasi("Anlatici sesi yok: ELEVENLABS_VOICE_ID ya da masal.eleven_voice_id ayarlayin.")

    def ses_kimligi(self, konusan):
        if konusan and konusan in self.A["sesler"]:
            return self.A["sesler"][konusan]
        return self.A["anlatici"]

    def seslendir(self, metin, konusan=None, onceki="", sonraki=""):
        if self.motor == "espeak":
            return self._espeak(metin)
        if self.motor == "piper":
            return self._piper(metin)
        ses_id = self.ses_kimligi(konusan)
        anahtar = json.dumps([metin, ses_id, self.A["model"], self.A["ayar"], self.A["dil"]], ensure_ascii=False,
                             sort_keys=True)
        h = hashlib.sha1(anahtar.encode("utf-8")).hexdigest()[:16]
        mp3, js = self.dizin / f"{h}.mp3", self.dizin / f"{h}.json"
        if not (mp3.exists() and js.exists()):
            self._elevenlabs(metin, ses_id, onceki, sonraki, mp3, js)
        hiz = json.loads(js.read_text(encoding="utf-8"))
        ses = _mp3_coz(mp3.read_bytes())
        ses, kirp = _sessizlik_kirp(ses)
        al = hiz.get("alignment") or {}
        harfler = al.get("characters")
        baslar = [max(0.0, b - kirp) for b in al.get("character_start_times_seconds", [])] or None
        return Klip(metin, ses, harfler, baslar)

    def _elevenlabs(self, metin, ses_id, onceki, sonraki, mp3: Path, js: Path):
        import requests
        govde = dict(text=metin, model_id=self.A["model"], voice_settings=self.A["ayar"])
        if onceki:
            govde["previous_text"] = onceki
        if sonraki:
            govde["next_text"] = sonraki
        if self.A["dil"]:
            govde["language_code"] = self.A["dil"]
        url = f"{API}/text-to-speech/{ses_id}/with-timestamps?output_format=mp3_44100_128"
        son_hata = None
        for deneme in range(3):
            try:
                r = requests.post(url, json=govde, headers={"xi-api-key": self.A["anahtar"]}, timeout=120)
            except requests.RequestException as e:
                son_hata = f"baglanti hatasi: {e}"
                continue
            if r.status_code == 200:
                d = r.json()
                mp3.write_bytes(base64.b64decode(d["audio_base64"]))
                js.write_text(json.dumps({"metin": metin, "ses": ses_id, "alignment": d.get("alignment")},
                                         ensure_ascii=False), encoding="utf-8")
                return
            if r.status_code in (401, 403):
                raise SeslendirmeHatasi(f"ElevenLabs yetki hatasi ({r.status_code}): anahtari kontrol edin. {r.text[:200]}")
            if r.status_code == 422:
                raise SeslendirmeHatasi(f"ElevenLabs istegi reddetti (422): {r.text[:300]}")
            son_hata = f"HTTP {r.status_code}: {r.text[:200]}"
        raise SeslendirmeHatasi(f"ElevenLabs seslendirmesi basarisiz ({son_hata}). api.elevenlabs.io erisimini kontrol edin.")

    def _piper_sesi(self):
        if getattr(self, "_piper_v", None) is not None:
            return self._piper_v
        try:
            from piper import PiperVoice
        except ImportError as e:
            raise SeslendirmeHatasi("piper-tts kurulu degil: pip install piper-tts") from e
        dizin = KOK / "cikti" / "piper_sesler"
        dizin.mkdir(parents=True, exist_ok=True)
        katalog = json.loads(self._indir("voices.json", dizin / "voices.json").read_text(encoding="utf-8"))
        ad = self.A["piper_ses"]                          # ornek: tr_TR-fahrettin-medium
        turkce = sorted(k for k, v in katalog.items() if v.get("language", {}).get("code") == "tr_TR")
        if ad not in katalog:
            secim = [k for isim in PIPER_TERCIH for k in turkce if f"-{isim}-" in k]
            if not (secim or turkce):
                raise SeslendirmeHatasi("Piper katalogunda Turkce ses bulunamadi.")
            print(f"    Piper: '{ad}' katalogda yok; Turkce sesler: {', '.join(turkce)}", flush=True)
            ad = (secim or turkce)[0]
        print(f"    Piper sesi: {ad}", flush=True)
        dosyalar = [f for f in katalog[ad]["files"] if f.endswith((".onnx", ".onnx.json"))]
        yerel = {f: self._indir(f, dizin / Path(f).name) for f in dosyalar}
        onnx = next(v for k, v in yerel.items() if k.endswith(".onnx"))
        self._piper_v = PiperVoice.load(str(onnx))
        return self._piper_v

    @staticmethod
    def _indir(goreli, hedef: Path) -> Path:
        """Piper ses deposundan dosya indirir (varsa yeniden indirmez)."""
        if hedef.exists() and hedef.stat().st_size > 0:
            return hedef
        import requests
        url = PIPER_DEPO + goreli
        try:
            r = requests.get(url, timeout=300)
        except requests.RequestException as e:
            raise SeslendirmeHatasi(f"Piper dosyasi indirilemedi ({e}). huggingface.co erisimi gerekir.") from e
        if r.status_code != 200:
            raise SeslendirmeHatasi(f"Piper dosyasi indirilemedi: HTTP {r.status_code} ({url})")
        hedef.write_bytes(r.content)
        return hedef

    def _piper(self, metin):
        import wave
        from piper import SynthesisConfig
        yol = self.dizin / ("piper_" + hashlib.sha1(f"{self.A['piper_ses']}|{self.A['piper_hiz']}|{metin}".encode())
                            .hexdigest()[:14] + ".wav")
        if not yol.exists():
            ses = self._piper_sesi()
            temiz = metin.replace("“", "").replace("”", "").replace("…", "...").replace("’", "'")
            with wave.open(str(yol), "wb") as w:
                ses.synthesize_wav(temiz, w, syn_config=SynthesisConfig(length_scale=self.A["piper_hiz"]))
        ses, _ = _sessizlik_kirp(_wav_coz(yol))
        return Klip(metin, ses)

    def _espeak(self, metin):
        exe = shutil.which("espeak-ng") or shutil.which("espeak")
        if not exe:
            raise SeslendirmeHatasi("espeak-ng kurulu degil (test motoru icin: apt install espeak-ng)")
        yol = self.dizin / ("espeak_" + hashlib.sha1(metin.encode()).hexdigest()[:12] + ".wav")
        if not yol.exists():
            temiz = metin.replace("“", "").replace("”", "").replace("…", "...")
            subprocess.run([exe, "-v", "tr", "-s", "145", "-w", str(yol), temiz], check=True, capture_output=True)
        ses, _ = _sessizlik_kirp(_wav_coz(yol))
        return Klip(metin, ses)


def masali_seslendir(masal, motor="elevenlabs", onbellek=None):
    """Masalin her sayfasini cumle cumle seslendirir -> {sayfa_no: [Klip, ...]}.

    Metin karti olmayan sayfalar (kapak) icin sayfa tanimindaki 'seslendirme' metni okunur.
    """
    from src.masal_motoru import cumlelere_bol
    onbellek = onbellek or (KOK / "cikti" / "masal" / masal.kimlik / "seslendirme")
    S = Seslendirici(motor, onbellek)
    plan = {}
    for i, s in enumerate(masal.sayfalar):
        if s.kart:
            cumleler = s.kart.cumleler
            konusanlar = s.kart.konusanlar
        elif s.t.get("seslendirme"):
            cumleler = cumlelere_bol(s.t["seslendirme"])
            konusanlar = []
        else:
            continue
        klipler = []
        for j, c in enumerate(cumleler):
            k = konusanlar[j] if j < len(konusanlar) else None
            klipler.append(S.seslendir(c, k, onceki=" ".join(cumleler[:j])[-300:],
                                       sonraki=" ".join(cumleler[j + 1:])[:300]))
            print(f"    sayfa {i:2d} cumle {j}: {klipler[-1].sure:4.1f} sn  {c[:48]}", flush=True)
        plan[i] = klipler
    return plan

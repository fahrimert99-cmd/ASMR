"""
Uzun videodan altyazili dikey kisa klipler (Shorts / Reels / TikTok) uretir.

    python shorts/shorts.py "https://www.youtube.com/watch?v=..."
    python shorts/shorts.py "C:\\Videolar\\podcast.mp4" --klip-sayisi 5
    python shorts/shorts.py video.mp4 --oran 1:1 --altyazisiz

Motor: AI-Youtube-Shorts-Generator (MIT), yerel modda calistirilir:
  yt-dlp (indirme) -> faster-whisper (Turkce transkript) -> Ollama (en iyi
  anlari secme, API anahtarsiz) -> ffmpeg + OpenCV (kesme + dikey kadraj)
  -> altyazi.py (Turkce altyazi + H.264).

Once kurulum: python shorts/kurulum.py
"""
import argparse
import json
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

# Windows konsolu varsayilan olarak UTF-8 degil; Turkce karakterler icin.
for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

SHORTS = Path(__file__).resolve().parent
MOTOR = SHORTS / "motor"
CIKTI = SHORTS / "cikti"
ONBELLEK = CIKTI / "_onbellek"

sys.path.insert(0, str(SHORTS))


def ortami_hazirla() -> None:
    """.env'i yukler, varsayilanlari (Ollama, Turkce, onbellek klasoru) ayarlar
    ve ffmpeg'i PATH'e koyar. Motor import edilmeden ONCE cagrilmalidir;
    motorun config.py'si ortam degiskenlerini import aninda okur."""
    from dotenv import load_dotenv

    load_dotenv(SHORTS / ".env")
    varsayilan = {
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "ollama",
        "OPENAI_BASE_URL": "http://localhost:11434/v1",
        "OPENAI_MODEL": "qwen2.5:7b",
        "LOCAL_WHISPER_MODEL": "small",
        "LOCAL_WHISPER_DEVICE": "auto",
    }
    for k, v in varsayilan.items():
        os.environ.setdefault(k, v)
    # Indirilen video + transkript onbellegi her zaman shorts/cikti altinda.
    os.environ["LOCAL_OUTPUT_DIR"] = str(ONBELLEK)

    if shutil.which("ffmpeg") is None:
        # Sistemde ffmpeg yoksa imageio-ffmpeg'in getirdigi ikiliyi
        # "ffmpeg" adiyla PATH'e koy (motor ve yt-dlp bu adla cagirir).
        import imageio_ffmpeg

        kaynak = Path(imageio_ffmpeg.get_ffmpeg_exe())
        bin_klasor = SHORTS / ".bin"
        bin_klasor.mkdir(exist_ok=True)
        hedef = bin_klasor / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if not hedef.exists():
            shutil.copy2(kaynak, hedef)
            hedef.chmod(0o755)
        os.environ["PATH"] = str(bin_klasor) + os.pathsep + os.environ["PATH"]


def ollama_kontrol() -> None:
    """Dil modeli adresi yerel Ollama ise calisip calismadigini ve modelin
    indirilip indirilmedigini kontrol eder; anlasilir bir hata verir."""
    taban = os.environ["OPENAI_BASE_URL"].rstrip("/")
    if "localhost" not in taban and "127.0.0.1" not in taban:
        return
    model = os.environ["OPENAI_MODEL"]
    try:
        with urllib.request.urlopen(taban + "/models", timeout=5) as yanit:
            modeller = [m["id"] for m in json.load(yanit).get("data", [])]
    except OSError:
        sys.exit(
            "HATA: Ollama calismiyor.\n"
            "  - Ollama kurulu degilse: https://ollama.com/download\n"
            "  - Kuruluysa Ollama uygulamasini acin (veya terminalde: ollama serve)"
        )
    if not any(m == model or m.split(":")[0] == model for m in modeller):
        sys.exit(f"HATA: '{model}' modeli Ollama'da yok. Terminalde calistirin:\n  ollama pull {model}")


def main() -> int:
    p = argparse.ArgumentParser(description="Uzun videodan altyazili dikey klipler uretir.")
    p.add_argument("kaynak", help="YouTube linki veya bilgisayardaki video dosyasi")
    p.add_argument("--klip-sayisi", type=int, default=3, help="Kac klip uretilsin (varsayilan 3)")
    p.add_argument("--oran", default="9:16", help="En-boy orani: 9:16 (Shorts/Reels/TikTok), 1:1, 4:5")
    p.add_argument("--dil", default="tr", help="Konusma dili (varsayilan tr). Otomatik icin: auto")
    p.add_argument("--kalite", default="1080", help="YouTube indirme cozunurlugu: 480 / 720 / 1080")
    p.add_argument("--altyazisiz", action="store_true", help="Altyazi yazma, sadece kes + kadrajla")
    a = p.parse_args()

    if not (MOTOR / "shorts_generator").exists():
        sys.exit("HATA: Motor kurulu degil. Once calistirin:  python shorts/kurulum.py")

    ortami_hazirla()
    ollama_kontrol()
    sys.path.insert(0, str(MOTOR))
    from shorts_generator import generate_shorts
    from altyazi import altyazi_yaz, kliple_kesis

    kaynak = a.kaynak.strip().strip('"')
    sonuc = generate_shorts(
        youtube_url=kaynak,
        num_clips=a.klip_sayisi,
        aspect_ratio=a.oran,
        download_format=a.kalite,
        language=None if a.dil == "auto" else a.dil,
        mode="local",
    )

    klasor = CIKTI / time.strftime("%Y%m%d-%H%M%S")
    klasor.mkdir(parents=True, exist_ok=True)
    segmentler = sonuc["transcript"]["segments"]
    ozet = []
    for n, s in enumerate(sonuc["shorts"], 1):
        ham = s.get("clip_url")
        if not ham:
            print(f"[shorts] klip {n} uretilemedi: {s.get('error')}")
            continue
        bas, son = float(s["start_time"]), float(s["end_time"])
        hedef = klasor / f"klip_{n:02d}.mp4"
        klip_segment = kliple_kesis(segmentler, bas, son)
        print(f"[altyazi] {n}/{len(sonuc['shorts'])}: {hedef.name}", flush=True)
        altyazi_yaz(ham, str(hedef), [] if a.altyazisiz else klip_segment, oran=a.oran)
        Path(ham).unlink(missing_ok=True)
        s["clip_url"] = str(hedef)
        ozet.append(
            f"#{n}  {hedef.name}   puan: {s.get('score')}   {bas:.0f}s - {son:.0f}s\n"
            f"Baslik : {s.get('title')}\n"
            f"Kanca  : {s.get('hook_sentence')}\n"
            f"Neden  : {s.get('virality_reason')}\n"
            f"Metin  : {' '.join(x['text'] for x in klip_segment)}\n"
        )

    (klasor / "klipler.txt").write_text("\n".join(ozet), encoding="utf-8")
    with open(klasor / "sonuc.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"Bitti: {len(ozet)} klip -> {klasor}")
    print("Basliklar, kanca cumleleri ve klip metinleri: klipler.txt")
    print("=" * 60)
    return 0 if ozet else 1


if __name__ == "__main__":
    sys.exit(main())

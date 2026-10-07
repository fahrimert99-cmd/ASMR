"""
Shorts uretici kurulumu (tek seferlik). VS Code'da: Terminal -> Run Task ->
"Shorts: 1) Kurulum"  veya terminalde:

    python shorts/kurulum.py

Yaptiklari:
  1. Python surumunu kontrol eder (3.10 - 3.12 onerilir).
  2. AI-Youtube-Shorts-Generator motorunu sabit bir surumden shorts/motor/
     klasorune indirir (git varsa git ile, yoksa zip ile).
  3. Python paketlerini kurar (shorts/requirements.txt).
  4. shorts/.env dosyasini ornekten olusturur (API anahtarsiz Ollama ayari).
  5. Ollama kuruluysa dil modelini indirir; degilse ne yapilacagini soyler.
"""
import io
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

SHORTS = Path(__file__).resolve().parent
MOTOR = SHORTS / "motor"
REPO = "https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator"
# Test edilen surum; motor guncellenirse once burada degistirip deneyin.
SURUM = "a0fad0fb315a64da56c496202923abcae0f0c47d"


def adim(metin: str) -> None:
    print(f"\n==> {metin}", flush=True)


def python_kontrol() -> None:
    adim(f"Python {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 10):
        sys.exit("HATA: Python 3.10 veya ustu gerekli. https://www.python.org/downloads/")
    if sys.version_info >= (3, 13):
        print("UYARI: Python 3.13+ ile bazi paketler (faster-whisper) sorun cikarabilir; "
              "sorun olursa Python 3.12 kullanin.")
    if sys.prefix == sys.base_prefix:
        print("UYARI: Sanal ortam (venv) disindasiniz. VS Code'da Ctrl+Shift+P -> "
              "'Python: Create Environment' -> Venv ile olusturmaniz onerilir.")


def motoru_indir() -> None:
    adim("Motor (AI-Youtube-Shorts-Generator) indiriliyor")
    if (MOTOR / "shorts_generator").exists():
        print("Zaten var, atlaniyor. (Yeniden indirmek icin shorts/motor klasorunu silin.)")
        return
    if shutil.which("git"):
        subprocess.run(["git", "clone", "--quiet", REPO + ".git", str(MOTOR)], check=True)
        subprocess.run(["git", "-C", str(MOTOR), "checkout", "--quiet", SURUM], check=True)
    else:
        with urllib.request.urlopen(f"{REPO}/archive/{SURUM}.zip", timeout=120) as yanit:
            arsiv = zipfile.ZipFile(io.BytesIO(yanit.read()))
        gecici = SHORTS / "_motor_zip"
        arsiv.extractall(gecici)
        shutil.move(str(next(gecici.iterdir())), str(MOTOR))
        shutil.rmtree(gecici)
    print(f"Tamam: {MOTOR}")


def paketleri_kur() -> None:
    adim("Python paketleri kuruluyor (ilk seferde birkac dakika surebilir)")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "-r", str(SHORTS / "requirements.txt")],
        check=True,
    )


def env_olustur() -> str:
    adim("Ayar dosyasi (shorts/.env)")
    env = SHORTS / ".env"
    if env.exists():
        print("Zaten var, dokunulmadi.")
    else:
        shutil.copy2(SHORTS / ".env.ornek", env)
        print("Olusturuldu (API anahtari gerekmez; Ollama kullanir).")
    model = "qwen2.5:7b"
    for satir in env.read_text(encoding="utf-8").splitlines():
        if satir.strip().startswith("OPENAI_MODEL="):
            model = satir.split("=", 1)[1].split("#")[0].strip()
    return model


def ollama_hazirla(model: str) -> bool:
    adim(f"Ollama + dil modeli ({model})")
    if not shutil.which("ollama"):
        print("Ollama bulunamadi. Kurmak icin: https://ollama.com/download\n"
              f"Kurduktan sonra bu gorevi tekrar calistirin veya terminalde: ollama pull {model}")
        return False
    print("Model indiriliyor (ilk seferde ~4-5 GB)...")
    sonuc = subprocess.run(["ollama", "pull", model])
    if sonuc.returncode != 0:
        print("UYARI: Model indirilemedi. Ollama uygulamasinin acik oldugundan emin olun.")
        return False
    return True


def main() -> int:
    python_kontrol()
    motoru_indir()
    paketleri_kur()
    model = env_olustur()
    ollama_tamam = ollama_hazirla(model)

    print("\n" + "=" * 60)
    if ollama_tamam:
        print("KURULUM TAMAM. Simdi: Terminal -> Run Task -> 'Shorts: 2) Klip uret'")
    else:
        print("Kurulum tamam, yalnizca Ollama eksik (yukaridaki adima bakin).")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ✂️ shorts/ — Uzun videodan altyazılı dikey klipler (VS Code)

Bir YouTube linki veya bilgisayarınızdaki bir video dosyası verirsiniz; sistem
en dikkat çekici anları bulur, **dikey (9:16) kısa klipler** keser ve üzerine
**Türkçe altyazı** yazar. Shorts, Reels ve TikTok için hazır çıkar.

- **Tamamen ücretsiz.** API anahtarı **gerekmez**.
- Her şey **kendi bilgisayarınızda** çalışır; video hiçbir yere yüklenmez.
- Motor: [AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator)
  (MIT lisanslı). Bu klasör onu yerel modda, Ollama ile ve Türkçe altyazıyla çalıştırır.

```
Video / YouTube linki
   │
   ├─ yt-dlp ............ videoyu indirir
   ├─ faster-whisper .... konuşmayı yazıya döker (Türkçe)
   ├─ Ollama ............ en iyi anları seçer (yerel yapay zekâ, anahtarsız)
   ├─ ffmpeg + OpenCV ... keser, yüzü takip ederek dikeye çevirir
   └─ altyazi.py ........ Türkçe altyazı yazar, 1080×1920 H.264'e çevirir
```

---

## 1. Önce bunları kurun (bir kez)

| Program | Nereden | Not |
|---|---|---|
| **Python 3.12** | https://www.python.org/downloads/ | Windows'ta kurulumun ilk ekranında **"Add python.exe to PATH"** kutusunu işaretleyin |
| **VS Code** | https://code.visualstudio.com/ | Açınca önerilen **Python** eklentisini kurun |
| **Git** | https://git-scm.com/downloads | Repoyu indirmek için |
| **Ollama** | https://ollama.com/download | Kurduktan sonra uygulamayı açık bırakın (saat yanındaki simge) |

> FFmpeg'i ayrıca kurmanıza **gerek yok**; sistemde yoksa otomatik gelir.

## 2. Repoyu VS Code'da açın

1. VS Code → `Ctrl+Shift+P` → **Git: Clone** → `https://github.com/fahrimert99-cmd/ASMR.git`
2. Bir klasör seçin → **Open** (Aç).

## 3. Sanal ortam oluşturun

`Ctrl+Shift+P` → **Python: Create Environment** → **Venv** → Python 3.12'yi seçin.

## 4. Kurulumu çalıştırın

Üst menü **Terminal → Run Task… → `Shorts: 1) Kurulum`**

Bu görev şunları yapar: motoru indirir, gerekli paketleri kurar, ayar dosyasını
(`shorts/.env`) oluşturur ve Ollama dil modelini (~4,7 GB) indirir.
İlk seferde **10–20 dakika** sürebilir. Ekranda `KURULUM TAMAM` yazınca hazırsınız.

## 5. Klip üretin

**Terminal → Run Task… → `Shorts: 2) Klip uret`**

1. YouTube linkini **veya** video dosyasının yolunu yapıştırın
   (Windows'ta dosyaya Shift + sağ tık → **Yol olarak kopyala**).
2. Kaç klip istediğinizi seçin (3 / 5 / 8).
3. Formatı seçin: `9:16` (Shorts/Reels/TikTok), `1:1` (kare), `4:5` (Instagram akışı).

Bitince klipler şurada olur: **`shorts/cikti/<tarih-saat>/`**

| Dosya | İçerik |
|---|---|
| `klip_01.mp4`, `klip_02.mp4` … | Altyazılı, 1080×1920 klipler; doğrudan yüklenebilir |
| `klipler.txt` | Her klibin başlığı, kanca cümlesi, puanı ve **konuşma metni** |
| `sonuc.json` | Tüm teknik çıktı (transkript, tüm aday anlar) |

Klasörü açmak için: **Run Task → `Shorts: Cikti klasorunu ac`**

> 💡 **Gönderi metni için:** `klipler.txt` içindeki konuşma metnini bir yapay zekâ
> sohbetine yapıştırıp LinkedIn, X ve Instagram açıklaması yazdırabilirsiniz.

### Terminalden kullanım (isteğe bağlı)

```bash
python shorts/shorts.py "https://www.youtube.com/watch?v=..."
python shorts/shorts.py "C:\Videolar\podcast.mp4" --klip-sayisi 5
python shorts/shorts.py video.mp4 --oran 1:1 --altyazisiz
python shorts/shorts.py video.mp4 --dil auto      # Türkçe dışı videolar
```

---

## ⚙️ Ayarlar — `shorts/.env`

| Ayar | Varsayılan | Ne zaman değiştirilir |
|---|---|---|
| `OPENAI_MODEL` | `qwen2.5:7b` | Bilgisayarınız yavaşsa / RAM 8 GB'tan azsa `qwen2.5:3b` yapın, sonra terminalde `ollama pull qwen2.5:3b` |
| `LOCAL_WHISPER_MODEL` | `small` | Altyazıda hata çoksa `medium` (daha doğru, daha yavaş) |
| `LOCAL_WHISPER_DEVICE` | `auto` | NVIDIA ekran kartı varsa otomatik kullanılır |
| `ALTYAZI_BUYUK_HARF` | `1` | Normal yazım için `0` |

Ücretsiz **Gemini** anahtarı kullanmak isterseniz `.env` içindeki açıklamaya bakın.

## 🖥️ Donanım

- **En az:** 8 GB RAM. Ekran kartı gerekmez; yalnızca daha yavaş çalışır.
- **Önerilen:** 16 GB RAM. NVIDIA ekran kartı varsa işlem çok hızlanır.
- 30 dakikalık bir video, ekran kartı olmayan orta seviye bir bilgisayarda yaklaşık 15–30 dakika sürer.
  Transkript önbelleğe alınır; aynı videoyu tekrar işlemek çok daha hızlıdır.

## 🛠️ Sorun giderme

| Mesaj | Çözüm |
|---|---|
| `HATA: Ollama calismiyor` | Ollama uygulamasını açın (Windows'ta Başlat menüsünden) |
| `HATA: 'qwen2.5:7b' modeli Ollama'da yok` | Terminalde: `ollama pull qwen2.5:7b` |
| `HATA: Motor kurulu degil` | `Shorts: 1) Kurulum` görevini çalıştırın |
| YouTube indirme hatası | YouTube sık değişir. Terminalde `pip install -U yt-dlp` yazın; olmazsa videoyu indirip dosya yolunu verin |
| `Whisper produced no segments` | Videoda konuşma yok veya dil farklı; `--dil auto` deneyin |
| Altyazı kelimeleri hatalı | `.env` → `LOCAL_WHISPER_MODEL=medium` |
| Klip başlıkları İngilizce | Başlıkları yapay zekâ üretir; klipler ve altyazı yine Türkçedir. Başlıkları `klipler.txt` üzerinden düzenleyin |

## 📁 Dosyalar

```
shorts/
├── kurulum.py        # Tek seferlik kurulum (motor + paketler + .env + Ollama modeli)
├── shorts.py         # Ana komut: video → altyazılı klipler
├── altyazi.py        # Türkçe altyazı yazıcı + 1080p H.264 çıktı
├── requirements.txt
├── .env.ornek        # Ayar şablonu (anahtarsız Ollama)
├── motor/            # (kurulumda iner, repoya girmez)
└── cikti/            # (klipleriniz, repoya girmez)
```

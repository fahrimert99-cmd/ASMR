# 🎧 ASMR — Otonom ASMR Video Üretim Sistemi

Yapay zekâ ile **tamamen ücretsiz** araçlar kullanarak, YouTube için otonom
ASMR / rahatlama / uyku videoları üreten sistem. **Hiçbir API anahtarı
gerektirmez** — ambient ses `numpy` ile telifsiz üretilir, görseller
Pollinations (anahtarsız) ile gelir.

İki bağımsız üretim yolu vardır:

---

## 1) Sıfırdan ASMR üret — `asmr.py`

Telifsiz, kodla üretilen ambient ses ortamı (yağmur, okyanus, şömine/ateş,
gece/orman, rüzgâr, beyaz/pembe/kahverengi gürültü) + sakinleştirici görsellerin
yavaş "Ken Burns" akışı.

```bash
python asmr.py --tema yagmur --sure 1800        # 30 dk yağmur ASMR
python asmr.py --tema somine --sure 3600        # 60 dk şömine/ateş
python asmr.py --tema okyanus --gorsel-sayisi 5 # okyanus dalgaları
python asmr.py --tema gece --anlatim "..."      # yumuşak anlatımlı ASMR
```

- **Temalar:** `yagmur` · `okyanus` · `somine` · `gece` · `ruzgar` · `beyaz` ·
  `pembe` · `kahve` (veya serbest bir görsel tarifi yazın; ses tipi metinden çözülür).
- **Bellek dostu ses:** Dikişsiz (seamless) dönen ~120 sn'lik ambient loop üretilip
  WAV'a hedef süreye kadar tekrar yazılır; 60 dk ses birkaç on MB bellekle çıkar.
- **Verimli render:** Kısa bir "Ken Burns" temel video üretilir, `ffmpeg` ile hedef
  süreye döngülenir → 60 dk video birkaç dakikada oluşur.

---

## 2) Kendi kliplerinizden uzun ASMR — `birlestir.py`

Kendi ürettiğiniz kısa video kliplerini **`klipler/`** klasörüne koyup push
ettiğinizde iş akışı **otomatik** çalışır: klipleri sırayla yumuşak geçişle
birleştirir, hedef süreye (varsayılan **30 dk**) **döngüler**. **Klip sesleri
korunur.**

```bash
python birlestir.py                               # klipler/ , 30 dk
python birlestir.py --klasor klipler --sure 3600  # 60 dk
```

- **Yükleme:** `klipler/` altına doğrudan (`01.mp4, 02.mp4…`) veya tarih
  alt-klasörü ile (`klipler/2026-09-02/…`). Alt-klasör varsa **en yenisi** işlenir.
- **Ses modları** (`config/ayarlar.yaml` → `klip.ses`): `koru` (klip sesi) ·
  `ambient_ekle` (klip sesinin altına telifsiz ambient) · `ambient_degistir`.
- Ayrıntı: [`klipler/README.md`](klipler/README.md).

---

## 🚀 Kurulum

```bash
git clone https://github.com/asilmertkimya-png/ASMR.git
cd ASMR
pip install -r requirements.txt

cp config/ayarlar.ornek.yaml config/ayarlar.yaml   # (opsiyonel; varsayılanlar da çalışır)
```

> `ayarlar.yaml` `.gitignore`'dadır; anahtarlarınız (varsa) repoya gitmez.
> Hiç anahtar girmeseniz de sistem çalışır (ambient ses + Pollinations görsel).

### 🎨 Opsiyonel: MuAPI ile üst kalite AI görsel

[Open-Generative-AI](https://github.com/Anil-matcha/Open-Generative-AI) projesinin
kullandığı [MuAPI](https://muapi.ai) (400+ görsel/video modeli) görsel motoru olarak
seçilebilir. **Ücretli/kredilidir**; anahtar yoksa, kredi biterse veya hata olursa
sistem otomatik olarak Pollinations'a düşer (üretim durmaz).

```bash
export MUAPI_API_KEY="..."                          # veya ayarlar.yaml → sahne.muapi_api_key
python asmr.py --tema yagmur --motor muapi          # varsayılan model: FLUX.1 Dev
```

Model `config/ayarlar.yaml` → `sahne.muapi_model` ile değiştirilir
(ör. `flux-schnell-image`); modele özel ek parametreler `sahne.muapi_params` altına yazılır.

## ☁️ GitHub Actions ile otomatik üretim (bedava, GPU gerekmez)

- **`ASMR`** iş akışı: her gün ~21:00 TR otomatik + manuel (`workflow_dispatch`);
  tema/süre/görsel sayısı/anlatım seçilebilir.
- **`Klip Birlestir - ASMR`** iş akışı: `klipler/**` altına video push edilince
  otomatik + manuel çalışır.
- Çıktılar: ilgili çalışmanın **Artifacts** bölümünde (`asmr-video` /
  `birlesik-asmr-video`).

### YouTube'a otomatik yükleme (opsiyonel)
Repo → **Settings → Secrets and variables → Actions**'a şu sırları ekleyin:
`YOUTUBE_OAUTH_JSON` ve `YOUTUBE_TOKEN_JSON` (kurulum: `scripts/youtube_token_al.py`).
Eklemezseniz video her zaman Artifacts'te hazır bekler.

## 🗂️ Klasör Yapısı

```
.
├── asmr.py                  # Sıfırdan ASMR orkestratörü
├── birlestir.py             # Kliplerden uzun ASMR birleştirici
├── requirements.txt
├── config/
│   └── ayarlar.ornek.yaml   # Örnek ayar dosyası (asmr / klip bölümleri)
├── klipler/                 # Günlük yüklediğiniz video klipleri (otomatik işlenir)
├── scripts/                 # YouTube token alma + yükleme
├── .github/workflows/
│   ├── asmr.yml             # Sıfırdan ASMR (günlük otomatik + manuel)
│   └── klip-birlestir.yml   # Kliplerden ASMR (push ile otomatik)
└── src/
    ├── asmr_ses.py          # Telifsiz ambient ses üreteci (numpy)
    ├── asmr_montaj.py       # ASMR montajı (Ken Burns + ffmpeg döngü)
    ├── klip_montaj.py       # Klipleri birleştir + ffmpeg döngü
    ├── sahne.py             # Pollinations/Pexels/MuAPI görsel üretimi
    ├── seslendirme.py       # edge-tts anlatım
    ├── uyku_muzik.py        # yumuşak müzik üreteci (yardımcı)
    ├── masal_montaj.py      # Ken Burns / geçiş yardımcıları
    ├── video_araci.py       # moviepy 1.x/2.x uyumluluk katmanı
    └── yukleme.py           # YouTube'a yükleme
```

---
*Kod ve yapı burada durur; ağır AI üretimi GitHub Actions'ın bedava
sunucusunda (CPU) veya yerel makinede çalışır.*

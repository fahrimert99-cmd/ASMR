# 🎧 ASMR — Otonom ASMR Video Üretim Sistemi

Yapay zekâ ile **tamamen ücretsiz** araçlar kullanarak, YouTube için otonom
ASMR / rahatlama / uyku videoları üreten sistem. **Hiçbir API anahtarı
gerektirmez** — ambient ses `numpy` ile telifsiz üretilir, görseller
Pollinations (anahtarsız) ile gelir.

Üç bağımsız üretim yolu vardır:

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

## 3) Avatar ile 1 dakikalık video — `avatar.py`

Tek bir avatar görselinden **dikey 9:16 (YouTube Shorts uyumlu), 60 saniyelik
"Nefes Molası"** videosu. Avatar izleyiciyle birlikte **nefes alır** (göğüs
yükselir, omuzlar genişler), doğal aralıklarla **göz kırpar**, son döngülerde
nefes verirken gözlerini huzurla kapatır. Ekrandaki **nefes halkası**
AL (4 sn) → TUT (2 sn) → VER (6 sn) ritmini, geri sayımı ve döngüyü gösterir.

```bash
python avatar.py                                 # avatar/avatar.jpg, 60 sn
python avatar.py --sure 90                       # daha uzun (döngü sayısı artar)
python avatar.py --ses-motoru piper              # tamamen çevrimdışı Türkçe ses
python avatar.py --ambient okyanus               # arka plan ambient değiştir
python avatar.py --gorsel foto.jpg --profil yok  # başka görsel (göz kırpmasız)
```

- **Akış:** 6 sn giriş (başlık + karşılama) · 4 × 12 sn nefes döngüsü · 6 sn kapanış.
- **Ses:** her replik ayrı seslendirilip zamanına konur — `edge-tts` (internet) →
  yoksa **Piper** (`sherpa-onnx`, çevrimdışı; model ilk sefer `modeller/` altına
  iner) → yoksa anlatımsız. Altına döngülere hizalı yumuşak akor pad'i, faz
  başlarında çan, hava akışına göre nefes sesi ve hafif yağmur (hepsi `numpy`, telifsiz).
- **Avatar profili** (`avatar/avatar.yaml`): yüz odağı, göğüs çizgisi ve göz
  kapağı eğrileri. Başka bir avatar için görseli değiştirip bu koordinatları
  güncelleyin; `gozler: []` bırakılırsa avatar yalnızca göz kırpmaz.
- **Çıktı:** `cikti/avatar-nefes-molasi/video/avatar_nefes_molasi.mp4`
  (+ `kapak.jpg`). Ayarlar: `config/ayarlar.ornek.yaml` → **`avatar`** bölümü.

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
├── avatar.py                # Avatarlı 1 dk nefes molası videosu
├── avatar/                  # Avatar görseli + profili (göz/odak koordinatları)
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
    ├── avatar_senaryo.py    # Nefes molası zaman çizelgesi (fazlar + replikler)
    ├── avatar_ses.py        # Seslendirme (edge/Piper) + müzik/çan/nefes karışımı
    ├── avatar_montaj.py     # Nefes alan, göz kırpan avatar render'ı (numpy + ffmpeg)
    ├── asmr_montaj.py       # ASMR montajı (Ken Burns + ffmpeg döngü)
    ├── klip_montaj.py       # Klipleri birleştir + ffmpeg döngü
    ├── sahne.py             # Pollinations/Pexels görsel üretimi
    ├── seslendirme.py       # edge-tts anlatım
    ├── uyku_muzik.py        # yumuşak müzik üreteci (yardımcı)
    ├── masal_montaj.py      # Ken Burns / geçiş yardımcıları
    ├── video_araci.py       # moviepy 1.x/2.x uyumluluk katmanı
    └── yukleme.py           # YouTube'a yükleme
```

---
*Kod ve yapı burada durur; ağır AI üretimi GitHub Actions'ın bedava
sunucusunda (CPU) veya yerel makinede çalışır.*

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

## 3) Osmanlı haritası animasyonu (20 sn, sesli) — `osmanli.py`

Osmanlı'nın **kuruluşundan (1299, Söğüt) en geniş sınırlarına (1683)** kadar
olan dönemi **20 saniyelik** bir harita animasyonuyla anlatır. Görüntü de ses
de **tamamen kodla** üretilir (telifsiz, API anahtarı ya da GPU gerekmez).

```bash
python osmanli.py                      # yatay 1920x1080 + dikey 1080x1920 (Shorts/Reels)
python osmanli.py --format yatay       # yalnızca YouTube yatay
python osmanli.py --format dikey --fps 60
python osmanli.py --onizleme 7.0       # 7. saniyenin tek kare PNG önizlemesi
```

- **Harita:** Natural Earth kıyı/göl/nehir verisi, Lambert konik projeksiyon,
  parşömen dokulu kara + koyu deniz. Sınırlar fetih sırasına göre **mevcut
  sınırdan ya da fethedilen şehirden dışa doğru yayılır**; vasal devletler
  taralı gösterilir.
- **Anlatım:** yıl sayacı, 11 dönüm noktası (Kuruluş, Bursa, Edirne, I. Kosova,
  İstanbul, Mısır, Mohaç, Preveze, Kıbrıs, Girit, 1683), padişah/komutan adı,
  canlı yüzölçümü sayacı (1683'te ≈ 5 milyon km²), başkent yıldızı, zaman çizelgesi.
- **Sentez ses (`src/osmanli_ses.py`):** mehter davulu (düyek usulü) ve zil,
  Hicaz makamında ney ezgisi, Re demi, top atışları (İstanbul, Mohaç, Girit),
  kılıç şakırtısı ve savaş narası (Kosova), dalga + top (Preveze), gong,
  kamera "whoosh"ları, yıl sayacı tıkırtısı, sınırlar büyüdükçe artan gürleme,
  final öncesi yükselen gerilim ve büyük vuruş. Ses −14 LUFS'a normalize edilir.
- **Çıktı:** `cikti/osmanli/osmanli_1299_1683_{yatay,dikey}.mp4`
  (hazır örnekler: `videolar/`).
- **Veri:** Tarihsel bölgeler/olaylar `src/osmanli_veri.py` içinde; harita verisi
  `veri/osmanli/harita.json` (yenilemek için `scripts/osmanli_veri_hazirla.py`).
  Sınırlar 20 saniyelik anlatım için özetlenmiştir (1402 Fetret kayıpları ve
  1683'te elde olmayan geçici fetihler gösterilmez).

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
├── osmanli.py               # Osmanlı 1299–1683 harita animasyonu (20 sn)
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
    ├── osmanli_harita.py    # Harita animasyonu render çekirdeği
    ├── osmanli_ses.py       # Sentez ses efektleri (davul, top, ney...)
    ├── osmanli_veri.py      # Tarihsel bölgeler, olaylar, kamera
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

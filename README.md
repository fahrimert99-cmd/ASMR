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

## 3) Tarihi harita Shorts'ları (20 sn, sesli, otonom yayın) — `harita.py`

Bir devletin **kuruluşundan en geniş sınırlarına** büyümesini 20 saniyelik bir
harita animasyonuyla anlatır: yıl sayacı, olay başlıkları, canlı yüzölçümü,
sentez müzik ve efektler. Görüntü de ses de **tamamen kodla** üretilir
(telifsiz; API anahtarı ya da GPU gerekmez). Her konu `senaryolar/` altında bir
veri dosyasıdır.

```bash
python harita.py --liste                          # senaryolar + yayın kuyruğu
python harita.py --senaryo osmanli                # dikey (Shorts) + yatay video
python harita.py --senaryo mogol --format dikey   # yalnızca Shorts
python harita.py --senaryo roma --onizleme 9      # tek kare PNG
python harita.py --senaryo timur --kontrol        # doğrulama + kontak sayfası
python harita.py --siradaki --format dikey --yukle   # kuyruktaki konu → YouTube (zamanlı)
```

**Hazır senaryolar:** Osmanlı (1299–1683), Roma (MÖ 509–MS 117), Büyük İskender
(MÖ 336–323), Moğol (1206–1279), Büyük Selçuklu (1037–1092), İslam devleti
(622–743), Timur (1370–1405). Örnek video: `videolar/`.

- **Harita:** Natural Earth kıyı/göl/nehir verisi, senaryoya özel Lambert konik
  projeksiyon. Sınırlar mevcut sınırdan ya da fethedilen şehirden dışa doğru
  yayılır; vasal devletler taralı gösterilir.
- **Ses (`src/harita_ses.py`):** mehter usulü davul ve zil, senaryonun makamında
  (hicaz, uşşak, saba, kürdi, nihavend, pentatonik…) otomatik bestelenen ney ezgisi,
  dem, top / kuşatma / ok yağmuru / kılıç / nara / dalga efektleri, sınır büyüdükçe
  artan gürleme, final vuruşu. −14 LUFS.
- **Yeni konu yazmak:** [`senaryolar/YAZIM_REHBERI.md`](senaryolar/YAZIM_REHBERI.md),
  konu havuzu: [`senaryolar/KONULAR.md`](senaryolar/KONULAR.md).

### 🤖 Otonom yayın (her gün 1 Shorts)

- **`Harita Shorts (günlük)`** iş akışı her gün ~17:40'ta (TR) `senaryolar/sira.json`
  kuyruğundaki ilk konuyu üretir, YouTube'a **gizli** yükler ve **ertesi gün 19:00'da
  otomatik yayınlanacak** şekilde zamanlar. Arada YouTube Studio'dan kontrol edip
  yayını iptal edebilirsiniz. Elle çalıştırırken senaryo ve yayın modu
  (`zamanli`, `hemen`, `gizli`, `yukleme-yok`) seçilebilir.
- **`Harita senaryo önizleme`** iş akışı, senaryo değiştiren her PR'da tüm
  senaryoları doğrular ve yeni senaryoların videosunu Artifacts'e koyar.
- **Haftalık Claude rutini** kuyruk azaldıkça `KONULAR.md`'deki sıradaki konuları
  senaryoya döker ve PR açar; siz önizleme videosunu izleyip birleştirirsiniz.

**Kurulum (bir kez):**

1. Bu dalı `main`'e birleştirin (zamanlanmış iş akışları yalnızca varsayılan dalda çalışır).
2. Google Cloud Console'da **YouTube Data API v3**'ü açın, *OAuth istemcisi (Masaüstü
   uygulaması)* oluşturun ve `client_secret.json`'ı indirin. *OAuth izin ekranı*nı
   **"Üretimde" (In production)** durumuna alın — "Test" durumundaki uygulamaların
   yenileme anahtarı 7 günde geçersiz olur.
3. Yerel bilgisayarınızda `python scripts/youtube_token_al.py` çalıştırın; oluşan
   `token.json` içeriğini repo → *Settings → Secrets and variables → Actions* altına
   **`YOUTUBE_TOKEN_JSON`** olarak, `client_secret.json` içeriğini **`YOUTUBE_OAUTH_JSON`** olarak ekleyin.
4. *Settings → Actions → General → Workflow permissions* → **Read and write** (kuyruk dosyası güncellenebilsin).
5. **Önemli:** Google, denetimden geçmemiş API projelerinden yüklenen videoları
   **"gizli (kilitli)"** tutar. Herkese açık / zamanlı yayın için projeniz adına
   *YouTube API Services – Audit and Quota Extension* formunu doldurun. Onay
   gelene kadar iş akışını `yukleme-yok` modunda çalıştırıp videoyu Artifacts'ten
   indirerek elle yükleyebilirsiniz.

## 4) Resimli kitap üslubunda masal videoları — `masal.py`

Görüntü, müzik ve efektlerin tamamı kodla üretilen, 2–3 dakikalık yatay
(1920×1080) masal videoları ve her masaldan ~30 sn'lik dikey (1080×1920) Shorts
tanıtımı. İlk masal: **Keloğlan ile Kapı** (13 sayfa, ~2,5 dk).

```bash
pip install skia-python numpy scipy pillow     # Linux'ta skia için: sudo apt install libegl1
python masal.py --liste                               # masallar + yayın kuyruğu
python masal.py --masal keloglan_kapi --kontrol       # doğrula + her sahneyi dene + kontak.png
python masal.py --masal keloglan_kapi --onizleme 52   # tek kare
python masal.py --masal keloglan_kapi --format ikisi  # yatay video + Shorts → cikti/masal/keloglan_kapi/
python masal.py --masal keloglan_kapi --seslendirme piper --format ikisi   # anlatımlı
```

- **Görsel dil:** krem kağıt dokusu üzerinde sulu boya/guaş (pigment dokusu,
  kenarda koyulaşan boya, ıslak lekeler), titrek sepya mürekkep çizgileri; eklemli
  kukla karakterler (yürüme, koşma, konuşma, göz kırpma); sayfa altında süslü ilk
  harfli metin kartı, cümle cümle belirir; sayfalar arasında kıvrılan sayfa çevirme.
- **Ses:** bağlama (Karplus-Strong), kaval, def, düğünde davul-zurna; makamlar
  koma doğruluğunda (Rast, Uşşak, Hüseyni, Hicaz). Kapı gıcırtısı, GÜM, cırcır böceği,
  baykuş, kurt, ateş, altın şıngırtısı, horoz, sayfa hışırtısı; −14 LUFS.
- **ElevenLabs seslendirmesi (isteğe bağlı):** `--seslendirme elevenlabs` her sayfayı
  cümle cümle seslendirir (zaman damgalı uç nokta). Cümleler anlatıcı okurken belirir;
  sayfa süreleri, sahne animasyonları ve efektler seslendirmeye göre kayar; anlatıcı
  konuşurken müzik kısılır. Gerekenler: `ELEVENLABS_API_KEY` ve `ELEVENLABS_VOICE_ID`
  (Voice Library'den **Türkçe** bir ses; karakter sesleri için `ELEVENLABS_SES_KELOGLAN`,
  `ELEVENLABS_SES_ANA`, `ELEVENLABS_SES_HARAMI`). Sesler `veri/seslendirme/<kimlik>/`
  altında önbelleğe alınır ve repoya kaydedilir; aynı metin tekrar sentezlenmez/ücretlendirilmez. GitHub'da **Masal videosu**
  iş akışı aynı işi repo secret'larıyla yapar. `--seslendirme piper` ücretsiz ve
  anahtarsız Türkçe sinir ağı sesi kullanır (`pip install piper-tts`; ses modeli ilk
  çalıştırmada huggingface.co'dan iner). Masal dosyalarını değiştiren PR'larda **Masal
  videosu** iş akışı Piper sesiyle kendiliğinden çalışır. `--seslendirme espeak` yalnızca
  hattı anahtarsız denemek içindir (mekanik ses).
- **Shorts tanıtımı:** masal dosyasındaki `SHORTS = dict(sayfalar=(...))` ile seçilen
  1–3 ardışık sayfa (en komik an) dikey sayfaya yerleştirilir: üstte masal adı, ortada
  çerçeveli resim, altta büyük puntolu metin, sonda "Masalın tamamı kanalımızda ▶".
- **Yeni masal:** `masallar/<kimlik>.py` içinde `SAYFALAR` listesi; her sayfa bir
  sahne sınıfı (`arka`: bir kez çizilen resim, `on`: her karede çizilen hareketli
  katman), metin, konuşanlar, kamera ve ses ipuçları (`sesler`) içerir. Karakter ve
  dekorlar `src/masal_cizim.py` kütüphanesindedir. Ayrıntılı kurallar:
  [`masallar/YAZIM_REHBERI.md`](masallar/YAZIM_REHBERI.md); konu havuzu:
  [`masallar/KONULAR.md`](masallar/KONULAR.md).

### 🤖 Otonom masal üretimi (haftada 1)

1. **Pazartesi — yazım (Claude rutini):** kuyrukta 3'ten az masal varsa rutin
   `KONULAR.md`'deki sıradaki konuyu seçer, masalı kendi cümleleriyle yeniden anlatır,
   sahnelerini (gerekirse yeni karakterleri) kodlar, `--kontrol` ile doğrular,
   `masallar/sira.json` kuyruğuna ekler ve **PR açar**.
2. **Önizleme (otomatik):** **Masal videosu** iş akışı PR'da masalı doğrular, Piper
   sesiyle seslendirir (seslendirmeyi PR dalına kaydeder) ve yatay video + Shorts'u
   *Artifacts* altına koyar.
3. **Onay (siz):** videoları izleyin; beğendiyseniz PR'ı birleştirin. İstemediğiniz
   bir şey varsa PR'a yorum yazın ya da kapatın — birleşmeyen masal yayınlanmaz.
4. **Cuma — yayın (otomatik):** **Masal yayını (haftalık)** iş akışı kuyruktaki ilk
   masalı üretir, iki videoyu YouTube'a gizli yükler ve **cumartesi 19:00'da (TR)**
   kendiliğinden yayınlanacak şekilde zamanlar ("çocuklara özel" beyanıyla). Shorts
   açıklamasında ana videonun bağlantısı bulunur. Elle çalıştırırken masal, yayın modu
   (`zamanli`, `hemen`, `gizli`, `yukleme-yok`) ve anlatıcı seçilebilir.

Kurulum, harita hattıyla aynıdır (yukarıdaki *Kurulum (bir kez)* adımları: `main`'e
birleştirme, `YOUTUBE_TOKEN_JSON`, OAuth "Üretimde", iş akışı yazma izni, API denetimi).

**Ayrı masal kanalı (önerilir):** Masallar "çocuklara özel" işaretlendiği için tarih
haritalarından ayrı bir kanalda yayınlanmaları daha iyidir; iki kitle aynı kanalda
olunca YouTube ikisini de daha az önerir. `scripts/youtube_token_al.py`'yi bir kez daha
çalıştırın, Google giriş ekranında masal kanalını (marka hesabını) seçin ve oluşan
`token.json` içeriğini **`YOUTUBE_TOKEN_JSON_MASAL`** sırrı olarak ekleyin. Aynı
`client_secret.json` (aynı Google Cloud projesi ve API denetimi) iki kanal için de
kullanılır. Bu sır yoksa masallar `YOUTUBE_TOKEN_JSON`'ın kanalına yüklenir. Yalnızca
`YOUTUBE_TOKEN_JSON_MASAL`'ı eklerseniz harita Shorts'ları yüklenmez; harita yayını
beklemede kalırken masallar yayınlanır.

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
├── harita.py                # Tarihi harita Shorts'ları (senaryolar/ + otonom yayın)
├── senaryolar/              # Konu başına bir veri dosyası + sira.json yayın kuyruğu
├── masal.py                 # Resimli kitap üslubunda masal videoları
├── masallar/                # Masal başına bir dosya + sira.json kuyruğu, YAZIM_REHBERI, KONULAR
├── veri/seslendirme/        # Masal seslendirme önbelleği (Piper/ElevenLabs; repoya kaydedilir)
├── requirements.txt
├── config/
│   └── ayarlar.ornek.yaml   # Örnek ayar dosyası (asmr / klip bölümleri)
├── klipler/                 # Günlük yüklediğiniz video klipleri (otomatik işlenir)
├── scripts/                 # YouTube token alma + yükleme
├── .github/workflows/
│   ├── harita-shorts.yml    # Günlük harita Shorts'u (otomatik + manuel)
│   ├── harita-onizleme.yml  # Senaryo PR'ları için doğrulama + önizleme
│   ├── masal.yml            # Masal PR önizlemesi: doğrula + Piper seslendir + video & Shorts
│   ├── masal-yayin.yml      # Haftalık masal yayını (cuma üret → cumartesi 19:00 yayın)
│   ├── asmr.yml             # Sıfırdan ASMR (günlük otomatik + manuel)
│   └── klip-birlestir.yml   # Kliplerden ASMR (push ile otomatik)
└── src/
    ├── asmr_ses.py          # Telifsiz ambient ses üreteci (numpy)
    ├── asmr_montaj.py       # ASMR montajı (Ken Burns + ffmpeg döngü)
    ├── harita_motoru.py     # Harita animasyonu render çekirdeği
    ├── harita_ses.py        # Sentez müzik ve ses efektleri
    ├── harita_kontrol.py    # Senaryo doğrulayıcı
    ├── harita_yayin.py      # Yayın kuyruğu + zamanlı YouTube yükleme
    ├── masal_motoru.py      # Masal: sulu boya fırça, kağıt, metin kartı, sayfa çevirme
    ├── masal_cizim.py       # Masal: karakterler (eklemli kukla) ve dekorlar
    ├── masal_ses.py         # Masal: bağlama, kaval, def, zurna + efektler
    ├── masal_seslendirme.py # Masal: Piper / ElevenLabs seslendirme (zaman damgalı, önbellekli)
    ├── masal_shorts.py      # Masal: dikey Shorts tanıtımı
    ├── masal_kontrol.py     # Masal doğrulayıcı (yapı + sahne denemesi)
    ├── masal_yayin.py       # Masal yayın kuyruğu + zamanlı YouTube yükleme
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

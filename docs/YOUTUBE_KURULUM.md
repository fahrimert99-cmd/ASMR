# 📺 YouTube Otomatik Yükleme Kurulumu (tek seferlik)

Bu rehber, ASMR videolarının GitHub Actions'tan **otomatik** olarak YouTube'a
yüklenmesi için gereken **tek seferlik** yetkilendirmeyi anlatır. Tamamlandığında
her günkü video kanalına **liste dışı (unlisted)** olarak yüklenir; sen inceleyip
onaylayınca **herkese açık (public)** yapılır.

> ⚠️ Bu adımı **senin yapman** gerekir — Google hesabına tarayıcıdan giriş
> gerektiği için yerine biri yapamaz. ~10 dakika sürer, ömür boyu bir kez.

---

## Adım 1 — Google Cloud'da proje + YouTube API

1. https://console.cloud.google.com/ adresine gir (Google hesabınla).
2. Üst çubuktan **yeni proje** oluştur (ör. `asmr-yukleme`).
3. **APIs & Services → Library** → "**YouTube Data API v3**" ara → **Enable**.

## Adım 2 — OAuth izin ekranı (consent screen)

1. **APIs & Services → OAuth consent screen**.
2. **User type: External** → Create.
3. Uygulama adı (ör. `ASMR Yukleyici`), destek e-postası, geliştirici e-postası
   olarak kendi e-postanı gir → Save and Continue.
4. **Scopes** ekranını boş geç (Save and Continue).
5. **Test users** → **+ ADD USERS** → **kendi Gmail adresini** ekle → Save.
   (Uygulama "Testing" modunda kalabilir; yayınlamana gerek yok.)

## Adım 3 — OAuth istemcisi (client_secret.json)

1. **APIs & Services → Credentials → + CREATE CREDENTIALS → OAuth client ID**.
2. **Application type: Desktop app** → adı gir → Create.
3. Açılan pencereden **DOWNLOAD JSON** ile dosyayı indir.
4. Bu dosyayı proje kök klasörüne **`client_secret.json`** adıyla koy.

## Adım 4 — Token üret (bir kez, kendi bilgisayarında)

Kendi bilgisayarında, proje klasöründe:

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
python scripts/youtube_token_al.py
```

- Tarayıcı açılır → Google hesabınla giriş yap → izin ver.
- ("Google bu uygulamayı doğrulamadı" uyarısı görürsen: **Advanced → Go to …
  (unsafe)** ile devam et; bu senin kendi uygulaman.)
- İşlem bitince proje klasöründe **`token.json`** oluşur.

## Adım 5 — GitHub Secrets'a ekle

GitHub'da: **Repo → Settings → Secrets and variables → Actions → New repository secret**

İki secret ekle:

| Secret adı | Değeri |
| :--- | :--- |
| `YOUTUBE_TOKEN_JSON` | **`token.json`** dosyasının **tüm içeriği** (kopyala-yapıştır) |
| `YOUTUBE_OAUTH_JSON` | **`client_secret.json`** dosyasının **tüm içeriği** (kopyala-yapıştır) |

> `token.json` ve `client_secret.json` `.gitignore`'dadır — repoya gitmez.
> Sadece içeriklerini Secrets'a yapıştırıyorsun.

---

## ✅ Kurulum bitti — günlük akış

1. **Klip yükle:** `klipler/` klasörüne günün kliplerini push et
   (`01.mp4, 02.mp4…` veya `klipler/2026-09-03/…`).
2. **Otomatik üretim:** `Klip Birlestir - ASMR` iş akışı çalışır → videoyu
   birleştirir, profesyonel TR+EN başlık/açıklama/etiket üretir ve YouTube'a
   **unlisted** yükler.
3. **İncele:** İlgili Actions çalışmasının **Summary** bölümünde video bağlantısı
   ve ID'si görünür. İzle, kontrol et.
4. **Yayınla:** **Actions → "YouTube Yayinla" → Run workflow** → video ID'yi
   yapıştır → video **public** olur. (Alternatif: YouTube Studio'dan herkese açık yap.)

## Manuel üretim
- **Sıfırdan ASMR:** Actions → **ASMR** → Run workflow (tema/süre/gizlilik seç).
- **Kliplerden:** Actions → **Klip Birlestir - ASMR** → Run workflow.

## Sık sorunlar
- **Yükleme adımı atlandı:** `YOUTUBE_TOKEN_JSON` secret'i eksik/boş. Adım 5'i kontrol et.
- **`invalid_grant` / token expired:** Testing modunda refresh token ~7 günde
  bir dolabilir. Adım 4'ü tekrar çalıştırıp `YOUTUBE_TOKEN_JSON`'ı güncelle,
  ya da OAuth consent screen'i "In production"a alarak kalıcı token al.
- **Kota:** YouTube API günlük yükleme kotası sınırlıdır (varsayılan ~6 video/gün).
  Günde 1 video için fazlasıyla yeterli.

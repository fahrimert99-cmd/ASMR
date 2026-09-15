# 4 — Elle Kurulum Adımları

Her şey sizin elinizle yapılacak. Aşağıdaki sıra takip edilirse hiçbir adım
geriye dönmeyi gerektirmez.

---

## A. Kanalı Oluşturma (bir kez)

1. Kanalı açacağınız Google hesabıyla **youtube.com**'a girin.
2. Sağ üst profil → **Kanal oluştur**. (Mevcut bir kanaldan farklı bir kanal
   açacaksanız: profil → **Hesap değiştir** → **Tüm kanalları göster** →
   **Yeni kanal oluştur**.)
3. Kanal adını girin — `01-KANAL-KIMLIGI.md` §1.1'den seçtiğiniz ad.
4. **Handle'ı hemen alın.** Handle benzersizdir; beklerseniz kapılabilir.

> **Dikkat:** Doğru kanalda olduğunuzdan emin olun. Studio'ya girdiğinizde
> sağ üstteki avatara bakın; birden fazla kanalınız varsa yanlış kanala
> yükleme yapmak çok kolaydır.

---

## B. Marka Görselleri

**YouTube Studio → Özelleştirme → Marka bilgileri**

| Alan | Dosya | Ölçü |
|---|---|---|
| Profil fotoğrafı | avatar | 800 × 800 px, daire kırpılır |
| Banner | kanal sanatı | 2560 × 1440 px, güvenli alan 1546 × 423 |
| Video filigranı | küçük logo | 150 × 150 px, şeffaf PNG |

Banner'ı yükledikten sonra **önizlemede TV / masaüstü / telefon sekmelerinin
üçüne de bakın.** Yazı telefonda kırpılıyorsa güvenli alanın dışına taşmıştır.

---

## C. Temel Bilgiler

**Özelleştirme → Temel bilgiler**

1. **Açıklama** alanına `01-KANAL-KIMLIGI.md` §1.2'deki **uzun sürümü**
   yapıştırın.
2. **Bağlantılar:** varsa web sitesi ve sosyal hesaplar. İlk birkaçı
   banner üzerinde görünür.
3. **İletişim e-postası:** iş birliği için ayrı bir adres kullanın.

**Ayarlar → Kanal → Temel bilgiler**
- **Anahtar kelimeler:** §1.6'daki listeyi yapıştırın.
- **Kanal dili:** English.
- **Ayarlar → Yükleme varsayılanları → Gelişmiş → Video dili: English.**
  Bunu şimdi ayarlarsanız her videoda tekrar seçmezsiniz.

---

## D. Oynatma Listelerini Oluşturma

**Studio → İçerik → Oynatma listeleri → Yeni oynatma listesi**

`02-OYNATMA-LISTELERI.md` içindeki beş listeyi sırayla oluşturun:
ad ve açıklamayı kopyalayın, görünürlüğü **Herkese açık** yapın.

Liste oluşturulduktan sonra listeyi açıp **sıralamayı "Manuel" yapın.**
Varsayılan "Eklenme tarihi"dir ve istediğiniz düzeni bozar.

---

## E. Video Yükleme (her video için)

**Studio → Oluştur → Video yükle**

| Adım | Ne yapılacak | Kaynak |
|---|---|---|
| 1 | Video dosyasını sürükleyin | montaj çıktınız |
| 2 | **Başlık** alanına yapıştırın | `03-VIDEO-METADATA.md` → ilgili videonun **Başlık** bloğu |
| 3 | **Açıklama** alanına yapıştırın | aynı dosyadaki **Açıklama** bloğu (bölümler dâhil) |
| 4 | **Küçük resim** yükleyin | 1280 × 720 px, ≤ 2 MB |
| 5 | **Oynatma listeleri** → ilgili listeyi işaretleyin | `02-OYNATMA-LISTELERI.md` |
| 6 | **İzleyici kitlesi** → "Hayır, çocuklara yönelik değil" | zorunlu seçim |
| 7 | **Daha fazla seçenek → Etiketler** | **Etiketler** bloğu |
| 8 | **Daha fazla seçenek → Dil** → English | altyazı eşleşmesi için |
| 9 | **Altyazı** → Yükle → SRT dosyasını seçin | aşağıdaki tablo |
| 10 | **Görünürlük** → Planla veya Yayınla | §G |

### Hangi SRT hangi videoya

| Video | Altyazı dosyası |
|---|---|
| Brokoli | ElevenLabs'ın kendi SRT çıktısı *(en doğrusu)* |
| Muz | ElevenLabs'ın kendi SRT çıktısı |
| Avokado | `ornekler/04-avokado-EN.srt` |

> **Not:** `04-avokado-SAHNE-77.srt` **altyazı değildir** — montaj aracı için
> üretilmiş sahne dosyasıdır, YouTube'a yüklemeyin. Ekrana basılacak altyazı
> `04-avokado-EN.srt`'dir.

---

## F. Bölüm Damgalarının Çalışması İçin

YouTube bölümleri **otomatik tanır**, ayrı bir alan yoktur. Çalışması için
açıklamanın şu dört şartı sağlaması gerekir — metinlerimiz sağlıyor, ama
elle düzenlerseniz bozmayın:

1. İlk damga **`0:00`** olmalı.
2. **En az üç** damga bulunmalı.
3. Her bölüm **en az 10 saniye** sürmeli.
4. Damgalar **artan sırada** ve **her biri kendi satırında** olmalı.

Yayınladıktan sonra oynatıcının ilerleme çubuğunda bölümlerin ayrıldığını
gözle doğrulayın. Ayrılmadıysa genellikle sebep bir damganın satır başında
olmamasıdır.

---

## G. Yayın Takvimi

**Haftada bir video, sabit gün ve saat.** Sebep: YouTube düzenli yüklemeyi
ödüllendirir, ama asıl fayda izleyicinin beklentisidir.

Önerilen sıra — en güçlü video başa:

| Sıra | Video | Gerekçe |
|---|---|---|
| 1 | **Brokoli × Karaciğer** | En net "şok": molekül brokolide yok, haşlayınca hiç oluşmuyor. |
| 2 | **Muz × Kaslar** | Yaygın bir inancı çürütüyor, arama hacmi yüksek. |
| 3 | **Avokado × Emilim** | Pratik sonucu en güçlü olan: yağsız sos uyarısı. |
| 4 | Nar × Damar | Ses üretilince. |

İlk videoyu yayınlamadan önce **kanal fragmanını** yükleyin ve
Özelleştirme → Düzen'den abone olmayanlara gösterin.

---

## H. Küçük Resim (Thumbnail) Standardı

| Özellik | Değer |
|---|---|
| Ölçü | **1280 × 720 px** (16:9) |
| Boyut | ≤ **2 MB** |
| Format | JPG, PNG veya GIF |

**Kanal geneli kurallar:**
- Sol yarı gıdanın gerçek makro fotoğrafı, sağ yarı organın 3D görseli.
- En fazla **üç kelime** metin. Küçük ekranda dördüncü kelime okunmaz.
- **Sağ alt köşeyi boş bırakın** — video süresi göstergesi orayı kapatır.
- Aynı palet: koyu zemin #14161A + videonun kendi aksan rengi.
- Ünlem, şoke yüz, kırmızı daire/ok yığını yok. Kanalın tonu bunu kaldırmaz.

---

## I. Dosya Adlandırma Kuralı

Yüklediğiniz her dosyanın adı **yalnızca ASCII** olsun ve kısa tutun:

```
brokoli-karaciger.mp4      ✅
04-avokado-EN.srt          ✅
Napoléon-vidéo-final.mp4   ❌  aksanlı harf
```

**Sebebi deneyimle sabit:** Moskova görsellerinde bir dosya adındaki `é`
karakteri montaj aracında "dosya bulunamadı" hatası verdi. Türkçe karakterler
(ğ, ü, ş, ı, ö, ç) de aynı riski taşır.

---

## J. Yayın Öncesi Kontrol Listesi

Her video için, **Yayınla**'ya basmadan önce:

- [ ] Doğru kanalda olduğumu sağ üstteki avatardan doğruladım
- [ ] Başlık 100 karakterin altında ve clickbait içermiyor
- [ ] Açıklamanın ilk iki satırı videoyu tek başına anlatıyor
- [ ] Bölüm damgaları `0:00` ile başlıyor, en az üç tane, her biri ≥10 sn
- [ ] Etiketler yapıştırıldı
- [ ] Video dili **English** seçildi
- [ ] Altyazı (SRT) yüklendi ve **sahne dosyası değil**, altyazı dosyası
- [ ] Küçük resim 1280×720 ve sağ alt köşe boş
- [ ] Doğru oynatma listesi işaretlendi
- [ ] "Çocuklara yönelik değil" seçildi
- [ ] Sorumluluk notu açıklamada duruyor
- [ ] Senaryodaki **kaynak doğrulama listesi** işaretlendi — doğrulanamayan
      sayısal değer kaldı mı?

Son madde en önemlisi. Kanalın tek sermayesi, söylediğinin doğru olması.

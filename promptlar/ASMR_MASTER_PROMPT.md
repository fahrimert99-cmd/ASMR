# 🎧 30 Saniyelik ASMR — Master Prompt

Bu doküman, **7 adet 5 saniyelik AI klibinden 30 saniyelik yatay (16:9) bir ASMR
videosu** üretmek için kullanılan master prompt'u içerir.

Üretilen klipler `klipler/` klasörüne `01.mp4 … 07.mp4` olarak yüklenir;
`birlestir.py` bunları yumuşak geçişle birleştirip tek bir 30 sn'lik videoya
dönüştürür.

---

## Süre matematiği (önce bunu okuyun)

Klipler crossfade ile **bindirilerek** birleşir (`padding=-gecis_sn`), bu yüzden
toplam süre klip sayısının basit çarpımı değildir:

```
toplam = N × klip_süresi − (N−1) × geçiş_süresi
```

| Klip sayısı | Hesap | Sonuç | Değerlendirme |
|---|---|---|---|
| **7 klip** | 7×5 − 6×0,8 | **30,2 sn → 30,0 sn'ye kırpılır** | ✅ Önerilen. Tekrar yok. |
| 6 klip | 6×5 − 5×0,8 | 26,0 sn | ❌ Eksik 4 sn döngüyle dolar, baş tekrar eder |
| 6 klip (geçiş 0) | 6×5 − 0 | 30,0 sn | ⚠️ Tam süre, ama sert kesim (ASMR'da rahatsız edici) |

**Bu yüzden sahne sayısı 7'dir.** 6 sahne istiyorsanız `klip.gecis_sn: 0`
yapmanız gerekir; ASMR'da yumuşak geçiş önerildiği için 7 sahne tercih edildi.

### Zaman çizelgesi

| Sahne | Ekranda | Dramatürjik görev |
|---|---|---|
| 1 | 0,0 – 5,0 | **Kanca** — hareket zaten başlamış |
| 2 | 4,2 – 9,2 | **Yaklaşma** — kamera dokuya iniyor |
| 3 | 8,4 – 13,4 | **İlk temas** — ilk tetikleyici ses |
| 4 | 12,6 – 17,6 | **Doruk** — ana tetikleyici, en yoğun an |
| 5 | 16,8 – 21,8 | **Açılma** — iç doku ortaya çıkıyor |
| 6 | 21,0 – 26,0 | **Dinlenme** — yavaşlama |
| 7 | 25,2 – 30,2 | **Kapanış** — 1. sahneye görsel olarak yakın kare |

7. sahnenin 1. sahneye benzemesi kasıtlıdır: izleyici videoyu tekrar
izlediğinde dikiş görünmez.

---

## Kullanım

1. Aşağıdaki bloğun tamamını kopyalayıp yapay zekâya yapıştırın.
2. Model `"Hangi ASMR konseptini üretmek istersiniz?"` diye soracaktır.
3. Konsepti yazın → 5 başlık gelir → birini seçin → 2–5. adımlar üretilir.
4. 7 video prompt'unu Veo / Kling / Luma / Runway'de **5 saniye, 16:9** ile çalıştırın.
5. Klipleri `01.mp4 … 07.mp4` olarak `klipler/` altına koyun.
6. `python birlestir.py` → `cikti/birlesik-asmr/birlesik_asmr.mp4` (30 sn, 1080p).

---

## Master Prompt

```
30 SANİYELİK ASMR VİDEOSU ÜRETİMİ İÇİN MASTER PROMPT

Rol: Sen, yapay zekâ ile üretilen kısa formatlı ASMR videolarının konseptini,
sahne dramaturjisini ve ses tasarımını hazırlayan profesyonel bir ASMR
yönetmenisin. Elinde sadece 30 saniye var ve bu 30 saniyede izleyiciyi
yakalamak, tek bir dokusal doruğa taşımak ve sakin bir kapanışla bırakmak
zorundasın.

ÜRETİM FELSEFESİ:
* Bu bir "izlenen" değil, "hissedilen" videodur. Her sahnenin merkezinde bir
  GÖRÜNTÜ değil, bir SES vardır; görüntü sadece o sesin bedenidir.
* Kısa formatın kanunu: TEK TETİKLEYİCİ. 30 saniyeye birden fazla ses fikri
  sığmaz. Tüm video tek bir dokunun etrafında kurulur.
* İlk 1,5 saniye videonun kaderidir. 1. sahne asla hazırlık sahnesi olamaz;
  perde açıldığında hareket ÇOKTAN BAŞLAMIŞ olmalıdır.
* Ritim gerçek zamanlıdır. Acele yok, sürpriz yok. Ses asla patlamaz.

DEĞİŞMEZ TEKNİK KURALLAR (her çıktıda geçerlidir):
* Format: YATAY 16:9, 1920x1080, sinematik.
* Sahne sayısı: TAM OLARAK 7. Her klip TAM OLARAK 5 saniye.
* Klipler yumuşak geçişle birleşip 30 saniyelik tek videoya dönüşecek.
* Ses: binaural / yakın mikrofon hissi, gerçek zamanlı, temiz ve kuru.
* YASAK: müzik, arka plan melodisi, konuşma/anlatım, yazı ve logo, hızlı
  kesme, ani hareket, hızlandırma, titreyen ışık, insan yüzü.
* İzin verilen insan öğesi: yalnızca eller (bakımlı, sakin, yavaş hareket eden).

SAHNE DRAMATURJİSİ (7 sahnenin görevleri sabittir):
  Sahne 1 - KANCA: En çarpıcı doku, hareket zaten başlamış hâlde.
  Sahne 2 - YAKLAŞMA: Kamera veya el dokuya iniyor, beklenti kuruluyor.
  Sahne 3 - İLK TEMAS: İlk tetikleyici ses duyuluyor.
  Sahne 4 - DORUK: Ana tetikleyici, videonun en yoğun anı.
  Sahne 5 - AÇILMA: Kesilen/kırılan şeyin iç dokusu ortaya çıkıyor.
  Sahne 6 - DİNLENME: Hareket ve ses yavaşlıyor.
  Sahne 7 - KAPANIŞ: 1. sahneye görsel olarak YAKIN bir kare (tekrar izlemede
            dikiş görünmesin diye).

Senden şu 5 adımı sırasıyla ve eksiksiz uygulamanı istiyorum:

1. ADIM: Başlık Önerileri
Seçilen konsepte uygun, kısa ve merak uyandıran 5 adet Türkçe başlık öner.
Başlıklar 60 karakteri geçmesin.
(Örn: "Bal Peteği Kesme ASMR | Bu Sesi Kulaklıkla Dinleyin")
Her başlığın yanına parantez içinde tek cümlelik "tetikleyici vaadi" yaz.

2. ADIM: Sahne Akışı ve Ses Haritası (Sound Design Map)
Kullanıcı bir başlık seçtiğinde, TAM OLARAK 7 sahnelik akışı kur.
Her sahne için şu dört satırı ver:
    Sahne No ve Görevi: (KANCA / YAKLAŞMA / İLK TEMAS / DORUK / AÇILMA /
    DİNLENME / KAPANIŞ — yukarıdaki sıraya birebir uy.)
    Görsel: Kamerada ne var, ne oluyor (tek cümle).
    Ana Tetikleyici: O sahnenin merkezindeki ses.
    Yoğunluk: Düşük / Orta / Yüksek.
Yoğunluk eğrisi şu şekilde olmalıdır:
    Orta → Düşük → Orta → Yüksek → Orta → Düşük → Düşük

* VİDEO AÇIKLAMASI: Sahne listesinin ardından, YouTube açıklama alanına
  konacak 2-3 cümlelik kısa bir Türkçe metin yaz. Bu metnin içinde şu ifade
  mutlaka aynen geçmelidir:
  "Bu videodaki her doku, gelişmiş yapay zekâ teknikleriyle sıfırdan üretildi.
  Kulaklığınızı takın ve sadece dinleyin."
  Metnin sonuna 5 adet ilgili hashtag ekle.
  (NOT: Video içinde anlatım/seslendirme YOKTUR. Bu metin sadece açıklama
  alanı içindir; 30 saniyeye konuşma sığmaz ve tetikleyiciyi bastırır.)

3. ADIM: Image Prompts (Görüntü Komutları)
7 sahnenin her biri için bir adet İngilizce Image Prompt oluştur.
(Tam olarak 7 adet — eksik veya fazla olmasın.)
Her prompt şu tutarlılık çapasıyla bitmelidir:
"...macro close-up, shallow depth of field, soft diffused studio light, dark
neutral background, ultra detailed texture, photorealistic, 8k, cinematic,
16:9 horizontal composition, no text, no watermark"
* Promptları sadece tırnak içinde (" ") ver.
* Promptların arasında mutlaka birer satır boşluk olsun.
* Kesinlikle numaralandırma, liste işareti veya ek açıklama yapma.

4. ADIM: Video Prompts (Video Komutları)
3. Adımda oluşturduğun her Image Prompt için, o görselin nasıl
hareketlendirileceğini ve NE SES ÇIKARACAĞINI anlatan İngilizce birer Video
Prompt yaz. (Veo / Kling / Luma / Runway için.)
Her video prompt şu üç bileşeni içermek zorundadır:
    a) Hareket: çok yavaş kamera hareketi veya sabit kamera + objenin kendi
       hareketi (kesilme, akma, kabarma, dökülme, titreşim).
    b) Ses: mutlaka "ASMR sound of ..." kalıbıyla, TEK ve net bir tetikleyici.
       7 sahnenin tamamı AYNI tetikleyici ailesinden olmalıdır.
    c) Kapanış kalıbı: "...5 seconds, 16:9, real-time slow pace, no music,
       no voice, crisp binaural audio"
* Promptları sadece tırnak içinde (" ") ver.
* Promptların arasında birer satır boşluk olsun.
* Kesinlikle numaralandırma veya liste işareti yapma.

5. ADIM: Kapak Görseli (Thumbnail) Tasarımı
Yatay (16:9) tek bir İngilizce thumbnail image prompt ver.
Prompt şunları içermelidir:
* Merkezde, tetikleyici anın tam donduğu makro bir kare (bıçağın yüzeye tam
  girdiği, kabuğun çatladığı, damlanın yüzeye değdiği an).
* Koyu, sade arka plan ve konuya çarpıcı bir kenar ışığı (rim light).
* Sağ üst köşede, büyük, beyaz ve kalın (bold) harflerle konsept adı.
* Sol alt köşede küçük bir kulaklık ikonu ve yanında "USE HEADPHONES" yazısı.
* Yüksek kontrast, doygun renk, telefon ekranında bile okunabilir netlik.
* 1920x1080, 16:9.

ÜRETİM HATTI NOTU (her işin sonunda ekle):
7 klibi 5 saniye ve 16:9 olarak üret; 01.mp4, 02.mp4 ... 07.mp4 şeklinde
sırayla adlandırıp "klipler/" klasörüne koy. Ardından "python birlestir.py"
komutu 30 saniyelik 1080p videoyu üretecektir.

Hazırsan; "Hangi ASMR konseptini üretmek istersiniz?" diyerek süreci başlat.
```

---

## Konsept Fikirleri

| Kategori | Örnek konseptler |
|---|---|
| Kesme / Çıtırtı | Bal peteği, kristal meyve, buz, şeker cam, sabun |
| Akış | Bal akışı, lav, reçine, eriyen mum, çikolata |
| Doku | Yosun, kürk, ıslak toprak, köpük, tüy, kadife |
| El işi | Ahşap yontma, seramik, hamur, mühür mumu |

Uzun form için yapılan niş analizinde en yüksek puanı alan **fantastik/tarihsel
ortam ASMR**'ı 30 saniyelik formatta kullanmak zordur: o niş bağlam kurmaya
dayanır, 30 saniyede bağlam kurulamaz. Kısa formatta **tek ve güçlü
tetikleyici** (kesme/çıtırtı/akış) daha isabetlidir.

## Kalite Kontrol Listesi

- [ ] Tam olarak 7 sahne var mı?
- [ ] Tam olarak 7 image prompt ve 7 video prompt var mı?
- [ ] Tüm klipler 5 saniye ve 16:9 olarak üretildi mi?
- [ ] 7 sahnenin tamamı AYNI tetikleyici ailesinden mi?
- [ ] 1. sahnede hareket ilk karede başlamış durumda mı?
- [ ] 7. sahne 1. sahneye görsel olarak yakın mı?
- [ ] Her video prompt'ta `ASMR sound of ...` ve `no music, no voice` var mı?
- [ ] Klipler `01.mp4 … 07.mp4` olarak adlandırıldı mı?
- [ ] Çıktı süresi 30,00 sn ve çözünürlük 1920x1080 mi?

---
*Hazırlayan: Fahri Mert*

# Moskova Belgeseli — Üretim Dosyaları

**Hedef:** ~15 dakikalık tarih belgeseli · **Dil:** İngilizce anlatım
**Görseller:** `gorseller/moskova-tarihi/` (59 adet, kronolojik)

## Dosyalar

| Dosya | İçerik |
|---|---|
| `MASTER-anlatim.md` | Anlatımın tamamı, `[001]`–`[059]` bölüm etiketleriyle. Her etiket aynı numaralı görsele karşılık gelir. |
| `part1.txt` · `part2.txt` · `part3.txt` | ElevenLabs'a **sırayla** yapıştırılacak parçalar. Hepsi 5.000 karakter sınırının altında. |
| `B-kare-promptlari.txt` | 59 yeni görsel prompt'u (B kareleri), stil eki eklenmiş, satır başına bir prompt. |
| `ZAMAN-PLANI.md` | 118 karenin başlangıç/süre tablosu. |

## Seslendirme

| Parça | Karakter | Bölümler | Sınır payı |
|---|---|---|---|
| part1 | 3.978 | 001–019 | 1.022 |
| part2 | 4.038 | 020–038 | 962 |
| part3 | 4.140 | 039–059 | 860 |
| **toplam** | **12.156** | 59 | ~15:15 |

Parçalar **ardışıktır** — birleştirildiğinde metin `MASTER-anlatim.md` ile
birebir aynıdır (doğrulandı). Kesim noktaları bölüm sınırında:

- part1 → part2 geçişi: *"...it came under Ivan the third."* / *"In fourteen eighty..."*
- part2 → part3 geçişi: *"...dictate the peace."* / *"Napoleon brought more than half a million men."*

İkisi de yeni bir düşünce başlattığı için birleştirmede dikiş duyulmaz.

**Üretim kuralları:** Üç parçayı da **aynı ses ve aynı ayarlarla** üretin
(Stability 45–55 · Similarity 75 · Style 0–20). Parçalar arasına montajda
0,7–1 sn boşluk bırakın.

**Yıllar yazıyla yazıldı** (*eleven forty seven*, *eighteen twelve*,
*nineteen forty one*) — TTS rakamlı yılları tutarsız okuyor.

## Görseller

59 bölüm × 2 kare = **118 kare**, ortalama **7,8 sn**.

- **A kareleri:** elinizdeki 59 görsel, sırayla.
- **B kareleri:** `B-kare-promptlari.txt` içindeki 59 yeni prompt. Her biri
  kendi bölümünün A karesini tamamlar (yakın plan, alternatif açı, detay).

Tek başına 59 görselle 15 dakika doldurulursa kare başına 15,4 sn düşer ve
video durağanlaşır. İkinci kare seti bunu 7,8 sn'ye indiriyor.

## Sırada

Ses üretilip **SRT** alındığında zaman planı tahminden gerçeğe çevrilir ve
kareler blok sınırlarına birebir hizalanır.

---

## Üretilen Ses ve SRT (11 Eylül 2026)

Seslendirme **Edward (British, Dark, Seductive, Low)** sesiyle yapıldı.

| Dosya (yükleme saati) | Etiket | Süre | Parça |
|---|---|---|---|
| 13:50:36 | SES1 | 5:28.10 | part1 |
| 13:51:37 | "SES3" | 5:27.08 | **part2** — etiket yanlış |
| 13:54:33 | SES3 | 5:31.02 | part3 |

**Toplam: 16:26.20**

Eşleşme iki bağımsız kanıtla doğrulandı: üretim saat sırası ve karakter/süre
oranlarının tutarlılığı (0,0825 / 0,0810 / 0,0800 — sapma %1,5).

### Tempo kalibrasyonu

| Ses | sn/karakter | Not |
|---|---|---|
| Arthur | 0,0760 | Beslenme videolarında ölçüldü |
| **Edward** | **0,0810** | Arthur'dan ~%8 yavaş |

İleride Edward için süre tahmini: `karakter × 0,0810`. Bu metin 15:15 olarak
tahmin edilmiş, gerçekte 16:26 çıkmıştı — fark tamamen ses değişiminden.

### SRT dosyaları

| Dosya | Blok | Kapsam |
|---|---|---|
| `SES1-part1.srt` | 73 | 0'dan başlar, part1 sesi için |
| `SES2-part2.srt` | 64 | 0'dan başlar, part2 sesi için |
| `SES3-part3.srt` | 63 | 0'dan başlar, part3 sesi için |
| `TAM-VIDEO.srt` | 200 | Üçü ardışık birleştirilmiş tek video için |

**`TAM-VIDEO.srt` varsayımı:** parçalar arasında boşluk yok. Montajda araya
sessizlik koyarsanız part2 zamanlarına o boşluk, part3 zamanlarına iki
boşluğun toplamı eklenmelidir.

### ⚠️ SRT'ler tahminidir

Bu oturumda konuşma tanıma aracı yok. Zamanlama, brokoli ve muz
videolarının **gerçek** ElevenLabs SRT'lerinden fit edilen tempo modeliyle
(`süre = 0,0629 × karakter + 0,115 sn`, bloklar arası 0,72 sn) hesaplanıp
her dosyanın **ölçülen gerçek süresine** ölçeklendi. Metin birebir doğru,
parça toplam süreleri kesin; blok sınırları yaklaşıktır.

Altyazıyı ekrana basacaksanız **ElevenLabs'ın kendi SRT dışa aktarımını**
kullanın — üretim sayfasından indirilebiliyor ve örneklem düzeyinde kesindir.
Görsel hizalama için bu dosyalar yeterlidir.

---

## Hangi SRT Nerede Kullanılır

Montaj araçları genelde **SRT blok sayısı = görsel sayısı** şartı arar.
Bu yüzden iki farklı amaca hizmet eden SRT'ler var:

| Dosya | Blok | Kullanım |
|---|---|---|
| `SAHNE-59.srt` | 59 | **Otomatik montaj aracına verilecek olan.** Her blok bir görselin ekranda kalacağı süreyi kapsar. Elinizdeki 59 görselle birebir eşleşir. |
| `SAHNE-118.srt` | 118 | B kareleri üretildikten sonra kullanılacak sürüm. Her sahne A ve B olarak ikiye bölünür. |
| `TAM-VIDEO.srt` | 200 | **Ekrana basılacak altyazı.** Cümle bazlı, okunabilir uzunlukta. Montaj aracına verilmez. |
| `SES1/2/3-part*.srt` | 73/64/63 | Parçaları ayrı ayrı işlemek gerekirse. |

### SAHNE-59.srt özellikleri

- Bloklar **kesintisiz**: her bloğun bitişi bir sonrakinin başlangıcına eşit
  (doğrulandı), ilk blok `00:00:00,000`'da başlar, son blok `16:26,200`'de biter.
  Görseller arasında boş kare oluşmaz.
- Süreler, her parçanın **ölçülen gerçek süresi** içinde bölüm metinlerinin
  karakter uzunluğuna göre dağıtıldı.
- Kare süresi: en kısa 9,0 sn · en uzun 25,7 sn · ortalama **16,7 sn**.

> **25,7 saniyelik tek görsel uzun.** 59 görsel 16,5 dakikayı doldurmak için
> az; B kareleri üretilip `SAHNE-118.srt`'ye geçildiğinde ortalama 8,4 sn'ye
> iner. Şimdilik montaj aracında Ken Burns / yavaş zoom açık olmalı, yoksa
> uzun kareler donuk durur.

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

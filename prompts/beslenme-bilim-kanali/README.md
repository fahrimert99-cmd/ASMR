# 🧬 Bilimsel & Biyolojik Beslenme YouTube Kanalı — İçerik Üretim Prosedürü

Bu klasör, gıdaların **hücresel ve organ düzeyindeki gerçek biyolojik etkilerini**
anlatan YouTube kanalının içerik üretim varlıklarını barındırır.

| Dosya | Amaç |
|-------|------|
| `MASTER_PROMPT.md` | Kanalın ana sistem promptu (persona, ton, şablon, çalıştırma komutu). Değiştirilmez; sürüm geçmişi git üzerinden takip edilir. |
| `SENARYO_SABLONU.md` | Her yeni video için doldurulacak boş şablon. Başlık/zaman damgası yapısı korunur. |
| `ornekler/` | Şablonun tam uygulanmış örnek çıktıları. |

## Çalıştırma

Master promptu yükleyip yalnızca iki parametre verin:

```
Gıda: [Gıda Adı]
Hedef Organ/Sistem: [Oynatma listesi 1–5]
```

Çıktı daima üç parçadır: **(1)** Başlık & Thumbnail konsepti · **(2)** Zaman damgalı
detaylı senaryo · **(3)** B-Roll ve 3D/animasyon direktifleri.

## Oynatma Listesi Yapısı
1. Kalp, Kan ve Damar Sağlığı (Heart & Arteries)
2. Beyin Sağlığı (Brain Health)
3. Bağırsak ve Sindirim Sağlığı (Gut Health)
4. Karaciğer ve Hücresel Detoks
5. Kaslar, Hücreler ve Bağışıklık (Muscles, Cells & Immunity)

## Kalite Kuralları (yayın öncesi kontrol)
- [ ] Başlıkta clickbait, mucizevi kür vaadi veya abartılı iddia yok.
- [ ] Her mekanizma anlatımı moleküler basamak düzeyinde; "antioksidan iyidir" tipi
      genellemeyle geçiştirilmemiş.
- [ ] Kanıt gücü olduğu gibi aktarılmış; zayıf çalışmalar zayıf olarak sunulmuş.
- [ ] Tüm sayısal değerler birincil kaynaktan doğrulanmış; doğrulanamayanlar çıkarılmış.
- [ ] Tıbbi tavsiye olmadığına dair sorumluluk notu ve varsa ilaç etkileşimi uyarısı eklenmiş.
- [ ] CTA "gıda adı + organ" formatında.

## Bu Depoyla İlişkisi
Depodaki mevcut üretim hattı (`asmr.py`, `birlestir.py`, `src/`) ses ve montaj
tarafını; bu klasör ise **senaryo ve içerik** tarafını kapsar. Senaryo metni,
seslendirme için `src/seslendirme.py` (edge-tts) girdisi olarak kullanılabilir.

---
**Hazırlayan / Onaylayan:** Fahri Mert

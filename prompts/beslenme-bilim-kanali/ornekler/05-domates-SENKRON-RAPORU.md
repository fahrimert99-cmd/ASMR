# Domates Paketi — Senkron Kontrol Raporu

Kontrol tarihi: 14.09.2026 · Kontrol eden: Fahri Mert

## 1. Dosya Kimlik Kontrolü

| Dosya | Karşılaştırma | Sonuç |
|---|---|---|
| `05-domates-damar_Edward.mp3` | md5 `cf68c8030f1abfe8a19f6264f35deeac` | Bayt bayt aynı |
| `05-domates-EN.srt` (ham ElevenLabs) | satır satır | Aynı |
| `05-tomato-arteries-EN-5000.txt` | satır satır | Aynı |
| `05-domates-image-promptlari.txt` | 80 satır | **Geçersiz** — güncel liste 83 satırlık |

Ses: 407,28 sn (6:47,28) · 128 kbps · 44.100 Hz · Edward (British, Dark,
Seductive, Low) · `sp100 s50 sb75 f25`

## 2. Bütünlük Kontrolü

Kaynak metin ile SRT, kelime düzeyinde hizalandı (`difflib.SequenceMatcher`):

- Kaynak: **814 kelime** · SRT: **814 kelime**
- **Düşen cümle yok.** (Muz videosunda ElevenLabs "One serious warning."
  cümlesini sessizce atlamıştı; bu üretimde o sorun görülmedi.)

## 3. Tespit Edilen Sapmalar

On bir sapma bulundu. Sekizi ElevenLabs altyazı motorunun imla/sayı
normalizasyonudur — ses doğru, yalnızca yazım farklı:

| Blok | Zaman | Metin | Ham SRT |
|---|---|---|---|
| 27 | 02:42 | flavour | flavor |
| 39 | 03:26 | oxidised | oxidized |
| 40 | 03:32 | oxidised | oxidized |
| 49 | 04:25 | randomised | randomized |
| 50 | 04:29 | benefit | benefits |
| 54 | 04:50 | sceptical | skeptical |
| 55 | 04:54 | nineteen nineties | 1990s |
| 69 | 05:40 | Three. | 3. |
| 72 | 05:51 | Four. | 4. |

Üçü anlam taşıyor:

| Blok | Zaman | Metin | Ham SRT | Değerlendirme |
|---|---|---|---|---|
| 6 | **00:38** | several times **easier** | several times **the house** | Fonetik olarak uzak. Altyazı motorunun uydurması olması muhtemel, ancak sesin de bozuk olma ihtimali var. **Dinlenmeli.** |
| 65 | **05:28** | the better **source** | the better **sauce** | İngiliz aksanında iki sözcük neredeyse aynı sesleniyor. Düşük risk. |

## 4. Uygulanan Düzeltme

`05-domates-ALTYAZI.srt` üretildi: zaman kodları ham SRT ile birebir aynı,
metin yazılı senaryonun sözcüklerine döndürüldü. Ham SRT olduğu gibi
yüklenseydi izleyici ekranda *"several times the house"* okuyacaktı.

`05-domates-SAHNE-83.srt` içindeki blok metinleri de aynı şekilde düzeltildi.
Zaman kodlarına dokunulmadı — bitişik yapı ve `00:00:00,000 → 00:06:47,280`
aralığı korundu.

Doğrulandı: düzeltme sonrası kaynak metin ile altyazı arasında kelime düzeyinde
**sıfır sapma**.

## 5. Hangi Dosya Nereye

| Amaç | Dosya |
|---|---|
| Montaj aracı (senkron planı) | `05-domates-SAHNE-83.srt` — bitişik, sıfır boşluk |
| YouTube altyazısı | `05-domates-ALTYAZI.srt` — düzeltilmiş metin, doğal boşluklar |
| Görsel üretimi | `05-domates-image-promptlari-83.txt` — 83 satır |
| Seslendirme | `sesler/beslenme-kanali/05-domates-damar_Edward.mp3` |

Ham `05-domates-EN.srt` yalnızca kayıt amacıyla saklanıyor; hiçbir yerde
kullanılmamalı.

## 6. Sonraki Videolarda Aynı Kontrol

Ses üretildikten sonra kaynak metin ile SRT'yi kelime düzeyinde hizalayın.
Blok sayısı karşılaştırması yetmez — ElevenLabs cümle atlarsa blok sayısı da
düşer ve fark edilmez. Kelime sayısı eşitse hiçbir şey düşmemiştir; sapma
listesi de imla farkı ile gerçek okuma hatasını ayırmanızı sağlar.

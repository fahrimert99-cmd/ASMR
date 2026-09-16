# Seslendirme Dosyaları

ElevenLabs'ta üretilen ses dosyaları. Dosya adları düzenlendi: UUID önekleri
ve otomatik ElevenLabs eklentileri kaldırıldı, içeriğe göre adlandırıldı.

## moskova-belgeseli/

| Dosya | Süre | Kapsam | Metin |
|---|---|---|---|
| `moskova-01-bolum-001-019_Edward.mp3` | 5:28.10 | Bölüm 001–019 | `prompts/moskova-belgeseli/part1.txt` |
| `moskova-02-bolum-020-038_Edward.mp3` | 5:27.08 | Bölüm 020–038 | `part2.txt` |
| `moskova-03-bolum-039-059_Edward.mp3` | 5:31.02 | Bölüm 039–059 | `part3.txt` |

**Toplam: 16:26.20** · Ses: Edward (British, Dark, Seductive, Low) ·
Ayarlar: `sp100 s50 sb75 f25`

### Birleştirilmiş dosya

`moskova-TAM_Edward.mp3` — üç parça tek dosyada, **16:26.20**, 15 MB.

Birleştirme frame düzeyinde yapıldı (ffmpeg olmadan): üç dosya da 128 kbps /
44.100 Hz / mono CBR olduğu için ID3 etiketleri atılıp MPEG frame'leri
doğrudan uç uca eklendi. Yeniden kodlama yok, **kalite kaybı yok**.
Doğrulandı: 37.753 frame, hizalanmamış bayt 0, süre parçaların toplamına eşit.

**Parçalar arasında boşluk yok.** Bu bilinçli: `TAM-VIDEO.srt` sıfır boşluk
varsayımıyla üretildi, dolayısıyla bu ses dosyasıyla senkron. Araya sessizlik
eklerseniz altyazı kayar.

Geçiş noktaları: part2 → **5:28.10**, part3 → **10:55.18**

> **Düzeltilen hata:** Orijinal yüklemede ikinci ve üçüncü dosya **ikisi de
> `SES3`** adını taşıyordu. Doğru sıra, üretim saat damgalarından
> (13:50:36 → 13:51:37 → 13:54:33) ve karakter/süre oranlarının
> tutarlılığından (0,0825 / 0,0810 / 0,0800 — sapma %1,5) belirlendi.
> Yeni adlar bölüm aralığını taşıdığı için karışma riski kalmadı.

Altyazılar: `prompts/moskova-belgeseli/` altında `SES1-part1.srt`,
`SES2-part2.srt`, `SES3-part3.srt` ve birleşik `TAM-VIDEO.srt`.

## beslenme-kanali/

| Dosya | Süre | Metin |
|---|---|---|
| `03-muz-kaslar_Arthur.mp3` | 6:17.65 | `prompts/beslenme-bilim-kanali/ornekler/03-banana-muscles-EN-5000.txt` |
| `04-avokado-emilim_Edward.mp3` | 6:23.82 | `prompts/beslenme-bilim-kanali/ornekler/04-avocado-absorption-EN-5000.txt` |
| `05-domates-damar_Edward.mp3` | 6:47.28 | `prompts/beslenme-bilim-kanali/ornekler/05-tomato-arteries-EN-5000.txt` |
| `06-goji-goz_Edward.mp3` | 6:36.64 | `prompts/beslenme-bilim-kanali/ornekler/06-goji-eyes-EN-5000.txt` |

Ses: Arthur (Clear, Engaging, American Male Audiobook Narrator) ·
Ayarlar: `sp100 s62 sb71 f25`
Edward (British, Dark, Seductive, Low) · Ayarlar: `sp100 s50 sb75 f25`

Altyazılar: `05-domates-EN.srt` (ham ElevenLabs, 83 blok, bloklar arası 0,4–2,0 sn
boşluk — altyazı için) ve `05-domates-SAHNE-83.srt` (bitişik, sıfır boşluk —
montaj için).

## Ses Tempo Kalibrasyonu

Süre tahminlerinde kullanılacak katsayılar (gerçek ölçümlerden):

| Ses | sn/karakter | Aralık | Ölçüm |
|---|---|---|---|
| Arthur | **0,0760** | 0,0760–0,0761 | 2 (brokoli, muz) |
| Edward | **0,0809** (ort.) | 0,0782–0,0839 | 6 (Moskova ×3, avokado, domates, goji) |

Arthur çok kararlı; iki ölçümü neredeyse aynı. **Edward içeriğe göre
değişiyor** — avokadoda 0,0782'ye indi, domateste 0,0839'a çıktı. Bu %7'lik
bir yayılım: 4.900 karakterlik bir metinde 28 saniye fark eder.

Domates metninde birçok çok kısa cümle var ("Straight molecules stack badly.",
"Mechanism.", "Strong.") ve Edward bunların her birinin arkasına belirgin bir
duraklama koyuyor. Katsayının yükselme sebebi okuma hızı değil, **duraklama
sayısı**. Kısa cümle yoğunluğu yüksek metinlerde üst sınırı kullanın.

**Edward için tahmin yaparken aralık verin:** `karakter × 0,078` ile
`karakter × 0,084` arası. Tek sayıya güvenmeyin.

Goji metninde **0,0799** çıktı ve tahmin aralığı (6:27–6:57) gerçeği (6:36,64)
kapsadı. Altı ölçümün tamamı 0,078–0,084 bandının içinde kaldı; aralık
yöntemi çalışıyor.

**Hedef süreden karakter hesabı:** `karakter = hedef_saniye ÷ katsayı`

| Hedef | Arthur (0,0760) | Edward (0,0811 ort.) |
|---|---|---|
| 5 dk | 3.950 krk | 3.700 krk |
| 6 dk | 4.740 krk | 4.440 krk |
| 10 dk | 7.890 krk | 7.400 krk |
| 15 dk | 11.840 krk | 11.100 krk |

Edward'da ±%4 pay bırakın.

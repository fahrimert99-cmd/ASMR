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

Ses: Arthur (Clear, Engaging, American Male Audiobook Narrator) ·
Ayarlar: `sp100 s62 sb71 f25`

## Ses Tempo Kalibrasyonu

Süre tahminlerinde kullanılacak katsayılar (gerçek ölçümlerden):

| Ses | sn/karakter | Ölçüm sayısı |
|---|---|---|
| Arthur | 0,0760 | 2 (brokoli 4.945 krk → 6:16, muz 4.946 krk → 6:17) |
| Edward | 0,0810 | 3 (Moskova parçaları) |

Edward, Arthur'dan yaklaşık **%8 yavaş** okuyor. Aynı metin Edward'la
seslendirilirse süre bu oranda uzar.

**Hedef süreden karakter hesabı:** `karakter = hedef_saniye ÷ katsayı`
Örnek: Edward ile 10 dakika → 600 ÷ 0,0810 ≈ **7.400 karakter**.

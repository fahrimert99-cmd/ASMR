# 🎬 Kurgu Canavarı — Chrome Eklentisi

Numaralı sahneleri, **SRT zaman kodlarını sesin ana saati kabul ederek** tek bir
videoya dizer. Sunucuya hiçbir şey yüklenmez; tüm render tarayıcının içinde,
WebCodecs ile yapılır.

## Kurulum

1. Chrome'da `chrome://extensions` adresini açın.
2. Sağ üstten **Geliştirici modu**'nu açın.
3. **Paketlenmemiş öğe yükle** → bu klasörü (`eklenti/kurgu-canavari`) seçin.
4. Araç çubuğundaki simgeye tıklayın; pano yeni sekmede açılır.

## Kullanım

| Girdi | Ne verilir |
|---|---|
| **01 Seslendirme** | Tek MP3 / WAV / M4A dosyası. Videonun toplam süresini bu belirler. |
| **02 Senkron SRT** | Aynı seslendirmeye ait zaman kodlu altyazı. Zorunlu. |
| **03 Numaralı sahneler** | Görseller ve videolar birlikte: `Video 01.mp4`, `Görsel 02.png`, `03.jpg` … |

SRT'deki **n**. blok, adında **n** geçen dosyaya bağlanır. Sahne numarası dosya
adındaki **ilk** rakam öbeğinden okunur; böylece `Video 01 1080p.mp4` gibi bir
adda çözünürlük sahne numarası sanılmaz.

Dosyalar seçilir seçilmez **denetim tablosu** çıkar: hangi blok hangi dosyaya
bağlandı, süreler ne, eksik/çakışan numara var mı, hangi video klip bloğundan
kısa olduğu için döngüye girecek — hepsi render'dan önce görünür.

## Zamanlama kuralları

- **Ses ana saattir.** Videonun toplam süresi seslendirmenin süresidir.
- **Bloklar arası boşluklarda** (konuşmanın durduğu anlarda) ekran karartılmaz,
  bir önceki sahne tutulur.
- **İlk bloktan önceki** bölümde 1. sahne görünür.
- **Klip bloğundan kısaysa** döngüye alınır, uzunsa baştan gerektiği kadarı kullanılır.
- **Çakışan SRT blokları** otomatik düzeltilir ve uyarı olarak bildirilir.

## Çıktı biçimi

Kodek desteği çalışma anında ölçülür:

| Tarayıcı | Video | Ses | Kap |
|---|---|---|---|
| Google Chrome | H.264 | AAC | **MP4** |
| Patentli kodek içermeyen Chromium | VP9 | Opus | **WebM** |

İkisi de YouTube'a doğrudan yüklenebilir.

## İzinler

Eklenti **hiçbir izin istemez**. Host izni, depolama, ağ erişimi yoktur; dosyalar
yalnızca `<input type="file">` ile okunur ve çıktı tarayıcı belleğinde üretilir.
Manifest V3 uzaktan kod yüklemeyi yasakladığı için kap yazıcıları (`mp4-muxer`,
`webm-muxer`) `vendor/` altında yerel olarak durur.

## Bilinen sınırlar

- **Video sahneleri yavaş render edilir.** Kare doğruluğu için her karede klip
  üzerinde arama (seek) yapılır. Yalnızca görsellerden oluşan bir proje çok
  daha hızlıdır.
- **Uzun projeler bellek ister.** Çıktı tamamlanana kadar bellekte tutulur;
  10 dakikanın üzerindeki işlerde sekmeyi başka işle meşgul etmeyin.
- **Sahne videolarının sesi kullanılmaz.** Ses hattı yalnızca seslendirmedir.

## Dosya düzeni

```
eklenti/kurgu-canavari/
├── manifest.json          # MV3, izinsiz
├── dashboard.html         # pano
├── css/dashboard.css
├── js/
│   ├── arka_plan.js       # simgeye tıklayınca panoyu açar
│   ├── srt.js             # SRT ayrıştırıcı (BOM, CRLF, çakışma onarımı)
│   ├── eslestirme.js      # dosya ↔ blok eşleştirme + zaman çizelgesi
│   ├── render.js          # WebCodecs render motoru
│   └── dashboard.js       # arayüz mantığı
├── vendor/                # mp4-muxer, webm-muxer (yerel, MV3 gereği)
└── ikonlar/
```

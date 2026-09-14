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

## Render hızı

Aynı makinede, 12 sn / 360 kare üreten ölçümler (kare/sn — yüksek olan iyi):

| Senaryo | Önce | Sonra | Kazanç |
|---|---|---|---|
| 6 görsel · 720p30 · Ken Burns kapalı | 118,6 | **263,9** | 2,23× |
| 6 görsel · 720p30 · Ken Burns açık | 86,4 | **118,5** | 1,37× |
| 6 görsel · 1080p30 · Ken Burns açık | 47,2 | **65,7** | 1,39× |
| 3 video · 720p30 | 11,6 | **29,6** | 2,55× |

Hızı belirleyen dört değişiklik:

1. **Video sahneleri artık aranmıyor, sıralı okunuyor.** Ölçümde kare başına
   maliyetin %79'u (46 ms) klipte arama (seek) yapmaktan geliyordu. Klip
   oynatılıp kareler geldikleri gibi alınınca bu tamamen kalkıyor.
   *Oynatma hızını artırmak işe yaramaz:* yakalama ekran tazeleme hızıyla
   sınırlı olduğundan 4× hızda karelerin %75'i düşüyor (ölçüldü).
2. **Sabit görseller yeniden çizilmiyor.** Ken Burns kapalıyken bir sahnenin
   tüm kareleri birebir aynıdır; tuval yalnızca sahne değişince boyanır.
3. **Gereksiz siyah zemin kaldırıldı.** Kaplayarak çizim tuvalin tamamını
   zaten örttüğü için altına boyamak boş işti (1080p'de belirgin fark).
4. **Büyük görseller bir kez küçültülüyor.** 4K bir kaynağı her karede
   ölçeklemek yerine hazırlıkta hedefe indirilir. Yalnızca küçültmede
   uygulanır; kaynak zaten hedef boyuttaysa büyütüp saklamak yavaşlatıyordu
   (ölçüldü: 49 → 43,7 kare/sn).

Kalan sınır: video sahneleri **gerçek zamanın altına inemez** (saniyede ~30
kare). Bu, tarayıcının kare yakalama hızından gelir; aşmak için klibin
demux edilip `VideoDecoder` ile çözülmesi gerekir.

## Bilinen sınırlar

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

## Üyelik / hesap

Yoktur ve gerekmez. Eklenti tek kullanıcı içindir: hesap, giriş, lisans anahtarı
veya sunucu doğrulaması içermez. Chrome Web Store'a yüklemeye de gerek yoktur;
"paketlenmemiş öğe yükle" ile kalıcı olarak kurulu kalır.

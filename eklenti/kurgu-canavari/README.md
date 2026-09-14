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

## Altyazı

SRT'deki metin, aynı zaman kodlarıyla sahnenin üzerine işlenir. On stil vardır:

| | |
|---|---|
| **Kapalı** | Altyazı işlenmez |
| **Klasik beyaz** | Beyaz yazı, siyah kontur |
| **Koyu kutu** | Yarı saydam siyah kutu üzerine beyaz yazı |
| **Sarı vurgulu** | Sarı kutu üzerine koyu yazı |
| **Neon mor** | Mor parlamalı yazı |
| **Sinema** | Krem rengi yazı, yumuşak gölge |
| **Minimal** | Kutusuz, ince beyaz yazı |
| **Karaoke** | Kelimeler ilerledikçe sarıya döner |
| **Typewriter** | Metin karakter karakter açılır, imleçli |
| **Lower Third** | Sola yaslı bant, camgöbeği kenar çizgisi |

Konum (alt / orta / üst) ve boyut (küçük / orta / büyük) ayrıca seçilir.

Panodaki stil kartlarının önizlemeleri, videoyu çizen işlevin **aynısıyla**
üretilir; kartta gördüğünüz ile çıktıdaki birebir aynıdır.

**Altyazı yalnızca bloğun kendi aralığında görünür.** Bloklar arası
boşluklarda sahne tutulur ama yazı ekranda asılı kalmaz.

## Sahne geçişi

| Seçenek | Ne yapar |
|---|---|
| **Yumuşak fade** | Giden sahne, gelen sahnenin üzerinde yavaşça saydamlaşır |
| **Karartarak geçiş** | Giden sahne karartılır, gelen sahne karanlıktan açılır |
| **Sert kesim** | Geçiş yok |

Süre 0,3 / 0,5 / 0,8 / 1,2 sn seçilebilir.

Geçiş penceresi **yeni sahnenin başına** yerleştirilir. Ortalanmış bir pencere,
gelen video klibini kendi başlangıcından önce oynatmayı gerektirirdi. Giden
sahne, geçiş başlarken tuvalden alınan anlık görüntüdür; yarım saniyelik bir
harmanda donuk olması göze çarpmaz ve iki video akışını aynı anda çalıştırma
karmaşasını ortadan kaldırır.

**Altyazı geçişten etkilenmez**; harmanın üzerine tam görünürlükte çizilir.

## Canlı ön izleme

Çizelge hazır olunca ön izleme paneli açılır. Zaman çubuğunu sürükleyerek
herhangi bir ana atlayabilir, **Oynat** ile seslendirmeyi dinleyerek sahnelerin
ve altyazının nerede değiştiğini görebilirsiniz. Ayarları (Ken Burns, altyazı
stili, konum, boyut, çözünürlük) değiştirdiğinizde görünen kare anında yenilenir.

Ön izleme ile çıktı **aynı çizim kodunu** kullanır (`parcaBul`,
`altyaziDurumu`, `gorselKareCiz`); ayrı kod yolları olsaydı ikisi zamanla
birbirinden ayrışırdı. Doğrulaması testlerdedir: beş ayrı zaman noktasında ön
izleme karesi ile render edilmiş kare karşılaştırılır.

Sahneler talep edildikçe açılır ve aynı anda en fazla dördü bellekte tutulur;
elli sahnelik bir projede hepsini açık tutmak yüzlerce MB ederdi.

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

12 sn / 360 kare üreten ölçümler; her senaryo 3 kez çalıştırılıp **ortanca**
alınmıştır (tek ölçüm bu makinede %20'ye varan sapma gösteriyor):

| Senaryo | Önce | Sonra | Kazanç |
|---|---|---|---|
| 3 video · 720p30 | 11,1 | **106,2** | 9,6× |
| 6 görsel · 720p30 · Ken Burns kapalı | 125,3 | **252,1** | 2,0× |
| 6 görsel · 1080p30 · Ken Burns açık | 54,8 | **65,0** | 1,19× |
| 6 görsel · 720p30 · Ken Burns açık | 126,6 | **134,6** | 1,06× |

Hızı belirleyen değişiklikler:

1. **Video sahneleri demux edilip doğrudan kod çözücüye veriliyor**
   (mediabunny + `VideoDecoder`). Ölçümde kare başına maliyetin %79'u (46 ms)
   klipte arama (seek) yapmaktan geliyordu. Üç kademeli yedek zinciri var:
   kod çözme → oynatarak yakalama → kare kare arama.
2. **Sabit görseller yeniden çizilmiyor.** Ken Burns kapalıyken bir sahnenin
   tüm kareleri birebir aynıdır; tuval yalnızca sahne değişince boyanır.
3. **Gereksiz siyah zemin kaldırıldı.** Kaplayarak çizim tuvali zaten örtüyor.
4. **Kuyruk beklemesi** `setTimeout(0)` yerine `dequeue` olayına bağlı.

### Denenip elenen iki yol

- **Oynatma hızını artırmak:** yakalama ekran tazeleme hızıyla sınırlı
  olduğundan 4× hızda karelerin %75'i düşüyor. Kod çözme yolu bu tavanı
  tamamen kaldırdığı için gereksiz kaldı.
- **Görselleri hazırlıkta hedefe ön ölçeklemek:** 4K kaynakta bile kayıptı
  (75,2 < 78,9). Canvas'ın kare başına küçültmesi zaten ucuz; tek seferlik
  yeniden örnekleme karşılığını vermiyor. Kaldırıldı.

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

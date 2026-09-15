# 🖼️ Görsel Kurgu — Chrome Eklentisi

Numaralı görselleri eşit süreli sahnelere bölüp tek bir videoya dizer.
**SRT gerekmez, seslendirme gerekmez.**

Kurgu Canavarı'nın SRT'siz kardeşidir; render motoru ikisinde ortaktır
(`eklenti/ortak/`).

## Kurulum

`chrome://extensions` → **Geliştirici modu** → **Paketlenmemiş öğe yükle** →
bu klasörü seçin.

## Kullanım

| Girdi | Ne verilir |
|---|---|
| **01 Görseller** | Numaralı görseller ve videolar: `01.png`, `Görsel 02.jpg`, `Video 03.mp4` … |
| **02 Fon sesi** | MP3/WAV/M4A &bull; **isteğe bağlı** |

Sıra, dosya adındaki **ilk rakam öbeğine** göre kurulur. Görsel başına süre
3–10 saniye arasında seçilir (varsayılan 5).

- **Ses vermezseniz** sessiz video üretilir; ses izi hiç açılmaz.
- **Ses verirseniz** videonun süresine uydurulur: uzunsa kırpılır, kısaysa
  sessizlikle tamamlanır.
- Görsellerin arasına **video klip** de koyabilirsiniz; klip sahne süresinden
  kısaysa döngüye girer, uzunsa baştan gerektiği kadarı kullanılır.

## Ayarlar

Çözünürlük, işleme modu (hızlı / dengeli / yüksek kalite / özel), sahne geçişi
(yumuşak fade / karartarak / sert kesim), görsel hareketi (sırayla yakınlaş-uzaklaş
/ yakınlaş / uzaklaş / hareketsiz) ve görsel efekt (sinematik kontrast, sıcak,
soğuk, siyah beyaz, vinyet).

Bu eklentide **altyazı yoktur** — altyazı SRT gerektirir, o da Kurgu Canavarı'nın işidir.

## Hangisini kullanmalı?

| | Kurgu Canavarı | **Görsel Kurgu** |
|---|---|---|
| Seslendirme | zorunlu | isteğe bağlı |
| SRT | zorunlu | yok |
| Altyazı | 10 stil | yok |
| Sahne süresi | SRT bloklarından | eşit, siz seçersiniz |

Elinizde zaman kodlu bir seslendirme varsa Kurgu Canavarı; yalnızca bir görsel
yığını varsa bu eklenti.

## Çıktı nereye yazılır

**Oluştur**'a bastığınızda tarayıcı kayıt yeri sorar ve video oradaki dosyaya
**doğrudan akıtılır**. Bellekte kopya tutulmaz.

Bu bir tercih değil, zorunluluktu: çıktı bellekte biriktirildiğinde 5,5
dakikalık 28 Mbps'lik bir video ~1,2 GB ediyor ve tampon büyürken kısa
süreliğine bunun iki katı gerekiyordu — render `Array buffer allocation failed`
ile düşüyordu.

İki sonucu var:

- Bitince ön izleme ve "indir" bağlantısı görünmez; dosya zaten kaydedilmiştir.
- MP4'te `moov` başlığı dosyanın **sonuna** yazılır (baştan yazan kip akışla
  bağdaşmıyor). Yerel oynatmada ve YouTube yüklemesinde fark etmez.

Sahneler de sırası geldikçe açılır, hepsi baştan değil: 1080p bir görsel
bellekte ~8 MB tutar, elli sahnelik bir projede hepsini açık tutmak yüzlerce
MB ederdi.

## İzinler

Yoktur. Ağ erişimi, depolama, host izni istemez; her şey tarayıcı belleğinde olur.

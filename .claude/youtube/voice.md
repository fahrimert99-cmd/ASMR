# voice.md — Kanal ses ve üslup profili

Bu dosyayı `.claude/skills/yt-*` skill'leri okur (`/yt-package`, `/yt-seo`, `/yt-plan`,
`/yt-script`, `/yt-comment`, `/yt-audit`). Repoda durduğu için her oturumda aynı profil kullanılır.

`_(doldurulacak)_` yazan bölümler boş sayılır: skill o bölüme ihtiyaç duyarsa tahmin etmez, size
sorar ve cevabı buraya yazar. Bu dosyaya on dakika ayırmak, yazılabilecek her prompt'tan daha çok
işe yarar.

## Kimle konuşuyorum

Tek bir kişiyi tarif edin. "İzleyiciler" değil; örneğin "gece yarısı uyuyamayan, telefonu
yastığın yanında, 40 dakikalık yağmur sesiyle uykuya dalmak isteyen biri".

_(doldurulacak)_

## Kanal dili

Başlıklar, açıklamalar ve yorum cevapları hangi dilde? (Türkçe / İngilizce / ikisi)
Not: `title.py` ve `hookscore.py` İngilizce kelime listeleriyle puanlıyor; Türkçe başlıklarda
puanlar yol gösterici değildir.

_(doldurulacak)_

## Nasıl konuşuyorum

Varsa en iyi performans gösteren videonuzun açıklamasını, başlıklarını veya anlatım metnini
buraya yapıştırın. Olmak istediğiniz değil, olduğunuz gibi.

_(doldurulacak)_

## Asla kullanmadığım kelimeler

Size ait olmayanlar. Somut yazın: "inanılmaz", "efsane", "kaçırma", "unlock", "game-changer".

_(doldurulacak)_

## Kullandığım kelimeler

Size özgü ifadeler, kalıplar. Bunlar korunur.

_(doldurulacak)_

## İddia etmeyeceklerim

Gösteremeyeceğiniz sayılar, size ait olmayan sonuçlar, kanıtlanmamış faydalar. Örneğin:
"bilimsel olarak kanıtlanmış uyku etkisi", "%100 telifsiz" (kendi kliplerinizdeki müziği
kontrol etmediyseniz), izlenme/abone rakamları.

_(doldurulacak)_

## Formatım

Aşağıdakiler repodaki üretim hattından alınmıştır; yanlış veya eksikse düzeltin.

- **Tür:** Uzun form ASMR / rahatlama / uyku videosu, tipik süre 30-60+ dakika.
- **Kamera:** Kimse kamera karşısında değil; yüz ve konuşan kişi yok.
- **Görüntü:** Ya yapay zekâ görselleri üzerinde yavaş "Ken Burns" kaydırma/yakınlaşma, ya da
  kendi ürettiğim kısa kliplerin yumuşak geçişlerle birleştirilip hedef süreye döngülenmesi.
- **Ses:** Kodla üretilen telifsiz ambient ses (yağmur, okyanus, şömine/ateş, gece/orman,
  rüzgâr, beyaz/pembe/kahverengi gürültü) veya kendi kliplerimin sesi.
- **Anlatım:** Çoğu videoda yok. Varsa edge-tts ile çok yavaş, yumuşak Türkçe anlatım
  (`tr-TR-EmelNeural`, `-12%` tempo). Anlatım sentetik sesle okunduğu için metin "kameraya
  okunacak" değil, TTS'e uygun, kısa ve sakin cümlelerle yazılmalı.
- **Yayın:** YouTube'a yükleme `scripts/youtube_yukle.py` ile. Yayın sıklığı ve günü:
  _(doldurulacak)_
- **Konular:** Temalar yukarıdaki ambient türleri. Repoda ayrıca Moskova tarihini anlatan 59
  sahnelik bir görsel seti var (tarih temalı uyku videosu). Bu seri kanal formatına dahil mi:
  _(doldurulacak)_
- **Giriş / kapanış, küçük resim stili, küfür vb.:** _(doldurulacak)_

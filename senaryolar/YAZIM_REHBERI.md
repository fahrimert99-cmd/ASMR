# Harita Senaryosu Yazım Rehberi

Bu klasördeki her `.py` dosyası, 20 saniyelik bir tarihi harita videosunun
**verisidir**: bir devletin kuruluşundan en geniş sınırlarına büyümesi.
Motor (`src/harita_motoru.py`) bu veriyi okur; kod yazmanız gerekmez.

> Bu rehber hem insanlar hem de her hafta yeni senaryo yazan Claude rutini için
> yazılmıştır. Örnek olarak `osmanli.py`, `roma.py`, `mogol.py` dosyalarına bakın.

## 1. Hızlı başlangıç

```bash
cp senaryolar/selcuklu.py senaryolar/yeni_konu.py      # en yakın örneği kopyalayın
python harita.py --senaryo yeni_konu --kontrol          # doğrula + cikti/harita/yeni_konu/kontrol.png
python harita.py --senaryo yeni_konu --onizleme 17      # tek kare (yatay + dikey)
python harita.py --senaryo yeni_konu --format dikey     # tam video (~3-5 dk)
```

Kimlik (dosya adı) küçük harf, Türkçe karaktersiz ve alt çizgili olmalı:
`buyuk_hun`, `gokturk`, `babur`.

## 2. Dosya yapısı

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `BASLIK` | evet | Büyük harf, ör. `"BÜYÜK SELÇUKLU DEVLETİ"` |
| `ALT_BASLIK` | evet | Giriş kartındaki alt satır, ör. `"Horasan'dan Akdeniz'e"` |
| `PROJEKSIYON` | evet | `dict(lon0=, lat0=, lat1=, lat2=)` — Lambert konik; `lon0/lat0` imparatorluğun ortası, `lat1/lat2` kuzey-güney yayılımının ~1/6 ve ~5/6'sı |
| `RENK` | evet | Ana renk (R, G, B). Mavi tonlardan kaçının (deniz ile karışır). Kullanılanlar: Osmanlı kırmızı, Roma mor, İskender amber, Moğol turuncu, Selçuklu turkuaz, İslam devleti yeşil, Timur menekşe |
| `BARUT` | evet | ~1450 öncesi için `False` (top sesi yerine kuşatma sesi çalar) |
| `MUZIK` | evet | `dict(makam=, kok=, tohum=)` — makamlar: `hicaz, nihavend, kurdi, ussak, saba, rast, dorian, pentatonik`; kök: `C D E F G A B`. İsteğe bağlı `sekizlik=0.22` (davul temposu), `ezgi=[...]` (elle ezgi) |
| `YOUTUBE` | evet | `dict(baslik=, aciklama=, etiketler=[...])` — başlık ≤ 100 karakter ve `#Shorts` içermeli |
| `LEJANT` | hayır | İki lejant metni; varsayılan `("Doğrudan yönetim", "Vasal / bağlı devlet")` |
| `OLAYLAR` | evet | Zaman çizelgesi (aşağıda) |
| `BASKENTLER` | evet | `[(yıl, "Şehir adı"), ...]` — ad `SEHIRLER`'de olmalı |
| `SEHIRLER` | evet | `(ad, boylam, enlem, belirdiği yıl, tür)`; tür: `buyuk`, `kucuk`, `savas` (çapraz kılıç) |
| `BOLGELER` | evet | Fetih bölgeleri (aşağıda) |
| `KAMERA` | evet | `(t, (batı, güney, doğu, kuzey))` anahtar kareleri |
| `KITALAR` | hayır | Finalde beliren büyük harfli adlar: `("ASYA", boylam, enlem, 0)` |

**Yıllar:** MÖ yıllar negatif yazılır (`-336`); ekranda "MÖ 336" görünür.
Zaman çizelgesi MÖ'den MS'ye geçebilir (Roma örneği).

## 3. Olaylar (20 saniye)

```python
dict(t=5.3, yil=1048, baslik="PASİNLER SAVAŞI", alt="Bizans'a karşı ilk büyük zafer",
     yer=(41.68, 39.98), ses="savas"),
```

- **9–12 olay.** İlki `t=1.6` ve `ses="kurulus"`, sonuncusu `t=15.7` ve `ses="final"`
  (finalden önce 1,5 sn'lik gerilim sesi ve büyük vuruş otomatik gelir).
- Olaylar arası en az **1,1 sn** (başlık okunabilsin); yıllar kesin artmalı.
- `baslik` büyük harf ve kısa (≤ 26 karakter), `alt` ≤ 45 karakter. Uzunlar otomatik küçülür ama okunmaz olur.
- `yer`: olayın geçtiği yer (nabız halkası ve stereo ses yönü buradan).
- `ses`: `kurulus`, `fetih`, `savas` (kılıç + nara), `ok` (ok yağmuru), `kusatma`, `top` (yalnızca barut çağı), `deniz` (dalga + top/kuşatma), `final`.

## 4. Bölgeler

```python
_b("Doğu Anadolu", "d", (1071, 1073), [(38.0, 40.6), (39.5, 40.4), ...], tohum=[(42.53, 39.15)]),
_b("Gürcistan", "v", (1067, 1070), [...], dogrudan=(1085, 1087)),
_b("Kuruluş bölgesi", "d", None, [...], tohum=[(61.83, 37.60)], zaman=(0.85, 1.6)),
```

- Halka: `(boylam, enlem)` noktaları, ~10–30 nokta. **Kıyılarda denize taşırın**:
  kara verisi kıyıyı zaten kırpar. Boğaz ve dar kanallarda (İstanbul, Çanakkale,
  Messina, Cebelitarık, Hürmüz) halka kenarını tam su ortasından geçirin.
- **Komşu bölgeleri bindirin.** Sonra fethedilen bölge, önceki bölgenin içine
  0,2–0,5° taşabilir (erken olan kazanır). Kenarları "aynı çizgi" diye bırakmayın:
  aradaki ince şeritler delik olarak kalır.
- `yil=(a, b)`: bölge bu yıllar arasında **mevcut sınırdan dışa doğru** yayılır.
  `tohum` verilirse o şehir(ler)den yayılır (ör. Endülüs için Cebelitarık).
  Aralık `ilk_yil..son_yil` dışına çıkamaz.
- `"v"` vasal/bağlı devlet taralı gösterilir; `dogrudan=(a, b)` ile sonradan doğrudan yönetime geçer.
- İlk bölge (kuruluş) `zaman=(0.85, 1.6)` ile giriş kartı sırasında büyür.
- Çok kısa pencereler otomatik en az 0,35 sn'ye uzatılır.

## 5. Doğruluk kuralları

1. Harita **son yıldaki** sınırları göstermeli. Son yıldan önce kaybedilen geçici
   fetihleri (ör. Osmanlı için Yemen, Tebriz) hiç eklemeyin.
2. Kalıcı toprak kazandırmayan seferler (Viyana, Delhi, Mohi) yalnızca `SEHIRLER`'de
   `savas` işaretiyle gösterilir.
3. Yüzölçümü (`--kontrol` çıktısı) yaygın kabul gören değerin **±%20**'si içinde olmalı.
4. Tartışmalı/özetlenmiş noktaları dosyanın başındaki açıklamada belirtin.
5. Türkçe adlar: Türkçe literatürdeki yaygın biçim (Kudüs, Bağdat, Semerkant, Kurtuba).

## 6. Kamera

- 12–14 anahtar kare; `t=0` ve `t=20` zorunlu. İlk kare kuruluş yerine yakın
  (~4–8° genişlik), son kareler imparatorluğun tamamı + kenar payı.
- Kutu dikey (Shorts) ve yatay formata otomatik sığdırılır; ikisini de `--onizleme` ile kontrol edin.
- Harita verisi boylam **-30..160**, enlem **-10..78** arasını kapsar (Amerika,
  Avustralya ve Güney Afrika yok). Kutular bu alanın içinde kalmalı.

## 7. Kontrol listesi (PR öncesi)

- [ ] `python harita.py --senaryo X --kontrol` → **HATA yok**.
- [ ] `DELIK` satırı yok; varsa tarihen gerçek bir boşluktur ve dosya açıklamasında yazılıdır.
- [ ] `kontrol.png` incelendi: etiketler okunuyor, renkler seçilebiliyor, kamera tüm imparatorluğu gösteriyor.
- [ ] Yüzölçümü yaygın değere yakın.
- [ ] `senaryolar/sira.json` → `sira` listesinin sonuna kimlik eklendi.
- [ ] `senaryolar/KONULAR.md` → konu işaretlendi.

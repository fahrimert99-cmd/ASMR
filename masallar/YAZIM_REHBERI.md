# Masal Yazım Rehberi

Bu klasördeki her `.py` dosyası, resimli kitap üslubunda 2–3 dakikalık bir masal
videosudur: sayfa metinleri, her sayfanın kodla çizilen sahnesi, kamera, müzik ve
ses efekti ipuçları. Görüntü, müzik ve efektler kodla; anlatım Piper (ücretsiz) ya
da ElevenLabs ile üretilir.

> Bu rehber hem insanlar hem de her hafta yeni masal yazan Claude rutini içindir.
> Tam örnek: `keloglan_kapi.py`. Ortak sahne yardımcıları: `_ortak.py`.
> Karakter ve dekor kütüphanesi: `src/masal_cizim.py`.

## 1. Hızlı başlangıç

```bash
python masal.py --masal yeni_masal --kontrol        # doğrula + her sahneyi dene + cikti/masal/yeni_masal/kontak.png
python masal.py --masal yeni_masal --onizleme 40    # tek kare (saniye)
python masal.py --masal yeni_masal --format ikisi   # seslendirmesiz tam video + Shorts (~10 dk)
python masal.py --masal yeni_masal --seslendirme piper --format ikisi   # anlatımlı (huggingface.co gerekir)
```

Kimlik (dosya adı) küçük harf, Türkçe karaktersiz, alt çizgili: `keloglan_dev`,
`tavsan_kaplumbaga`. `_` ile başlayan dosyalar masal sayılmaz (ortak kod).

## 2. Konu ve dil kuralları

1. **Yalnızca kamu malı kaynak:** Anadolu halk masalları (Keloğlan), Nasreddin Hoca
   fıkraları, Ezop / La Fontaine fablları, Grimm ve Andersen masalları. Modern
   uyarlamalardan (kitap, çizgi film) metin ya da sahne kopyalama; masalı **kendi
   cümlelerinle yeniden anlat**.
2. **Çocuğa uygun:** Kan, ölüm, korkutucu şiddet yok. Kötüler kaçar, ders alır,
   barışır. Ölümle biten masalları yumuşat ya da seçme.
3. **Masal dili:** Duyulan geçmiş zaman (-mış): "yaşarmış, demiş". Açılış kalıbı
   (kapak seslendirmesi): "Bir varmış, bir yokmuş…". Kapanış: "Onlar ermiş
   muradına…" ve/veya "Gökten üç elma düşmüş…".
4. **Metin uzunluğu:** Sayfa başına 15–40 kelime, 2–3 cümle. Konuşmalar tırnak
   içinde (“…”) ayrı cümle olsun; ekranda italik görünür ve konuşanın ağzı oynar.
5. **Süre:** 10–14 sayfa; anlatımla toplam 2–3 dakika.

## 3. Dosya yapısı

| Alan | Zorunlu | Açıklama |
|---|---|---|
| `BASLIK` | evet | "Keloğlan ile Kapı" (kapakta ve Shorts başlığında kullanılır) |
| `ALT_BASLIK` | evet | "Bir Anadolu masalı" |
| `YOUTUBE` | evet | `dict(baslik=, aciklama=, etiketler=[...])`; başlık ≤ 100 karakter. İsteğe bağlı `shorts_baslik`, `shorts_aciklama` |
| `SHORTS` | evet | `dict(sayfalar=("a", "b"), alt_baslik=..., cagri=...)` — ardışık 1–3 sayfa (en komik ya da merak uyandıran an, sonu söylemeden) |
| `COCUKLARA_YONELIK` | evet | `True` (YouTube "çocuklara özel" beyanı) |
| `SAYFALAR` | evet | sayfa sözlükleri listesi (aşağıda) |

### Sayfa sözlüğü

| Anahtar | Açıklama |
|---|---|
| `kimlik` | benzersiz kısa ad (`"kapak"`, `"dugun"`) |
| `sahne` | sahne sınıfının örneği (aşağıda) |
| `metin` | sayfa metni (kapak ve metinsiz sayfalarda yok) |
| `konusanlar` | cümle başına konuşan: `[None, "ana", "kel"]` — ağız animasyonu ve (ElevenLabs'te) karakter sesi |
| `muzik` | ruh hâli: `giris, koy, merak, komik, dugun, aksam, gece, gerilim, kacis, sabah, final, son` |
| `sesler` | efekt ipuçları: `[("gicirti", 0.6, dict(sure=1.7)), ("kopma", "c1"), ("elma", "k:bana\|1.7")]` |
| `kamera` | `[(0.0, 1.0, 960, 540), (1.0, 1.05, 1000, 520)]` — (sayfa ilerlemesi 0..1, zoom ≥ 1, merkez x, y) |
| `sure` | sabit süre (yalnızca kapak/son sayfa için; diğerleri metinden/anlatımdan hesaplanır) |
| `seslendirme` | metin kartı olmayan sayfada okunacak metin (kapak: "Bir varmış, bir yokmuş… <Başlık>.") |
| `seslendirme_bas` | anlatımın sayfada başlayacağı an (varsayılan 0,8 sn) |
| `suslu_harf` | `False`: süslü ilk harf kullanma (ör. "GÜM!" ile başlayan sayfa) |

**Efektler:** `cinlama, kuslar, tavuk, adimlar, agir_adimlar, kosma, gicirti, kopma,
dusme, hayal, kurt, circir, baykus, ates, ates_uzak, altin, tirmanma, kalp, kayma,
whoosh, gum, altin_sacilma, horoz, elma, ruzgar` (+ `gulme`: yalnızca düğün müziğinde işaret).

**Zaman ifadeleri:** sayı (sayfa başından sn; negatifse sayfa sonundan), `"c1"`
(1. cümlenin belirdiği an), `"c2+0.4"`, `"k:kelime|yedek"` (anlatımda kelimenin
başladığı an; anlatım yoksa yedek sn).

## 4. Sahne sınıfı

```python
class KapiCekme(EvYakin):
    def arka(self, c, f):            # BİR KEZ çizilen durağan resim (gök, tepeler, ev, ağaçlar)
        ...
    def on(self, c, f, t, d):        # HER KAREDE: karakterler, hareketli eşyalar, ışık
        ct = d["cumle_t"] + [99, 99]    # cümlelerin belirme anları (anlatıma göre kayar)
        kop = ara(t, ct[1], ct[1] + 0.45)
        ...
    def ust(self, c, f, t, d):       # (isteğe bağlı) kameradan bağımsız katman: başlık, "GÜM!" yazısı
        ...
    def sarsinti(self, t):           # (isteğe bağlı) kamera sarsıntısı -> (dx, dy)
        return (0.0, 0.0)
```

- Koordinatlar 1920×1080 "sahne birimi". Alttaki metin kartı y ≈ 810'dan aşağısını
  kaplar: zemin `ZEMIN = 785`; yüzler ve önemli hareket **y 150–780** arasında kalsın.
- `d`: `konusan` (o an konuşan karakter), `sure`, `u` (0..1 ilerleme), `cumle_t`, `sayfa`.
- **Olayları cümlelere bağla:** "Kapı menteşesinden çıkıvermiş!" cümlesi `ct[1]`'de
  beliriyorsa kapı o an kopsun. Sabit saniye yazma; anlatım gelince süreler değişir.
- Kamera zoom'u 1,0–1,08 arası; motor görüş alanını resmin içinde tutar.
- Gece sahnesi: karakterleri çizdikten sonra `gece_tonu(c, 0.8)`, ateş varsa
  `ates_feneri(c, x, y, r, t)`.

## 5. Kütüphane

**Karakterler** (`src/masal_cizim.py`, `C.` önekiyle): `keloglan`, `ana`,
`harami(tip="sisman|uzun|orta", oturuyor=)`, `koylu(kadin=, sapka="kasket|fes")`.
Hepsi `(c, f, x, y, boy, poz=None, yon=1)` alır; `y` ayak hizası, `boy` piksel boyu,
`yon=-1` sola bakar.

**Poz:** `dict(govde, bas, kol_on=(omuz, dirsek), kol_arka, bacak_on=(kalça, diz),
bacak_arka, zipla, goz, agiz, ifade="gul|sasir|zor|kork|sus|kiz", bakis, mutlu_goz)`.
Hazır pozlar: `C.yuru(faz)`, `C.kos(faz)`, `C.TASI` (sırtta yük). Yardımcılar:
`C.goz_kirp(t, tohum)`, `C.konus_agiz(t, d["konusan"] == "kel")`.

**Eşyalar:** `kapi`, `kapi_sirtta()`, `bohca()`, `heybe`, `altin_yigini`, `sikke`,
`elma`, `davul`, `zurna`, `fener`, `bayraklar`, `ates`, `duman`, `toz_bulutu`,
`kuslar`, `ay`, `yildizlar`, `yildizcik`, `dusunce_balonu`, `gum_yazisi`, `ter_damlasi`.

**Dekor (arka):** `gokyuzu`, `tepeler`, `agac_yuvarlak`, `kavak`, `cinar`, `ev`, `cit`,
`cimen_tutamlari`, `cicekler`; `_ortak.manzara(c, f, palet)` paletler:
`sabah, ikindi, aksam, gece, safak, gunbatimi`. Küçük hayvanlar: `_ortak.tavuk`,
`kurt`, `baykus`.

**Yeni şekil:** `f.boya(c, yol, renk, murekkep=0.9, golge=0.3)` — yol için
`egri([...])` (yumuşak), `leke(cx, cy, rx, ry)` (organik), `elips`, `daire`,
`kapsul`, `dikdortgen`, `cokgen`. Yumuşak ışık/yanak: `f.yumusak(...)`.

### Yeni karakter eklemek

Masal yeni bir karakter istiyorsa (dev, Nasreddin Hoca, tavşan…) onu
`src/masal_cizim.py`'ye ekle:
- İmza `(c, f, x, y, boy, poz=None, yon=1, ...)`; 100 birimlik tasarım boyu
  (ayak y=0, baş üstü y≈-100), `k = 100 / boy`, `B = Boyaci(c, f, k)`.
- Gövde parçaları `B(yol, renk)`, kol/bacak `uzuv(...)`, yüz `yuz(B, cx, cy, p, ...)`;
  `p = _poz(poz)` ile ortak poz alanları (göz kırpma, ağız, ifade) kendiliğinden çalışır.
- Dört ayaklı hayvanlarda da aynı yaklaşım: gövde `leke`, bacaklar `uzuv`, yüz `yuz`
  (küçük ölçekle). Mevcut çizimleri bozma; yalnızca ekle.

## 6. Kontrol listesi (PR öncesi)

- [ ] `python masal.py --masal X --kontrol` → **Sonuç: temiz** (HATA yok).
- [ ] `cikti/masal/X/kontak.png` incelendi: karakterler kart üstünde görünüyor,
      sahne metni anlatıyor, gece sahneleri okunuyor.
- [ ] Birkaç kritik an `--onizleme` ile tam boy kontrol edildi.
- [ ] `masallar/sira.json` → `sira` listesinin sonuna kimlik eklendi.
- [ ] `masallar/KONULAR.md` → konu ✅ işaretlendi.
- [ ] PR açıldı. "Masal videosu" iş akışı PR'da Piper anlatımıyla yatay video ve
      Shorts'u render eder, seslendirmeyi dala commit'ler; videolar Artifacts'tedir.

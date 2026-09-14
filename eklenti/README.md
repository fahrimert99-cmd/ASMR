# Eklentiler

İki tarayıcı eklentisi ve paylaştıkları kod.

| Klasör | Ne yapar |
|---|---|
| [`kurgu-canavari/`](kurgu-canavari/) | Seslendirme + SRT + numaralı sahnelerden altyazılı video |
| [`gorsel-kurgu/`](gorsel-kurgu/) | Yalnızca görsellerden eşit süreli video (SRT gerekmez) |
| `ortak/` | İki eklentinin paylaştığı kaynak dosyalar |

## ortak/ ve eşitleme

Tarayıcı eklentileri paket yöneticisi kullanmaz ve Manifest V3 uzaktan kod
yüklemeyi yasaklar; bu yüzden paylaşılan dosyaların **her eklentinin içinde**
bulunması gerekir.

**Tek kaynak `ortak/` klasörüdür.** Eklenti klasörlerindeki şu dosyalar
üretilmiştir, elle düzenlemeyin:

```
js/render.js   js/altyazi.js   js/eslestirme.js   js/arka_plan.js
css/dashboard.css   vendor/*.mjs
```

Düzenleme `ortak/` altında yapılır, sonra:

```bash
python3 eklenti/esitle.py            # ortak/ -> eklentilere kopyala
python3 eklenti/esitle.py --denetle  # kopyalamadan, farkli olanları listele
```

`--denetle` fark bulursa sıfırdan farklı çıkış kodu döner; sürekli
entegrasyonda kullanılabilir.

## Her eklentiye özel kalanlar

`manifest.json`, `dashboard.html`, `js/dashboard.js`, `ikonlar/` ve `README.md`.

# ⚡ Toplu Üretim — Chrome Eklentisi

Bir üretim sitesinin arayüzünü sizin yerinize kullanır: prompt listesini sırayla
işler, görselleri iliştirir, sonucu bekler ve çıkan klipleri **numaralı** olarak
indirir (`01.mp4`, `02.mp4` …) — yani doğrudan Kurgu Canavarı'na girecek düzende.

## Önce bunları bilin

- **Erişim açmaz.** Yalnızca sizin elinizle yapabildiğinizi tekrarlar. Giriş
  yapamadığınız veya krediniz bitmiş bir serviste hiçbir şey yapamaz.
- **Kullanım şartları.** Çoğu servis arayüzünün otomatik sürülmesini sınırlar ve
  hız limiti uygular. Gecikmeyi düşük tutmayın; hesabınıza kısıtlama gelebilir.
- **Siteye özeldir.** Site arayüzünü değiştirirse seçiciler bozulur — ama
  eklentinin tamamı değil, yalnızca öğrettiğiniz dört seçici.

## Kurulum

`chrome://extensions` → **Geliştirici modu** → **Paketlenmemiş öğe yükle** →
bu klasörü seçin.

## Kullanım

**1 · Siteye bağlan.** Üretim sayfasının adresini yazıp *İzin ver ve sekmeyi aç*
deyin. Chrome yalnızca o site için izin ister; eklenti başka hiçbir siteye
erişmez.

**2 · Seçicileri öğret.** Dört satırın her birinde *Öğret*'e basıp açılan
sekmede ilgili öğeye tıklayın:

| Seçici | Neye tıklanır |
|---|---|
| Prompt kutusu | Metni yazdığınız alan |
| Görsel yükleme alanı | Dosya seçme girdisi *(isteğe bağlı)* |
| Üret düğmesi | Üretimi başlatan düğme |
| Sonucun çıktığı alan | Videonun belirdiği kutu (tek videoyu değil, **kapsayıcıyı** seçin) |

Seçiciler kaydedilir; bir daha öğretmeniz gerekmez. Site değişirse yalnızca
bozulanı yeniden öğretirsiniz.

**3 · Promptları girin.** Her prompt arasında bir boş satır. `.txt` dosyası da
yükleyebilirsiniz. Görsel verirseniz sırayla eşleşir: 1. görsel → 1. prompt.
Sayılar eşit değilse eşleşen kadarı işlenir.

**4 · Başlat.** Kuyruk tablosu her işin durumunu, günlük ise ne olduğunu gösterir.
*Durdur* o anki iş bitince durur.

## Ayarlar

**Gecikme (en az / en çok)** — işler arasında bu aralıkta rastgele beklenir.
Sabit aralık yerine rastgele olması bilinçlidir; düzenli aralıklarla istek
göndermek otomasyonun en görünür işaretidir.

**İş başına en fazla bekleme** — sonuç bu sürede gelmezse o iş hatalı sayılır ve
kuyruk devam eder; tek takılan iş tüm listeyi durdurmaz.

**İndirme klasörü** ve **ilk dosya numarası** — numaralandırma buradan devam
eder, böylece ikinci partiyi `08.mp4`'ten başlatabilirsiniz.

## Nasıl çalışıyor

| Parça | İşi |
|---|---|
| `js/icerik.js` | Sayfaya girer: seçici öğrenir, prompt yazar, görsel iliştirir, üret'e basar, sonucu bekler |
| `js/dashboard.js` | Kuyruğu döndürür, gecikmeleri uygular, indirir, günlüğü yazar |
| `js/arka_plan.js` | Simgeye tıklanınca panoyu açar |

Kuyruk panoda döner, arka planda değil: Manifest V3 servis çalışanı boşta kalınca
sonlandırılır ve saatler sürebilen bir kuyruk orada yaşayamaz.

Prompt yazarken değer doğrudan `.value` ile atanmaz; React gibi çatılar bunu
kendi durumlarında takip etmediği için arayüz güncellenmez. Yerel ayarlayıcı
çağrılıp `input`/`change` olayları tetiklenir.

## Doğrulama durumu

Motor, gerçek bir tarayıcıda **sahte bir üretim sitesine** karşı uçtan uca
sınandı: öğrenme kipi doğru seçicileri çıkardı, kuyruk üç işi sırayla üretti,
görseller sayfanın yükleme alanına iliştirildi, dosyalar numaralı olarak indi.

**Pika'nın kendi seçicileri sınanmadı** — o siteye erişimim yok. Öğrenme kipi
zaten bunun için var: seçicileri siz öğretirsiniz, ben tahmin etmem.

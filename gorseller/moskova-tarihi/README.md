# Moskova Tarihi Belgeseli — Görsel Seti

59 adet `.webp`, kronolojik sırada: **`01.webp` – `59.webp`**

## Dosya adları neden sadeleştirildi

İlk hâlde adlar `NNN_<uzun-ingilizce-aciklama>.webp` desenindeydi. Otomatik
montaj aracı bu setle **"A requested file or directory could not be found"**
hatası verdi. İki sebep tespit edildi:

1. **`039_Napoleons-vast-Grande-Armée-...`** dosyası adında **`é`** taşıyordu.
   ASCII dışı karakterler, tarayıcı ile arka uç arasında kodlama uyuşmazlığı
   yaratıp dosyanın bulunamamasına yol açar.
2. **`044_...`** dosyasının adı **108 karakterdi** (sosyal medya kaynaklı sayı
   eki). Uzun yollar Windows'ta sınır aşımına yol açabilir.

Yeni adlar aracın belgelediği desenle aynı (`01`, `02`, `03`…), tamamen ASCII
ve kısa. Numaralandırma ve sıra korundu.

## Kronoloji

| Aralık | Dönem |
|--------|-------|
| 01–08 | Kuruluş öncesi: donmuş vahşi doğa, ilk ahşap yerleşim, yaklaşan tehdit |
| 09–13 | Moğol istilası ve yıkım |
| 14–20 | Moskova Knezliği'nin yükselişi, haraç düzeni, bağımsızlık |
| 21–29 | Kremlin, taç giyme, Korkunç İvan dönemi |
| 30–34 | Tatar akınları, Polonya işgali, kurtuluş |
| 35–37 | Başkentin taşınması, sessiz dönem |
| 38–44 | 1812: Napolyon, Moskova yangını, geri çekilme |
| 45–48 | Devrim ve Sovyet dönemi |
| 49–52 | İkinci Dünya Savaşı, Moskova savunması |
| 53–54 | Sovyet dönemi sonu |
| 55–59 | Modern Moskova ve kapanış |

## Dosya Eşlemesi

Her görselin özgün açıklaması (eski dosya adından):

| Dosya | İçerik |
|---|---|
| `01.webp` | A vast frozen wilderness at dawn endless snow cove |
| `02.webp` | A medieval wooden city engulfed in towering flames |
| `03.webp` | Fresh green sprouts emerging through a layer of me |
| `04.webp` | An endless primeval boreal forest with frozen mars |
| `05.webp` | A small rustic wooden fortress with timber palisad |
| `06.webp` | A stern medieval Russian prince in fur robes and a |
| `07.webp` | A vulnerable timber settlement surrounded by dark  |
| `08.webp` | A dramatic sky suddenly turning black and ominous  |
| `09.webp` | A massive Mongol cavalry horde charging across the |
| `10.webp` | Mongol warriors on horseback storming a burning wo |
| `11.webp` | The smoldering ruins of a destroyed wooden city at |
| `12.webp` | A lone hooded figure standing among ruins watching |
| `13.webp` | A split visual of an antique historical engraving  |
| `14.webp` | A grand living historical tableau of medieval Mosc |
| `15.webp` | A cunning medieval Russian prince in rich furs sea |
| `16.webp` | Peasants and officials counting stacks of coins an |
| `17.webp` | A vast medieval battlefield on an open plain Russi |
| `18.webp` | A triumphant Russian prince raising his sword on h |
| `19.webp` | A powerful bearded Russian ruler in ornate golden  |
| `20.webp` | A sovereign tearing a Mongol tribute charter in a  |
| `21.webp` | The magnificent red brick walls and towers of the  |
| `22.webp` | A grand Orthodox coronation scene with golden icon |
| `23.webp` | A towering Orthodox cathedral interior glowing wit |
| `24.webp` | A dark ominous throne room with long shadows creep |
| `25.webp` | A menacing crowned Tsar with a piercing gaze seate |
| `26.webp` | The colorful onion domes of Saint Basils Cathedral |
| `27.webp` | A shadowy Tsar watching coldly from a high window  |
| `28.webp` | Terrified townspeople fleeing through dark medieva |
| `29.webp` | A city sky filled with dark swirling clouds and di |
| `30.webp` | Tatar raiders on horseback setting a wooden city a |
| `31.webp` | Polish soldiers in 17th century armor occupying th |
| `32.webp` | A desolate snow covered Moscow at its darkest hour |
| `33.webp` | A humble butcher and a noble prince rallying an ar |
| `34.webp` | The city rising again at dawn liberated people che |
| `35.webp` | A grand imperial procession departing Moscow towar |
| `36.webp` | The quiet Moscow skyline at twilight golden cathed |
| `37.webp` | Ominous storm clouds gathering over the Moscow hor |
| `38.webp` | A dramatic dark canvas with the year 1812 implied  |
| `39.webp` | Napoleons vast Grande Armée marching in endless co |
| `40.webp` | Napoleon on horseback entering an eerily empty Mos |
| `41.webp` | The first flames erupting across the rooftops of M |
| `42.webp` | The great fire of Moscow an entire city self immol |
| `43.webp` | Napoleon standing alone amid the burning ruins of  |
| `44.webp` | The French army retreating through a deadly frozen_801284266_1716358366084459_8062260711645569216_n |
| `45.webp` | A revolutionary crowd surging through Moscow stree |
| `46.webp` | The fall of the Tsars imperial eagle and the rise  |
| `47.webp` | Red Square filled with a massive Soviet crowd and  |
| `48.webp` | Glowing red stars mounted atop the Kremlin towers  |
| `49.webp` | A dark menacing horizon with military might approa |
| `50.webp` | Nazi forces halted in the frozen fields just outsi |
| `51.webp` | Soviet soldiers defending Moscow in a blinding bli |
| `52.webp` | The city standing unbroken amid the snow as the ti |
| `53.webp` | A towering Soviet era Moscow skyline with monument |
| `54.webp` | The fall of the Soviet flag over the Kremlin in 19 |
| `55.webp` | A breathtaking aerial view of modern Moscow at gol |
| `56.webp` | A powerful montage of Moscow through the ages burn |
| `57.webp` | The Kremlin and Saint Basils Cathedral rising triu |
| `58.webp` | A majestic sweeping view of Moscow at sunset embod |
| `59.webp` | A poetic closing shot of the Moscow skyline fading |

## Kullanım

Montaj aracında bu 59 dosya `prompts/moskova-belgeseli/SAHNE-59.srt` ile
birlikte kullanılır — SRT'nin N. bloğu `NN.webp` dosyasına karşılık gelir.

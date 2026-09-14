# Domates × Damar — Görsel Prompt Listesi (83 blok, SRT hizalı)

Kaynak SRT: ElevenLabs / Edward, 83 blok, 407,28 sn.
Numaralar artık cümlelere değil **SRT bloklarına** karşılık geliyor;
montaj aracının beklediği numaralandırma budur.

> Cümle bazlı eski liste: [`05-domates-image-promptlari.md`](05-domates-image-promptlari.md)
> Zaman çizelgesi: [`05-domates-SAHNE-TABLOSU.md`](05-domates-SAHNE-TABLOSU.md)
> Üretime hazır liste: [`05-domates-image-promptlari-83.txt`](05-domates-image-promptlari-83.txt)

## Ortak Stil Eki

```
cinematic scientific documentary still, dark charcoal background, dramatic rim
lighting, shallow depth of field, photorealistic macro or clean medical 3D render,
deep tomato red and warm gold accents, no text, no letters, no watermark, 16:9
```

## Tamamı yeniden üretiliyor

Bu liste **83 karenin tamamını sıfırdan üretmek** için hazırlandı; eski 80'lik
setten dosya taşınmasına gerek yok. `05-domates-yeniden-adlandir.sh/.ps1`
betikleri yalnızca eski görselleri korumak isteyenler için duruyor.

Dört prompt (44, 54, 56, 82) yazı taşıyan nesnelerden arındırıldı — belge,
manşet, soru işareti gibi ögeler modele harf ürettiriyordu. Yerlerine boş
yüzeyli karşılıkları kondu.

## Değişenler

- **YENİ (5 adet):** blok 5, 30, 31, 35, 58 — ElevenLabs uzun cümleleri böldü.
- **Kullanılmayan:** eski prompt 1 ve 20 — o cümleler komşusuyla tek bloğa birleşti.
- **İmza kareler** artık blok **21–22** ("Straight molecules stack badly." / "Bent ones fit.") — yan yana, aynı seed.
- **Seed grupları:** eski 9–12 → **8–11**, eski 18–23 → **17–22**, eski 34–39 → **36–41**.
- **Renk kuralı:** likopen daima kırmızı, yağ/misel daima altın.

---

| # | Süre | Anlatım (kısalt.) | Görsel Prompt | Eski no |
|---|---|---|---|---|
| 1 | 12.51 | Never boil your broccoli... | broccoli lowered into violently boiling water with a glowing red prohibition mark above it | 2 |
| 2 | 4.32 | Today I am going to tell you to cook your tomatoes. | ripe tomatoes sliding into a hot pan of olive oil, steam rising, warm approving light | 3 |
| 3 | 6.96 | And the reason those two statements... | split frame, boiling water crossed out on one side and a hot pan approved on the other | 4 |
| 4 | 4.00 | A raw tomato is not the best version... | a perfect raw tomato on a pedestal under cold flat light, beautiful but curiously lifeless | 5 |
| 5 | 1.04 | Cooking it (⚡ 0,64 sn) | a halved tomato touching a hot oiled pan for the very first time, one oil droplet bursting into a sizzle at the point of contact, extreme close, a split second of impact | **YENİ** |
| 6 | 11.44 | Cooking it... makes its most valuable molecule... | the same tomato in a pan, its interior beginning to glow from within as heat reaches it | 6 |
| 7 | 4.24 | The red in a tomato is a pigment called lycopene. | extreme macro of tomato flesh where the red pigment appears as dense glowing granules | 7 |
| 8 | 5.36 | It belongs to the same family as beta carotene... | carrot, tomato and pepper side by side, each radiating its own pigment colour | 8 |
| 9 | 4.36 | But inside a raw tomato, lycopene is not free. | pigment granules held rigidly inside a plant cell, immobilised, unable to drift | 9 |
| 10 | 8.16 | It sits inside structures called chromoplasts... | 3D render of a chromoplast, pigment crystals bound into a mesh of protein and membrane | 10 |
| 11 | 3.44 | Your digestion is not good at breaking that open. | digestive enzymes striking a tough plant cell wall and bouncing away, no entry | 11 |
| 12 | 9.92 | Eat a raw tomato and much of the lycopene passes... | intact plant cell fragments travelling through the intestine, pigment still locked inside | 12 |
| 13 | 2.88 | Heat does three things to that. | three glowing markers igniting in sequence against darkness, abstract and minimal | 13 |
| 14 | 3.84 | First, it ruptures the cell walls. | a plant cell wall splitting open under heat, contents spilling free, dramatic release | 14 |
| 15 | 2.00 | ⚡ Mechanical release. | a sealed vessel cracking apart, its glowing contents escaping outward | 15 |
| 16 | 5.60 | The pigment is no longer trapped behind cellulose... | pigment molecules drifting freely away from shattered cellulose fibres | 16 |
| 17 | 10.56 | Second, it denatures the proteins holding the pigment... | a protein mesh unravelling and releasing the pigment crystals it was gripping | 17 |
| 18 | 6.64 | Third... heat changes the shape of the molecule itself. | a long straight molecule suspended in dark space, heat shimmer approaching it | 18 |
| 19 | 8.64 | In a raw tomato most lycopene is a straight, rod like form... | a perfectly straight rod shaped molecule in 3D, rigid and symmetrical, cold lighting | 19 |
| 20 | 13.44 | And that bent shape packs far more easily into the micelles... | a bent molecule sliding smoothly into the core of a micelle, perfect fit | 21 |
| 21 | 2.96 | ⚡ Straight molecules stack badly. | straight rods jamming awkwardly against a micelle opening, refusing to enter | 22 |
| 22 | 2.04 | ⚡ Bent ones fit. | a single curved molecule slipping cleanly inside a glowing micelle, effortless | 23 |
| 23 | 7.36 | So the same amount of lycopene, cooked, reaches your bloodstream... | two identical portions of pigment, one trickling and one flooding into a bloodstream | 24 |
| 24 | 11.84 | In controlled human studies, lycopene from tomato paste... | a spoon of tomato paste beside fresh tomatoes in a clinical setting, measurement bars behind | 25 |
| 25 | 2.48 | There is a second multiplier. | a second glowing marker igniting beside the first, abstract minimal composition | 26 |
| 26 | 6.44 | Lycopene is fat soluble, so without fat there are no micelles... | pigment molecules repelled by water, clumping together with no micelle anywhere in sight | 27 |
| 27 | 3.92 | Cooking tomatoes in olive oil is not just flavour. | olive oil poured into a pan of tomatoes, golden swirls spreading through red | 28 |
| 28 | 2.56 | It completes the delivery system. | micelles assembling rapidly around pigment molecules the moment oil arrives | 29 |
| 29 | 3.04 | Same mechanism we covered with avocado... | an avocado half and a tomato connected by a shared glowing micelle between them | 30 |
| 30 | 2.08 | The fat is not the nutrient. | a single golden olive oil droplet resting alone on dark slate, plain and inert, carrying nothing, no glow of its own | **YENİ** |
| 31 | 1.84 | The fat is the vehicle. | the same golden droplet now formed into a carrier vessel with a glowing red molecule seated inside it, moving forward through dark space | **YENİ** |
| 32 | 2.72 | Now follow it past the intestine. | a glowing particle leaving the intestinal wall and entering the body's interior | 31 |
| 33 | 9.12 | Absorbed lycopene is packed into chylomicrons... | a large chylomicron particle entering a lymph vessel and rising through the chest | 32 |
| 34 | 4.00 | From there it transfers into your lipoproteins... | pigment molecules transferring from one carrier particle into another in the bloodstream | 33 |
| 35 | 2.72 | And this is where it gets specific. | a wide field of pale drifting lipoprotein spheres with focus racking down onto one single particle, everything else falling away into blur | **YENİ** |
| 36 | 5.04 | Lycopene concentrates inside LDL particles. | cross section of an LDL particle with red pigment molecules embedded in its lipid core | 34 |
| 37 | 1.44 | ⚡ That matters. | a single LDL particle held in a narrow spotlight against black, weight and significance | 35 |
| 38 | 6.00 | Because the first step in arterial plaque is not LDL itself. | an ordinary LDL particle drifting harmlessly along an artery, unremarkable | 36 |
| 39 | 5.52 | It is LDL becoming oxidised inside the artery wall. | an LDL particle inside the artery wall being attacked and chemically altered, sparks of damage | 37 |
| 40 | 8.84 | An oxidised LDL particle is what a macrophage swallows... | a macrophage engulfing oxidised particles uncontrollably and swelling into a foam cell | 38 |
| 41 | 5.92 | Lycopene riding inside that particle sits exactly where the damage starts. | red pigment glowing inside an LDL particle precisely as oxidative attack arrives | 39 |
| 42 | 3.04 | It also builds up in tissue. | glowing pigment accumulating gradually within dense body tissue | 40 |
| 43 | 8.56 | The liver, the adrenal glands, the testes and the prostate... | anatomical body map with four organs highlighted in warm red, clean medical render | 41 |
| 44 | 2.96 | So what does the evidence say? | stacked pages and glowing data screens in a dim laboratory, every surface blank and abstract, only light and shape | 42 |
| 45 | 3.52 | Here it splits, and I want to be careful. | a single path dividing into two diverging routes, one lit and one dim | 43 |
| 46 | 4.64 | On observational data it is consistent. | a clean downward trend line across a wide scatter of data points | 44 |
| 47 | 12.32 | People with higher lycopene intake... lower rates of cardiovascular disease | population silhouettes with varying internal glow, healthier arteries beside brighter ones | 45 |
| 48 | 3.04 | Meta analyses of those studies agree. | a forest plot style diagram with markers clustered consistently on one side | 46 |
| 49 | 4.08 | On randomised trials it is thinner. | a sparse thin data line barely rising, honest and underwhelming | 47 |
| 50 | 7.72 | Supplementing isolated lycopene has not reliably reproduced the benefit. | a supplement capsule beside a whole tomato, the capsule dim and the tomato glowing | 48 |
| 51 | 3.28 | That gap usually means one of two things. | two separate doors in darkness, both closed, equal weight | 49 |
| 52 | 6.96 | Either the whole food matters more than the single molecule... | a whole tomato dissolving into hundreds of different molecules, only one of them highlighted | 50 |
| 53 | 3.36 | We do not yet know which. | an unanswered question formed by light over an empty laboratory bench | 51 |
| 54 | 4.16 | On prostate cancer, be sceptical of what you have heard. | a bold blank banner crumbling into dust, the shape of a claim collapsing, deliberately unconvincing | 52 |
| 55 | 6.72 | The claim was strong in the nineteen nineties and has been downgraded. | a bar of evidence visibly shrinking over time along a timeline | 53 |
| 56 | 4.48 | Regulators now describe that evidence as very limited. | an official looking blank document under cold light bearing only an embossed seal, nothing written on it | 54 |
| 57 | 1.16 | ⚡ Mechanism, strong. | a solid stone block engraved with a molecular diagram, immovable | 55 |
| 58 | 1.84 | Strong. (⚡ mekanizma) | a thick anchored pillar of dark stone standing immovable, a glowing red molecule embedded at its core, weight and certainty | **YENİ** |
| 59 | 3.20 | ⚡ Population data, consistent. | a steady row of aligned markers stretching into the distance | 56 |
| 60 | 3.60 | ⚡ Isolated supplement trials, disappointing. | a collapsed scaffold beside an empty capsule, grey and flat | 57 |
| 61 | 1.84 | So, four rules. | four plain objects arranged in a precise row on dark slate | 58 |
| 62 | 1.20 | ⚡ One. | a single ripe tomato lit alone in clean light | 59 |
| 63 | 1.36 | ⚡ Cook them. | tomatoes simmering in a pan, gentle bubbles, warm rising steam | 60 |
| 64 | 4.64 | Sauce, roasted, stewed, or paste. | four preparations of tomato arranged together, sauce, roasted, stewed and paste | 61 |
| 65 | 7.92 | The processed form is genuinely the better source here. | a jar of tomato paste glowing brighter than the fresh tomatoes beside it | 62 |
| 66 | 1.20 | ⚡ Two. | a bottle of olive oil standing beside a tomato, side lit | 63 |
| 67 | 2.00 | Cook them in oil. | olive oil poured over tomatoes in a hot pan, golden and generous | 64 |
| 68 | 4.00 | Without fat the lycopene has no way across. | pigment molecules stopped at the intestinal wall with no micelle to carry them | 65 |
| 69 | 1.36 | ⚡ Three. | a spoonful of dense tomato paste held up in clean light | 66 |
| 70 | 5.60 | Tomato paste is the most concentrated lycopene source... | a small jar of paste beside a large pile of fresh tomatoes, equal glow from both | 67 |
| 71 | 4.96 | One spoonful carries more than several fresh tomatoes. | a single spoon of paste radiating intensely beside several dimmer whole tomatoes | 68 |
| 72 | 1.44 | ⚡ Four. | a fresh raw tomato slice on dark slate, crisp and bright | 69 |
| 73 | 4.88 | Keep some raw, because cooking does cost you vitamin C. | a raw tomato slice glowing on one side while a cooked one dims, honest comparison | 70 |
| 74 | 3.80 | This is a real trade, not a free upgrade. | a balance scale with something gained on one pan and something lost on the other | 71 |
| 75 | 4.72 | Cooked for lycopene, raw for vitamin C, and eat both. | a plate holding both cooked tomato sauce and fresh raw slices together | 72 |
| 76 | 1.44 | Two quick notes. | two small objects placed deliberately on a dark surface, clinical calm | 73 |
| 77 | 5.36 | Very high long term intake can tint the skin faintly orange. | human skin under clinical light with an extremely faint warm tint, subtle and factual | 74 |
| 78 | 2.92 | It is harmless and it reverses. | the same skin tone returning to normal, reassuring soft light | 75 |
| 79 | 8.32 | And if you have reflux, tomato is a common trigger... | anatomical stomach and oesophagus with a mild warm irritation glow, medical illustration | 76 |
| 80 | 2.48 | None of this was really about a tomato. | a tomato dissolving upward into abstract glowing molecular particles | 77 |
| 81 | 10.96 | It was about a molecule that is present but unavailable. | a glowing molecule sealed inside a transparent locked container, visible but unreachable | 78 |
| 82 | 3.12 | So which molecule should we follow next? | an array of whole foods glowing faintly in darkness with one empty pedestal waiting among them | 79 |
| 83 | 5.89 | Write a food and an organ in the comments... | luminous speech bubbles floating above a glowing artery silhouette | 80 |

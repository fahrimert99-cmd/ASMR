// Pano mantığı: dosyaları oku, çizelgeyi kur, denetle, render et.

import { srtAyristir, zamanBicimle } from "./srt.js";
import { dosyalariEslestir, zamanCizelgesiKur } from "./eslestirme.js";
import { render, sesCoz, kodekSec, videoOnDenetim, sahneKaynagiAc, onizlemeKaresiCiz } from "./render.js";
import { STILLER, altyaziCiz } from "./altyazi.js";

const $ = (id) => document.getElementById(id);
const el = {
  ses: $("ses"), srt: $("srt"), sahneler: $("sahneler"),
  cozunurluk: $("cozunurluk"), fps: $("fps"), bitrate: $("bitrate"), kenburns: $("kenburns"),
  olustur: $("olustur"), durdur: $("durdur"), durum: $("durum"),
  panelDenetim: $("panel-denetim"), mesajlar: $("mesajlar"), cizelge: $("cizelge"),
  panelIlerleme: $("panel-ilerleme"), cubuk: $("cubuk"),
  ilerlemeBaslik: $("ilerleme-baslik"), ilerlemeMetin: $("ilerleme-metin"),
  stilIzgara: $("stil-izgara"), altyaziKonum: $("altyazi-konum"), altyaziBoyut: $("altyazi-boyut"),
  panelOnizleme: $("panel-onizleme"), onizlemeTuval: $("onizleme-tuval"), onizlemeBilgi: $("onizleme-bilgi"),
  onizlemeOynat: $("onizleme-oynat"), onizlemeCubuk: $("onizleme-cubuk"), onizlemeZaman: $("onizleme-zaman"),
  onizlemeSes: $("onizleme-ses"),
  panelSonuc: $("panel-sonuc"), sonucBilgi: $("sonuc-bilgi"),
  onizleme: $("onizleme"), indir: $("indir"),
};

const durum = { sesTamponu: null, sesAdi: "", bloklar: [], parcalar: [], hazir: false };
const bozukVideolar = new Set();
const klipSureleri = new Map();
let iptalIstendi = false;
let sonUrl = null;

function mesaj(tur, metin) {
  const d = document.createElement("div");
  d.className = `mesaj ${tur}`;
  d.textContent = metin;
  el.mesajlar.appendChild(d);
}

function durumYaz(metin) { el.durum.textContent = metin; }

// ------------------------------------------------------------------- girdiler

el.ses.addEventListener("change", async () => {
  const dosya = el.ses.files[0];
  if (!dosya) { durum.sesTamponu = null; return cizelgeyiTazele(); }
  durumYaz(`"${dosya.name}" çözülüyor…`);
  try {
    durum.sesTamponu = await sesCoz(dosya);
    durum.sesAdi = dosya.name;
    if (el.onizlemeSes.src) URL.revokeObjectURL(el.onizlemeSes.src);
    el.onizlemeSes.src = URL.createObjectURL(dosya);
    durumYaz(`Seslendirme hazır — ${zamanBicimle(durum.sesTamponu.duration)}`);
  } catch (e) {
    durum.sesTamponu = null;
    durumYaz(`Ses çözülemedi: ${e.message}`);
  }
  await cizelgeyiTazele();
});

el.srt.addEventListener("change", async () => {
  const dosya = el.srt.files[0];
  if (!dosya) { durum.bloklar = []; return cizelgeyiTazele(); }
  const metin = await dosya.text();
  const sonuc = srtAyristir(metin);
  durum.bloklar = sonuc.bloklar;
  durum.srtUyarilari = sonuc.uyarilar;
  await cizelgeyiTazele();
});

el.sahneler.addEventListener("change", () => cizelgeyiTazele());

// --------------------------------------------------------- çizelge + denetim

async function cizelgeyiTazele() {
  el.mesajlar.innerHTML = "";
  el.cizelge.innerHTML = "";
  durum.hazir = false;
  bozukVideolar.clear();
  klipSureleri.clear();
  durdurOnizleme();
  onbellegiBosalt();
  el.panelOnizleme.hidden = true;

  const sesVar = !!durum.sesTamponu;
  const blokVar = durum.bloklar.length > 0;
  const dosyalar = [...(el.sahneler.files || [])];

  el.panelDenetim.hidden = !(blokVar || dosyalar.length);

  if (!sesVar || !blokVar || !dosyalar.length) {
    const eksikler = [];
    if (!sesVar) eksikler.push("seslendirme");
    if (!blokVar) eksikler.push("SRT");
    if (!dosyalar.length) eksikler.push("sahne dosyaları");
    durumYaz(`Eksik: ${eksikler.join(", ")}.`);
    el.olustur.disabled = true;
    if (blokVar || dosyalar.length) cizelgeyiCiz([], dosyalar.length);
    return;
  }

  for (const u of durum.srtUyarilari || []) mesaj("uyari", u);

  const { sahneler, sorunlar } = dosyalariEslestir(dosyalar, durum.bloklar.length);
  for (const s of sorunlar) mesaj(s.tur, s.mesaj);

  const parcalar = zamanCizelgesiKur(durum.bloklar, sahneler, durum.sesTamponu.duration);
  durum.parcalar = parcalar;

  // Sesin SRT'den belirgin biçimde kısa/uzun olması, yanlış SRT seçildiğinin
  // en sık işaretidir; sessizce render etmek yerine açıkça söylenir.
  const srtSonu = durum.bloklar[durum.bloklar.length - 1].bit;
  const fark = durum.sesTamponu.duration - srtSonu;
  if (Math.abs(fark) > 1.5) {
    mesaj(
      "uyari",
      `Ses ${zamanBicimle(durum.sesTamponu.duration)}, SRT ise ${zamanBicimle(srtSonu)} bitiyor ` +
      `(${fark > 0 ? "ses" : "SRT"} ${Math.abs(fark).toFixed(1)} sn daha uzun). ` +
      `Farklı bir seslendirmenin SRT'sini seçmiş olabilirsiniz.`
    );
  }

  // Video sahneleri render'dan ÖNCE sınanır: çözülemeyen bir klip, ancak
  // butona basıldıktan sonra değil, burada görünsün.
  const videolar = [...new Map(parcalar.filter((p) => p.sahne?.tur === "video")
    .map((p) => [p.sahne.no, p.sahne])).values()];
  if (videolar.length) {
    durumYaz(`${videolar.length} video sahnesi sınanıyor…`);
    const sonuclar = await Promise.all(videolar.map((s) => videoOnDenetim(s.dosya)));
    sonuclar.forEach((r, i) => {
      const s = videolar[i];
      if (!r.ok) {
        bozukVideolar.add(s.no);
        mesaj("hata", `"${s.dosya.name}" kullanılamıyor: ${r.hata}.`);
      } else {
        klipSureleri.set(s.no, r.sure);
      }
    });
  }

  cizelgeyiCiz(parcalar, dosyalar.length);

  const eksikSahne = parcalar.filter((p) => !p.sahne).length + bozukVideolar.size;
  if (eksikSahne) {
    durumYaz(`${eksikSahne} blok kullanılamıyor (dosya yok veya video çözülemedi). Eksikleri tamamlayın.`);
    el.olustur.disabled = true;
  } else {
    mesaj("iyi", `${parcalar.length} blok, ${parcalar.length} sahne ile tam eşleşti. Toplam süre ${zamanBicimle(durum.sesTamponu.duration)}.`);
    durumYaz("Çizelge hazır. Oluşturabilirsiniz.");
    el.olustur.disabled = false;
    durum.hazir = true;
    el.panelOnizleme.hidden = false;
    onizlemeyiTazele(cubuktanZaman());
  }
}

function cizelgeyiCiz(parcalar, dosyaSayisi) {
  for (const p of parcalar) {
    const tr = document.createElement("tr");
    if (!p.sahne) tr.className = "bos";
    const hucre = (metin, sinif) => {
      const td = document.createElement("td");
      td.textContent = metin;
      if (sinif) td.className = sinif;
      return td;
    };
    tr.append(
      hucre(String(p.sahneNo), "mono"),
      hucre(zamanBicimle(p.bas)),
      hucre(zamanBicimle(p.bit)),
      hucre((p.bit - p.bas).toFixed(2) + " sn"),
      hucre(p.sahne ? p.sahne.dosya.name : "— dosya yok —"),
      hucre(
        !p.sahne ? "—"
        : p.sahne.tur === "görsel" || p.sahne.tur === "gorsel" ? "görsel"
        : bozukVideolar.has(p.sahne.no) ? "video (çözülemedi)"
        : klipSureleri.has(p.sahne.no)
          ? `video ${klipSureleri.get(p.sahne.no).toFixed(1)} sn` +
            (klipSureleri.get(p.sahne.no) < p.bit - p.bas - 0.05 ? " • döngüye girecek" : "")
          : "video"
      ),
      hucre(p.metin.length > 60 ? p.metin.slice(0, 60) + "…" : p.metin)
    );
    el.cizelge.appendChild(tr);
  }
  if (!parcalar.length && dosyaSayisi) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 7;
    td.textContent = "SRT seçilmeden çizelge kurulamaz.";
    tr.appendChild(td);
    el.cizelge.appendChild(tr);
  }
}

// ---------------------------------------------------------------- oluşturma

el.durdur.addEventListener("click", () => {
  iptalIstendi = true;
  el.durdur.disabled = true;
  el.ilerlemeMetin.textContent = "Durduruluyor…";
});

el.olustur.addEventListener("click", async () => {
  if (!durum.hazir) return;

  const [en, boy] = el.cozunurluk.value.split("x").map(Number);
  const fps = Number(el.fps.value);
  const bitOrani = Math.round(Number(el.bitrate.value) * 1_000_000);

  iptalIstendi = false;
  el.olustur.disabled = true;
  el.durdur.hidden = false;
  el.durdur.disabled = false;
  el.panelIlerleme.hidden = false;
  el.panelSonuc.hidden = true;
  el.cubuk.style.width = "0%";
  el.ilerlemeBaslik.textContent = "Render sürüyor…";

  const baslangic = performance.now();
  try {
    const secim = await kodekSec(en, boy, fps);
    el.ilerlemeMetin.textContent = `Kodek: ${secim.video.ad} + ${secim.ses.ad} (${secim.kap.toUpperCase()})`;

    const sonuc = await render({
      parcalar: durum.parcalar,
      sesTamponu: durum.sesTamponu,
      en, boy, fps, bitOrani,
      kenBurns: el.kenburns.checked,
      altyazi: altyaziAyari(),
      iptal: () => iptalIstendi,
      ilerleme: (d) => {
        if (d.asama === "hazirlik") { el.ilerlemeMetin.textContent = "Sahneler hazırlanıyor…"; return; }
        if (d.asama === "ses") { el.ilerlemeMetin.textContent = "Ses kodlandı, görüntüye geçiliyor…"; return; }
        const yuzde = Math.round(d.oran * 100);
        el.cubuk.style.width = yuzde + "%";
        const gecen = (performance.now() - baslangic) / 1000;
        const tahmin = d.oran > 0.02 ? gecen / d.oran - gecen : null;
        el.ilerlemeMetin.textContent =
          `%${yuzde} — ${d.kare}/${d.toplamKare} kare` +
          (tahmin ? ` • tahmini kalan ${zamanBicimle(tahmin)}` : "");
      },
    });

    const blob = new Blob([sonuc.veri], { type: sonuc.mime });
    if (sonUrl) URL.revokeObjectURL(sonUrl);
    sonUrl = URL.createObjectURL(blob);

    const ad = (durum.sesAdi.replace(/\.[^.]+$/, "") || "kurgu") + "." + sonuc.kap;
    el.onizleme.src = sonUrl;
    el.indir.href = sonUrl;
    el.indir.download = ad;
    el.sonucBilgi.innerHTML = "";
    const bilgi = document.createElement("div");
    bilgi.className = "mesaj iyi";
    bilgi.textContent =
      `${ad} — ${zamanBicimle(sonuc.sure)} • ${en}×${boy} • ${fps} fps • ${sonuc.kodekAdi} • ` +
      `${(blob.size / 1048576).toFixed(1)} MB • ${((performance.now() - baslangic) / 1000).toFixed(0)} sn'de üretildi`;
    el.sonucBilgi.appendChild(bilgi);
    el.panelSonuc.hidden = false;
    el.ilerlemeBaslik.textContent = "Render tamamlandı";
    durumYaz("Video hazır.");
  } catch (e) {
    el.ilerlemeBaslik.textContent = "Render durdu";
    el.ilerlemeMetin.textContent = e.message;
    durumYaz(`Hata: ${e.message}`);
  } finally {
    el.olustur.disabled = false;
    el.durdur.hidden = true;
  }
});


// ------------------------------------------------------------ canlı ön izleme
//
// Önizleme, render'ın çizim işlevlerinin AYNISINI kullanır; ayrı bir çizim yolu
// olsaydı önizleme ile çıktı zamanla birbirinden ayrışırdı.

const ONBELLEK_SINIRI = 4;          // aynı anda açık tutulan sahne kaynağı
const onizlemeOnbellek = new Map(); // sahneNo -> kaynak
let onizlemeCiziliyor = false;      // üst üste binen çizimleri engeller
let onizlemeBekleyen = null;        // en son istenen zaman
let oynuyor = false;

async function kaynakCoz(sahne) {
  if (onizlemeOnbellek.has(sahne.no)) return onizlemeOnbellek.get(sahne.no);
  const kaynak = await sahneKaynagiAc(sahne);
  onizlemeOnbellek.set(sahne.no, kaynak);
  // Tüm sahneleri bellekte tutmak uzun projelerde yüzlerce MB eder; en eski
  // girdiler bırakılır.
  while (onizlemeOnbellek.size > ONBELLEK_SINIRI) {
    const [ilkNo, ilkKaynak] = onizlemeOnbellek.entries().next().value;
    try { ilkKaynak.serbest(); } catch (_) {}
    onizlemeOnbellek.delete(ilkNo);
  }
  return kaynak;
}

function onbellegiBosalt() {
  for (const k of onizlemeOnbellek.values()) { try { k.serbest(); } catch (_) {} }
  onizlemeOnbellek.clear();
}

async function onizlemeCizDerhal(t) {
  const tuval = el.onizlemeTuval;
  const [en, boy] = el.cozunurluk.value.split("x").map(Number);
  // Önizleme tuvali çıktı oranında ama daha küçük çizilir: 1080p kareyi her
  // fare hareketinde üretmek gereksiz.
  const olcek = Math.min(1, 960 / en);
  const pEn = Math.round(en * olcek), pBoy = Math.round(boy * olcek);
  if (tuval.width !== pEn || tuval.height !== pBoy) { tuval.width = pEn; tuval.height = pBoy; }
  tuval.style.aspectRatio = `${en} / ${boy}`;

  const ctx = tuval.getContext("2d", { alpha: false });
  const parca = await onizlemeKaresiCiz(ctx, durum.parcalar, kaynakCoz, t, {
    en: pEn, boy: pBoy, kenBurns: el.kenburns.checked, altyazi: altyaziAyari(),
  });

  el.onizlemeZaman.textContent = zamanBicimle(t);
  const kilit = altyaziAyari().stil === "kapali" ? "Altyazı kapalı" : "SRT kilidi aktif";
  el.onizlemeBilgi.textContent = `${kilit} • Sahne ${parca.sahneNo} • ${t.toFixed(3)} sn`;
}

// Çizimler sıraya alınır: kullanıcı çubuğu hızlı sürüklerken her ara değer için
// çizim başlatmak yerine yalnızca en son istenen zaman çizilir.
async function onizlemeyiTazele(t) {
  if (!durum.parcalar.length) return;
  onizlemeBekleyen = t;
  if (onizlemeCiziliyor) return;
  onizlemeCiziliyor = true;
  try {
    while (onizlemeBekleyen !== null) {
      const hedef = onizlemeBekleyen;
      onizlemeBekleyen = null;
      await onizlemeCizDerhal(hedef);
    }
  } catch (e) {
    el.onizlemeBilgi.textContent = "Ön izleme çizilemedi: " + e.message;
  } finally {
    onizlemeCiziliyor = false;
  }
}

function cubuktanZaman() {
  const sure = durum.sesTamponu?.duration || 0;
  return (Number(el.onizlemeCubuk.value) / 1000) * sure;
}

el.onizlemeCubuk.addEventListener("input", () => {
  if (oynuyor) durdurOnizleme();
  onizlemeyiTazele(cubuktanZaman());
});

function durdurOnizleme() {
  oynuyor = false;
  el.onizlemeSes.pause();
  el.onizlemeOynat.textContent = "▶ Oynat";
}

el.onizlemeOynat.addEventListener("click", async () => {
  if (oynuyor) return durdurOnizleme();
  if (!durum.sesTamponu) return;
  oynuyor = true;
  el.onizlemeOynat.textContent = "❚❚ Duraklat";
  el.onizlemeSes.currentTime = cubuktanZaman();
  try { await el.onizlemeSes.play(); } catch (_) {}
  const adim = () => {
    if (!oynuyor) return;
    const t = el.onizlemeSes.currentTime;
    const sure = durum.sesTamponu.duration;
    el.onizlemeCubuk.value = String(Math.round((t / sure) * 1000));
    onizlemeyiTazele(t);
    if (t >= sure - 0.02) return durdurOnizleme();
    requestAnimationFrame(adim);
  };
  requestAnimationFrame(adim);
});

// Ayar değişince görünen kare de değişmeli.
for (const g of [el.kenburns, el.cozunurluk, el.altyaziKonum, el.altyaziBoyut]) {
  g.addEventListener("change", () => onizlemeyiTazele(cubuktanZaman()));
}

// ------------------------------------------------------------ altyazı stili

let secilenStil = "klasik";

function altyaziAyari() {
  return { stil: secilenStil, konum: el.altyaziKonum.value, boyut: el.altyaziBoyut.value };
}

// Kartlardaki önizlemeler, videoda kullanılan çizim işleviyle üretilir; böylece
// kartta görünen ile çıktıdaki birebir aynıdır.
function stilKartlariniKur() {
  el.stilIzgara.innerHTML = "";
  for (const [anahtar, tanim] of Object.entries(STILLER)) {
    const kart = document.createElement("div");
    kart.className = "stil-kart" + (anahtar === secilenStil ? " secili" : "");
    kart.dataset.stil = anahtar;

    const tuval = document.createElement("canvas");
    tuval.width = 300; tuval.height = 120;
    const ctx = tuval.getContext("2d");
    ctx.fillStyle = "#10192b";
    ctx.fillRect(0, 0, 300, 120);
    if (anahtar === "kapali") {
      ctx.fillStyle = "#5b6b87";
      ctx.font = '600 22px "Segoe UI", system-ui, sans-serif';
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText("Aa", 150, 60);
    } else {
      altyaziCiz(ctx, "Hikâye burada", { stil: anahtar, konum: "orta", puntoOran: 0.19 }, 300, 120, 0.6);
    }

    const ad = document.createElement("div");
    ad.className = "ad";
    ad.textContent = tanim.ad;

    kart.append(tuval, ad);
    kart.addEventListener("click", () => {
      secilenStil = anahtar;
      [...el.stilIzgara.children].forEach((k) => k.classList.toggle("secili", k.dataset.stil === anahtar));
      onizlemeyiTazele(cubuktanZaman());
    });
    el.stilIzgara.appendChild(kart);
  }
}
stilKartlariniKur();

// Kodek desteğini açılışta bildir: kullanıcı dosyaları seçmeden önce
// hangi kapta çıktı alacağını bilsin.
(async () => {
  try {
    const s = await kodekSec(1920, 1080, 30);
    durumYaz(
      `Hazır. Bu tarayıcı ${s.video.ad} + ${s.ses.ad} destekliyor; çıktı ${s.kap.toUpperCase()} olacak. ` +
      `Başlamak için üç dosya grubunu da seçin.`
    );
  } catch (e) {
    durumYaz(`Bu tarayıcıda render yapılamaz: ${e.message}`);
    el.olustur.disabled = true;
  }
})();

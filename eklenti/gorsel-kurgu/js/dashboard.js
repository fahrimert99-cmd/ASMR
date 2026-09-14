// Görsel Kurgu panosu.
//
// Kurgu Canavarı'nın SRT'siz kardeşi: sahneler blok zamanlarına değil, eşit
// sürelere oturur. Render motoru (js/render.js) ve eşleştirme mantığı iki
// eklentide ortaktır; kaynağı eklenti/ortak/ altındadır.

import { dosyalariEslestir, sabitCizelgeKur } from "./eslestirme.js";
import {
  render, sesCoz, kodekSec, videoOnDenetim,
  sahneKaynagiAc, onizlemeKaresiCiz, sesiSureyeUydur,
} from "./render.js";

const $ = (id) => document.getElementById(id);
const el = {
  sahneler: $("sahneler"), ses: $("ses"), sahneSure: $("sahne-sure"),
  cozunurluk: $("cozunurluk"), mod: $("mod"), fps: $("fps"), bitrate: $("bitrate"),
  gecis: $("gecis"), gecisSure: $("gecis-sure"), hareket: $("hareket"), efekt: $("efekt"),
  olustur: $("olustur"), durdur: $("durdur"), durum: $("durum"),
  panelDenetim: $("panel-denetim"), mesajlar: $("mesajlar"), cizelge: $("cizelge"),
  panelOnizleme: $("panel-onizleme"), onizlemeTuval: $("onizleme-tuval"),
  onizlemeBilgi: $("onizleme-bilgi"), onizlemeOynat: $("onizleme-oynat"),
  onizlemeCubuk: $("onizleme-cubuk"), onizlemeZaman: $("onizleme-zaman"), onizlemeSes: $("onizleme-ses"),
  panelIlerleme: $("panel-ilerleme"), cubuk: $("cubuk"),
  ilerlemeBaslik: $("ilerleme-baslik"), ilerlemeMetin: $("ilerleme-metin"),
  panelSonuc: $("panel-sonuc"), sonucBilgi: $("sonuc-bilgi"),
  onizleme: $("onizleme"), indir: $("indir"),
};

const durum = { sesTamponu: null, sesAdi: "", parcalar: [], sure: 0, hazir: false };
const bozukVideolar = new Set();
const klipSureleri = new Map();
let iptalIstendi = false;
let sonUrl = null;

const zamanBicimle = (sn) => {
  if (!isFinite(sn)) return "--:--";
  const d = Math.floor(sn / 60);
  return `${String(d).padStart(2, "0")}:${(sn - d * 60).toFixed(2).padStart(5, "0")}`;
};
const durumYaz = (m) => (el.durum.textContent = m);
function mesaj(tur, metin) {
  const d = document.createElement("div");
  d.className = `mesaj ${tur}`;
  d.textContent = metin;
  el.mesajlar.appendChild(d);
}

// ------------------------------------------------------------------- ayarlar

const MODLAR = { hizli: { fps: "24", mbps: 6 }, dengeli: { fps: "30", mbps: 12 }, yuksek: { fps: "30", mbps: 28 } };
function moduUygula() {
  const m = MODLAR[el.mod.value];
  el.fps.disabled = !!m;
  el.bitrate.disabled = !!m;
  if (m) { el.fps.value = m.fps; el.bitrate.value = String(m.mbps); }
}
el.mod.addEventListener("change", moduUygula);
moduUygula();

const gecisAyari = () => ({ tur: el.gecis.value, sure: Number(el.gecisSure.value) });
const cizimAyari = () => ({
  hareket: el.hareket.value,
  efekt: el.efekt.value,
  altyazi: { stil: "kapali" },   // bu eklentide altyazı yok
  gecis: gecisAyari(),
});

// ------------------------------------------------------------ canlı ön izleme

const ONBELLEK_SINIRI = 4;
const onbellek = new Map();
let ciziliyor = false, bekleyen = null, oynuyor = false;

async function kaynakCoz(sahne) {
  if (onbellek.has(sahne.no)) return onbellek.get(sahne.no);
  const kaynak = await sahneKaynagiAc(sahne);
  onbellek.set(sahne.no, kaynak);
  while (onbellek.size > ONBELLEK_SINIRI) {
    const [no, k] = onbellek.entries().next().value;
    try { k.serbest(); } catch (_) {}
    onbellek.delete(no);
  }
  return kaynak;
}
function onbellegiBosalt() {
  for (const k of onbellek.values()) { try { k.serbest(); } catch (_) {} }
  onbellek.clear();
}

async function onizlemeyiTazele(t) {
  if (!durum.parcalar.length) return;
  bekleyen = t;
  if (ciziliyor) return;
  ciziliyor = true;
  try {
    while (bekleyen !== null) {
      const hedef = bekleyen;
      bekleyen = null;
      const [en, boy] = el.cozunurluk.value.split("x").map(Number);
      const olcek = Math.min(1, 960 / en);
      const pEn = Math.round(en * olcek), pBoy = Math.round(boy * olcek);
      if (el.onizlemeTuval.width !== pEn) { el.onizlemeTuval.width = pEn; el.onizlemeTuval.height = pBoy; }
      const ctx = el.onizlemeTuval.getContext("2d", { alpha: false });
      const parca = await onizlemeKaresiCiz(ctx, durum.parcalar, kaynakCoz, hedef, { en: pEn, boy: pBoy, ...cizimAyari() });
      el.onizlemeZaman.textContent = zamanBicimle(hedef);
      el.onizlemeBilgi.textContent = `Sahne ${parca.sahneNo} • ${hedef.toFixed(3)} sn`;
    }
  } catch (e) {
    el.onizlemeBilgi.textContent = "Ön izleme çizilemedi: " + e.message;
  } finally {
    ciziliyor = false;
  }
}

const cubuktanZaman = () => (Number(el.onizlemeCubuk.value) / 1000) * (durum.sure || 0);

function durdurOnizleme() {
  oynuyor = false;
  el.onizlemeSes.pause();
  el.onizlemeOynat.textContent = "▶ Oynat";
}

el.onizlemeCubuk.addEventListener("input", () => {
  if (oynuyor) durdurOnizleme();
  onizlemeyiTazele(cubuktanZaman());
});

el.onizlemeOynat.addEventListener("click", async () => {
  if (oynuyor) return durdurOnizleme();
  if (!durum.sure) return;
  oynuyor = true;
  el.onizlemeOynat.textContent = "❚❚ Duraklat";
  // Fon sesi yoksa ön izleme zamanı elle ilerletilir.
  const sesVar = !!durum.sesTamponu && el.onizlemeSes.src;
  const baslangic = cubuktanZaman();
  const t0 = performance.now();
  if (sesVar) { el.onizlemeSes.currentTime = baslangic; try { await el.onizlemeSes.play(); } catch (_) {} }
  const adim = () => {
    if (!oynuyor) return;
    const t = sesVar ? el.onizlemeSes.currentTime : baslangic + (performance.now() - t0) / 1000;
    el.onizlemeCubuk.value = String(Math.round((t / durum.sure) * 1000));
    onizlemeyiTazele(Math.min(t, durum.sure));
    if (t >= durum.sure - 0.02) return durdurOnizleme();
    requestAnimationFrame(adim);
  };
  requestAnimationFrame(adim);
});

for (const g of [el.sahneSure, el.cozunurluk, el.gecis, el.gecisSure, el.hareket, el.efekt]) {
  g.addEventListener("change", () => {
    if (g === el.sahneSure) cizelgeyiTazele();
    else onizlemeyiTazele(cubuktanZaman());
  });
}

// --------------------------------------------------------------- girdi + çizelge

el.ses.addEventListener("change", async () => {
  const dosya = el.ses.files[0];
  if (!dosya) { durum.sesTamponu = null; durum.sesAdi = ""; return cizelgeyiTazele(); }
  durumYaz(`"${dosya.name}" çözülüyor…`);
  try {
    durum.sesTamponu = await sesCoz(dosya);
    durum.sesAdi = dosya.name;
    if (el.onizlemeSes.src) URL.revokeObjectURL(el.onizlemeSes.src);
    el.onizlemeSes.src = URL.createObjectURL(dosya);
  } catch (e) {
    durum.sesTamponu = null;
    mesaj("hata", `Ses çözülemedi: ${e.message}`);
  }
  cizelgeyiTazele();
});

el.sahneler.addEventListener("change", () => cizelgeyiTazele());

async function cizelgeyiTazele() {
  el.mesajlar.innerHTML = "";
  el.cizelge.innerHTML = "";
  durum.hazir = false;
  bozukVideolar.clear();
  klipSureleri.clear();
  durdurOnizleme();
  onbellegiBosalt();
  el.panelOnizleme.hidden = true;

  const dosyalar = [...(el.sahneler.files || [])];
  el.panelDenetim.hidden = !dosyalar.length;
  if (!dosyalar.length) {
    durumYaz("Başlamak için görselleri seçin.");
    el.olustur.disabled = true;
    return;
  }

  const { sahneler, sorunlar } = dosyalariEslestir(dosyalar, null);
  for (const s of sorunlar) mesaj(s.tur, s.mesaj);

  const sureBasina = Number(el.sahneSure.value);
  const parcalar = sabitCizelgeKur(sahneler, sureBasina);
  durum.parcalar = parcalar;
  durum.sure = parcalar.length ? parcalar[parcalar.length - 1].bit : 0;

  // Video sahneleri render'dan önce sınanır.
  const videolar = [...new Map(parcalar.filter((p) => p.sahne?.tur === "video")
    .map((p) => [p.sahne.no, p.sahne])).values()];
  if (videolar.length) {
    durumYaz(`${videolar.length} video sınanıyor…`);
    const r = await Promise.all(videolar.map((s) => videoOnDenetim(s.dosya)));
    r.forEach((sonuc, i) => {
      const s = videolar[i];
      if (!sonuc.ok) { bozukVideolar.add(s.no); mesaj("hata", `"${s.dosya.name}" kullanılamıyor: ${sonuc.hata}.`); }
      else klipSureleri.set(s.no, sonuc.sure);
    });
  }

  for (const p of parcalar) {
    const tr = document.createElement("tr");
    const hucre = (m, sinif) => { const td = document.createElement("td"); td.textContent = m; if (sinif) td.className = sinif; return td; };
    const tur = p.sahne.tur === "gorsel" ? "görsel"
      : bozukVideolar.has(p.sahne.no) ? "video (çözülemedi)"
      : klipSureleri.has(p.sahne.no)
        ? `video ${klipSureleri.get(p.sahne.no).toFixed(1)} sn` +
          (klipSureleri.get(p.sahne.no) < p.bit - p.bas - 0.05 ? " • döngüye girecek" : "")
        : "video";
    if (bozukVideolar.has(p.sahne.no)) tr.className = "bos";
    tr.append(hucre(String(p.sahneNo), "mono"), hucre(zamanBicimle(p.bas)), hucre(zamanBicimle(p.bit)),
              hucre((p.bit - p.bas).toFixed(2) + " sn"), hucre(p.sahne.dosya.name), hucre(tur));
    el.cizelge.appendChild(tr);
  }

  if (bozukVideolar.size) {
    durumYaz(`${bozukVideolar.size} dosya kullanılamıyor. Çıkarın veya değiştirin.`);
    el.olustur.disabled = true;
    return;
  }

  mesaj("iyi", `${parcalar.length} sahne × ${sureBasina} sn = ${zamanBicimle(durum.sure)}` +
    (durum.sesTamponu ? " • fon sesi bu süreye uydurulacak" : " • sessiz video"));
  durumYaz("Hazır. Oluşturabilirsiniz.");
  el.olustur.disabled = false;
  durum.hazir = true;
  el.panelOnizleme.hidden = false;
  onizlemeyiTazele(cubuktanZaman());
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
    el.ilerlemeMetin.textContent = `Kodek: ${secim.video.ad} (${secim.kap.toUpperCase()})`;

    const sonuc = await render({
      parcalar: durum.parcalar,
      sesTamponu: durum.sesTamponu ? sesiSureyeUydur(durum.sesTamponu, durum.sure) : null,
      en, boy, fps, bitOrani, ...cizimAyari(),
      iptal: () => iptalIstendi,
      ilerleme: (d) => {
        if (d.asama !== "goruntu") return;
        const yuzde = Math.round(d.oran * 100);
        el.cubuk.style.width = yuzde + "%";
        const gecen = (performance.now() - baslangic) / 1000;
        const tahmin = d.oran > 0.02 ? gecen / d.oran - gecen : null;
        el.ilerlemeMetin.textContent = `%${yuzde} — ${d.kare}/${d.toplamKare} kare` +
          (tahmin ? ` • tahmini kalan ${zamanBicimle(tahmin)}` : "");
      },
    });

    const blob = new Blob([sonuc.veri], { type: sonuc.mime });
    if (sonUrl) URL.revokeObjectURL(sonUrl);
    sonUrl = URL.createObjectURL(blob);
    const ad = ((durum.sesAdi || "").replace(/\.[^.]+$/, "") || "gorsel-kurgu") + "." + sonuc.kap;
    el.onizleme.src = sonUrl;
    el.indir.href = sonUrl;
    el.indir.download = ad;
    el.sonucBilgi.innerHTML = "";
    const bilgi = document.createElement("div");
    bilgi.className = "mesaj iyi";
    bilgi.textContent = `${ad} — ${zamanBicimle(sonuc.sure)} • ${en}×${boy} • ${fps} fps • ` +
      `${sonuc.kodekAdi} • ${(blob.size / 1048576).toFixed(1)} MB • ` +
      `${((performance.now() - baslangic) / 1000).toFixed(0)} sn'de üretildi`;
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

(async () => {
  try {
    const s = await kodekSec(1920, 1080, 30);
    durumYaz(`Hazır. Çıktı ${s.kap.toUpperCase()} olacak (${s.video.ad}). Başlamak için görselleri seçin.`);
  } catch (e) {
    durumYaz(`Bu tarayıcıda render yapılamaz: ${e.message}`);
    el.olustur.disabled = true;
  }
})();

// Zaman çizelgesini gerçek bir video dosyasına dönüştüren render motoru.
//
// Tarayıcı içinde WebCodecs ile kodlama yapılır; kap (container) yazımı
// eklentiye gömülü mp4-muxer / webm-muxer ile olur. Manifest V3 uzaktan kod
// yüklemeyi yasakladığı için bu kütüphaneler vendor/ altında yerel durur.

import { Muxer as Mp4Muxer, ArrayBufferTarget as Mp4Hedef } from "../vendor/mp4-muxer.mjs";
import { Muxer as WebmMuxer, ArrayBufferTarget as WebmHedef } from "../vendor/webm-muxer.mjs";
import { Input, BlobSource, ALL_FORMATS, VideoSampleSink } from "../vendor/mediabunny.min.mjs";
import { altyaziCiz, ANIMASYONLU } from "./altyazi.js";

const SES_ORNEKLEME = 48000;   // Opus 48 kHz zorunlu kılar; AAC de sorunsuz kabul eder
const SES_KANAL = 2;
const SES_PARCA = 1024;        // AudioData başına kare

// ---------------------------------------------------------------- kodek seçimi

// Chrome'da H.264 + AAC vardır ve MP4 üretilir. Patentli kodek içermeyen
// Chromium türevlerinde bunlar yoktur; o durumda VP9 + Opus ile WebM üretilir.
// Seçim çalışma anında yapılır, derleme anında varsayılmaz.
export async function kodekSec(en, boy, fps) {
  if (typeof VideoEncoder === "undefined" || typeof AudioEncoder === "undefined") {
    throw new Error("Bu tarayıcı WebCodecs desteklemiyor. Chrome 94+ gerekir.");
  }

  const videoAdaylari = [
    { ad: "H.264", codec: "avc1.4d0028", kap: "mp4", ek: { avc: { format: "avc" } } },
    { ad: "H.264", codec: "avc1.42001f", kap: "mp4", ek: { avc: { format: "avc" } } },
    { ad: "VP9", codec: "vp09.00.10.08", kap: "webm", ek: {} },
    { ad: "VP8", codec: "vp8", kap: "webm", ek: {} },
  ];
  const sesAdaylari = [
    { ad: "AAC", codec: "mp4a.40.2", kap: "mp4" },
    { ad: "Opus", codec: "opus", kap: "webm" },
  ];

  let video = null;
  for (const a of videoAdaylari) {
    try {
      const s = await VideoEncoder.isConfigSupported({
        codec: a.codec, width: en, height: boy, bitrate: 8_000_000, framerate: fps, ...a.ek,
      });
      if (s.supported) { video = a; break; }
    } catch (_) { /* desteklenmeyen kodek: sıradakine geç */ }
  }
  if (!video) throw new Error("Tarayıcı hiçbir video kodlayıcıyı desteklemiyor.");

  // Ses kodeği kabı takip etmeli: AAC'yi WebM'e, Opus'u MP4'e koymak yaygın
  // oynatıcılarda sorun çıkarır.
  let ses = null;
  for (const a of sesAdaylari) {
    if (a.kap !== video.kap) continue;
    try {
      const s = await AudioEncoder.isConfigSupported({
        codec: a.codec, sampleRate: SES_ORNEKLEME, numberOfChannels: SES_KANAL, bitrate: 192000,
      });
      if (s.supported) { ses = a; break; }
    } catch (_) { /* yoksay */ }
  }
  // Ses kodlayıcı bulunamazsa sessiz video yine üretilebilir; hata yalnızca
  // gerçekten seslendirme verildiğinde anlamlıdır ve orada bildirilir.
  return { video, ses, kap: video.kap };
}

// ------------------------------------------------------------------- ses çözme

// OfflineAudioContext 48 kHz olarak açılır; decodeAudioData çözerken kaynağı
// bu hıza yeniden örnekler, böylece MP3/WAV/M4A ne gelirse gelsin kodlayıcıya
// tek tip veri gider.
export async function sesCoz(dosya) {
  const veri = await dosya.arrayBuffer();
  const ctx = new OfflineAudioContext(SES_KANAL, SES_ORNEKLEME, SES_ORNEKLEME);
  const tampon = await ctx.decodeAudioData(veri);
  return tampon;
}

// Ses tamponunu hedef süreye uydurur: uzunsa kırpar, kısaysa sessizlikle
// tamamlar. Sabit süreli modda videonun uzunluğunu sahneler belirler; ses
// olduğu gibi bırakılsaydı kap içinde görüntüden uzun bir ses izi kalırdı.
export function sesiSureyeUydur(tampon, hedefSure) {
  const hedefUzunluk = Math.max(1, Math.round(hedefSure * SES_ORNEKLEME));
  if (Math.abs(tampon.length - hedefUzunluk) < 2) return tampon;
  const ctx = new OfflineAudioContext(SES_KANAL, hedefUzunluk, SES_ORNEKLEME);
  const yeni = ctx.createBuffer(SES_KANAL, hedefUzunluk, SES_ORNEKLEME);
  const kopyalanacak = Math.min(tampon.length, hedefUzunluk);
  for (let k = 0; k < SES_KANAL; k++) {
    const kaynak = tampon.getChannelData(Math.min(k, tampon.numberOfChannels - 1));
    yeni.getChannelData(k).set(kaynak.subarray(0, kopyalanacak));
  }
  return yeni;
}

// --------------------------------------------------------------- sahne kaynağı

// Görsel, olduğu gibi saklanır.
//
// Hazırlıkta hedef boyuta ön ölçekleme denendi ve ÖLÇÜMLE ELENDİ: canvas'ın
// kare başına küçültmesi zaten ucuz, tek seferlik yeniden örnekleme ise
// karşılığını vermiyor. 4K kaynakta bile kayıptı (kare/sn, 3 ölçüm ortancası):
//   720p  Ken Burns açık : ön ölçekleme 112.6  <  kapalı 129.7
//   1080p Ken Burns açık : 64.9  <  64.4 (fark yok)
//   4K -> 1080p          : 75.2  <  78.9
async function gorselHazirla(dosya) {
  const bitmap = await createImageBitmap(dosya);
  return { tur: "gorsel", bitmap, sure: Infinity, serbest: () => bitmap.close() };
}

async function videoHazirla(dosya) {
  const url = URL.createObjectURL(dosya);
  const el = document.createElement("video");
  el.src = url;
  el.muted = true;          // sahne sesi kullanılmaz: ses hattı seslendirmedir
  el.preload = "auto";
  await new Promise((coz, red) => {
    el.onloadedmetadata = coz;
    el.onerror = () => red(new Error(`"${dosya.name}" çözülemedi (desteklenmeyen video kodeği olabilir).`));
  });
  return {
    tur: "video",
    dosya,
    el,
    sure: el.duration,
    serbest: () => { el.src = ""; URL.revokeObjectURL(url); },
  };
}

// Video sahnelerinin gerçekten çözülebildiğini ÖNCEDEN sınar.
//
// Bu denetim olmadan, çözülemeyen tek bir klip render'ı ancak kullanıcı
// butona bastıktan sonra düşürür. Tarayıcının hangi kodekleri çözebildiği
// (özellikle H.264) yapıya göre değiştiği için sınama çalışma anında yapılır.
export async function videoOnDenetim(dosya) {
  const url = URL.createObjectURL(dosya);
  const el = document.createElement("video");
  el.preload = "metadata";
  el.muted = true;
  try {
    const sure = await new Promise((coz, red) => {
      const zamanAsimi = setTimeout(() => red(new Error("çözümleme zaman aşımına uğradı")), 15000);
      el.onloadedmetadata = () => { clearTimeout(zamanAsimi); coz(el.duration); };
      el.onerror = () => { clearTimeout(zamanAsimi); red(new Error("tarayıcı bu video kodeğini çözemiyor")); };
      el.src = url;
    });
    return { ok: true, sure };
  } catch (e) {
    return { ok: false, hata: e.message };
  } finally {
    el.src = "";
    URL.revokeObjectURL(url);
  }
}

// Tek bir sahnenin kaynağını açar (canlı önizleme talep ettikçe kullanır).
export async function sahneKaynagiAc(sahne) {
  return sahne.tur === "gorsel" ? gorselHazirla(sahne.dosya) : videoHazirla(sahne.dosya);
}

export async function sahneKaynaklariHazirla(parcalar, en, boy, ilerleme) {
  const kaynaklar = new Map();
  let n = 0;
  for (const p of parcalar) {
    if (!p.sahne || kaynaklar.has(p.sahne.no)) continue;
    kaynaklar.set(
      p.sahne.no,
      p.sahne.tur === "gorsel" ? await gorselHazirla(p.sahne.dosya) : await videoHazirla(p.sahne.dosya)
    );
    ilerleme?.(++n);
  }
  return kaynaklar;
}

// Video sahnelerini KOD ÇÖZEREK besleyen akış (en hızlı yol).
//
// Oynatarak yakalama, ekran tazeleme hızıyla sınırlıdır: saniyede ~30 kareden
// hızlı olamaz (ölçüldü). Klibi demux edip doğrudan VideoDecoder ile çözmek bu
// tavanı kaldırır; çözme işlemcinin izin verdiği hızda ilerler.
//
// Kod çözücü klibin kodeğini desteklemiyorsa (örn. patentli kodek içermeyen bir
// yapıda H.264) kurulum başarısız olur ve çağıran taraf oynatma yoluna düşer.
class VideoCozucuAkisi {
  constructor(dosya) {
    this.dosya = dosya;
    this.girdi = null;
    this.yutucu = null;
    this.yineleyici = null;
    this.sonOrnek = null;
    this.sonZaman = -1;
    this.bitti = false;
  }

  static destekliMi() {
    return typeof VideoDecoder !== "undefined";
  }

  async hazirla() {
    this.girdi = new Input({ source: new BlobSource(this.dosya), formats: ALL_FORMATS });
    const iz = await this.girdi.getPrimaryVideoTrack();
    if (!iz) throw new Error("video izi bulunamadı");
    if (!(await iz.canDecode())) throw new Error("bu kodek çözülemiyor");
    this.yutucu = new VideoSampleSink(iz);
  }

  async baslat() {
    this.#ornegiBirak();
    this.yineleyici = this.yutucu.samples();
    this.sonZaman = -1;
    this.bitti = false;
  }

  async kareAl(hedef) {
    while (!this.bitti && this.sonZaman < hedef) {
      const { value, done } = await this.yineleyici.next();
      if (done || !value) { this.bitti = true; break; }
      this.#ornegiBirak();
      this.sonOrnek = value;
      this.sonZaman = value.timestamp;
    }
    if (!this.sonOrnek) return null;
    const resim = this.sonOrnek.toCanvasImageSource();
    return { resim, en: resim.displayWidth ?? resim.width, boy: resim.displayHeight ?? resim.height };
  }

  #ornegiBirak() {
    if (this.sonOrnek) { try { this.sonOrnek.close(); } catch (_) {} this.sonOrnek = null; }
  }

  async kapat() {
    try { this.yineleyici && (await this.yineleyici.return()); } catch (_) {}
    this.#ornegiBirak();
    try { this.girdi && this.girdi.dispose && (await this.girdi.dispose()); } catch (_) {}
    this.yineleyici = null;
  }
}

// Bir video sahnesi için en hızlı çalışan akışı açar.
//
// Sıra: kod çözme (tavansız) → oynatarak yakalama (gerçek zamanla sınırlı)
// → kare kare arama (en yavaş, son çare).
async function akisAc(kaynak) {
  if (VideoCozucuAkisi.destekliMi()) {
    const akis = new VideoCozucuAkisi(kaynak.dosya);
    try {
      await akis.hazirla();
      await akis.baslat();
      return { akis, yol: "cozucu" };
    } catch (_) {
      try { await akis.kapat(); } catch (_) {}
    }
  }
  if (VideoAkisi.destekliMi()) {
    const akis = new VideoAkisi(kaynak.el);
    try {
      await akis.baslat(0);
      return { akis, yol: "oynatma" };
    } catch (_) {
      try { await akis.kapat(); } catch (_) {}
    }
  }
  return null;   // arama yoluna düşülecek
}

// --------------------------------------------------------------------- çizim

// Kaynak en-boy oranı hedefe uymadığında kırparak doldurur (cover). Sığdırmak
// (contain) siyah bantlar bırakır ve belgesel akışında dikkat dağıtır.
function kaplayarakCiz(ctx, kaynak, kEn, kBoy, en, boy, zoom = 1) {
  const olcek = Math.max(en / kEn, boy / kBoy) * zoom;
  const g = kEn * olcek, y = kBoy * olcek;
  ctx.drawImage(kaynak, (en - g) / 2, (boy - y) / 2, g, y);
}

async function videoKaresineGit(el, zaman) {
  const hedef = Math.min(Math.max(zaman, 0), Math.max(el.duration - 0.001, 0));
  if (Math.abs(el.currentTime - hedef) < 1e-3 && el.readyState >= 2) return;
  await new Promise((coz) => {
    const bitti = () => { el.removeEventListener("seeked", bitti); coz(); };
    el.addEventListener("seeked", bitti);
    el.currentTime = hedef;
  });
}

// Video sahnelerini SIRALI OKUMA ile besleyen akış.
//
// Neden: kare başına arama (seek) ölçümde 46 ms tutuyordu ve toplam maliyetin
// %79'uydu. Klibi oynatıp kareleri geldikleri gibi almak aramayı tamamen
// ortadan kaldırır; ölçümde saniyede ~30 kare veriyor (aramalı yöntem ~17).
// Oynatma hızını artırmak işe yaramaz: yakalama ekran tazeleme hızıyla sınırlı
// olduğu için 4x hızda karelerin %75'i düşüyor (ölçüldü).
//
// Kareler kendi zaman damgalarıyla geldiği için çıktı kare hızı klibinkinden
// farklı olsa bile klip gerçek hızında akar.
class VideoAkisi {
  constructor(el) {
    this.el = el;
    this.okuyucu = null;
    this.iz = null;
    this.sonKare = null;      // elde tutulan son kare (ödünç, kapatılmaz)
    this.sonZaman = -1;
    this.bitti = false;
  }

  static destekliMi() {
    return typeof MediaStreamTrackProcessor !== "undefined" &&
           typeof HTMLMediaElement !== "undefined" &&
           typeof HTMLMediaElement.prototype.captureStream === "function";
  }

  async baslat(bas = 0) {
    await this.kapat(false);
    this.el.currentTime = bas;
    this.iz = this.el.captureStream().getVideoTracks()[0];
    this.okuyucu = new MediaStreamTrackProcessor({ track: this.iz }).readable.getReader();
    this.bitti = false;
    this.sonZaman = -1;
    await this.el.play();
  }

  // Kaynak zamanı 'hedef' olan kareyi verir. Akış ileri sarılamaz; bu yüzden
  // hedefe ulaşana kadar kareler okunup atılır, hedef geçilince son kare tutulur.
  async kareAl(hedef) {
    if (!this.okuyucu) return this.#paket();
    while (!this.bitti && this.sonZaman < hedef) {
      const { value, done } = await this.okuyucu.read();
      if (done || !value) { this.bitti = true; break; }
      if (this.sonKare) this.sonKare.close();
      this.sonKare = value;
      this.sonZaman = value.timestamp / 1e6;
    }
    return this.#paket();
  }

  #paket() {
    if (!this.sonKare) return null;
    return { resim: this.sonKare, en: this.sonKare.displayWidth, boy: this.sonKare.displayHeight };
  }

  async kapat(tamamen = true) {
    try { this.okuyucu && (await this.okuyucu.cancel()); } catch (_) {}
    try { this.iz && this.iz.stop(); } catch (_) {}
    try { !this.el.paused && this.el.pause(); } catch (_) {}
    if (tamamen && this.sonKare) { try { this.sonKare.close(); } catch (_) {} this.sonKare = null; }
    this.okuyucu = null;
    this.iz = null;
  }
}

// ------------------------------------------------- ortak çizim (paylaşılan)
//
// Bu üç işlevi hem render döngüsü hem canlı önizleme kullanır. Ayrı kod
// yolları olsaydı önizleme ile çıktı zamanla birbirinden ayrışırdı.

export function parcaBul(parcalar, t) {
  let i = 0;
  while (i < parcalar.length - 1 && t >= parcalar[i].bit) i++;
  return { parca: parcalar[i], indeks: i };
}

// Altyazı yalnızca bloğun KENDİ aralığında görünür; boşluklarda sahne tutulur
// ama metin ekranda asılı kalmaz.
export function altyaziDurumu(parca, t, altyazi) {
  const acik = !!altyazi && altyazi.stil && altyazi.stil !== "kapali";
  const icinde = acik && t >= parca.blokBas && t < parca.blokBit;
  return {
    metin: icinde ? parca.metin : "",
    oran: icinde ? (t - parca.blokBas) / Math.max(parca.blokBit - parca.blokBas, 1e-6) : 1,
  };
}

// Sahne geçişi.
//
// Geçiş penceresi YENİ sahnenin başına yerleştirilir: [bas, bas + süre].
// Ortalanmış bir pencere, gelen video klibini kendi başlangıcından önce
// oynatmayı gerektirirdi. Giden sahne, geçiş başlarken tuvalden alınan anlık
// görüntüdür; 0,5 sn'lik bir harmanda donuk olması göze çarpmaz ve iki video
// akışını aynı anda çalıştırma karmaşasını ortadan kaldırır.
// Görsel hareketi.
//
// "sirayla" ardışık sahneleri dönüşümlü yakınlaştırıp uzaklaştırır; tek yönlü
// hareket uzun bir belgeselde tekdüze hissettirir.
export const HAREKETLER = {
  yok:      "Hareketsiz",
  yakinlas: "Yavaşça yakınlaş",
  uzaklas:  "Yavaşça uzaklaş",
  sirayla:  "Sırayla yakınlaş / uzaklaş",
};

const ZOOM_MIKTARI = 0.06;

export function hareketYonu(hareket, sahneNo) {
  if (hareket === "sirayla") return sahneNo % 2 === 1 ? "yakinlas" : "uzaklas";
  return hareket || "yok";
}

// Görsel efektleri.
//
// Filtreler canvas'ın kendi 'filter' özelliğiyle uygulanır; ayrı bir piksel
// döngüsünden çok daha hızlıdır. Vinyet filtreyle ifade edilemediği için
// sahnenin üzerine radyal bir gradyanla çizilir.
export const EFEKTLER = {
  yok:         { ad: "Yok" },
  sinematik:   { ad: "Sinematik kontrast", filtre: "contrast(1.18) saturate(1.12) brightness(0.97)", vinyet: 0.34 },
  sicak:       { ad: "Sıcak ton", filtre: "sepia(0.22) saturate(1.18) brightness(1.03)" },
  soguk:       { ad: "Soğuk ton", filtre: "contrast(1.06) saturate(1.05) hue-rotate(-12deg) brightness(1.02)" },
  siyah_beyaz: { ad: "Siyah beyaz", filtre: "grayscale(1) contrast(1.12)" },
  vinyet:      { ad: "Yalnız vinyet", vinyet: 0.5 },
};

export function vinyetCiz(ctx, guc, en, boy) {
  if (!guc) return;
  const g = ctx.createRadialGradient(en / 2, boy / 2, Math.min(en, boy) * 0.32,
                                     en / 2, boy / 2, Math.max(en, boy) * 0.72);
  g.addColorStop(0, "rgba(0,0,0,0)");
  g.addColorStop(1, `rgba(0,0,0,${guc})`);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, en, boy);
}

export function gecisDurumu(indeks, parca, t, gecis) {
  if (!gecis || gecis.tur === "yok" || !(gecis.sure > 0) || indeks === 0) {
    return { aktif: false, oran: 1 };
  }
  const pencere = Math.min(gecis.sure, Math.max(parca.bit - parca.bas, 0.001));
  if (t >= parca.bas + pencere) return { aktif: false, oran: 1 };
  return { aktif: true, oran: (t - parca.bas) / pencere, tur: gecis.tur };
}

// Yeni sahne tuvale çizilmiş durumdayken çağrılır; üzerine gideni harmanlar.
export function gecisUygula(ctx, anlik, durum, en, boy) {
  const o = Math.min(Math.max(durum.oran, 0), 1);
  if (durum.tur === "karart") {
    // İlk yarı: giden sahne karartılır. İkinci yarı: gelen sahne karanlıktan açılır.
    if (o < 0.5) {
      ctx.drawImage(anlik, 0, 0, en, boy);
      ctx.fillStyle = `rgba(0,0,0,${o * 2})`;
    } else {
      ctx.fillStyle = `rgba(0,0,0,${(1 - o) * 2})`;
    }
    ctx.fillRect(0, 0, en, boy);
  } else {
    ctx.save();
    ctx.globalAlpha = 1 - o;
    ctx.drawImage(anlik, 0, 0, en, boy);
    ctx.restore();
  }
}

export function gorselKareCiz(ctx, bitmap, parca, t, en, boy, hareket) {
  // Siyah zemin boyanmaz: kaplayarak çizim tuvalin tamamını örter.
  const ham = (t - parca.bas) / Math.max(parca.bit - parca.bas, 1e-6);
  const oran = Math.min(Math.max(ham, 0), 1);
  const yon = hareketYonu(hareket, parca.sahneNo);
  const zoom = yon === "yakinlas" ? 1 + ZOOM_MIKTARI * oran
             : yon === "uzaklas"  ? 1 + ZOOM_MIKTARI * (1 - oran)
             : 1;
  kaplayarakCiz(ctx, bitmap, bitmap.width, bitmap.height, en, boy, zoom);
}

// Tek bir kareyi rastgele zamanda çizer (canlı önizleme için).
//
// Render döngüsü video sahnelerini sıralı okur; önizlemede rastgele erişim
// gerektiği için burada arama (seek) kullanılır. Çizim kuralları aynıdır.
async function tekSahneCiz(ctx, parca, kaynakCoz, t, en, boy, hareket, efekt) {
  const tanim = EFEKTLER[efekt] || EFEKTLER.yok;
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, en, boy);
  const kaynak = parca.sahne ? await kaynakCoz(parca.sahne) : null;
  if (tanim.filtre) ctx.filter = tanim.filtre;
  if (kaynak?.tur === "gorsel") {
    gorselKareCiz(ctx, kaynak.bitmap, parca, t, en, boy, hareket);
  } else if (kaynak?.tur === "video") {
    const klipSure = kaynak.sure > 0 ? kaynak.sure : 1;
    await videoKaresineGit(kaynak.el, (t - parca.bas) % klipSure);
    kaplayarakCiz(ctx, kaynak.el, kaynak.el.videoWidth, kaynak.el.videoHeight, en, boy, 1);
  }
  ctx.filter = "none";   // vinyet, geçiş ve altyazı filtreden etkilenmemeli
  vinyetCiz(ctx, tanim.vinyet, en, boy);
}

export async function onizlemeKaresiCiz(ctx, parcalar, kaynakCoz, t, ayar) {
  const { en, boy, hareket, efekt, altyazi, gecis } = ayar;
  const { parca, indeks } = parcaBul(parcalar, t);
  const { metin, oran } = altyaziDurumu(parca, t, altyazi);

  await tekSahneCiz(ctx, parca, kaynakCoz, t, en, boy, hareket, efekt);

  // Ön izleme rastgele erişimlidir; render'daki gibi bir önceki kareyi elde
  // tutamaz, giden sahneyi o an ayrıca çizer.
  const gd = gecisDurumu(indeks, parca, t, gecis);
  if (gd.aktif) {
    const onceki = parcalar[indeks - 1];
    const anlik = new OffscreenCanvas(en, boy);
    const actx = anlik.getContext("2d", { alpha: false });
    await tekSahneCiz(actx, onceki, kaynakCoz, Math.max(onceki.bit - 0.001, onceki.bas), en, boy, hareket, efekt);
    gecisUygula(ctx, anlik, gd, en, boy);
  }

  if (metin) altyaziCiz(ctx, metin, altyazi, en, boy, oran);
  return parca;
}

// --------------------------------------------------------------------- render

// Kodlayıcı kuyruğu boşalana kadar bekler.
//
// setTimeout(0) tarayıcıda en az ~1 ms'e yuvarlanır ve kare başına birkaç kez
// çağrıldığında toplamda kayda değer zaman yer. 'dequeue' olayı varsa kuyruk
// gerçekten boşaldığı anda uyanırız.
function kuyrukBekle(kodlayici, ustSinir, altSinir) {
  if (kodlayici.encodeQueueSize <= ustSinir) return Promise.resolve();
  if (typeof kodlayici.addEventListener !== "function") {
    return new Promise((coz) => {
      const yokla = () => (kodlayici.encodeQueueSize <= altSinir ? coz() : setTimeout(yokla, 0));
      yokla();
    });
  }
  return new Promise((coz) => {
    const kontrol = () => {
      if (kodlayici.encodeQueueSize <= altSinir) {
        kodlayici.removeEventListener("dequeue", kontrol);
        coz();
      }
    };
    kodlayici.addEventListener("dequeue", kontrol);
    kontrol();
  });
}

export async function render(ayar) {
  const { parcalar, sesTamponu, en, boy, fps, hareket, efekt, bitOrani, altyazi, gecis, ilerleme, iptal } = ayar;

  const secim = await kodekSec(en, boy, fps);
  // Ses varsa ana saat odur; yoksa süreyi çizelgenin sonu belirler.
  const toplamSure = sesTamponu
    ? sesTamponu.duration
    : (parcalar.length ? parcalar[parcalar.length - 1].bit : 0);
  const toplamKare = Math.max(1, Math.round(toplamSure * fps));

  const hedef = secim.kap === "mp4" ? new Mp4Hedef() : new WebmHedef();
  const muxer =
    secim.kap === "mp4"
      ? new Mp4Muxer({
          target: hedef,
          video: { codec: "avc", width: en, height: boy },
          // Ses izi yalnızca seslendirme verildiğinde açılır; boş bir iz
          // bazı oynatıcılarda bozuk dosya gibi görünür.
          ...(sesTamponu ? { audio: { codec: "aac", sampleRate: SES_ORNEKLEME, numberOfChannels: SES_KANAL } } : {}),
          fastStart: "in-memory",   // moov başa alınır: dosya web'de anında oynar
        })
      : new WebmMuxer({
          target: hedef,
          video: { codec: secim.video.codec.startsWith("vp09") ? "V_VP9" : "V_VP8", width: en, height: boy, frameRate: fps },
          ...(sesTamponu ? { audio: { codec: "A_OPUS", sampleRate: SES_ORNEKLEME, numberOfChannels: SES_KANAL } } : {}),
        });

  let hataMesaji = null;
  const videoKodlayici = new VideoEncoder({
    output: (parca, meta) => muxer.addVideoChunk(parca, meta),
    error: (e) => (hataMesaji = e.message),
  });
  videoKodlayici.configure({
    codec: secim.video.codec, width: en, height: boy,
    bitrate: bitOrani, framerate: fps, latencyMode: "quality", ...secim.video.ek,
  });

  let sesKodlayici = null;
  if (sesTamponu) {
    if (!secim.ses) {
      throw new Error(`Bu tarayıcı ${secim.kap.toUpperCase()} için ses kodlayıcı sunmuyor; seslendirmesiz deneyin.`);
    }
    sesKodlayici = new AudioEncoder({
      output: (parca, meta) => muxer.addAudioChunk(parca, meta),
      error: (e) => (hataMesaji = e.message),
    });
    sesKodlayici.configure({
      codec: secim.ses.codec, sampleRate: SES_ORNEKLEME, numberOfChannels: SES_KANAL, bitrate: 192000,
    });
  }

  // --- ses ---
  if (sesTamponu) {
  const kanallar = [];
  for (let k = 0; k < SES_KANAL; k++) {
    kanallar.push(sesTamponu.numberOfChannels > k ? sesTamponu.getChannelData(k) : sesTamponu.getChannelData(0));
  }
  const toplamOrnek = sesTamponu.length;
  for (let ofs = 0; ofs < toplamOrnek; ofs += SES_PARCA) {
    const adet = Math.min(SES_PARCA, toplamOrnek - ofs);
    const duz = new Float32Array(adet * SES_KANAL);
    for (let k = 0; k < SES_KANAL; k++) duz.set(kanallar[k].subarray(ofs, ofs + adet), k * adet);
    const ad = new AudioData({
      format: "f32-planar", sampleRate: SES_ORNEKLEME, numberOfFrames: adet,
      numberOfChannels: SES_KANAL, timestamp: Math.round((ofs / SES_ORNEKLEME) * 1e6), data: duz,
    });
    sesKodlayici.encode(ad);
    ad.close();
    await kuyrukBekle(sesKodlayici, 32, 16);
  }
  }
  ilerleme?.({ asama: "ses", oran: 1 });

  // --- görüntü ---
  const kaynaklar = await sahneKaynaklariHazirla(parcalar, en, boy, () =>
    ilerleme?.({ asama: "hazirlik" })
  );

  const tuval = new OffscreenCanvas(en, boy);
  const ctx = tuval.getContext("2d", { alpha: false });
  const kareSure = 1e6 / fps;
  let parcaIdx = 0;

  let aktifAkis = null, aktifSahneNo = null, sonYerel = -1, sonImza = null;
  let kullanilanYol = null;   // "cozucu" | "oynatma" | "arama" — sonuçta bildirilir

  const altyaziAcik = !!altyazi && altyazi.stil && altyazi.stil !== "kapali";
  const altyaziAnimasyonlu = altyaziAcik && ANIMASYONLU.has(altyazi.stil);

  const efektTanimi = EFEKTLER[efekt] || EFEKTLER.yok;
  const hareketsiz = hareketYonu(hareket, 1) === "yok";

  // Geçişte giden sahne olarak kullanılacak anlık görüntü.
  const anlikTuval = new OffscreenCanvas(en, boy);
  const anlikCtx = anlikTuval.getContext("2d", { alpha: false });
  let oncekiIdx = -1;

  try {
    for (let kare = 0; kare < toplamKare; kare++) {
      if (iptal?.()) throw new Error("İşlem kullanıcı tarafından durduruldu.");
      const t = kare / fps;

      const bulunan = parcaBul(parcalar, t);
      parcaIdx = bulunan.indeks;
      const parca = bulunan.parca;
      const kaynak = parca.sahne ? kaynaklar.get(parca.sahne.no) : null;

      // Video sahnesinden çıkıldıysa akışı bırak: oynatma arka planda sürerse
      // boşuna kod çözme yapılır.
      if (aktifAkis && kaynak?.tur !== "video") {
        await aktifAkis.kapat(); aktifAkis = null; aktifSahneNo = null;
      }

      const { metin: altyaziMetni, oran: blokOrani } = altyaziDurumu(parca, t, altyazi);
      const gd = gecisDurumu(parcaIdx, parca, t, gecis);

      // Parça değiştiği anda tuval hâlâ önceki sahnenin son karesini taşır;
      // geçişte kullanılacak anlık görüntü tam burada alınır.
      if (parcaIdx !== oncekiIdx) {
        if (oncekiIdx >= 0) anlikCtx.drawImage(tuval, 0, 0, en, boy);
        oncekiIdx = parcaIdx;
      }

      if (kaynak?.tur === "gorsel") {
        // Ken Burns kapalı ve altyazı durağan ise sahnenin her karesi birebir
        // aynıdır; tuvali yeniden boyamak gereksiz iştir. İmzaya altyazı metni
        // de girer, yoksa metin görünüp kaybolduğunda kare güncellenmezdi.
        const imza = `${parca.sahne.no}|${altyaziMetni}`;
        // Geçiş sırasında her kare farklıdır; hızlı yol devre dışı kalmalı.
        const sabit = hareketsiz && !altyaziAnimasyonlu && !gd.aktif && sonImza === imza;
        if (!sabit) {
          if (efektTanimi.filtre) ctx.filter = efektTanimi.filtre;
          gorselKareCiz(ctx, kaynak.bitmap, parca, t, en, boy, hareket);
          ctx.filter = "none";
          vinyetCiz(ctx, efektTanimi.vinyet, en, boy);
          if (gd.aktif) gecisUygula(ctx, anlikTuval, gd, en, boy);
          if (altyaziMetni) altyaziCiz(ctx, altyaziMetni, altyazi, en, boy, blokOrani);
          sonImza = gd.aktif ? null : imza;
        }
      } else if (kaynak?.tur === "video") {
        // Klip bloktan kısaysa döngüye alınır; uzunsa baştan gerektiği kadarı kullanılır.
        const klipSure = kaynak.sure > 0 ? kaynak.sure : 1;
        const yerel = (t - parca.bas) % klipSure;
        ctx.fillStyle = "#000";
        ctx.fillRect(0, 0, en, boy);
        if (efektTanimi.filtre) ctx.filter = efektTanimi.filtre;

        if (aktifSahneNo !== parca.sahne.no) {
          aktifAkis && (await aktifAkis.kapat());
          const acilan = await akisAc(kaynak);
          aktifAkis = acilan?.akis ?? null;
          kullanilanYol = acilan?.yol ?? "arama";
          aktifSahneNo = parca.sahne.no;
          sonYerel = -1;
        } else if (aktifAkis && yerel + 1e-6 < sonYerel) {
          await aktifAkis.baslat(0);   // klip başa sardı
        }
        sonYerel = yerel;

        if (aktifAkis) {
          const k = await aktifAkis.kareAl(yerel);
          if (k) kaplayarakCiz(ctx, k.resim, k.en, k.boy, en, boy, 1);
        } else {
          await videoKaresineGit(kaynak.el, yerel);
          kaplayarakCiz(ctx, kaynak.el, kaynak.el.videoWidth, kaynak.el.videoHeight, en, boy, 1);
        }
        ctx.filter = "none";
        vinyetCiz(ctx, efektTanimi.vinyet, en, boy);
        if (gd.aktif) gecisUygula(ctx, anlikTuval, gd, en, boy);
        if (altyaziMetni) altyaziCiz(ctx, altyaziMetni, altyazi, en, boy, blokOrani);
        sonImza = null;
      } else {
        ctx.fillStyle = "#000";
        ctx.fillRect(0, 0, en, boy);
        if (gd.aktif) gecisUygula(ctx, anlikTuval, gd, en, boy);
        if (altyaziMetni) altyaziCiz(ctx, altyaziMetni, altyazi, en, boy, blokOrani);
        sonImza = null;
      }

      const vf = new VideoFrame(tuval, { timestamp: Math.round(kare * kareSure), duration: Math.round(kareSure) });
      videoKodlayici.encode(vf, { keyFrame: kare % (fps * 2) === 0 });
      vf.close();

      await kuyrukBekle(videoKodlayici, 8, 4);
      if (kare % 5 === 0 || kare === toplamKare - 1) {
        ilerleme?.({ asama: "goruntu", oran: (kare + 1) / toplamKare, kare: kare + 1, toplamKare });
      }
      if (hataMesaji) throw new Error(hataMesaji);
    }

    await videoKodlayici.flush();
    if (sesKodlayici) await sesKodlayici.flush();
    muxer.finalize();
    if (hataMesaji) throw new Error(hataMesaji);

    return {
      veri: hedef.buffer,
      kap: secim.kap,
      mime: secim.kap === "mp4" ? "video/mp4" : "video/webm",
      kodekAdi: sesTamponu ? `${secim.video.ad} + ${secim.ses.ad}` : `${secim.video.ad} • sessiz`,
      videoYolu: kullanilanYol,
      sure: toplamSure,
      kare: toplamKare,
    };
  } finally {
    if (aktifAkis) { try { await aktifAkis.kapat(); } catch (_) {} }
    for (const k of kaynaklar.values()) { try { k.serbest(); } catch (_) {} }
    try { videoKodlayici.state !== "closed" && videoKodlayici.close(); } catch (_) {}
    try { sesKodlayici && sesKodlayici.state !== "closed" && sesKodlayici.close(); } catch (_) {}
  }
}

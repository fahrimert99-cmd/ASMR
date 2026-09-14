// Zaman çizelgesini gerçek bir video dosyasına dönüştüren render motoru.
//
// Tarayıcı içinde WebCodecs ile kodlama yapılır; kap (container) yazımı
// eklentiye gömülü mp4-muxer / webm-muxer ile olur. Manifest V3 uzaktan kod
// yüklemeyi yasakladığı için bu kütüphaneler vendor/ altında yerel durur.

import { Muxer as Mp4Muxer, ArrayBufferTarget as Mp4Hedef } from "../vendor/mp4-muxer.mjs";
import { Muxer as WebmMuxer, ArrayBufferTarget as WebmHedef } from "../vendor/webm-muxer.mjs";

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
  if (!ses) throw new Error(`${video.kap.toUpperCase()} için ses kodlayıcı bulunamadı.`);

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

// --------------------------------------------------------------- sahne kaynağı

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

export async function sahneKaynaklariHazirla(parcalar, ilerleme) {
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

// --------------------------------------------------------------------- render

export async function render(ayar) {
  const { parcalar, sesTamponu, en, boy, fps, kenBurns, bitOrani, ilerleme, iptal } = ayar;

  const secim = await kodekSec(en, boy, fps);
  const toplamSure = sesTamponu.duration;
  const toplamKare = Math.max(1, Math.round(toplamSure * fps));

  const hedef = secim.kap === "mp4" ? new Mp4Hedef() : new WebmHedef();
  const muxer =
    secim.kap === "mp4"
      ? new Mp4Muxer({
          target: hedef,
          video: { codec: "avc", width: en, height: boy },
          audio: { codec: "aac", sampleRate: SES_ORNEKLEME, numberOfChannels: SES_KANAL },
          fastStart: "in-memory",   // moov başa alınır: dosya web'de anında oynar
        })
      : new WebmMuxer({
          target: hedef,
          video: { codec: secim.video.codec.startsWith("vp09") ? "V_VP9" : "V_VP8", width: en, height: boy, frameRate: fps },
          audio: { codec: "A_OPUS", sampleRate: SES_ORNEKLEME, numberOfChannels: SES_KANAL },
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

  const sesKodlayici = new AudioEncoder({
    output: (parca, meta) => muxer.addAudioChunk(parca, meta),
    error: (e) => (hataMesaji = e.message),
  });
  sesKodlayici.configure({
    codec: secim.ses.codec, sampleRate: SES_ORNEKLEME, numberOfChannels: SES_KANAL, bitrate: 192000,
  });

  // --- ses ---
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
    if (sesKodlayici.encodeQueueSize > 32) await new Promise((r) => setTimeout(r, 0));
  }
  ilerleme?.({ asama: "ses", oran: 1 });

  // --- görüntü ---
  const kaynaklar = await sahneKaynaklariHazirla(parcalar, () =>
    ilerleme?.({ asama: "hazirlik" })
  );

  const tuval = new OffscreenCanvas(en, boy);
  const ctx = tuval.getContext("2d", { alpha: false });
  const kareSure = 1e6 / fps;
  let parcaIdx = 0;

  try {
    for (let kare = 0; kare < toplamKare; kare++) {
      if (iptal?.()) throw new Error("İşlem kullanıcı tarafından durduruldu.");
      const t = kare / fps;

      while (parcaIdx < parcalar.length - 1 && t >= parcalar[parcaIdx].bit) parcaIdx++;
      const parca = parcalar[parcaIdx];
      const kaynak = parca.sahne ? kaynaklar.get(parca.sahne.no) : null;

      ctx.fillStyle = "#000";
      ctx.fillRect(0, 0, en, boy);

      if (kaynak?.tur === "gorsel") {
        // Ken Burns: sahne boyunca %0 → %6 arası yavaş yakınlaşma.
        const oran = (t - parca.bas) / Math.max(parca.bit - parca.bas, 1e-6);
        const zoom = kenBurns ? 1 + 0.06 * Math.min(Math.max(oran, 0), 1) : 1;
        kaplayarakCiz(ctx, kaynak.bitmap, kaynak.bitmap.width, kaynak.bitmap.height, en, boy, zoom);
      } else if (kaynak?.tur === "video") {
        // Klip bloktan kısaysa döngüye alınır; uzunsa baştan gerektiği kadarı kullanılır.
        const yerel = kaynak.sure > 0 ? (t - parca.bas) % kaynak.sure : 0;
        await videoKaresineGit(kaynak.el, yerel);
        kaplayarakCiz(ctx, kaynak.el, kaynak.el.videoWidth, kaynak.el.videoHeight, en, boy, 1);
      }

      const vf = new VideoFrame(tuval, { timestamp: Math.round(kare * kareSure), duration: Math.round(kareSure) });
      videoKodlayici.encode(vf, { keyFrame: kare % (fps * 2) === 0 });
      vf.close();

      if (videoKodlayici.encodeQueueSize > 8) {
        while (videoKodlayici.encodeQueueSize > 4) await new Promise((r) => setTimeout(r, 0));
      }
      if (kare % 5 === 0 || kare === toplamKare - 1) {
        ilerleme?.({ asama: "goruntu", oran: (kare + 1) / toplamKare, kare: kare + 1, toplamKare });
      }
      if (hataMesaji) throw new Error(hataMesaji);
    }

    await videoKodlayici.flush();
    await sesKodlayici.flush();
    muxer.finalize();
    if (hataMesaji) throw new Error(hataMesaji);

    return {
      veri: hedef.buffer,
      kap: secim.kap,
      mime: secim.kap === "mp4" ? "video/mp4" : "video/webm",
      kodekAdi: `${secim.video.ad} + ${secim.ses.ad}`,
      sure: toplamSure,
      kare: toplamKare,
    };
  } finally {
    for (const k of kaynaklar.values()) { try { k.serbest(); } catch (_) {} }
    try { videoKodlayici.state !== "closed" && videoKodlayici.close(); } catch (_) {}
    try { sesKodlayici.state !== "closed" && sesKodlayici.close(); } catch (_) {}
  }
}

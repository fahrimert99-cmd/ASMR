// SRT ayrıştırıcı.
//
// Kurgu Canavarı'nda SRT yalnızca altyazı değil, zaman çizelgesinin ta kendisidir:
// n numaralı blok, n numaralı sahne dosyasının ekranda kalacağı aralığı tanımlar.
// Bu yüzden ayrıştırma hataya toleranslı ama sessizce yanlış sonuç üretmeyen
// bir biçimde yapılır; kusurlar 'uyarilar' içinde geri döner.

const ZAMAN = /(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})/;

function saniyeye(sa, dk, sn, ms) {
  return (+sa) * 3600 + (+dk) * 60 + (+sn) + (+ms.padEnd(3, "0")) / 1000;
}

export function srtAyristir(metin) {
  const uyarilar = [];
  // BOM ve satır sonu normalizasyonu: Windows'ta üretilen SRT'ler CRLF gelir.
  const temiz = metin.replace(/^﻿/, "").replace(/\r\n?/g, "\n");

  const bloklar = [];
  // Bloklar boş satırla ayrılır; ancak bazı araçlar fazladan boş satır bırakır.
  for (const ham of temiz.split(/\n{2,}/)) {
    const satirlar = ham.split("\n").filter((s) => s.trim() !== "");
    if (!satirlar.length) continue;

    const zamanSatiri = satirlar.findIndex((s) => ZAMAN.test(s));
    if (zamanSatiri === -1) {
      uyarilar.push(`Zaman kodu olmayan blok atlandı: "${satirlar[0].slice(0, 40)}"`);
      continue;
    }

    const m = satirlar[zamanSatiri].match(ZAMAN);
    const bas = saniyeye(m[1], m[2], m[3], m[4]);
    const bit = saniyeye(m[5], m[6], m[7], m[8]);
    const metinSatirlari = satirlar.slice(zamanSatiri + 1).join(" ").trim();

    if (bit <= bas) {
      uyarilar.push(`Bitişi başlangıcından küçük/eşit blok atlandı (${m[0]}).`);
      continue;
    }
    bloklar.push({ sira: bloklar.length + 1, bas, bit, metin: metinSatirlari });
  }

  if (!bloklar.length) return { bloklar, uyarilar, sure: 0 };

  // Zaman sırasına göre diz: elle düzenlenmiş SRT'lerde sıra bozulabilir ve
  // bozuk sıra, sahnelerin yanlış dosyalara bağlanması demektir.
  const sirasiz = bloklar.some((b, i) => i > 0 && b.bas < bloklar[i - 1].bas);
  if (sirasiz) {
    uyarilar.push("Bloklar zaman sırasında değildi; başlangıç zamanına göre yeniden sıralandı.");
    bloklar.sort((a, b) => a.bas - b.bas);
    bloklar.forEach((b, i) => (b.sira = i + 1));
  }

  // Çakışma: iki blok üst üste binerse hangi sahnenin görüneceği belirsizleşir.
  for (let i = 1; i < bloklar.length; i++) {
    if (bloklar[i].bas < bloklar[i - 1].bit - 1e-6) {
      uyarilar.push(
        `${i} ve ${i + 1}. bloklar çakışıyor; ${i + 1}. blok ${bloklar[i - 1].bit.toFixed(3)} sn'ye kaydırıldı.`
      );
      bloklar[i].bas = bloklar[i - 1].bit;
      if (bloklar[i].bit <= bloklar[i].bas) bloklar[i].bit = bloklar[i].bas + 0.04;
    }
  }

  return { bloklar, uyarilar, sure: bloklar[bloklar.length - 1].bit };
}

export function zamanBicimle(sn) {
  if (!isFinite(sn)) return "--:--";
  const d = Math.floor(sn / 60);
  const s = sn - d * 60;
  return `${String(d).padStart(2, "0")}:${s.toFixed(2).padStart(5, "0")}`;
}

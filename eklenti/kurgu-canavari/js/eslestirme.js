// Dosya ↔ SRT bloğu eşleştirmesi ve zaman çizelgesinin kurulması.

const GORSEL_UZANTI = ["png", "jpg", "jpeg", "webp", "gif", "bmp", "avif"];
const VIDEO_UZANTI = ["mp4", "webm", "mov", "m4v", "mkv"];

function uzanti(ad) {
  const n = ad.lastIndexOf(".");
  return n === -1 ? "" : ad.slice(n + 1).toLowerCase();
}

export function dosyaTuru(dosya) {
  const u = uzanti(dosya.name);
  if (GORSEL_UZANTI.includes(u)) return "gorsel";
  if (VIDEO_UZANTI.includes(u)) return "video";
  if (dosya.type.startsWith("image/")) return "gorsel";
  if (dosya.type.startsWith("video/")) return "video";
  return null;
}

// Dosya adındaki sahne numarası.
//
// Kullanılan düzen "Video 01.mp4", "Görsel 02.png", "01.png" biçiminde olduğu
// için adın İLK rakam öbeği alınır. Son öbek alınsaydı "Video 01 1080p.mp4"
// gibi bir adda çözünürlük sahne numarası sanılırdı.
export function sahneNumarasi(ad) {
  const govde = ad.replace(/\.[^.]+$/, "");
  const m = govde.match(/\d+/);
  return m ? parseInt(m[0], 10) : null;
}

export function dosyalariEslestir(dosyalar, blokSayisi) {
  const sahneler = new Map();
  const sorunlar = [];
  const cakisan = new Map();

  for (const dosya of dosyalar) {
    const tur = dosyaTuru(dosya);
    if (!tur) {
      sorunlar.push({ tur: "hata", mesaj: `"${dosya.name}" desteklenmeyen bir dosya türü; atlandı.` });
      continue;
    }
    const no = sahneNumarasi(dosya.name);
    if (no === null) {
      sorunlar.push({ tur: "hata", mesaj: `"${dosya.name}" adında sahne numarası yok; atlandı.` });
      continue;
    }
    if (sahneler.has(no)) {
      cakisan.set(no, [...(cakisan.get(no) || [sahneler.get(no).dosya.name]), dosya.name]);
      continue;
    }
    sahneler.set(no, { no, dosya, tur });
  }

  for (const [no, adlar] of cakisan) {
    sorunlar.push({
      tur: "hata",
      mesaj: `${no} numarası birden fazla dosyada: ${adlar.join(", ")}. İlki kullanıldı.`,
    });
  }

  // Eksik numaralar: 1..blokSayisi aralığında karşılığı olmayan bloklar.
  const eksik = [];
  for (let i = 1; i <= blokSayisi; i++) if (!sahneler.has(i)) eksik.push(i);
  if (eksik.length) {
    sorunlar.push({
      tur: "hata",
      mesaj: `Şu bloklara karşılık gelen dosya yok: ${eksik.join(", ")}.`,
    });
  }

  // Fazla dosyalar: SRT'de karşılığı olmayan sahneler sessizce yok sayılırsa
  // kullanıcı eksik render'ı fark etmez; bu yüzden açıkça uyarılır.
  const fazla = [...sahneler.keys()].filter((n) => n > blokSayisi || n < 1).sort((a, b) => a - b);
  if (fazla.length) {
    sorunlar.push({
      tur: "uyari",
      mesaj: `SRT'de ${blokSayisi} blok var; şu numaralar kullanılmayacak: ${fazla.join(", ")}.`,
    });
  }

  return { sahneler, sorunlar, eksik };
}

// Zaman çizelgesi.
//
// Ses ana saattir: toplam süre sesin süresidir. SRT blokları arasındaki
// boşluklarda (konuşmanın durduğu anlarda) ekran karartılmaz, bir önceki sahne
// tutulur; karartmak belgesel akışında göz kırpması gibi görünürdü.
export function zamanCizelgesiKur(bloklar, sahneler, sesSuresi) {
  const parcalar = [];
  if (!bloklar.length) return parcalar;

  for (let i = 0; i < bloklar.length; i++) {
    const blok = bloklar[i];
    const sonraki = bloklar[i + 1];
    const bas = i === 0 ? 0 : blok.bas;              // ilk blok öncesi de 1. sahne
    const bit = sonraki ? sonraki.bas : Math.max(blok.bit, sesSuresi); // boşlukları doldur
    parcalar.push({
      sahneNo: blok.sira,
      bas,
      bit: Math.max(bit, bas + 1 / 1000),
      blokBas: blok.bas,
      blokBit: blok.bit,
      metin: blok.metin,
      sahne: sahneler.get(blok.sira) || null,
    });
  }
  // Ses son bloktan kısaysa çizelgeyi sesin bittiği yerde kes.
  const son = parcalar[parcalar.length - 1];
  if (sesSuresi > 0 && son.bit > sesSuresi) son.bit = Math.max(son.bas + 0.001, sesSuresi);
  return parcalar;
}

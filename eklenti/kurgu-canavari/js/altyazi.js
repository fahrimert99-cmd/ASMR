// SRT metnini sahnenin üzerine işleyen altyazı motoru.
//
// Altyazı yalnızca bloğun KENDİ zaman aralığında görünür. Bloklar arası
// boşluklarda sahne tutulur ama metin görünmez; aksi halde konuşma bittikten
// sonra da yazı ekranda asılı kalırdı.

export const KONUMLAR = { alt: "Alt", orta: "Orta", ust: "Üst" };
export const BOYUTLAR = { kucuk: 0.040, orta: 0.050, buyuk: 0.062 };

// Zamanla değişen stiller: bunlarda her kare farklıdır, sabit kare hızlı yolu
// devre dışı kalmalıdır.
export const ANIMASYONLU = new Set(["karaoke", "typewriter"]);

export const STILLER = {
  kapali:     { ad: "Kapalı" },
  klasik:     { ad: "Klasik beyaz" },
  koyu_kutu:  { ad: "Koyu kutu" },
  sari:       { ad: "Sarı vurgulu" },
  neon_mor:   { ad: "Neon mor" },
  sinema:     { ad: "Sinema" },
  minimal:    { ad: "Minimal" },
  karaoke:    { ad: "Karaoke" },
  typewriter: { ad: "Typewriter" },
  lower_third:{ ad: "Lower Third" },
};

function yaziTipi(px, kalin = true) {
  return `${kalin ? "700 " : "400 "}${Math.round(px)}px "Segoe UI", system-ui, -apple-system, sans-serif`;
}

// Metni verilen genişliğe sığacak satırlara böler.
function satirlaraBol(ctx, metin, enSinir) {
  const kelimeler = metin.split(/\s+/).filter(Boolean);
  const satirlar = [];
  let satir = "";
  for (const k of kelimeler) {
    const deneme = satir ? satir + " " + k : k;
    if (ctx.measureText(deneme).width <= enSinir || !satir) satir = deneme;
    else { satirlar.push(satir); satir = k; }
  }
  if (satir) satirlar.push(satir);
  return satirlar;
}

function yuvarlakKutu(ctx, x, y, g, yuk, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + g, y, x + g, y + yuk, r);
  ctx.arcTo(x + g, y + yuk, x, y + yuk, r);
  ctx.arcTo(x, y + yuk, x, y, r);
  ctx.arcTo(x, y, x + g, y, r);
  ctx.closePath();
  ctx.fill();
}

// Satırların yerleşeceği başlangıç y'si.
function baslangicY(konum, boy, satirSayisi, satirYuk, kenar) {
  const toplam = satirSayisi * satirYuk;
  if (konum === "ust") return kenar;
  if (konum === "orta") return (boy - toplam) / 2;
  return boy - kenar - toplam;    // alt
}

/**
 * Altyazıyı tuvale çizer.
 * @param oran Blok içindeki ilerleme (0..1) — karaoke ve typewriter için.
 */
export function altyaziCiz(ctx, metin, ayar, en, boy, oran = 1) {
  const stil = ayar.stil || "kapali";
  if (stil === "kapali" || !metin) return;

  // puntoOran: küçük önizleme tuvallerinde yazıyı okunur kılmak için kullanılır.
  // Videoda verilmez; oradaki punto her zaman kare yüksekliğine oranlıdır.
  const punto = boy * (ayar.puntoOran ?? BOYUTLAR[ayar.boyut] ?? BOYUTLAR.orta);
  const kenar = boy * 0.065;
  const enSinir = en * 0.86;
  const satirYuk = punto * 1.32;

  ctx.save();
  ctx.textBaseline = "top";
  ctx.textAlign = stil === "lower_third" ? "left" : "center";
  ctx.font = yaziTipi(punto, stil !== "minimal");

  // Typewriter: metin karakter karakter açılır.
  let gorunen = metin;
  if (stil === "typewriter") {
    const n = Math.max(1, Math.ceil(metin.length * Math.min(Math.max(oran, 0), 1)));
    gorunen = metin.slice(0, n);
  }

  const satirlar = satirlaraBol(ctx, gorunen, enSinir);
  const y0 = baslangicY(ayar.konum || "alt", boy, satirlar.length, satirYuk, kenar);
  const merkez = en / 2;

  satirlar.forEach((satir, i) => {
    const y = y0 + i * satirYuk;
    const g = ctx.measureText(satir).width;

    switch (stil) {
      case "klasik": {
        ctx.lineWidth = Math.max(2, punto * 0.16);
        ctx.strokeStyle = "rgba(0,0,0,0.85)";
        ctx.lineJoin = "round";
        ctx.strokeText(satir, merkez, y);
        ctx.fillStyle = "#ffffff";
        ctx.fillText(satir, merkez, y);
        break;
      }
      case "koyu_kutu": {
        const pad = punto * 0.34;
        ctx.fillStyle = "rgba(0,0,0,0.72)";
        yuvarlakKutu(ctx, merkez - g / 2 - pad, y - pad * 0.55, g + pad * 2, satirYuk, punto * 0.18);
        ctx.fillStyle = "#ffffff";
        ctx.fillText(satir, merkez, y);
        break;
      }
      case "sari": {
        const pad = punto * 0.36;
        ctx.fillStyle = "#facc15";
        yuvarlakKutu(ctx, merkez - g / 2 - pad, y - pad * 0.55, g + pad * 2, satirYuk, punto * 0.22);
        ctx.fillStyle = "#1a1505";
        ctx.fillText(satir, merkez, y);
        break;
      }
      case "neon_mor": {
        const pad = punto * 0.36;
        ctx.fillStyle = "rgba(30,10,60,0.70)";
        yuvarlakKutu(ctx, merkez - g / 2 - pad, y - pad * 0.55, g + pad * 2, satirYuk, punto * 0.5);
        ctx.shadowColor = "#c084fc";
        ctx.shadowBlur = punto * 0.55;
        ctx.fillStyle = "#e9d5ff";
        ctx.fillText(satir, merkez, y);
        ctx.fillText(satir, merkez, y);   // parlamayı güçlendirir
        ctx.shadowBlur = 0;
        break;
      }
      case "sinema": {
        ctx.shadowColor = "rgba(0,0,0,0.9)";
        ctx.shadowBlur = punto * 0.35;
        ctx.shadowOffsetY = punto * 0.06;
        ctx.fillStyle = "#f5f0e6";
        ctx.fillText(satir, merkez, y);
        ctx.shadowBlur = 0;
        ctx.shadowOffsetY = 0;
        break;
      }
      case "minimal": {
        ctx.fillStyle = "rgba(255,255,255,0.94)";
        ctx.fillText(satir, merkez, y);
        break;
      }
      case "typewriter": {
        ctx.lineWidth = Math.max(2, punto * 0.14);
        ctx.strokeStyle = "rgba(0,0,0,0.8)";
        ctx.lineJoin = "round";
        ctx.strokeText(satir, merkez, y);
        ctx.fillStyle = "#d1fae5";
        ctx.fillText(satir, merkez, y);
        // imleç yalnızca son satırda ve metin bitmemişken
        if (i === satirlar.length - 1 && gorunen.length < metin.length) {
          ctx.fillStyle = "#d1fae5";
          ctx.fillRect(merkez + g / 2 + punto * 0.1, y, punto * 0.09, punto);
        }
        break;
      }
      case "lower_third": {
        const x = en * 0.07;
        const pad = punto * 0.34;
        ctx.fillStyle = "rgba(8,14,28,0.78)";
        yuvarlakKutu(ctx, x - pad, y - pad * 0.55, g + pad * 2, satirYuk, punto * 0.12);
        ctx.fillStyle = "#38bdf8";
        ctx.fillRect(x - pad, y - pad * 0.55, punto * 0.11, satirYuk);
        ctx.fillStyle = "#ffffff";
        ctx.fillText(satir, x + punto * 0.16, y);
        break;
      }
      case "karaoke": {
        // SRT kelime zamanı taşımaz; ilerleme bloğa eşit bölünerek yaklaşılır.
        const tumKelimeler = metin.split(/\s+/).filter(Boolean);
        const acik = Math.floor(tumKelimeler.length * Math.min(Math.max(oran, 0), 1));
        let sayac = 0;
        for (let j = 0; j < i; j++) sayac += satirlaraBol(ctx, gorunen, enSinir)[j].split(/\s+/).length;

        const kelimeler = satir.split(/\s+/);
        const bosluk = ctx.measureText(" ").width;
        let x = merkez - g / 2;
        ctx.lineWidth = Math.max(2, punto * 0.15);
        ctx.strokeStyle = "rgba(0,0,0,0.85)";
        ctx.lineJoin = "round";
        ctx.textAlign = "left";
        for (const kelime of kelimeler) {
          const kg = ctx.measureText(kelime).width;
          ctx.strokeText(kelime, x, y);
          ctx.fillStyle = sayac < acik ? "#facc15" : "#ffffff";
          ctx.fillText(kelime, x, y);
          x += kg + bosluk;
          sayac++;
        }
        ctx.textAlign = "center";
        break;
      }
      default: {
        ctx.fillStyle = "#ffffff";
        ctx.fillText(satir, merkez, y);
      }
    }
  });

  ctx.restore();
}

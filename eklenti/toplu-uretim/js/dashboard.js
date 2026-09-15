// Toplu Üretim panosu — kuyruğu burada döndürür.
//
// Kuyruk neden panoda: MV3 servis çalışanı boşta kalınca sonlandırılır; saatler
// sürebilen bir üretim kuyruğu orada yaşayamaz. Ayrıca indirme için gereken
// URL.createObjectURL servis çalışanında yoktur, eklenti sayfasında vardır.

const $ = (id) => document.getElementById(id);
const el = {
  site: $("site"), izinVer: $("izin-ver"), baglantiDurum: $("baglanti-durum"),
  promptlar: $("promptlar"), promptDosya: $("prompt-dosya"), gorseller: $("gorseller"),
  eslesme: $("eslesme"), gecikmeAlt: $("gecikme-alt"), gecikmeUst: $("gecikme-ust"),
  zamanAsimi: $("zaman-asimi"), klasor: $("klasor"), baslangicNo: $("baslangic-no"),
  basla: $("basla"), durdur: $("durdur"), durum: $("durum"),
  panelKuyruk: $("panel-kuyruk"), kuyruk: $("kuyruk"), gunluk: $("gunluk"),
};

const ALANLAR = ["prompt", "gorsel", "uret", "sonuc"];
let secici = { prompt: "", gorsel: "", uret: "", sonuc: "" };
let hedefSekmeId = null;
let hedefCerceveId = 0;   // seçicinin öğrenildiği çerçeve; işler oraya gönderilir
let calisiyor = false;
let durdurIstendi = false;

// ------------------------------------------------------------------- yardımcı

const bekle = (ms) => new Promise((r) => setTimeout(r, ms));
const durumYaz = (m) => (el.durum.textContent = m);

function gunlukYaz(metin, sinif = "") {
  const t = new Date().toLocaleTimeString("tr-TR");
  const satir = document.createElement("span");
  satir.className = sinif;
  satir.textContent = `[${t}] ${metin}\n`;
  el.gunluk.appendChild(satir);
  el.gunluk.scrollTop = el.gunluk.scrollHeight;
}

async function ayarlariYukle() {
  const d = await chrome.storage.local.get(["secici", "site", "klasor", "gecikme"]);
  if (d.secici) secici = { ...secici, ...d.secici };
  if (d.site) el.site.value = d.site;
  if (d.klasor) el.klasor.value = d.klasor;
  if (d.gecikme) { el.gecikmeAlt.value = d.gecikme[0]; el.gecikmeUst.value = d.gecikme[1]; }
  seciciyiGoster();
}
const ayarlariKaydet = () => chrome.storage.local.set({
  secici, site: el.site.value, klasor: el.klasor.value,
  gecikme: [Number(el.gecikmeAlt.value), Number(el.gecikmeUst.value)],
});

function seciciyiGoster() {
  for (const a of ALANLAR) $("s-" + a).textContent = secici[a] || "—";
  hazirMi();
}

function hazirMi() {
  const tamam = hedefSekmeId && secici.prompt && secici.uret && secici.sonuc && islerVar();
  el.basla.disabled = !tamam || calisiyor;
  return tamam;
}

// -------------------------------------------------------------- siteye bağlan

el.izinVer.addEventListener("click", async () => {
  let adres;
  try { adres = new URL(el.site.value); } catch { return durumYaz("Adres geçersiz."); }
  const kaynak = `${adres.protocol}//${adres.hostname}/*`;

  const verildi = await chrome.permissions.request({ origins: [kaynak] });
  if (!verildi) { el.baglantiDurum.textContent = "İzin verilmedi."; return; }

  const sekme = await chrome.tabs.create({ url: el.site.value, active: true });
  hedefSekmeId = sekme.id;
  gunlukYaz(`Sekme açıldı: ${el.site.value}`);

  // Sayfanın yüklenmesini bekle, sonra betiği enjekte et.
  for (let i = 0; i < 30; i++) {
    await bekle(1000);
    try {
      const s = await chrome.tabs.get(hedefSekmeId);
      if (s.status === "complete") break;
    } catch { hedefSekmeId = null; return el.baglantiDurum.textContent = "Sekme kapandı."; }
  }
  await betigiEnjekteEt();
  await ayarlariKaydet();
});

async function betigiEnjekteEt() {
  try {
    // allFrames: sitenin editörü bir iframe içinde olabilir; yalnızca üst
    // çerçeveye enjekte etmek o durumda hiçbir şey yakalamaz.
    const enjekte = await chrome.scripting.executeScript({
      target: { tabId: hedefSekmeId, allFrames: true }, files: ["js/icerik.js"],
    });
    gunlukYaz(`İçerik betiği ${enjekte.length} çerçeveye yerleşti.`);
    const c = await chrome.tabs.sendMessage(hedefSekmeId, { tur: "canli" });
    el.baglantiDurum.textContent = `Bağlandı: ${c.baslik || c.adres}`;
    gunlukYaz("İçerik betiği çalışıyor.", "iyi");
  } catch (e) {
    el.baglantiDurum.textContent = "Bağlanamadı: " + e.message;
    gunlukYaz("Bağlantı hatası: " + e.message, "hata");
    hedefSekmeId = null;
  }
  hazirMi();
}

// ------------------------------------------------------------------- öğrenme

document.querySelectorAll("[data-alan]").forEach((d) => {
  d.addEventListener("click", async () => {
    if (!hedefSekmeId) return durumYaz("Önce siteye bağlanın.");
    const alan = d.dataset.alan;
    try {
      await chrome.tabs.update(hedefSekmeId, { active: true });
      await chrome.tabs.sendMessage(hedefSekmeId, { tur: "ogren" });
      durumYaz(`↗ PİKA SEKMESİNE GEÇİN ve "${alan}" öğesine tıklayın. (ESC ile vazgeçin)`);
      gunlukYaz(`Öğrenme kipi: ${alan} — şimdi sitedeki öğeye tıklamanız bekleniyor`);
      beklenenAlan = alan;
      bekleyisiGoster(alan);
    } catch (e) {
      gunlukYaz("Öğrenme başlatılamadı: " + e.message, "hata");
    }
  });
});

let beklenenAlan = null;
let bekleyisZamanlayici = null;

// Öğrenme, kullanıcı SİTEDE bir öğeye tıklayana kadar tamamlanmaz. Bu adım
// atlanınca günlükte yalnızca "Öğrenme kipi" satırı kalıyor ve neyin eksik
// olduğu anlaşılmıyordu; bekleyiş artık panoda açıkça görünür.
function bekleyisiGoster(alan) {
  clearTimeout(bekleyisZamanlayici);
  document.body.classList.add("ogrenme-bekliyor");
  const k = document.getElementById("ogrenme-uyari");
  k.hidden = false;
  k.textContent = `Bekleniyor: Pika sekmesine geçip "${alan}" öğesine tıklayın. Sayfanın üstünde mavi şerit görünmüyorsa betik o çerçevede çalışmıyordur — bunu bana bildirin.`;
  bekleyisZamanlayici = setTimeout(() => {
    if (beklenenAlan === alan) {
      gunlukYaz(`"${alan}" için 45 sn'dir tıklama gelmedi. Sitede mavi şerit göründü mü?`, "hata");
    }
  }, 45000);
}
function bekleyisiKapat() {
  clearTimeout(bekleyisZamanlayici);
  document.body.classList.remove("ogrenme-bekliyor");
  document.getElementById("ogrenme-uyari").hidden = true;
}
chrome.runtime.onMessage.addListener((m, gonderen) => {
  if (m.tur === "ogrenildi" && beklenenAlan) {
    secici[beklenenAlan] = m.secici;
    if (typeof gonderen?.frameId === "number") hedefCerceveId = gonderen.frameId;
    gunlukYaz(`${beklenenAlan} ← ${m.secici}  (<${m.etiket}>)`, "iyi");
    if (m.yukariCikildi) {
      gunlukYaz(`(<${m.yukariCikildi}> simgesine tıkladınız; kaydedilen öğe onu içeren <${m.etiket}>)`, "");
    }
    if (beklenenAlan === "prompt" && !m.metinAlani) {
      gunlukYaz("Not: tıkladığınız öğe yazı kutusu değil. Üretimde yakınındaki " +
        "gerçek yazı alanı aranacak; olmazsa doğrudan metnin yazıldığı kutuya tıklayın.", "");
    }
    if (beklenenAlan === "sonuc" && ["a", "video", "img", "button"].includes(m.etiket)) {
      gunlukYaz(`Dikkat: sonuç seçicisi bir <${m.etiket}> — tek bir öğe seçilmiş olabilir. ` +
        "Videoların BELİRDİĞİ kutuyu seçmek daha güvenilirdir.", "hata");
    }
    if (beklenenAlan === "gorsel" && !m.dosyaGirdisi) {
      gunlukYaz("Not: tıkladığınız öğe dosya girdisi değil. Üretim sırasında " +
        "yakınındaki gizli input[type=file] aranacak; çalışmazsa farklı bir öğe deneyin.", "");
    }
    beklenenAlan = null;
    bekleyisiKapat();
    seciciyiGoster();
    ayarlariKaydet();
    durumYaz("Seçici kaydedildi.");
  } else if (m.tur === "ogrenme-iptal") {
    beklenenAlan = null;
    bekleyisiKapat();
    durumYaz("Öğrenme iptal edildi.");
  }
});

// ---------------------------------------------------------------- girdi/kuyruk

function promptlariAyikla() {
  return el.promptlar.value.split(/\n\s*\n/).map((s) => s.trim()).filter(Boolean);
}
const gorselleriAl = () => [...(el.gorseller.files || [])]
  .sort((a, b) => a.name.localeCompare(b.name, "tr", { numeric: true }));

const islerVar = () => promptlariAyikla().length > 0;

function eslesmeyiGoster() {
  const p = promptlariAyikla(), g = gorselleriAl();
  if (!p.length) { el.eslesme.textContent = ""; el.panelKuyruk.hidden = true; return hazirMi(); }
  el.eslesme.textContent = g.length
    ? `${p.length} prompt, ${g.length} görsel` + (g.length !== p.length ? " — sayılar eşit değil, eşleşenler işlenir." : " — birebir eşleşiyor.")
    : `${p.length} prompt, görsel yok (metinden üretim).`;
  kuyrugaCiz();
  hazirMi();
}

function kuyrugaCiz() {
  const p = promptlariAyikla(), g = gorselleriAl();
  const adet = g.length ? Math.min(p.length, g.length) : p.length;
  el.kuyruk.innerHTML = "";
  for (let i = 0; i < adet; i++) {
    const tr = document.createElement("tr");
    tr.id = "is-" + i;
    const h = (m, s) => { const td = document.createElement("td"); td.textContent = m; if (s) td.className = s; return td; };
    tr.append(h(String(i + 1), "mono"), h(g[i]?.name || "—"),
              h(p[i].length > 70 ? p[i].slice(0, 70) + "…" : p[i]), h("bekliyor"), h("—"));
    el.kuyruk.appendChild(tr);
  }
  el.panelKuyruk.hidden = adet === 0;
}

el.promptlar.addEventListener("input", eslesmeyiGoster);
el.gorseller.addEventListener("change", eslesmeyiGoster);
el.promptDosya.addEventListener("change", async () => {
  const d = el.promptDosya.files[0];
  if (!d) return;
  el.promptlar.value = await d.text();
  eslesmeyiGoster();
  gunlukYaz(`Prompt dosyası okundu: ${d.name}`);
});

const satirDurum = (i, metin, sinif) => {
  const tr = $("is-" + i);
  if (!tr) return;
  tr.className = sinif || "";
  tr.children[3].textContent = metin;
};
const satirSonuc = (i, metin) => { const tr = $("is-" + i); if (tr) tr.children[4].textContent = metin; };

// ------------------------------------------------------------------- üretim

const dosyaOku = (dosya) => new Promise((coz, red) => {
  const o = new FileReader();
  o.onload = () => coz(String(o.result).split(",")[1]);
  o.onerror = () => red(new Error("görsel okunamadı"));
  o.readAsDataURL(dosya);
});

el.durdur.addEventListener("click", () => {
  durdurIstendi = true;
  el.durdur.disabled = true;
  durumYaz("Bu iş bitince duracak…");
});

el.basla.addEventListener("click", async () => {
  if (!hazirMi()) return;
  const promptlar = promptlariAyikla();
  const gorseller = gorselleriAl();
  const adet = gorseller.length ? Math.min(promptlar.length, gorseller.length) : promptlar.length;
  const altGecikme = Math.max(0, Number(el.gecikmeAlt.value));
  const ustGecikme = Math.max(altGecikme, Number(el.gecikmeUst.value));
  const zamanAsimi = Number(el.zamanAsimi.value) * 1000;
  const klasor = (el.klasor.value || "toplu-uretim").replace(/[^\w\-./]/g, "");
  let no = Math.max(1, Number(el.baslangicNo.value));

  calisiyor = true; durdurIstendi = false;
  el.basla.disabled = true; el.durdur.hidden = false; el.durdur.disabled = false;
  gunlukYaz(`Üretim başlıyor: ${adet} iş.`, "iyi");

  let basarili = 0, hatali = 0;
  for (let i = 0; i < adet; i++) {
    if (durdurIstendi) { gunlukYaz("Kullanıcı durdurdu."); break; }
    satirDurum(i, "çalışıyor…", "calisiyor");
    durumYaz(`${i + 1}/${adet} işleniyor…`);

    try {
      const is = { secici, prompt: promptlar[i], zamanAsimi };
      if (gorseller[i] && secici.gorsel) {
        is.gorsel = { ad: gorseller[i].name, veri: await dosyaOku(gorseller[i]) };
      }
      const cevap = await chrome.tabs.sendMessage(hedefSekmeId, { tur: "is", is }, { frameId: hedefCerceveId });
      if (!cevap?.ok) throw new Error(cevap?.hata || "yanıt yok");

      const adresler = cevap.sonuc.adresler;
      gunlukYaz(`${i + 1}. iş: ${adresler.length} sonuç bulundu.`);
      for (const adres of adresler) {
        const okuma = await chrome.tabs.sendMessage(hedefSekmeId, { tur: "oku", adres }, { frameId: hedefCerceveId });
        if (!okuma?.ok) throw new Error(okuma?.hata || "sonuç okunamadı");
        const bayt = Uint8Array.from(atob(okuma.dosya.veri), (c) => c.charCodeAt(0));
        const uzanti = okuma.dosya.tur.includes("webm") ? "webm" : "mp4";
        const ad = `${klasor}/${String(no).padStart(2, "0")}.${uzanti}`;
        const url = URL.createObjectURL(new Blob([bayt], { type: okuma.dosya.tur }));
        await chrome.downloads.download({ url, filename: ad, conflictAction: "uniquify" });
        setTimeout(() => URL.revokeObjectURL(url), 60000);
        satirSonuc(i, ad);
        gunlukYaz(`indirildi: ${ad} (${(okuma.dosya.boyut / 1048576).toFixed(1)} MB)`, "iyi");
        no++;
      }
      satirDurum(i, "tamam", "tamam");
      basarili++;
    } catch (e) {
      satirDurum(i, "hata", "hatali");
      satirSonuc(i, e.message);
      gunlukYaz(`${i + 1}. iş başarısız: ${e.message}`, "hata");
      hatali++;
    }

    if (i < adet - 1 && !durdurIstendi) {
      const s = altGecikme + Math.random() * (ustGecikme - altGecikme);
      gunlukYaz(`${s.toFixed(1)} sn bekleniyor…`);
      await bekle(s * 1000);
    }
  }

  calisiyor = false;
  el.durdur.hidden = true;
  durumYaz(`Bitti — ${basarili} başarılı, ${hatali} hatalı.`);
  gunlukYaz(`Üretim bitti: ${basarili} başarılı, ${hatali} hatalı.`, hatali ? "hata" : "iyi");
  hazirMi();
});

for (const g of [el.site, el.klasor, el.gecikmeAlt, el.gecikmeUst]) g.addEventListener("change", ayarlariKaydet);
ayarlariYukle();
eslesmeyiGoster();
gunlukYaz("Hazır.");

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
  panelIlerleme: $("panel-ilerleme"), ilerlemeBaslik: $("ilerleme-baslik"),
  ilerlemeSayac: $("ilerleme-sayac"), cubuk: $("cubuk"),
  ilerlemeMetin: $("ilerleme-metin"), ilerlemeSure: $("ilerleme-sure"),
};

const ALANLAR = ["prompt", "gorsel", "uret", "sonuc"];
let secici = { prompt: "", gorsel: "", uret: "", sonuc: "" };
let izler = {};   // öğelerin parmak izleri: seçici bozulursa kurtarma için
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
  const d = await chrome.storage.local.get(["secici", "izler", "site", "klasor", "gecikme"]);
  if (d.secici) secici = { ...secici, ...d.secici };
  if (d.izler) izler = d.izler;
  if (d.site) el.site.value = d.site;
  if (d.klasor) el.klasor.value = d.klasor;
  if (d.gecikme) { el.gecikmeAlt.value = d.gecikme[0]; el.gecikmeUst.value = d.gecikme[1]; }
  seciciyiGoster();
}
const ayarlariKaydet = () => chrome.storage.local.set({
  secici, izler, site: el.site.value, klasor: el.klasor.value,
  gecikme: [Number(el.gecikmeAlt.value), Number(el.gecikmeUst.value)],
});

function seciciyiGoster() {
  for (const a of ALANLAR) $("s-" + a).textContent = secici[a] || "—";
  hazirMi();
}

function hazirMi() {
  // sonuç seçicisi zorunlu değil: boşsa tüm sayfa izlenir
  const tamam = hedefSekmeId && secici.prompt && secici.uret && islerVar();
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

// Her seçicinin sayfada neye denk geldiğini yerinde gösterir. Teşhis için
// ekran görüntüsü alıp göndermek gerekmesin.
document.querySelectorAll("[data-temizle]").forEach((d) => {
  d.addEventListener("click", () => {
    const alan = d.dataset.temizle;
    secici[alan] = "";
    delete izler[alan];
    ayarlariKaydet();
    seciciyiGoster();
    document.getElementById("s-" + alan).parentElement.querySelector(".sina-sonuc")?.remove();
    gunlukYaz(`${alan} seçicisi temizlendi — artık tüm sayfa izlenecek.`, "iyi");
  });
});

document.querySelectorAll("[data-sina]").forEach((d) => {
  d.addEventListener("click", async () => {
    const alan = d.dataset.sina;
    const kutu = document.getElementById("s-" + alan);
    const yaz = (metin, sinif) => {
      kutu.parentElement.querySelector(".sina-sonuc")?.remove();
      const n = document.createElement("span");
      n.className = "sina-sonuc " + sinif;
      n.textContent = metin;
      kutu.parentElement.appendChild(n);
    };
    if (!hedefSekmeId) return yaz("Önce siteye bağlanın.", "hata");
    if (!secici[alan]) {
      return alan === "sonuc"
        ? yaz("Boş — üretim sırasında tüm sayfa izlenecek. En dayanıklı ayar budur.", "iyi")
        : yaz("Bu seçici henüz öğretilmedi.", "hata");
    }
    try {
      const c = await chrome.tabs.sendMessage(hedefSekmeId, { tur: "sina", secici: secici[alan], alan, iz: izler[alan] },
        hedefCerceveId ? { frameId: hedefCerceveId } : undefined);
      const r = c.sonuc;
      yaz(r.mesaj, r.ok ? "iyi" : "hata");
      gunlukYaz(`sına ${alan}: ${r.mesaj}`, r.ok ? "iyi" : "hata");
    } catch (e) {
      yaz("Sınanamadı: " + e.message, "hata");
    }
  });
});

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
    if (m.iz) izler[beklenenAlan] = m.iz;
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

el.durdur.addEventListener("click", async () => {
  durdurIstendi = true;
  el.durdur.disabled = true;
  durumYaz("Durduruluyor — süren iş kesiliyor…");
  el.ilerlemeMetin.textContent = "Durduruluyor — süren iş kesiliyor…";
  // Süren iş zaman aşımını beklemesin: içerik betiğine de haber ver.
  // Beklerken bulduğu sonuç varsa geri gönderir, indirilir.
  try {
    if (hedefSekmeId !== null) {
      await chrome.tabs.sendMessage(hedefSekmeId, { tur: "durdur" }, { frameId: hedefCerceveId });
    }
  } catch { /* sekme kapanmış olabilir, sorun değil */ }
});

// İlerleme göstergesi.
//
// Seksen klipte "işleniyor…" yazısı yetmiyor: kullanıcı ne kadar kaldığını ve
// tek bir işin ne süredir beklediğini görmeli. Tahmini süre, o ana kadar
// TAMAMLANMIŞ işlerin ortalamasından hesaplanır; ilk iş bitmeden tahmin
// verilmez, yanıltıcı olur.
const sureBicim = (sn) => {
  if (!isFinite(sn) || sn < 0) return "—";
  const s = Math.round(sn), d = Math.floor(s / 60), st = Math.floor(d / 60);
  return st ? `${st} sa ${d % 60} dk` : d ? `${d} dk ${s % 60} sn` : `${s} sn`;
};

let ilerlemeZamanlayici = null;

function ilerlemeKur(toplam) {
  el.panelIlerleme.hidden = false;
  el.ilerlemeBaslik.textContent = "Üretim sürüyor…";
  el.cubuk.style.width = "0%";
  el.ilerlemeSayac.innerHTML = `0 / ${toplam}`;
  el.ilerlemeMetin.textContent = "Başlıyor…";
  el.ilerlemeSure.textContent = "";
}

function ilerlemeGuncelle({ biten, toplam, basarili, hatali, baslangic, durum, isBaslangici }) {
  const oran = toplam ? biten / toplam : 0;
  el.cubuk.style.width = Math.round(oran * 100) + "%";
  el.ilerlemeSayac.innerHTML =
    `${biten} / ${toplam}  ·  <b>${basarili} başarılı</b>` + (hatali ? `  ·  <i>${hatali} hatalı</i>` : "");
  el.ilerlemeMetin.textContent = durum;

  clearInterval(ilerlemeZamanlayici);
  const yaz = () => {
    const gecen = (Date.now() - baslangic) / 1000;
    let metin = `geçen ${sureBicim(gecen)}`;
    if (biten > 0 && biten < toplam) {
      metin += ` · tahmini kalan ${sureBicim((gecen / biten) * (toplam - biten))}`;
    }
    if (isBaslangici) metin += ` · bu iş ${sureBicim((Date.now() - isBaslangici) / 1000)}`;
    el.ilerlemeSure.textContent = metin;
  };
  yaz();
  if (isBaslangici) ilerlemeZamanlayici = setInterval(yaz, 1000);
}

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
  ilerlemeKur(adet);
  const baslangicAn = Date.now();

  let basarili = 0, hatali = 0;
  for (let i = 0; i < adet; i++) {
    if (durdurIstendi) { gunlukYaz("Kullanıcı durdurdu."); break; }
    satirDurum(i, "çalışıyor…", "calisiyor");
    durumYaz(`${i + 1}/${adet} işleniyor…`);
    const isAn = Date.now();
    ilerlemeGuncelle({ biten: i, toplam: adet, basarili, hatali, baslangic: baslangicAn,
      durum: `${i + 1}. iş üretiliyor — sonuç bekleniyor`, isBaslangici: isAn });

    try {
      const is = { secici, izler, prompt: promptlar[i], zamanAsimi };
      if (gorseller[i] && secici.gorsel) {
        is.gorsel = { ad: gorseller[i].name, veri: await dosyaOku(gorseller[i]) };
      }
      const cevap = await chrome.tabs.sendMessage(hedefSekmeId, { tur: "is", is }, { frameId: hedefCerceveId });
      if (!cevap?.ok) throw new Error(cevap?.hata || "yanıt yok");

      for (const not of cevap.sonuc.kurtarmalar || []) gunlukYaz("kurtarma — " + not, "hata");
      for (const not of cevap.sonuc.notlar || []) gunlukYaz("not — " + not);
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
      if (cevap.sonuc.durduruldu) {
        // Kesilen iş ne başarılı ne hatalı: indirilen çıktı varsa sayılır,
        // yoksa hiç yapılmamış işlerle birlikte eksik kalır.
        satirDurum(i, adresler.length ? "durduruldu (indirildi)" : "durduruldu", "hatali");
        if (!adresler.length) satirSonuc(i, "durduruldu — sonuç çıkmamıştı");
        gunlukYaz(`${i + 1}. iş kullanıcı isteğiyle kesildi.`);
        if (adresler.length) basarili++;
      } else {
        satirDurum(i, "tamam", "tamam");
        basarili++;
      }
    } catch (e) {
      satirDurum(i, "hata", "hatali");
      satirSonuc(i, e.message);
      gunlukYaz(`${i + 1}. iş başarısız: ${e.message}`, "hata");
      hatali++;
    }

    if (i < adet - 1 && !durdurIstendi) {
      const s = altGecikme + Math.random() * (ustGecikme - altGecikme);
      gunlukYaz(`${s.toFixed(1)} sn bekleniyor…`);
      ilerlemeGuncelle({ biten: i + 1, toplam: adet, basarili, hatali, baslangic: baslangicAn,
        durum: `Sıradaki iş için ${s.toFixed(0)} sn bekleniyor…`, isBaslangici: null });
      await bekle(s * 1000);
    }
  }

  calisiyor = false;
  el.durdur.hidden = true;
  clearInterval(ilerlemeZamanlayici);
  // Durdurulduysa cubuk gercekten islenen orani gostermeli; %100 yalan olurdu.
  const biten = basarili + hatali;
  el.cubuk.style.width = (adet ? Math.round((biten / adet) * 100) : 100) + "%";
  el.ilerlemeBaslik.textContent = durdurIstendi ? "Üretim durduruldu" : "Üretim tamamlandı";
  el.ilerlemeSayac.innerHTML = `${biten} / ${adet}  ·  <b>${basarili} başarılı</b>` +
    (hatali ? `  ·  <i>${hatali} hatalı</i>` : "");
  el.ilerlemeMetin.textContent = durdurIstendi
    ? `${adet - biten} iş tamamlanmadan durduruldu.`
    : hatali ? "Hatalı işler için günlüğe bakın." : "Tüm işler tamamlandı.";
  el.ilerlemeSure.textContent = `toplam ${sureBicim((Date.now() - baslangicAn) / 1000)}`;
  durumYaz(`Bitti — ${basarili} başarılı, ${hatali} hatalı.`);
  gunlukYaz(`Üretim bitti: ${basarili} başarılı, ${hatali} hatalı.`, hatali ? "hata" : "iyi");
  hazirMi();
});

for (const g of [el.site, el.klasor, el.gecikmeAlt, el.gecikmeUst]) g.addEventListener("change", ayarlariKaydet);
ayarlariYukle();
eslesmeyiGoster();
gunlukYaz("Hazır.");

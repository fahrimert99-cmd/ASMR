// Hedef sitenin sayfasına enjekte edilen betik.
//
// İki işi var: (1) kullanıcı bir öğeye tıklayınca onun için sağlam bir seçici
// çıkarmak, (2) verilen işi sayfada yürütmek (prompt yaz, görsel ekle, üret'e
// bas, sonucu bekle).
//
// Seçiciler burada TAHMİN EDİLMEZ, öğrenilir. Site arayüzünü değiştirdiğinde
// eklentinin tamamı değil yalnızca öğretilen seçiciler yenilenir.

(() => {
  if (window.__topluUretimKurulu) return;
  window.__topluUretimKurulu = true;

  // ------------------------------------------------------------ seçici çıkarma

  const ANLAMLI_NITELIK = ["data-testid", "data-test", "data-qa", "aria-label", "name", "placeholder", "type"];

  // Rastgele üretilmiş görünen kimlikleri elemek için: uzun, rakam/harf karışık
  // diziler her sayfa yüklemesinde değişebilir, seçici olarak güvenilmez.
  function kimlikSaglamMi(kimlik) {
    if (!kimlik || kimlik.length > 40) return false;
    if (/^[0-9]/.test(kimlik)) return false;
    const rakam = (kimlik.match(/\d/g) || []).length;
    return rakam / kimlik.length < 0.4;
  }

  function nitelikSecici(el) {
    for (const n of ANLAMLI_NITELIK) {
      const d = el.getAttribute(n);
      if (d && d.length < 60) {
        const s = `${el.tagName.toLowerCase()}[${n}="${CSS.escape(d).replace(/\\/g, "")}"]`;
        try { if (document.querySelectorAll(s).length === 1) return s; } catch (_) {}
      }
    }
    return null;
  }

  // Tıklanan öğeyi anlamlı olana çevirir.
  //
  // Düğmelerin içinde <svg>, <span> gibi süs öğeleri olur ve fare onlara denk
  // gelir. Kaydedilmesi gereken düğmenin kendisidir: hem daha kararlı bir
  // seçici verir (aria-label gibi), hem de tıklanacak olan odur.
  //
  // Yalnızca süs öğelerinde yukarı çıkılır; sıradan bir <div> tıklandığında
  // (örneğin sonucun çıktığı alan) olduğu gibi bırakılır, yoksa kapsayan bir
  // bağlantıya sıçrayıp yanlış öğe seçilirdi.
  const SUS_OGE = new Set(["svg", "use", "path", "g", "circle", "rect", "polygon", "line",
                           "span", "i", "em", "b", "strong", "small", "img", "figure", "picture"]);
  const AKSIYON = 'button, a, label, input, textarea, select, [role="button"], [contenteditable="true"], [contenteditable=""]';

  function hedefiNormalize(el) {
    if (!el?.tagName) return el;
    if (!SUS_OGE.has(el.tagName.toLowerCase())) return el;
    return el.closest?.(AKSIYON) || el;
  }

  function nitelikParcasi(el) {
    for (const n of ANLAMLI_NITELIK) {
      const d = el.getAttribute(n);
      if (d && d.length < 60 && !/["\\]/.test(d)) return `[${n}="${d}"]`;
    }
    return null;
  }

  const benzersizMi = (s) => {
    try { return document.querySelectorAll(s).length === 1; } catch (_) { return false; }
  };

  // Öğe için olabildiğince KISA ve KARARLI bir seçici üretir.
  //
  // Konuma dayalı uzun yollar (body > div:nth-of-type(3) > ...) tek sayfa
  // uygulamaları arayüzü yeniden çizdiğinde bozulur. Bu yüzden önce kimlik ve
  // anlamlı nitelikler denenir, sonra kararlı bir atanın içine "kapsanmış"
  // kısa bir seçici kurulur; konum yolu yalnızca son çaredir.
  function secikiCikar(el) {
    const etiket = el.tagName.toLowerCase();

    if (el.id && kimlikSaglamMi(el.id) && benzersizMi("#" + CSS.escape(el.id))) {
      return "#" + CSS.escape(el.id);
    }
    const kendi = nitelikParcasi(el);
    if (kendi && benzersizMi(etiket + kendi)) return etiket + kendi;

    // Kararlı bir atanın içine kapsa: "form textarea", "#panel button" gibi.
    let ata = el.parentElement;
    for (let derinlik = 0; derinlik < 6 && ata && ata !== document.body; derinlik++, ata = ata.parentElement) {
      const ataSecici = (ata.id && kimlikSaglamMi(ata.id) && "#" + CSS.escape(ata.id))
        || (nitelikParcasi(ata) && ata.tagName.toLowerCase() + nitelikParcasi(ata));
      if (!ataSecici || !benzersizMi(ataSecici)) continue;

      for (const kuyruk of [etiket + (kendi || ""), etiket]) {
        const aday = `${ataSecici} ${kuyruk}`;
        if (benzersizMi(aday)) return aday;
        const kardesler = [...(el.parentElement?.children || [])].filter((c) => c.tagName === el.tagName);
        if (kardesler.length > 1) {
          const sirali = `${aday}:nth-of-type(${kardesler.indexOf(el) + 1})`;
          if (benzersizMi(sirali)) return sirali;
        }
      }
    }

    // Son çare: köke kadar konum yolu.
    const parcalar = [];
    let dugum = el;
    while (dugum && dugum.nodeType === 1 && dugum !== document.body) {
      const e = dugum.tagName.toLowerCase();
      const kardesler = [...(dugum.parentElement?.children || [])].filter((c) => c.tagName === dugum.tagName);
      parcalar.unshift(kardesler.length > 1 ? `${e}:nth-of-type(${kardesler.indexOf(dugum) + 1})` : e);
      const deneme = "body > " + parcalar.join(" > ");
      if (benzersizMi(deneme)) return deneme;
      dugum = dugum.parentElement;
    }
    return "body > " + parcalar.join(" > ");
  }

  // Öğenin "parmak izi": seçici bozulursa öğeyi yeniden bulmak için.
  function parmakIzi(el) {
    return {
      etiket: el.tagName.toLowerCase(),
      aria: el.getAttribute("aria-label") || "",
      rol: el.getAttribute("role") || "",
      tip: el.getAttribute("type") || "",
      isim: el.getAttribute("name") || "",
      ipucu: el.getAttribute("placeholder") || "",
      metin: (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 60),
    };
  }

  // Seçici tutmazsa parmak izinden arar. Site arayüzünü değiştirdiğinde
  // kullanıcıyı yeniden öğretmeye zorlamadan kurtarmayı dener; bulursa
  // bunu açıkça bildirir, sessizce farklı bir öğeye basmaz.
  function izdenBul(iz) {
    if (!iz?.etiket) return null;
    const adaylar = [...document.querySelectorAll(iz.etiket)];
    if (!adaylar.length) return null;
    const puanla = (el) => {
      let p = 0;
      if (iz.aria && el.getAttribute("aria-label") === iz.aria) p += 5;
      if (iz.isim && el.getAttribute("name") === iz.isim) p += 4;
      if (iz.ipucu && el.getAttribute("placeholder") === iz.ipucu) p += 4;
      if (iz.tip && el.getAttribute("type") === iz.tip) p += 2;
      if (iz.rol && el.getAttribute("role") === iz.rol) p += 2;
      if (iz.metin) {
        const m = (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 60);
        if (m === iz.metin) p += 4; else if (m && iz.metin.includes(m)) p += 1;
      }
      return p;
    };
    const puanli = adaylar.map((el) => ({ el, p: puanla(el) })).sort((a, b) => b.p - a.p);
    if (puanli[0].p < 4) return null;                       // zayıf eşleşmeye güvenme
    if (puanli[1] && puanli[1].p === puanli[0].p) return null;   // belirsizse dokunma
    return puanli[0].el;
  }

  // ------------------------------------------------------------- öğrenme kipi

  let ogrenmeAktif = false;
  let vurgu = null;

  function vurguKur() {
    vurgu = document.createElement("div");
    Object.assign(vurgu.style, {
      position: "fixed", pointerEvents: "none", zIndex: "2147483647",
      border: "2px solid #38bdf8", background: "rgba(56,189,248,.16)",
      borderRadius: "4px", transition: "all .05s linear",
    });
    const etiket = document.createElement("div");
    etiket.textContent = "Toplu Üretim: öğrenmek için tıklayın · ESC ile çık";
    Object.assign(etiket.style, {
      position: "fixed", zIndex: "2147483647", left: "0", right: "0", top: "0",
      background: "#0b1322", color: "#e2e8f0", font: "600 13px system-ui, sans-serif",
      padding: "8px 12px", textAlign: "center", pointerEvents: "none",
    });
    vurgu.__etiket = etiket;
    document.body.append(vurgu, etiket);
  }

  function vurguKaldir() {
    vurgu?.__etiket?.remove();
    vurgu?.remove();
    vurgu = null;
  }

  const uzerinde = (e) => {
    if (!ogrenmeAktif || !vurgu) return;
    const r = e.target.getBoundingClientRect();
    Object.assign(vurgu.style, {
      left: r.left + "px", top: r.top + "px", width: r.width + "px", height: r.height + "px",
    });
  };

  const tiklama = (e) => {
    if (!ogrenmeAktif) return;
    e.preventDefault();
    e.stopPropagation();
    const hedef = hedefiNormalize(e.target);
    const secici = secikiCikar(hedef);
    const tiklanan = e.target.tagName.toLowerCase();
    const dosyaGirdisi = (hedef.tagName === "INPUT" && hedef.type === "file")
      || !!hedef.querySelector?.('input[type="file"]');
    const metinAlani = metinAlaniMi(hedef) || !!hedef.querySelector?.(METIN_ALANI);
    const etiketAdi = hedef.tagName.toLowerCase();
    ogrenmeyiBitir();
    chrome.runtime.sendMessage({
      tur: "ogrenildi", secici, etiket: etiketAdi, dosyaGirdisi, metinAlani, iz: parmakIzi(hedef),
      yukariCikildi: tiklanan !== etiketAdi ? tiklanan : null,
    });
  };

  const tusa = (e) => {
    if (ogrenmeAktif && e.key === "Escape") {
      ogrenmeyiBitir();
      chrome.runtime.sendMessage({ tur: "ogrenme-iptal" });
    }
  };

  function ogrenmeyiBaslat() {
    ogrenmeAktif = true;
    vurguKur();
    document.addEventListener("mousemove", uzerinde, true);
    document.addEventListener("click", tiklama, true);
    document.addEventListener("keydown", tusa, true);
  }

  function ogrenmeyiBitir() {
    ogrenmeAktif = false;
    vurguKaldir();
    document.removeEventListener("mousemove", uzerinde, true);
    document.removeEventListener("click", tiklama, true);
    document.removeEventListener("keydown", tusa, true);
  }

  // --------------------------------------------------------------- iş yürütme

  const bekle = (ms) => new Promise((r) => setTimeout(r, ms));
  const bul = (s) => { try { return s ? document.querySelector(s) : null; } catch (_) { return null; } };

  let kurtarmaNotlari = [];
  let durdurIstendi = false;   // panodan gelen Durdur, süren işi keser

  // Önce seçiciyi dener; tutmazsa parmak izinden arar.
  function bulEsnek(secici, iz, ad) {
    const dogrudan = bul(secici);
    if (dogrudan) return dogrudan;
    const kurtarilan = izdenBul(iz);
    if (kurtarilan) {
      kurtarmaNotlari.push(`${ad}: seçici tutmadı, öğe parmak izinden bulundu`);
      return kurtarilan;
    }
    return null;
  }

  // Tek seferde bulunamazsa kısa süre yeniden dener: tek sayfa uygulamaları
  // arayüzü eşzamansız çizdiği için öğe bir an sonra belirebilir.
  async function bulBekle(s, iz, ad, sure = 6000) {
    const bitis = Date.now() + sure;
    for (;;) {
      const o = bulEsnek(s, iz, ad);
      if (o) return o;
      if (Date.now() > bitis) return null;
      await bekle(300);
    }
  }

  // React ve benzeri çatılar değer atamasını kendi durumlarında takip eder;
  // doğrudan .value yazmak arayüzü güncellemez. Yerel ayarlayıcıyı çağırıp
  // olay tetiklemek gerekir.
  const METIN_ALANI = 'textarea, input[type="text"], input[type="search"], input:not([type]), [contenteditable="true"], [contenteditable=""]';

  function metinAlaniMi(el) {
    return el instanceof HTMLTextAreaElement
      || (el instanceof HTMLInputElement && /^(text|search|)$/.test(el.type))
      || el?.isContentEditable === true;
  }

  // Öğretilen öğeden gerçek yazı alanını bulur.
  //
  // Kullanıcı çoğu zaman metin alanının kendisine değil onu saran kutuya
  // tıklar (öğe görsel olarak o kutudur). Yerel value ayarlayıcısını bir
  // <div> üzerinde çağırmak "Illegal invocation" verir; bu yüzden önce gerçek
  // alan aranır.
  function metinAlaniBul(secici, iz) {
    const oge = bulEsnek(secici, iz, "prompt");
    if (!oge) return null;
    if (metinAlaniMi(oge)) return oge;
    const icten = oge.querySelector?.(METIN_ALANI);
    if (icten) return icten;
    let ata = oge.parentElement;
    for (let i = 0; i < 4 && ata; i++, ata = ata.parentElement) {
      const k = ata.querySelector(METIN_ALANI);
      if (k) return k;
    }
    return document.querySelector(METIN_ALANI);
  }

  function degerYaz(el, metin) {
    if (el.isContentEditable) {
      el.focus();
      el.textContent = metin;
      el.dispatchEvent(new InputEvent("input", { bubbles: true, data: metin }));
      return true;
    }
    if (!(el instanceof HTMLTextAreaElement) && !(el instanceof HTMLInputElement)) {
      throw new Error(`prompt alanı yazı kutusu değil (<${el.tagName.toLowerCase()}>); ` +
        "seçiciyi metnin yazıldığı kutuya öğretin");
    }
    const proto = el instanceof HTMLTextAreaElement
      ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const ayarlayici = Object.getOwnPropertyDescriptor(proto, "value")?.set;
    el.focus();
    if (ayarlayici) ayarlayici.call(el, metin); else el.value = metin;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  // Öğretilen öğeden gerçek dosya girdisini bulur.
  //
  // Sitelerin çoğunda input[type=file] gizlidir ve görünen şey onu tetikleyen
  // süslü bir düğme/alandır. Kullanıcı görünene tıklamak zorunda olduğu için,
  // öğretilen öğe girdinin kendisi değilse önce içinde, sonra sayfanın
  // tamamında aranır.
  function dosyaGirdisiBul(secici, iz) {
    const oge = bulEsnek(secici, iz, "görsel");
    if (oge?.tagName === "INPUT" && oge.type === "file") return oge;
    const icten = oge?.querySelector?.('input[type="file"]');
    if (icten) return icten;
    // Öğretilen öğenin en yakın ortak atasında ara (düğme ile girdi genelde kardeştir).
    let ata = oge?.parentElement;
    for (let i = 0; i < 4 && ata; i++, ata = ata.parentElement) {
      const k = ata.querySelector('input[type="file"]');
      if (k) return k;
    }
    return document.querySelector('input[type="file"]');
  }

  async function gorselEkle(secici, iz, veri, ad) {
    const girdi = dosyaGirdisiBul(secici, iz);
    if (!girdi) throw new Error("sayfada dosya girdisi bulunamadı (öğretilen: " + secici + ")");
    const bayt = Uint8Array.from(atob(veri), (c) => c.charCodeAt(0));
    const dosya = new File([bayt], ad, { type: "image/png" });
    const aktarim = new DataTransfer();
    aktarim.items.add(dosya);
    girdi.files = aktarim.files;
    girdi.dispatchEvent(new Event("change", { bubbles: true }));
    await bekle(300);
  }

  const MEDYA_UZANTI = /\.(mp4|webm|mov|m4v)(\?|#|$)/i;

  // Bir adresin video olup olmadığına karar verir.
  //
  // Eskiden her a[href] toplanıyordu; gerçek bir sitede bu yüzlerce gezinme
  // bağlantısı demek ve üretimden sonra beliren herhangi bir bağlantı sonuç
  // sanılabilirdi. Artık yalnızca video öğeleri ve medya adresleri sayılır.
  const medyaAdresiMi = (u) => !!u && !u.startsWith("data:") &&
    (u.startsWith("blob:") || MEDYA_UZANTI.test(u));

  // Sonuç adreslerini toplar.
  //
  // Seçici verilmezse (veya tutmazsa) TÜM SAYFA izlenir. Kullanıcıyı videoların
  // belireceği kutuyu tam isabetle göstermeye zorlamak kırılgan bir gereksinim;
  // sayfanın tamamında yeni beliren videoyu aramak hem daha basit hem daha
  // dayanıklı.
  function medyaTopla(kok) {
    const adresler = new Set();
    const ekle = (u) => medyaAdresiMi(u) && adresler.add(u);
    if (kok.tagName === "VIDEO") ekle(kok.currentSrc || kok.src);
    kok.querySelectorAll?.("video, source").forEach((e) => ekle(e.currentSrc || e.src));
    kok.querySelectorAll?.("a[href]").forEach((e) => ekle(e.href));
    return adresler;
  }

  // Sonuç iki yerde birden aranır: öğretilen kutuda VE sayfanın tamamında.
  //
  // Kullanıcı sonuç alanı diye bir menü bağlantısını (#library) öğretmişti;
  // kutunun içinde eski bir bağlantı durduğu için "içi boş" sayılmıyor,
  // yedeğe de düşmüyor ve iş 300 sn sonra boşuna zaman aşımına uğruyordu.
  // Artık kutu yalnızca ÖNCELİK: orada yeni bir şey çıkarsa o alınır,
  // çıkmazsa sayfanın tamamındaki yeni adresler kullanılır.
  function sonucAdresleri(secici, iz) {
    const kok = (secici && bulEsnek(secici, iz, "sonuç")) || document;
    const kapsayici = medyaTopla(kok);
    if (kok === document) return { kap: [...kapsayici], tum: [...kapsayici] };
    const tum = medyaTopla(document);
    for (const u of kapsayici) tum.add(u);
    return { kap: [...kapsayici], tum: [...tum] };
  }

  async function isYurut(is) {
    const { secici, izler = {}, prompt, gorsel, zamanAsimi = 300000 } = is;
    kurtarmaNotlari = [];
    durdurIstendi = false;

    const promptEl = metinAlaniBul(secici.prompt, izler.prompt);
    if (!promptEl) {
      throw new Error("sayfada yazı kutusu bulunamadı (öğretilen: " + secici.prompt + ")");
    }

    // Üretimden ÖNCEKİ sonuçlar not edilir; yenisi bunların dışında çıkacak.
    const once = sonucAdresleri(secici.sonuc, izler.sonuc);
    const oncekiKap = new Set(once.kap), oncekiTum = new Set(once.tum);

    if (gorsel && secici.gorsel) await gorselEkle(secici.gorsel, izler.gorsel, gorsel.veri, gorsel.ad);
    degerYaz(promptEl, prompt);
    await bekle(250);

    const uretEl = await bulBekle(secici.uret, izler.uret, "üret");
    if (!uretEl) throw new Error("üret düğmesi bulunamadı: " + secici.uret);
    uretEl.click();

    const bitis = Date.now() + zamanAsimi;
    const tara = () => {
      const s = sonucAdresleri(secici.sonuc, izler.sonuc);
      const kap = s.kap.filter((u) => !oncekiKap.has(u));
      return kap.length ? { adresler: kap, nerede: "kutu" }
                        : { adresler: s.tum.filter((u) => !oncekiTum.has(u)), nerede: "sayfa" };
    };

    while (Date.now() < bitis) {
      await bekle(1500);
      const b = tara();
      if (b.adresler.length) {
        // Kutu dışında bulunmak bir hata değil, bilgi: günlükte kırmızı durmasın.
        const notlar = (b.nerede === "sayfa" && secici.sonuc)
          ? ["sonuç öğretilen kutunun dışında, sayfanın tamamında bulundu"] : [];
        return { adresler: b.adresler, kurtarmalar: kurtarmaNotlari.slice(), notlar };
      }
      // Durdur'a basıldıysa beklemeyi kesip o ana kadar çıkanı geri ver;
      // üretilmiş bir klibi elde kalmış sayıp atmak kullanıcının hakkı değil.
      if (durdurIstendi) {
        return { adresler: [], kurtarmalar: kurtarmaNotlari.slice(), durduruldu: true };
      }
    }
    const kalan = tara().adresler;
    if (kalan.length) return { adresler: kalan, kurtarmalar: kurtarmaNotlari.slice() };
    throw new Error(`sonuç ${Math.round(zamanAsimi / 1000)} sn içinde gelmedi`);
  }

  // Sonucu indirilebilir bayta çevirir. blob: adresleri yalnızca sayfa
  // bağlamından okunabildiği için indirme burada yapılır, panoya bayt gider.
  async function adresiOku(adres) {
    const y = await fetch(adres);
    if (!y.ok) throw new Error("indirilemedi: HTTP " + y.status);
    const b = new Uint8Array(await y.arrayBuffer());
    let s = "";
    for (let i = 0; i < b.length; i += 32768) s += String.fromCharCode(...b.subarray(i, i + 32768));
    return { veri: btoa(s), tur: y.headers.get("content-type") || "video/mp4", boyut: b.length };
  }

  // Seçiciyi sayfada sınar ve neye denk geldiğini anlatır.
  //
  // Ekran görüntüsü üzerinden teşhis yavaş ve seçiciler panoda kesik
  // görünüyordu; kullanıcı artık kendisi bakabilsin.
  function seciciSina(secici, alan, iz) {
    let ogeler;
    try { ogeler = document.querySelectorAll(secici); }
    catch (e) { return { ok: false, mesaj: "geçersiz seçici: " + e.message }; }

    if (!ogeler.length) {
      const kurtarilan = izdenBul(iz);
      return kurtarilan
        ? { ok: true, mesaj: `seçici tutmuyor AMA öğe parmak izinden bulunabiliyor: ` +
            `<${kurtarilan.tagName.toLowerCase()}>${kurtarilan.id ? "#" + kurtarilan.id : ""} — çalışır, yine de yeniden öğretmek daha sağlam` }
        : { ok: false, mesaj: "sayfada HİÇBİR öğeye uymuyor ve parmak izinden de bulunamadı" };
    }
    const oge = ogeler[0];
    const etiket = oge.tagName.toLowerCase();
    const kimlik = oge.id ? "#" + oge.id : "";
    const aria = oge.getAttribute("aria-label");
    const yazi = (oge.textContent || "").trim().replace(/\s+/g, " ").slice(0, 40);
    const tanim = `<${etiket}>${kimlik}` + (aria ? ` aria-label="${aria}"` : "") + (yazi ? ` "${yazi}"` : "");
    const coklu = ogeler.length > 1 ? ` — DİKKAT: ${ogeler.length} öğeye birden uyuyor` : "";

    if (alan === "prompt") {
      const alanOge = metinAlaniBul(secici, iz);
      return alanOge
        ? { ok: true, mesaj: `${tanim} → yazı kutusu bulundu: <${alanOge.tagName.toLowerCase()}>${alanOge.id ? "#" + alanOge.id : ""}${coklu}` }
        : { ok: false, mesaj: `${tanim} → içinde veya yakınında yazı kutusu YOK` };
    }
    if (alan === "gorsel") {
      const girdi = dosyaGirdisiBul(secici, iz);
      return girdi
        ? { ok: true, mesaj: `${tanim} → dosya girdisi bulundu${girdi.id ? " #" + girdi.id : ""}${coklu}` }
        : { ok: false, mesaj: `${tanim} → yakınında input[type=file] YOK` };
    }
    if (alan === "uret") {
      const tiklanabilir = typeof oge.click === "function";
      const dugme = etiket === "button" || oge.getAttribute("role") === "button" || etiket === "a";
      return tiklanabilir
        ? { ok: true, mesaj: `${tanim} → tıklanabilir${dugme ? "" : " (ama düğme değil, emin olun)"}${coklu}` }
        : { ok: false, mesaj: `${tanim} → tıklanamaz (SVG gibi bir öğe); düğmenin kendisini seçin` };
    }
    if (alan === "sonuc") {
      const icerde = sonucAdresleri(secici, iz).kap.length;
      const sayfada = sonucAdresleri("", null).tum.length;
      return { ok: true, mesaj: `${tanim} → şu an ${icerde} video adresi görünüyor ` +
        `(sayfanın tamamında ${sayfada}). Kutuda yeni bir sonuç çıkmazsa sayfanın ` +
        `tamamı da taranır, iş boşuna beklemez. Emin değilseniz bu alanı BOŞ bırakın.` + coklu };
    }
    return { ok: true, mesaj: tanim + coklu };
  }

  chrome.runtime.onMessage.addListener((mesaj, _gonderen, cevapla) => {
    (async () => {
      try {
        if (mesaj.tur === "canli") return cevapla({ ok: true, baslik: document.title, adres: location.href });
        if (mesaj.tur === "ogren") { ogrenmeyiBaslat(); return cevapla({ ok: true }); }
        if (mesaj.tur === "durdur") { durdurIstendi = true; return cevapla({ ok: true }); }
        if (mesaj.tur === "is") return cevapla({ ok: true, sonuc: await isYurut(mesaj.is) });
        if (mesaj.tur === "oku") return cevapla({ ok: true, dosya: await adresiOku(mesaj.adres) });
        if (mesaj.tur === "sina") return cevapla({ ok: true, sonuc: seciciSina(mesaj.secici, mesaj.alan, mesaj.iz) });
        cevapla({ ok: false, hata: "bilinmeyen mesaj" });
      } catch (e) {
        cevapla({ ok: false, hata: e.message });
      }
    })();
    return true;   // eşzamansız cevap
  });
})();

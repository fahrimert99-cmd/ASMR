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

  function secikiCikar(el) {
    if (el.id && kimlikSaglamMi(el.id)) {
      const s = `#${CSS.escape(el.id)}`;
      if (document.querySelectorAll(s).length === 1) return s;
    }
    const n = nitelikSecici(el);
    if (n) return n;

    // Son çare: köke kadar etiket + kardeş sırası. Sınıf adları derleyici
    // tarafından üretildiğinde (hash'li) değişken olduğu için kullanılmaz.
    const parcalar = [];
    let dugum = el;
    while (dugum && dugum.nodeType === 1 && dugum !== document.body) {
      const etiket = dugum.tagName.toLowerCase();
      const kardesler = [...(dugum.parentElement?.children || [])].filter((c) => c.tagName === dugum.tagName);
      const sira = kardesler.indexOf(dugum) + 1;
      parcalar.unshift(kardesler.length > 1 ? `${etiket}:nth-of-type(${sira})` : etiket);
      const deneme = "body > " + parcalar.join(" > ");
      try { if (document.querySelectorAll(deneme).length === 1) return deneme; } catch (_) {}
      dugum = dugum.parentElement;
    }
    return "body > " + parcalar.join(" > ");
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
    const secici = secikiCikar(e.target);
    ogrenmeyiBitir();
    chrome.runtime.sendMessage({ tur: "ogrenildi", secici, etiket: e.target.tagName.toLowerCase() });
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

  // React ve benzeri çatılar değer atamasını kendi durumlarında takip eder;
  // doğrudan .value yazmak arayüzü güncellemez. Yerel ayarlayıcıyı çağırıp
  // olay tetiklemek gerekir.
  function degerYaz(el, metin) {
    if (el.isContentEditable) {
      el.focus();
      el.textContent = metin;
      el.dispatchEvent(new InputEvent("input", { bubbles: true }));
      return true;
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

  async function gorselEkle(secici, veri, ad) {
    const girdi = bul(secici);
    if (!girdi) throw new Error("görsel alanı bulunamadı: " + secici);
    const bayt = Uint8Array.from(atob(veri), (c) => c.charCodeAt(0));
    const dosya = new File([bayt], ad, { type: "image/png" });
    const aktarim = new DataTransfer();
    aktarim.items.add(dosya);
    girdi.files = aktarim.files;
    girdi.dispatchEvent(new Event("change", { bubbles: true }));
    await bekle(300);
  }

  // Sonuçtaki bağlantıyı toplar: video[src], source[src] veya a[href].
  function sonucAdresleri(secici) {
    const kok = bul(secici) || document;
    const adresler = new Set();
    const ekle = (u) => u && !u.startsWith("data:") && adresler.add(u);
    if (kok.tagName === "VIDEO") ekle(kok.currentSrc || kok.src);
    if (kok.tagName === "A") ekle(kok.href);
    kok.querySelectorAll?.("video, source, a[href]").forEach((e) => {
      ekle(e.tagName === "A" ? e.href : (e.currentSrc || e.src));
    });
    return [...adresler];
  }

  async function isYurut(is) {
    const { secici, prompt, gorsel, zamanAsimi = 300000 } = is;

    const promptEl = bul(secici.prompt);
    if (!promptEl) throw new Error("prompt alanı bulunamadı: " + secici.prompt);

    // Üretimden ÖNCEKİ sonuçlar not edilir; yenisi bunların dışında çıkacak.
    const oncekiler = new Set(sonucAdresleri(secici.sonuc));

    if (gorsel && secici.gorsel) await gorselEkle(secici.gorsel, gorsel.veri, gorsel.ad);
    degerYaz(promptEl, prompt);
    await bekle(250);

    const uretEl = bul(secici.uret);
    if (!uretEl) throw new Error("üret düğmesi bulunamadı: " + secici.uret);
    uretEl.click();

    const bitis = Date.now() + zamanAsimi;
    while (Date.now() < bitis) {
      await bekle(1500);
      const yeni = sonucAdresleri(secici.sonuc).filter((u) => !oncekiler.has(u));
      if (yeni.length) return { adresler: yeni };
    }
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

  chrome.runtime.onMessage.addListener((mesaj, _gonderen, cevapla) => {
    (async () => {
      try {
        if (mesaj.tur === "canli") return cevapla({ ok: true, baslik: document.title, adres: location.href });
        if (mesaj.tur === "ogren") { ogrenmeyiBaslat(); return cevapla({ ok: true }); }
        if (mesaj.tur === "is") return cevapla({ ok: true, sonuc: await isYurut(mesaj.is) });
        if (mesaj.tur === "oku") return cevapla({ ok: true, dosya: await adresiOku(mesaj.adres) });
        cevapla({ ok: false, hata: "bilinmeyen mesaj" });
      } catch (e) {
        cevapla({ ok: false, hata: e.message });
      }
    })();
    return true;   // eşzamansız cevap
  });
})();

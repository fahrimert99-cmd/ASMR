// Araç çubuğundaki simgeye tıklanınca panoyu tam sekmede açar.
// Pano ağır render işi yaptığı için açılır pencere (popup) yerine sekme kullanılır:
// açılır pencere odak kaybında kapanır ve render yarıda kalırdı.
chrome.action.onClicked.addListener(async () => {
  const url = chrome.runtime.getURL("dashboard.html");
  const mevcut = await chrome.tabs.query({ url });
  if (mevcut.length) {
    await chrome.tabs.update(mevcut[0].id, { active: true });
    await chrome.windows.update(mevcut[0].windowId, { focused: true });
  } else {
    await chrome.tabs.create({ url });
  }
});

// Araç çubuğundaki simgeye tıklanınca panoyu tam sekmede açar.
// Kuyruk panonun kendisinde döner: MV3 servis çalışanı boşta kalınca
// sonlandırılır ve uzun süren bir üretim kuyruğu orada yaşayamaz.
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

/* 在非安全上下文中于 Web Worker 内执行 PBKDF2，避免阻塞登录界面。 */
importScripts("crypto-js.min.js");

self.onmessage = function handlePasswordHash(event) {
  const payload = event.data || {};
  try {
    if (typeof CryptoJS === "undefined" || !CryptoJS.PBKDF2) {
      throw new Error("CryptoJS 未加载");
    }
    const hash = CryptoJS.PBKDF2(
      String(payload.password || ""),
      CryptoJS.enc.Utf8.parse(String(payload.salt || "")),
      {
        keySize: 256 / 32,
        iterations: Number(payload.iterations) || 120000,
        hasher: CryptoJS.algo.SHA256
      }
    );
    self.postMessage({ hash: hash.toString(CryptoJS.enc.Hex) });
  } catch (error) {
    self.postMessage({ error: error.message || "密码哈希计算失败" });
  }
};

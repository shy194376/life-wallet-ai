# 本地前端依赖

以下文件随项目一起发布，避免 CDN 不可访问导致登录页失去样式或崩溃：

- `tailwindcss.js`
  - 来源：https://cdn.tailwindcss.com
  - 用途：Tailwind CSS Play CDN 浏览器运行时
  - 许可：MIT
- `crypto-js.min.js`
  - 来源：https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/crypto-js.min.js
  - 用途：非 HTTPS 局域网环境下的 PBKDF2-SHA256 兼容实现
  - 许可：MIT
- `password-worker.js`
  - 项目内代码
  - 用途：在 Web Worker 中执行 PBKDF2，避免阻塞登录界面

正式公网部署仍建议使用 HTTPS；安全上下文下会优先使用浏览器原生 Web Crypto。
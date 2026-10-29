/*
 * 部署配置：
 * - 如果 Flask 页面和 API 同源部署，保持 apiBaseUrl 为空。
 * - 如果 GitHub Pages 只托管静态页面，将其改为 Render 后端地址，例如：
 *   apiBaseUrl: "https://your-service.onrender.com"
 * 终端用户不需要修改此文件。
 */
window.LIFE_WALLET_CONFIG = {
  apiBaseUrl: ""
};

#!/usr/bin/env node
/**
 * 腾讯云 CloudBase Run 部署脚本。
 *
 * 使用前：
 *   1. 安装官方 CLI：npm install -g @cloudbase/cli
 *   2. 登录：tcb login --intl false
 *   3. 运行：node deploy-cloudbase.js <CloudBase环境ID>
 *
 * 脚本从项目根目录 .env 读取 DEEPSEEK_API_KEY，不会把密钥写入源码。
 */
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = __dirname;
const envId = process.argv[2] || process.env.CLOUDBASE_ENV_ID;
if (!envId) {
  console.error("Usage: node deploy-cloudbase.js <CloudBase env id>");
  process.exit(1);
}

const envPath = path.join(root, ".env");
if (!fs.existsSync(envPath)) {
  console.error(".env not found. Copy .env.example to .env and configure DEEPSEEK_API_KEY.");
  process.exit(1);
}

const envText = fs.readFileSync(envPath, "utf8");
const keyLine = envText.split(/\r?\n/).find((line) => line.startsWith("DEEPSEEK_API_KEY="));
if (!keyLine) {
  console.error("DEEPSEEK_API_KEY missing from .env");
  process.exit(1);
}
const apiKey = keyLine.slice(keyLine.indexOf("=") + 1).trim().replace(/^["']|["']$/g, "");
if (!apiKey) {
  console.error("DEEPSEEK_API_KEY is empty");
  process.exit(1);
}

const envParams = JSON.stringify({
  LLM_PROVIDER: "deepseek",
  DEEPSEEK_API_KEY: apiKey,
  DEEPSEEK_BASE_URL: "https://api.deepseek.com",
  DEEPSEEK_MODEL: "deepseek-flash",
  DEEPSEEK_KEEPALIVE_ENABLED: "true",
  DEEPSEEK_HEARTBEAT_SECONDS: "30",
  DEEPSEEK_RECONNECT_SECONDS: "5",
  ALLOW_LOCAL_FALLBACK: "false",
  PORT: "5000"
});

const tcbCommand = process.platform === "win32" ? "tcb.cmd" : "tcb";
const args = [
  "-e", envId,
  "cloudrun", "deploy",
  "--service-name", "life-wallet-ai",
  "--source", root,
  "--port", "5000",
  "--min-num", "1",
  "--max-num", "2",
  "--open-access-types", "PUBLIC",
  "--env-params", envParams,
  "--wait",
  "--force"
];

console.log("Deploying to Tencent CloudBase Run...");
const result = spawnSync(tcbCommand, args, {
  cwd: root,
  stdio: "inherit",
  shell: process.platform === "win32",
  env: process.env
});

if (result.error) {
  console.error(result.error);
  process.exit(1);
}
process.exit(result.status ?? 1);
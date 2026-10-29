# 全场景生活消费决策智能体

> 智能咨询固定使用 DeepSeek。GitHub Pages 只能托管静态页面，不能提供 DeepSeek 后端，请按本文档部署 Flask 服务。

## 项目简介

全场景生活消费决策智能体是面向个人与家庭生活消费场景的 AI Agent 应用。项目通过自然语言理解、DeepSeek Function Calling（OpenAI 兼容接口）、多平台商品与服务检索、优惠规则计算和预算分析，为用户生成可解释、可执行、可复盘的消费方案。

主要功能：

- 登录与注册：通过网址进入后必须先登录，支持个人账号；HTTPS 使用 Web Crypto，局域网 HTTP 自动使用 Web Worker 兼容模式
- 账号数据隔离：不同账号的预算、消费记录、复盘数据和对话分别保存
- 我的页面：展示昵称、邮箱、账号编号、注册与更新时间，并可修改昵称、查看预算/消费/咨询概览和退出登录
- 退出与恢复：退出登录不会删除个人数据，重新登录后自动恢复
- 全场景咨询：覆盖餐饮美食、商超日用、家居生活、数码家电、服饰鞋包、健康医疗、交通出行、教育学习、文体娱乐、亲子宠物、旅游住宿、本地服务和礼品文创等场景
- 组合场景规划：支持家庭采购、周末出游、租房改善、健康关怀、通勤出行、约会亲子和送礼等跨品类需求
- 智能咨询：多问题自动拆解并逐条回答、信息不足时先给带假设方案、不同问题生成差异化方案、多轮方案修改
- Function Calling：自主调用商品搜索、优惠计算和预算分配工具
- 多平台比价：模拟淘宝、拼多多、京东、美团、携程等平台商品、服务及优惠
- 优惠计算：匹配最优满减、会员权益、平台优惠和凑单方案
- 预算管理：按月/周独立设置预算，支持历史月份与周度切换、消费记录、剩余额度与超支提醒
- 消费复盘：与预算管理同步，支持当月、本周及历史月份/周度的分类结构、预算总结和消费优化建议
- 本地持久化：账号及个人数据按用户隔离保存在当前浏览器 LocalStorage
- 本地静态资源：Tailwind 和 CryptoJS 随项目发布，不依赖外部 CDN，避免网络波动导致页面崩溃
- 网址分享：Flask 同源托管页面与接口，支持一键复制网址、局域网访问和 Render/Docker 公网部署
- DeepSeek 常驻：服务启动后自动建立连接并每 30 秒心跳保活，断线自动重连；用户登录后可直接咨询，无需手动连接或等待

## 推荐使用方式：启动 Flask + DeepSeek

1. 双击 `setup.bat` 初始化 Python 虚拟环境。
2. 在 `.env` 中填写有效的 `DEEPSEEK_API_KEY`，保持 `LLM_PROVIDER=deepseek`。
3. 双击 `start.bat` 启动服务。
4. 浏览器访问 `http://127.0.0.1:5000`。服务端会在后台自动完成 DeepSeek 预热和保活，登录后即可直接提问。

智能咨询默认不允许静默降级到本地规则引擎。只有服务端显式设置 `ALLOW_LOCAL_FALLBACK=true` 时，才会在 DeepSeek 后端不可用时启用本地应急引擎。

## 通过网址分享

项目现在由 Flask 同时托管前端页面和后端接口。部署或启动后，其他人只需在浏览器中打开一个网址即可使用，无需下载项目或配置 Python。

### 方式一：同一局域网分享

1. 双击 `start.bat` 启动网页服务。
2. 本机访问：`http://127.0.0.1:5000`
3. 终端会同时显示类似下面的局域网地址：

```text
局域网分享：http://192.168.1.100:5000
```

4. 同一 Wi-Fi 或局域网内的其他设备打开该地址即可访问。
5. 如果其他设备无法访问，请允许 Windows 防火墙放行 Python 或 5000 端口。

局域网地址仅适用于同一网络。要分享给互联网上的其他人，请使用下面的公网部署方式。

### 方式二：Render 公网部署并生成 HTTPS 网址

项目已提供 `render.yaml`，可直接使用 Render Blueprint 部署。公开仓库可从这里开始：[一键部署到 Render](https://render.com/deploy?repo=https://github.com/shy194376/life-wallet-ai)。

1. 将整个项目上传到 GitHub 仓库。
2. 登录 Render，选择 **New → Blueprint**，连接该项目仓库。
3. Render 会自动读取 `render.yaml`。
4. 在环境变量中填写 `DEEPSEEK_API_KEY`；`DEEPSEEK_BASE_URL` 和 `DEEPSEEK_MODEL` 默认已配置。
5. 点击部署，等待构建完成。
6. Render 会生成类似下面的公网地址：

```text
https://life-wallet-ai.onrender.com
```

7. 将网址发送给其他人即可直接访问。页面右上角的“分享网址”按钮可一键复制当前公网地址。

`render.yaml` 默认使用 `starter` 实例，避免免费实例因长时间无人访问而休眠。Render 使用 `/ready` 作为健康检查；DeepSeek 未连通时部署会被判定为未就绪。

### 方式三：GitHub Pages 静态页面 + Render 后端

如果希望继续使用 GitHub Pages 公网地址，可让静态页面连接 Render 后端：

1. 先按上面的方式部署 Render 服务并获得 HTTPS 地址。
2. 修改 `runtime-config.js`：

```javascript
window.LIFE_WALLET_CONFIG = {
  apiBaseUrl: "https://你的服务名.onrender.com"
};
```

3. 提交并部署 GitHub Pages。终端用户只需打开网址，无需填写任何接口地址。

### 方式四：Docker 部署

```bash
docker build -t life-wallet-ai .
docker run --rm -p 5000:5000 --env-file .env life-wallet-ai
```

打开 `http://127.0.0.1:5000` 即可访问。Docker 镜像可继续部署到支持容器的云平台。

> 网页访问模式下，前端会自动使用同源接口；静态页面也可通过 `runtime-config.js` 固定后端地址，终端用户无需配置。

## 长期可用与数据保存

- 服务启动后后台自动连接 DeepSeek，30 秒心跳保活，断线自动重连。
- `render.yaml` 使用 `starter` 常驻实例，适合需要随时通过网址进入的场景。
- 注册账号、预算、消费记录、复盘数据和对话保存在当前浏览器 LocalStorage。
- 每次写入预算、消费记录、对话或账号数据前，都会保留上一份有效快照；当前数据损坏时自动恢复备份。\n- “我的”页面支持导出和导入当前账号的数据备份，可用于长期保存或迁移。
- 页面会申请浏览器持久化存储，降低长期未使用后数据被自动清理的概率。
- Service Worker 缓存页面、Tailwind、CryptoJS 和密码 Worker；网络短暂中断时页面仍能完整打开，恢复网络后自动重连 DeepSeek。
- 若浏览器主动清除站点数据，本地账号和数据仍会删除，这是浏览器安全机制，应用无法阻止。

## 项目结构

```text
人工智能大赛/
├── app.py
├── index.html
├── runtime-config.js
├── sw.js
├── manifest.webmanifest
├── assets/
│   ├── tailwindcss.js
│   ├── crypto-js.min.js
│   ├── password-worker.js
│   └── app-icon.svg
├── tests/
│   └── test_deepseek_resident.py
├── requirements.txt
├── .env.example
├── setup.bat
├── start.bat
├── requirements-deploy.txt
├── render.yaml
├── Procfile
├── Dockerfile
├── .dockerignore
├── README.md
├── data/
│   ├── products.json
│   ├── discount_rules.json
│   ├── mock_merchants.py
│   └── __init__.py
├── services/
│   ├── agent_service.py
│   ├── consumption_service.py
│   └── __init__.py
└── utils/
    ├── agent_tools.py
    ├── env_utils.py
    └── __init__.py
```

## 环境要求

### 运行智能咨询

- Windows 10 或 Windows 11
- 新版 Chrome 或 Microsoft Edge
- Python 3.9 或更高版本
- 可访问 DeepSeek API 的网络环境
- 有效的 DeepSeek API Key

安装 Python 时请勾选：

```text
Add Python to PATH
```

## 启动 DeepSeek 后端

### 后端第一步：运行 setup.bat

双击项目根目录中的：

```text
setup.bat
```

脚本会自动完成：

1. 检测 Python 是否安装以及版本是否不低于 3.9
2. 创建 `venv` Python 虚拟环境
3. 激活虚拟环境并升级 pip
4. 优先使用清华镜像安装 `requirements.txt`
5. 在缺少 `.env` 时自动从 `.env.example` 复制
6. 自动打开记事本，提示填写 DeepSeek API Key

### 后端第二步：填写 DeepSeek API Key

在脚本自动打开的 `.env` 文件中填写：

```dotenv
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的真实DeepSeek_API_Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-flash
ALLOW_LOCAL_FALLBACK=false
```

保存并关闭记事本。

注意：

- 不要把真实密钥提交到 Git 仓库。
- `.env` 已加入 `.gitignore`。
- DeepSeek 使用 OpenAI 兼容协议，但默认地址固定为 `https://api.deepseek.com`。

### 后端第三步：运行 start.bat 并通过网址访问

双击：

```text
start.bat
```

终端标题会显示：

```text
全场景生活消费决策智能体 - 网页服务
```

后端启动地址：

```text
http://127.0.0.1:5000
```

看到服务启动信息后，在浏览器中打开：

```text
http://127.0.0.1:5000
```

页面会自动使用当前网站地址作为后端接口，无需再单独双击 `index.html`。

## 后端接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/`、`/index.html` | 直接返回完整网页 |
| GET | `/health` | 运行状态、服务器时间、访问地址和 DeepSeek 配置状态 |
| GET | `/ready` | DeepSeek 常驻连接检查；未就绪返回 HTTP 503 |
| GET | `/sw.js` | 页面缓存与断网恢复 Service Worker |
| GET | `/manifest.webmanifest` | PWA 安装清单 |
| GET | `/runtime-config.js` | 静态页面使用的后端地址配置 |
| GET | `/api/merchants` | 生活消费商户筛选 |
| POST | `/api/recommendations` | 基础预算推荐 |
| POST | `/api/chat` | 智能体对话接口 |
| POST | `/api/agent/chat` | 智能体对话接口别名 |

`/api/chat` 和 `/api/agent/chat` 使用同一套 Agent 逻辑，两个接口都会保留。

## 配置说明

`.env.example` 内容如下（云端平台会自动注入 `PORT`，本地无需设置）：

```dotenv
# 使用说明：
# 1. 复制本文件为 .env；
# 2. 将 DEEPSEEK_API_KEY 替换为用户自己的 DeepSeek API Key；
# 3. 修改完成后保存，并重新运行 start.bat。

LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-flash

# 启动后自动连接、定时心跳并断线重连。
DEEPSEEK_KEEPALIVE_ENABLED=true
DEEPSEEK_HEARTBEAT_SECONDS=30
DEEPSEEK_RECONNECT_SECONDS=5

# 默认禁止静默降级，确保智能咨询始终由 DeepSeek 提供。
ALLOW_LOCAL_FALLBACK=false

# 云平台会自动注入 PORT；本地默认使用 5000。
# PORT=5000
```

后端启动后访问以下地址验证：

```text
http://127.0.0.1:5000/health
```

重点检查：

- `status` 是否为 `ok`
- `server_time` 是否随重启变化
- `config_status.deepseek_connected` 是否为 `true`
- `config_status.deepseek_connecting` 是否为 `false`
- `config_status.deepseek_last_success_at` 是否持续更新
- `config_status.deepseek_resident` 是否为 `true`
- `config_status.llm_ready` 是否为 `true`
- `config_status.local_fallback_enabled` 是否为 `false`
- `config_status.cors_enabled` 是否为 `true`

同时访问 `http://127.0.0.1:5000/ready`；DeepSeek 正常时应返回 HTTP 200。

## 常见问题排查

### 1. 登录失败或提示账号不存在

- 账号只保存在注册时的浏览器和访问地址中。`127.0.0.1`、`localhost`、局域网 IP 和公网域名属于不同存储空间，不能混用登录。
- 通过局域网 `http://IP:5000` 访问时，页面会提示使用兼容加密模式，并通过本地 Web Worker 完成 PBKDF2 密码哈希。
- 如果浏览器清除了站点数据，本地账号也会被清除，需要重新注册。
- 若原账号仍无法登录，请按 F12 查看 Console 中的具体错误，不要同时打开多个使用不同地址的页面。

### 2. 页面无样式或提示 `tailwind is not defined`

项目已将 Tailwind 和 CryptoJS 放入 `assets/` 目录，不再依赖 CDN。若仍出现该错误，请确认以下文件存在并返回 HTTP 200：

```text
/assets/tailwindcss.js
/assets/crypto-js.min.js
/assets/password-worker.js
```

### 3. 提示“后端服务未启动，请先运行 start.bat”

可能原因：

- 没有运行 `start.bat`
- 后端窗口已经关闭
- Python 启动失败
- 5000 端口被其他程序占用

解决方法：

1. 确认 `start.bat` 窗口仍在运行。
2. 访问 `http://127.0.0.1:5000/health`。
3. 如果健康检查无法打开，重新运行 `start.bat`。
4. 查看后端终端中的完整报错。
5. 如果提示端口占用，关闭占用 5000 端口的程序后重试。

### 4. 提示“跨域配置异常，请检查后端 CORS 设置并重启服务”

可能原因：

- 后端仍未重启，旧 CORS 配置未生效
- 使用了非项目提供的 `app.py`
- 浏览器缓存了旧页面

解决方法：

1. 关闭后端窗口。
2. 重新运行 `start.bat`。
3. 在浏览器中按 `Ctrl + F5` 强制刷新。
4. 确认 `app.py` 中存在全局 `CORS(...)` 配置。
5. 确认使用的是 `flask-cors==4.0.0`。

### 5. 提示“接口路径不匹配，请检查前后端路由是否一致”

可能原因：

- 前端请求地址不是 `/api/agent/chat` 或 `/api/chat`
- 后端代码不是最新版本
- 自定义代理或反向代理路径错误

解决方法：

1. 确认前端 `API_ENDPOINTS.chat` 为 `/api/agent/chat`。
2. 确认 `app.py` 包含：

```python
@flask_app.post("/api/agent/chat")
@flask_app.post("/api/chat")
def chat_with_agent():
    ...
```

3. 重启后端并强制刷新浏览器。

### 6. 提示“后端服务内部错误，请查看终端报错信息”

可能原因：

- DeepSeek API Key 无效
- `DEEPSEEK_BASE_URL` 或 `DEEPSEEK_MODEL` 配置错误
- 网络无法访问 DeepSeek
- DeepSeek 账户余额或模型权限不可用
- Python 依赖损坏

解决方法：

1. 查看 `start.bat` 后端窗口中的完整堆栈。
2. 访问 `/health` 检查 Key 是否配置成功。
3. 检查 `.env` 中是否存在空格、引号或错误字符。
4. 确认 DeepSeek 账户可访问 `DEEPSEEK_MODEL` 指定的模型（默认 `deepseek-flash`）。
5. 重新运行 `setup.bat` 修复依赖。

### Python 未检测到

重新安装 Python 3.9 或更高版本，并勾选 `Add Python to PATH`。

### 清华镜像安装失败

`setup.bat` 会自动尝试默认 PyPI 源。如果仍然失败，请检查网络、代理或防火墙设置。

### 浏览器直接打开 index.html 后仍然无法请求

项目后端 CORS 已允许：

- 所有来源
- 所有方法
- 所有请求头
- `supports_credentials=False`

因此 `file://` 页面可以直接请求后端。若仍失败，请确认后端窗口正在运行，并检查浏览器控制台中的真实 HTTP 状态码。

## 技术栈

- Python Flask 2.3.0
- flask-cors 4.0.0
- OpenAI Python SDK 1.3.0（用于调用 DeepSeek OpenAI 兼容接口）
- python-dotenv 1.0.0
- HTML5
- Tailwind CSS
- 原生 JavaScript
- LocalStorage
- Canvas

## 说明

本项目中的商品、服务、价格、优惠规则和商户均为模拟数据，仅用于功能体验，不代表真实平台价格、库存、服务范围或实时优惠。
# 全场景生活消费决策智能体

## 项目简介

全场景生活消费决策智能体是面向全国人工智能应用创新大赛的 AI Agent 演示项目。项目以个人与家庭的真实生活消费场景为核心，通过自然语言理解、OpenAI Function Calling、多平台商品与服务检索、优惠规则计算和预算分析，为用户生成可解释、可执行、可复盘的消费方案。

主要功能：

- 全场景咨询：覆盖餐饮美食、商超日用、家居生活、数码家电、服饰鞋包、健康医疗、交通出行、教育学习、文体娱乐、亲子宠物、旅游住宿、本地服务和礼品文创等场景
- 组合场景规划：支持家庭采购、周末出游、租房改善、健康关怀、通勤出行、约会亲子和送礼等跨品类需求
- 智能咨询：自然语言需求理解、模糊需求主动追问、多轮方案修改
- Function Calling：自主调用商品搜索、优惠计算和预算分配工具
- 多平台比价：模拟淘宝、拼多多、京东、美团、携程等平台商品、服务及优惠
- 优惠计算：匹配最优满减、会员权益、平台优惠和凑单方案
- 预算管理：按月/周独立设置预算，支持历史月份与周度切换、消费记录、剩余额度与超支提醒
- 消费复盘：与预算管理同步，支持当月、本周及历史月份/周度的分类结构、预算总结和消费优化建议
- 本地持久化：对话历史、预算和消费记录保存在 LocalStorage
- 比赛演示：项目介绍弹窗、典型场景测试、默认月度演示数据
- 网址分享：Flask 同源托管页面与接口，支持一键复制网址、局域网访问和 Render/Docker 公网部署
- 零配置运行：直接打开 `index.html` 即可使用内置本地演示 Agent

## 最快使用方式：无需部署

直接双击项目根目录中的：

```text
index.html
```

页面会自动启用“本地演示模式”，无需安装 Python、无需运行 Flask、无需填写 OpenAI API Key。内置生活消费商品、服务、优惠规则、组合场景算法、对话追问和方案修改均在浏览器本地完成。

完整 Flask + OpenAI Agent 后端仍然保留，可在需要真实模型能力时选择性启动。启动 Flask 后可直接通过 `http://127.0.0.1:5000` 使用完整页面，无需再单独打开 `index.html`。

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

项目已提供 `render.yaml`，可直接使用 Render Blueprint 部署：

1. 将整个项目上传到 GitHub 仓库。
2. 登录 Render，选择 **New → Blueprint**，连接该项目仓库。
3. Render 会自动读取 `render.yaml`。
4. 在环境变量中填写 `OPENAI_API_KEY`；`OPENAI_BASE_URL` 默认已配置。
5. 点击部署，等待构建完成。
6. Render 会生成类似下面的公网地址：

```text
https://life-wallet-ai.onrender.com
```

7. 将网址发送给其他人即可直接访问。页面右上角的“分享网址”按钮可一键复制当前公网地址。

即使暂未配置 `OPENAI_API_KEY`，部署后的页面仍可使用内置本地演示 Agent；配置密钥后可使用完整大模型 Agent 能力。

### 方式三：Docker 部署

```bash
docker build -t life-wallet-ai .
docker run --rm -p 5000:5000 --env-file .env life-wallet-ai
```

打开 `http://127.0.0.1:5000` 即可访问。Docker 镜像可继续部署到支持容器的云平台。

> 网页访问模式下，前端会自动使用当前网站的同源接口，无需手动填写 `127.0.0.1:5000`。

## 项目结构

```text
人工智能大赛/
├── app.py
├── index.html
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

### 直接使用 `index.html`

- Windows 10 或 Windows 11
- 新版 Chrome 或 Microsoft Edge
- 访问 Tailwind CSS CDN 的网络环境
- 不需要 Python、虚拟环境或 OpenAI API Key

### 可选：启动完整后端

- Python 3.9 或更高版本
- 可访问 OpenAI API 的网络环境
- 有效的 OpenAI API Key

安装 Python 时请勾选：

```text
Add Python to PATH
```

## 可选：启动完整后端模式

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
6. 自动打开记事本，提示填写 OpenAI API Key

### 后端第二步：填写 OpenAI API Key

在脚本自动打开的 `.env` 文件中填写：

```dotenv
OPENAI_API_KEY=你的真实OpenAI_API_Key
OPENAI_BASE_URL=https://api.openai.com/v1
```

保存并关闭记事本。

注意：

- 不要把真实密钥提交到 Git 仓库。
- `.env` 已加入 `.gitignore`。
- 如果使用兼容 OpenAI 协议的服务，可修改 `OPENAI_BASE_URL`。

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
| GET | `/health` | 健康检查、服务器时间、访问地址和配置状态 |
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
# 2. 将 OPENAI_API_KEY 替换为用户自己的 OpenAI API Key；
# 3. 修改完成后保存，并重新运行 start.bat。

OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

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
- `config_status.openai_api_key_configured` 是否为 `true`
- `config_status.cors_enabled` 是否为 `true`

## 常见问题排查

### 1. 提示“后端服务未启动，请先运行 start.bat”

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

### 2. 提示“跨域配置异常，请检查后端 CORS 设置并重启服务”

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

### 3. 提示“接口路径不匹配，请检查前后端路由是否一致”

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

### 4. 提示“后端服务内部错误，请查看终端报错信息”

可能原因：

- OpenAI API Key 无效
- `OPENAI_BASE_URL` 配置错误
- 网络无法访问 OpenAI
- 模型或账户权限不可用
- Python 依赖损坏

解决方法：

1. 查看 `start.bat` 后端窗口中的完整堆栈。
2. 访问 `/health` 检查 Key 是否配置成功。
3. 检查 `.env` 中是否存在空格、引号或错误字符。
4. 确认账户可访问 `gpt-3.5-turbo-1106`。
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
- OpenAI Python SDK 1.3.0
- python-dotenv 1.0.0
- HTML5
- Tailwind CSS
- 原生 JavaScript
- LocalStorage
- Canvas

## 说明

本项目中的商品、服务、价格、优惠规则、商户和演示消费记录均为模拟数据，仅用于比赛展示和功能演示，不代表真实平台价格、库存、服务范围或实时优惠。
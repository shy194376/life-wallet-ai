# 全场景生活消费决策智能体 - 完整源码

> 自动生成时间：2026-10-27 22:33:53
>
> 本文件汇总当前项目主要源码、云端部署配置和运行文档，便于比赛提交与审阅。

## 1. requirements.txt

````text
# Web 框架：比赛演示固定版本。
Flask==2.3.0

# 全局跨域支持，允许 file:// 前端页面访问后端。
flask-cors==4.0.0

# OpenAI 官方 Python SDK，提供 Chat Completions 与 Function Calling。
openai==1.3.0

# 在 Flask 实例创建前加载 .env 配置。
python-dotenv==1.0.0

# 兼容 Flask 2.3.x，避免自动安装 Werkzeug 3 后出现运行异常。
Werkzeug==2.3.8

# openai 1.3.0 与 httpx 0.28+ 存在代理参数兼容问题，固定到兼容版本。
httpx==0.27.2
````


## 2. requirements-deploy.txt

````text
# 生产环境 WSGI 服务器，仅用于 Linux 容器或云平台部署。
# Windows 本地环境继续使用 python app.py，不需要安装本文件。
gunicorn==23.0.0
````


## 3. .env.example

````dotenv
# 使用说明：
# 1. 复制本文件为 .env；
# 2. 将 OPENAI_API_KEY 替换为用户自己的 OpenAI API Key；
# 3. 修改完成后保存，并重新运行 start.bat。

# OpenAI API 密钥。请勿将真实密钥提交到代码仓库。
OPENAI_API_KEY=your_openai_api_key_here

# OpenAI 兼容接口地址，默认使用官方接口。
OPENAI_BASE_URL=https://api.openai.com/v1

# 云平台会自动注入 PORT；本地默认使用 5000。
# PORT=5000
````


## 4. render.yaml

````yaml
services:
  - type: web
    name: life-wallet-ai
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt -r requirements-deploy.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
    healthCheckPath: /health
    autoDeploy: true
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: OPENAI_API_KEY
        sync: false
      - key: OPENAI_BASE_URL
        value: https://api.openai.com/v1
````


## 5. Procfile

````text
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
````


## 6. Dockerfile

````dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /app

COPY requirements.txt requirements-deploy.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-deploy.txt

COPY . .

EXPOSE 5000

CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 4 --timeout 120"]
````


## 7. .dockerignore

````text
.env
.env.*
!.env.example
venv/
.venv/
__pycache__/
*.py[cod]
.git/
.pytest_cache/
tmp/
output/
Thumbs.db
.DS_Store
````


## 8. setup.bat

````bat
@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo   全场景生活消费决策智能体 - 环境初始化
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [错误] 未检测到 Python，请先安装 Python 3.9 或更高版本。
        echo 下载地址：https://www.python.org/downloads/
        echo 安装时请勾选 Add Python to PATH。
        echo.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)

echo [1/5] 正在检查 Python 版本...
%PYTHON_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)"
if errorlevel 1 (
    echo [错误] 当前 Python 版本低于 3.9，请升级后重试。
    pause
    exit /b 1
)
echo Python 检查通过。
echo.

echo [2/5] 正在创建 Python 虚拟环境 venv...
if not exist "venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败，请检查 Python 安装是否完整。
        pause
        exit /b 1
    )
) else (
    echo 已检测到 venv，跳过创建。
)

echo.
echo [3/5] 正在激活虚拟环境并升级 pip...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [错误] 虚拟环境激活失败。
    pause
    exit /b 1
)

python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [提示] 清华镜像升级 pip 失败，尝试使用默认源...
    python -m pip install --upgrade pip
    if errorlevel 1 (
        echo [错误] pip 升级失败，请检查网络连接。
        pause
        exit /b 1
    )
)

echo.
echo [4/5] 正在使用清华镜像安装 requirements.txt...
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [提示] 清华镜像安装失败，尝试使用默认源...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络连接或 requirements.txt。
        pause
        exit /b 1
    )
)

echo.
echo [5/5] 正在检查 .env 配置文件...
if not exist ".env" (
    copy /Y ".env.example" ".env" >nul
    if errorlevel 1 (
        echo [错误] 无法创建 .env 文件。
        pause
        exit /b 1
    )
    echo 已根据 .env.example 创建 .env。
    echo 即将打开记事本，请填写 OPENAI_API_KEY 后保存并关闭记事本。
    start "" notepad ".env"
) else (
    echo 已检测到 .env，跳过复制。
)

echo.
echo ============================================================
echo   环境初始化完成
echo ============================================================
echo 请确认 .env 中已经填写自己的 OPENAI_API_KEY。
echo 然后双击运行 start.bat 启动后端服务。
echo 后端启动后，再双击打开 index.html 即可使用。
echo ============================================================
echo.
pause
endlocal
````


## 9. start.bat

````bat
@echo off
chcp 65001 >nul
setlocal EnableExtensions
title 全场景生活消费决策智能体 - 网页服务
cd /d "%~dp0"

echo ============================================================
echo   全场景生活消费决策智能体 - 网页服务
echo ============================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [错误] 未检测到虚拟环境，请先双击运行 setup.bat。
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [提示] 未检测到 .env 配置文件，将使用本地演示模式启动。
    echo 如需连接真实大模型，请先运行 setup.bat 并填写 OPENAI_API_KEY。
    echo.
)

call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [错误] 虚拟环境激活失败，请重新运行 setup.bat。
    echo.
    pause
    exit /b 1
)

set "LAN_IP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do set "LAN_IP=%%a"
set "LAN_IP=%LAN_IP: =%"

echo 正在启动网页服务...
echo 本机访问：http://127.0.0.1:5000
if defined LAN_IP echo 局域网分享：http://%LAN_IP%:5000
echo 公网分享：完成云端部署后使用平台生成的 HTTPS 地址
echo 健康检查：http://127.0.0.1:5000/health
echo 按 Ctrl + C 可停止服务。
echo.

python app.py

echo.
echo ============================================================
echo 后端服务已退出，请查看上方错误信息（如有）。
echo ============================================================
pause
endlocal
````


## 10. app.py

````python
"""
全场景生活消费决策智能体 - Flask 主程序入口。

本模块负责：
1. 创建并配置 Flask 应用；
2. 加载项目根目录下的 .env 环境变量；
3. 启用跨域访问；
4. 在根路径直接提供前端页面，实现一个网址同时访问页面和接口；
5. 注册健康检查、基础业务接口和智能体对话接口；
6. 提供本地开发与云端部署环境下的服务启动入口。

运行方式：
    python app.py
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Union

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, HTTPException

from services.agent_service import AgentServiceError, run_agent
from services.consumption_service import list_merchants, recommend_consumption
from utils.env_utils import get_env

# 必须在 Flask 应用创建前加载 .env。
# load_dotenv 默认不覆盖系统中已经存在的环境变量，便于部署平台注入配置。
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE_PATH = BASE_DIR / ".env"
ENV_FILE_LOADED = load_dotenv(dotenv_path=ENV_FILE_PATH, override=False)


def create_app() -> Flask:
    """创建并返回完成配置的 Flask 应用实例。

    使用应用工厂模式可以避免测试代码与生产入口共享全局状态，
    也方便后续扩展数据库、日志和蓝图等组件。
    """

    flask_app = Flask(__name__)

    # 关闭 JSON 的 ASCII 转义，使接口中的中文在调试时保持可读。
    flask_app.json.ensure_ascii = False

    # 全局允许所有来源、方法和请求头，确保通过 file:// 打开前端页面时也可正常请求。
    CORS(
        flask_app,
        resources={r"/*": {"origins": "*"}},
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        supports_credentials=False,
        send_wildcard=True,
    )

    @flask_app.before_request
    def validate_api_json_request():
        """统一校验所有写接口的 Content-Type 和 JSON 语法。"""

        if (
            request.method in {"POST", "PUT", "PATCH"}
            and request.path.startswith("/api/")
        ):
            if not request.is_json:
                raise BadRequest("Content-Type 必须为 application/json")
            # 主动触发解析；非法 JSON 会抛出 BadRequest，由统一处理器返回 400。
            request.get_json()

    @flask_app.errorhandler(BadRequest)
    def handle_bad_request(error):
        """统一处理 /api/ 路由的非法 JSON、空请求体和 Content-Type 错误。"""

        if request.path.startswith("/api/"):
            flask_app.logger.warning(
                "API 请求参数错误：%s %s - %s",
                request.method,
                request.path,
                error.description,
            )
            return (
                jsonify(
                    {
                        "status": 400,
                        "error": "bad_request",
                        "message": "请求体不是合法 JSON 或 Content-Type 不正确。",
                        "detail": error.description,
                    }
                ),
                400,
            )
        return error

    @flask_app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """为 /api/ 路由统一返回 JSON 格式的 HTTP 错误。"""

        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "status": error.code,
                        "error": error.name.lower().replace(" ", "_"),
                        "message": error.description,
                    }
                ),
                error.code,
            )
        return error

    @flask_app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        """捕获未处理异常，打印完整堆栈并统一返回 500。"""

        flask_app.logger.exception(
            "服务器内部异常：%s %s",
            request.method,
            request.path,
        )
        return (
            jsonify(
                {
                    "status": 500,
                    "error": "internal_server_error",
                    "message": "服务器内部异常，请查看后端控制台日志。",
                }
            ),
            500,
        )

    @flask_app.get("/")
    @flask_app.get("/index.html")
    def serve_frontend():
        """直接返回前端页面，使部署后的访问地址同时承载页面和 API。"""

        response = send_from_directory(BASE_DIR, "index.html", mimetype="text/html")
        # 发布新版本后避免浏览器长期缓存旧页面。
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

    @flask_app.get("/health")
    def health_check():
        """返回服务健康状态、服务器时间和关键配置状态。"""

        openai_key_configured = bool(os.getenv("OPENAI_API_KEY", "").strip())
        return jsonify(
            {
                "status": "ok",
                "msg": "全场景生活消费Agent服务运行中",
                "app_url": request.host_url.rstrip("/"),
                "server_time": datetime.now().astimezone().isoformat(timespec="seconds"),
                "config_status": {
                    "openai_api_key_configured": openai_key_configured,
                    "env_file_loaded": bool(ENV_FILE_LOADED),
                    "cors_enabled": True,
                    "cors_origins": "*",
                    "supports_credentials": False,
                    "debug_mode": False,
                    "host": "0.0.0.0",
                    "port": int(os.getenv("PORT", "5000")),
                },
            }
        )

    @flask_app.get("/api/merchants")
    def get_merchants():
        """查询生活消费商户模拟数据，可按分类进行筛选。

        查询参数：
            category：可选，商户分类，例如“餐饮美食”“本地服务”。
        """

        # 去掉前后空格；空字符串视为未传分类。
        category = request.args.get("category")
        if category is not None:
            category = category.strip() or None

        merchant_list = list_merchants(category=category)
        return jsonify(
            {
                "code": 0,
                "message": "商户列表获取成功",
                "data": merchant_list,
            }
        )

    @flask_app.post("/api/recommendations")
    def get_recommendations():
        """根据预算和分类生成基础消费推荐。

        请求体示例：
            {"budget": 200, "category": "餐饮美食", "limit": 3}
        """

        # silent=True 可以避免请求体不是合法 JSON 时直接抛出框架异常。
        request_payload = request.get_json()
        if not isinstance(request_payload, dict):
            return jsonify({"code": 400, "message": "请求体必须是 JSON 对象"}), 400

        # 读取并转换请求参数；具体业务范围由服务层统一校验。
        try:
            budget = float(request_payload.get("budget"))
            category = request_payload.get("category")
            limit = int(request_payload.get("limit", 3))
            recommendations = recommend_consumption(
                budget=budget,
                category=category,
                limit=limit,
            )
        except (TypeError, ValueError) as error:
            raise BadRequest(str(error)) from error

        return jsonify(
            {
                "code": 0,
                "message": "消费推荐生成成功",
                "data": recommendations,
            }
        )

    @flask_app.post("/api/agent/chat")
    @flask_app.post("/api/chat")
    def chat_with_agent():
        """接收自然语言消费需求并返回智能体结构化方案。

        请求体：
            {
                "user_input": "再便宜一点",
                "history": [
                    {"role": "user", "content": "200元以内买耳机"},
                    {"role": "assistant", "content": "上一轮方案摘要"}
                ]
            }

        成功响应：
            {
                "answer": "自然语言方案总结",
                "plans": [...],
                "requires_input": False,
                "suggested_replies": [],
                "used_tools": ["search_products", "calculate_discount"]
            }
        """

        request_payload = request.get_json()
        if not isinstance(request_payload, dict):
            return (
                jsonify(
                    {
                        "answer": "请求体必须是 JSON 对象，并包含 user_input 字段。",
                        "plans": [],
                        "requires_input": False,
                        "suggested_replies": [],
                        "used_tools": [],
                    }
                ),
                400,
            )

        user_input = request_payload.get("user_input")
        if not isinstance(user_input, str) or not user_input.strip():
            return (
                jsonify(
                    {
                        "answer": "请输入具体的消费需求，例如选购商品、规划预算或安排一次生活消费。",
                        "plans": [],
                        "requires_input": True,
                        "suggested_replies": ["帮我规划本月家庭预算", "1000元安排一次周末周边游"],
                        "used_tools": [],
                    }
                ),
                400,
            )

        history = request_payload.get("history", [])
        if history is None:
            history = []
        if not isinstance(history, list):
            return (
                jsonify(
                    {
                        "answer": "history 必须是对话消息数组。",
                        "plans": [],
                        "requires_input": False,
                        "suggested_replies": [],
                        "used_tools": [],
                    }
                ),
                400,
            )

        try:
            # 所有需求拆解、工具选择和方案生成逻辑均封装在服务层。
            agent_result = run_agent(user_input, history=history)
        except AgentServiceError as error:
            # 业务异常只返回面向用户的友好提示，不暴露密钥或 API 内部信息。
            flask_app.logger.warning("智能体请求失败：%s", error)
            return (
                jsonify(
                    {
                        "answer": error.user_message,
                        "plans": [],
                        "requires_input": False,
                        "suggested_replies": [],
                        "used_tools": error.used_tools,
                    }
                ),
                error.status_code,
            )
        return jsonify(agent_result)

    return flask_app


# 暴露应用实例，便于 WSGI 服务器（例如 Gunicorn）通过 app:app 加载。
app = create_app()


if __name__ == "__main__":
    # 云平台通常会注入 PORT；本地默认仍使用 5000。
    server_port = int(os.getenv("PORT", "5000"))
    # 监听 0.0.0.0 便于本机、局域网和容器环境访问；比赛演示关闭 debug。
    app.run(host="0.0.0.0", port=server_port, debug=False)
````


## 11. services/__init__.py

````python
"""业务逻辑包。

对外暴露全生活消费推荐能力和 Agent 对话服务，入口层无需了解底层工具执行细节。
后续接入数据库、用户画像或更多工具时，可保持这里的公开接口稳定。
"""

from .agent_service import AgentServiceError, run_agent
from .consumption_service import list_merchants, recommend_consumption

__all__ = [
    "AgentServiceError",
    "list_merchants",
    "recommend_consumption",
    "run_agent",
]
````


## 12. services/agent_service.py

````python
"""全场景生活消费决策智能体核心服务。

Agent 决策流程：
1. 需求理解：模型从自然语言中提取品类、预算、场景、人数和偏好；
2. 工具规划：模型根据需求选择 search_products、calculate_discount
   或 budget_allocation；
3. 自主调用：本模块解析模型返回的 tool_calls，执行对应工具，并把结构化
   结果写回对话；
4. 多轮推理：模型可以基于工具结果继续调用其他工具，最多循环 6 轮；
5. 方案输出：模型输出包含 answer 和 plans 的 JSON，本模块校验并补充
   used_tools，最终返回给 Flask 接口。

API 调用采用 Chat Completions 的 tools/Function Calling 格式：
client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    temperature=0.3,
    tools=AGENT_TOOL_DEFINITIONS,
    tool_choice="auto",
    ...
)
"""

import json
import re
from typing import Any, Dict, List, Optional

from utils.agent_tools import AGENT_TOOL_DEFINITIONS, execute_agent_tool
from utils.env_utils import get_env, get_openai_api_key

# 用户明确指定的模型与采样参数，不在运行时替换成其他模型。
OPENAI_MODEL = "gpt-3.5-turbo-1106"
TEMPERATURE = 0.3
MAX_TOOL_ROUNDS = 6
MAX_USER_INPUT_LENGTH = 2000
MAX_HISTORY_MESSAGES = 12
MAX_HISTORY_CONTENT_LENGTH = 6000

# 系统提示词明确描述需求拆解、工具选择、方案约束和最终 JSON 格式。
SYSTEM_PROMPT = """
你是“全场景生活消费决策智能体”，面向个人、家庭、情侣、上班族、学生及其他普通消费者。你需要结合最近对话上下文，用中文帮助用户处理各类日常消费问题。

【场景覆盖】
可处理但不限于：
- 餐饮美食：三餐、外卖、聚餐、咖啡、生鲜、家庭食材；
- 商超日用与家居：日用品、家庭采购、厨房用品、家电、租房改善、乔迁；
- 数码与服饰：数码配件、小家电、通勤穿搭、鞋包；
- 健康与个护：健康用品、常备医疗物资、美妆洗护；
- 出行与旅行：通勤、打车、自驾、周边游、酒店、门票；
- 教育与娱乐：课程、图书、电影、健身、亲子活动；
- 宠物与本地服务：宠物用品、保洁、维修、搬家；
- 礼品与综合预算：送礼、节日、家庭月度预算、旅行预算和阶段性消费规划。

【需求理解】
从用户输入和历史对话中提取：
- 消费类型：单件购买、组合采购、服务预订、体验安排或预算规划；
- 品类/场景：餐饮美食、商超日用、家居生活、数码家电、服饰鞋包、健康医疗、交通出行、教育学习、文体娱乐、亲子宠物、旅游住宿、本地服务、礼品文创等；
- 预算：最低预算、最高预算、总预算；
- 时间与人数：个人、家庭、情侣、朋友、亲子，以及每周、每月、周末或一次性消费；
- 偏好与约束：性价比、品质、健康、实用、仪式感、距离、时间、忌口、品牌避雷等。

【追问原则】
1. 如果用户首次需求同时缺少预算和明确品类/场景，无法形成可执行方案，必须先追问，不要调用工具。
2. 追问要简短，最多提出 2 个最关键问题，优先询问预算和用途；多场景综合需求可先给预算框架。
3. 如果用户只缺少一项且可保守推断，可以直接给方案，并在 answer 中说明假设。
4. 历史对话中已经出现的信息不要重复询问。
5. 涉及医疗、用药、投资理财等专业风险时，只提供一般消费信息和预算建议，不作诊断、处方或收益承诺。

【工具与方案】
1. 购买实物商品：调用 search_products；跨多个品类时，按品类分别检索。
2. 本地服务、旅行或体验类消费：优先检索可用的商品/服务券，并结合 budget_allocation 拆分交通、住宿、餐饮、门票等预算。
3. 周预算、月预算、家庭预算、旅行预算或生活支出规划：调用 budget_allocation。
4. 已选出商品或服务后：调用 calculate_discount 计算平台优惠、会员权益、到手价和凑单空间。
5. 综合场景要覆盖用户真正关心的核心环节，不要只返回一件商品；预算规划类方案可以用“交通预算”“住宿预算”等预算项作为 plans.items。
6. 不得编造商品、价格、优惠、库存或商家规则；本地数据不足时明确说明可提供通用决策框架。
7. 优先给出 2 个差异化方案，数据不足时可给 1 个；total_price 必须与 items 的价格逻辑一致，且不得超出用户预算。

【方案修改】
1. 当用户说“再便宜一点”“换个方向”“预算降到100元”“住好一点”等，必须继承上一轮已确认的预算、场景、人数和偏好。
2. 只修改用户明确要求改变的部分，重新调用必要工具，不要从头重复询问。
3. 在 answer 中说明本次调整了什么，以及调整后的取舍。

【最终输出格式】
只输出一个合法 JSON 对象，不要输出 Markdown、代码围栏或额外解释：
{
  "answer": "自然语言总结；若需追问，这里就是追问内容",
  "plans": [],
  "requires_input": false,
  "suggested_replies": ["可选快捷回复1", "可选快捷回复2"]
}

需要追问时：
- requires_input 必须为 true；
- plans 必须为空数组；
- suggested_replies 提供 2-3 个简短可选回复。

生成方案时：
- requires_input 必须为 false；
- plans 中每个 item 必须包含 id、name、quantity、price 字段；
- total_price 使用数字，不要带货币符号。
"""


class AgentServiceError(RuntimeError):
    """Agent 服务可安全返回给接口调用方的业务异常。"""

    def __init__(
        self,
        user_message: str,
        status_code: int = 503,
        used_tools: Optional[List[str]] = None,
    ) -> None:
        super().__init__(user_message)
        self.user_message = user_message
        self.status_code = status_code
        self.used_tools = used_tools or []


def _create_openai_client() -> Any:
    """延迟创建 OpenAI 客户端，避免缺少密钥时影响 Flask 启动。"""

    try:
        from openai import OpenAI
    except ImportError as error:
        raise AgentServiceError(
            "智能体依赖尚未安装，请先执行 pip install -r requirements.txt。",
            status_code=503,
        ) from error

    try:
        api_key = get_openai_api_key()
    except RuntimeError as error:
        raise AgentServiceError(
            "智能体服务尚未配置 OPENAI_API_KEY，请在 .env 中填写密钥后重启服务。",
            status_code=503,
        ) from error

    # 支持通过环境变量切换兼容 OpenAI 协议的服务地址，默认使用 OpenAI 官方 API。
    base_url = get_env(
        "OPENAI_BASE_URL",
        "https://api.openai.com/v1",
    ).rstrip("/")

    # 超时和重试次数设置上限，避免单个 HTTP 请求长时间占用 Flask 工作线程。
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
        max_retries=1,
    )


def _extract_json_object(raw_content: str) -> Optional[Dict[str, Any]]:
    """从模型回复中提取 JSON 对象。

    正常情况下模型应直接返回 JSON；本函数仍兼容常见的 Markdown 代码围栏
    和前后附带说明文字的情况，以提高接口稳定性。
    """

    text = raw_content.strip()
    if not text:
        return None

    # 优先尝试直接解析完整内容。
    try:
        parsed_content = json.loads(text)
        return parsed_content if isinstance(parsed_content, dict) else None
    except json.JSONDecodeError:
        pass

    # 兼容 ```json ... ``` 代码围栏。
    fenced_blocks = re.findall(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL)
    for block in fenced_blocks:
        try:
            parsed_block = json.loads(block.strip())
            if isinstance(parsed_block, dict):
                return parsed_block
        except json.JSONDecodeError:
            continue

    # 最后尝试截取第一个左花括号到最后一个右花括号之间的内容。
    start_index = text.find("{")
    end_index = text.rfind("}")
    if start_index != -1 and end_index > start_index:
        try:
            parsed_object = json.loads(text[start_index : end_index + 1])
            return parsed_object if isinstance(parsed_object, dict) else None
        except json.JSONDecodeError:
            return None

    return None


def _normalize_price(value: Any) -> float:
    """把模型返回的价格转换为非负浮点数。"""

    if isinstance(value, str):
        value = value.replace("¥", "").replace("￥", "").replace(",", "").strip()
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return round(max(0.0, number), 2)


def _normalize_item(raw_item: Any, index: int) -> Optional[Dict[str, Any]]:
    """把模型输出的商品项统一成前端约定的字段。"""

    if isinstance(raw_item, str):
        return {
            "id": f"item-{index + 1}",
            "name": raw_item.strip() or f"商品{index + 1}",
            "quantity": 1,
            "price": 0.0,
            "final_price": 0.0,
            "platform": "",
        }

    if not isinstance(raw_item, dict):
        return None

    name = (
        raw_item.get("name")
        or raw_item.get("title")
        or raw_item.get("product_name")
        or f"商品{index + 1}"
    )
    price = _normalize_price(
        raw_item.get("price")
        or raw_item.get("unit_price")
        or raw_item.get("final_price")
    )
    final_price = _normalize_price(raw_item.get("final_price") or price)

    try:
        quantity = max(1, min(99, int(raw_item.get("quantity", 1))))
    except (TypeError, ValueError):
        quantity = 1

    return {
        "id": str(
            raw_item.get("id")
            or raw_item.get("product_id")
            or f"item-{index + 1}"
        ),
        "name": str(name),
        "quantity": quantity,
        "price": price,
        "final_price": final_price,
        "platform": str(raw_item.get("platform") or ""),
    }


def _normalize_plan(raw_plan: Dict[str, Any], index: int) -> Dict[str, Any]:
    """标准化单个方案，兼容模型可能使用的字段别名。"""

    raw_items = raw_plan.get("items")
    if not isinstance(raw_items, list):
        raw_items = raw_plan.get("products")
    if not isinstance(raw_items, list):
        raw_items = []

    normalized_items = [
        normalized_item
        for item_index, raw_item in enumerate(raw_items[:12])
        if (normalized_item := _normalize_item(raw_item, item_index)) is not None
    ]

    total_price = _normalize_price(
        raw_plan.get("total_price")
        or raw_plan.get("total")
        or raw_plan.get("price")
    )
    if total_price <= 0 and normalized_items:
        total_price = round(
            sum(
                float(item["final_price"]) * int(item["quantity"])
                for item in normalized_items
            ),
            2,
        )

    return {
        "name": str(raw_plan.get("name") or raw_plan.get("title") or f"方案{index}"),
        "desc": str(raw_plan.get("desc") or raw_plan.get("description") or ""),
        "items": normalized_items,
        "total_price": total_price,
        "advantage": str(
            raw_plan.get("advantage")
            or raw_plan.get("reason")
            or raw_plan.get("recommendation_reason")
            or ""
        ),
    }


def _normalize_string_list(value: Any, limit: int = 3) -> List[str]:
    """把字符串或列表统一为非空字符串列表。"""

    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        values = []

    normalized_values: List[str] = []
    for item in values[:limit]:
        if isinstance(item, str) and item.strip():
            normalized_values.append(item.strip())
    return normalized_values


def _normalize_agent_result(raw_result: Dict[str, Any]) -> Dict[str, Any]:
    """校验并标准化模型输出，保证前后端使用同一数据契约。"""

    answer_value = next(
        (
            value
            for value in (
                raw_result.get("answer"),
                raw_result.get("message"),
                raw_result.get("reply"),
            )
            if isinstance(value, str) and value.strip()
        ),
        "",
    )
    if not answer_value:
        raise AgentServiceError("智能体未能生成有效回复，请稍后重试。")

    raw_plans = raw_result.get("plans")
    if not isinstance(raw_plans, list):
        raw_plans = raw_result.get("recommendations")
    if not isinstance(raw_plans, list):
        raw_data = raw_result.get("data")
        raw_plans = raw_data.get("plans", []) if isinstance(raw_data, dict) else []

    normalized_plans = [
        _normalize_plan(raw_plan, index)
        for index, raw_plan in enumerate(raw_plans[:3], start=1)
        if isinstance(raw_plan, dict)
    ]

    raw_suggestions = (
        raw_result.get("suggested_replies")
        or raw_result.get("follow_up_options")
        or raw_result.get("suggestions")
    )
    suggested_replies = _normalize_string_list(raw_suggestions, limit=3)

    requires_input = bool(raw_result.get("requires_input", False))
    if normalized_plans:
        requires_input = False
    elif not requires_input and answer_value.rstrip().endswith(("?", "？")):
        requires_input = True

    return {
        "answer": answer_value.strip(),
        "plans": normalized_plans,
        "requires_input": requires_input,
        "suggested_replies": suggested_replies,
    }


def _request_structured_repair(
    client: Any,
    messages: List[Dict[str, Any]],
    raw_content: str,
) -> Dict[str, Any]:
    """当模型首次输出不是合法 JSON 时，发起一次格式修复请求。"""

    repair_messages = list(messages)
    repair_messages.extend(
        [
            {"role": "assistant", "content": raw_content},
            {
                "role": "user",
                "content": (
                    "请把上一条回复重新整理为合法 JSON 对象。"
                    "只能包含 answer 和 plans 两个顶层字段，不要输出任何解释或代码围栏。"
                ),
            },
        ]
    )

    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=TEMPERATURE,
        messages=repair_messages,
        response_format={"type": "json_object"},
        max_tokens=1600,
    )
    repaired_content = completion.choices[0].message.content or ""
    repaired_result = _extract_json_object(repaired_content)
    if repaired_result is None:
        raise AgentServiceError("智能体返回格式异常，请稍后重试。")

    return _normalize_agent_result(repaired_result)


def _build_assistant_tool_message(assistant_message: Any) -> Dict[str, Any]:
    """把 OpenAI 响应中的工具调用消息转换成下一轮可提交的消息结构。"""

    serialized_tool_calls = []
    for tool_call in assistant_message.tool_calls or []:
        serialized_tool_calls.append(
            {
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
        )

    return {
        "role": "assistant",
        "content": assistant_message.content or "",
        "tool_calls": serialized_tool_calls,
    }


def _run_tool_loop(
    client: Any,
    messages: List[Dict[str, Any]],
    used_tools: List[str],
) -> Dict[str, Any]:
    """执行 Agent 的多轮模型推理与工具调用循环。"""

    for _ in range(MAX_TOOL_ROUNDS):
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=TEMPERATURE,
            messages=messages,
            tools=AGENT_TOOL_DEFINITIONS,
            tool_choice="auto",
            max_tokens=1600,
        )

        if not completion.choices:
            raise AgentServiceError("智能体服务未返回有效结果，请稍后重试。")

        assistant_message = completion.choices[0].message
        tool_calls = assistant_message.tool_calls

        # 没有工具调用，说明模型已经准备生成最终方案。
        if not tool_calls:
            raw_content = assistant_message.content or ""
            parsed_result = _extract_json_object(raw_content)
            if parsed_result is None:
                parsed_result = _request_structured_repair(
                    client=client,
                    messages=messages,
                    raw_content=raw_content,
                )
            else:
                parsed_result = _normalize_agent_result(parsed_result)

            return {
                "answer": parsed_result["answer"],
                "plans": parsed_result["plans"],
                "requires_input": parsed_result["requires_input"],
                "suggested_replies": parsed_result["suggested_replies"],
                "used_tools": used_tools,
            }

        # 先把 Assistant 的工具调用消息写回上下文，再逐项追加工具结果。
        messages.append(_build_assistant_tool_message(assistant_message))

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            if tool_name not in used_tools:
                used_tools.append(tool_name)

            # 工具参数由模型以 JSON 字符串返回，需要自行解析和校验。
            try:
                tool_arguments = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError as error:
                tool_result: Any = {
                    "error": f"工具参数不是合法 JSON：{error.msg}"
                }
            else:
                tool_result = execute_agent_tool(tool_name, tool_arguments)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False,
                        default=str,
                    ),
                }
            )

    raise AgentServiceError(
        "智能体分析步骤过多，请缩小问题范围后重试。",
        status_code=503,
        used_tools=used_tools,
    )


def _normalize_history(history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    """清洗前端传入的最近对话历史，避免超长内容和非法角色进入模型。"""

    if not isinstance(history, list):
        return []

    normalized_history: List[Dict[str, str]] = []
    for item in history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        normalized_content = content.strip()[:MAX_HISTORY_CONTENT_LENGTH]
        if normalized_content:
            normalized_history.append({"role": role, "content": normalized_content})

    return normalized_history


def run_agent(
    user_input: str,
    history: Optional[List[Dict[str, Any]]] = None,
    client: Optional[Any] = None,
) -> Dict[str, Any]:
    """运行全场景生活消费决策智能体并返回接口所需结构。

    Args:
        user_input: 用户本轮自然语言消费需求。
        history: 最近对话历史，仅包含 user/assistant 的 content 文本。
        client: 可选的 OpenAI 客户端。生产环境传 None，测试时可注入模拟客户端。

    Returns:
        Dict[str, Any]: 包含 answer、plans 和 used_tools 的字典。

    Raises:
        AgentServiceError: 输入不合法、API 调用失败或模型输出异常时抛出。
    """

    if not isinstance(user_input, str) or not user_input.strip():
        raise AgentServiceError("请输入具体的消费需求，例如选购商品、规划家庭预算或安排周末出游。", status_code=400)

    normalized_input = user_input.strip()
    if len(normalized_input) > MAX_USER_INPUT_LENGTH:
        raise AgentServiceError(
            f"输入内容不能超过 {MAX_USER_INPUT_LENGTH} 个字符。",
            status_code=400,
        )

    used_tools: List[str] = []
    try:
        openai_client = client or _create_openai_client()
        normalized_history = _normalize_history(history)
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *normalized_history,
            {"role": "user", "content": normalized_input},
        ]
        return _run_tool_loop(
            client=openai_client,
            messages=messages,
            used_tools=used_tools,
        )
    except AgentServiceError:
        raise
    except Exception as error:
        # 不向接口调用方泄露 API 地址、密钥状态、堆栈等内部信息。
        raise AgentServiceError(
            "抱歉，智能体服务暂时不可用，请稍后重试或检查网络与 OPENAI_API_KEY 配置。",
            status_code=503,
            used_tools=used_tools,
        ) from error
````


## 13. services/consumption_service.py

````python
"""全生活消费场景的决策业务逻辑。

当前版本基于模拟商户数据完成预算筛选、分类筛选和基础排序，
后续可在此基础上接入向量检索、用户偏好画像及大模型推荐能力。
"""

from copy import deepcopy
from typing import Any, Dict, List, Optional

from data.mock_merchants import LIFE_MERCHANTS


def list_merchants(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取生活消费商户列表。

    Args:
        category: 可选的商户分类。传入 None 或空字符串时返回全部商户。

    Returns:
        List[Dict[str, Any]]: 商户信息列表。返回值均为深拷贝，
        调用方修改结果时不会污染模块中的原始模拟数据。
    """

    normalized_category = category.strip() if isinstance(category, str) else None

    if normalized_category:
        matched_merchants = [
            merchant
            for merchant in LIFE_MERCHANTS
            if merchant["category"] == normalized_category
        ]
    else:
        matched_merchants = list(LIFE_MERCHANTS)

    return [deepcopy(merchant) for merchant in matched_merchants]


def recommend_consumption(
    budget: float,
    category: Optional[str] = None,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """根据预算和消费分类生成基础商户推荐。

    推荐规则：
    1. 先排除超过预算的商户；
    2. 综合评分、剩余预算和距离计算推荐分数；
    3. 按推荐分数降序排序并截取指定数量；
    4. 为每条结果补充可解释的推荐理由。

    Args:
        budget: 用户预算，单位为元，必须大于 0。
        category: 可选消费分类，例如“餐饮美食”“商超日用”或“本地服务”。
        limit: 返回结果数量，取值范围为 1 到 10。

    Returns:
        List[Dict[str, Any]]: 按推荐优先级排序的商户列表；
        如果没有满足预算的商户，则返回空列表。

    Raises:
        ValueError: 预算或结果数量不合法时抛出。
    """

    # 入口层可能把任意输入传给服务层，因此这里再次执行边界校验。
    if budget <= 0:
        raise ValueError("预算必须大于 0")

    if not 1 <= limit <= 10:
        raise ValueError("limit 必须在 1 到 10 之间")

    # 仅在预算范围内筛选候选商户，保证推荐结果具有可执行性。
    affordable_merchants = [
        merchant
        for merchant in list_merchants(category=category)
        if float(merchant["average_price"]) <= budget
    ]

    # Python 的 sort 是稳定排序；复合键确保同分时优先选择评分更高、
    # 距离更近的商户。负号用于让评分按降序排列。
    affordable_merchants.sort(
        key=lambda merchant: (
            -_calculate_recommendation_score(merchant, budget),
            -float(merchant["rating"]),
            int(merchant["distance_meters"]),
        )
    )

    recommendations: List[Dict[str, Any]] = []
    for merchant in affordable_merchants[:limit]:
        result_item = deepcopy(merchant)
        result_item["recommendation_reason"] = _build_recommendation_reason(
            merchant=merchant,
            budget=budget,
        )
        recommendations.append(result_item)

    return recommendations


def _calculate_recommendation_score(
    merchant: Dict[str, Any],
    budget: float,
) -> float:
    """计算单个商户的基础推荐分数。

    固定评分权重之外，额外奖励预算利用率较高且距离较近的商户，
    从而让推荐结果更贴近本地生活消费场景。
    """

    rating = float(merchant["rating"])
    average_price = float(merchant["average_price"])
    distance_meters = int(merchant["distance_meters"])

    # 评分是主要因素；预算余量最高贡献 10 分；距离每 100 米扣 0.5 分。
    remaining_budget = max(0.0, budget - average_price)
    score = rating * 20 + min(remaining_budget, 20.0) * 0.5
    score -= distance_meters / 100.0 * 0.5
    return score


def _build_recommendation_reason(
    merchant: Dict[str, Any],
    budget: float,
) -> str:
    """根据预算、距离和标签生成可读的推荐理由。"""

    average_price = float(merchant["average_price"])
    distance_meters = int(merchant["distance_meters"])

    if average_price <= budget * 0.5:
        reason = f"人均约 {average_price:.0f} 元，预算占用较低"
    else:
        reason = f"人均约 {average_price:.0f} 元，符合 {budget:.0f} 元预算"

    if distance_meters <= 300:
        reason += "，步行距离近"
    elif distance_meters <= 600:
        reason += "，步行可达"

    # 最多展示两个标签，避免推荐理由过长。
    if merchant["tags"]:
        reason += f"，适合：{'、'.join(merchant['tags'][:2])}"

    return reason
````


## 14. utils/__init__.py

````python
"""通用工具包。

集中导出环境变量相关工具，业务模块可从 utils 包直接导入，
避免在多个文件中重复维护 .env 读取逻辑。
"""

from .env_utils import get_bool_env, get_env, get_openai_api_key, load_environment

__all__ = [
    "get_bool_env",
    "get_env",
    "get_openai_api_key",
    "load_environment",
]
````


## 15. utils/agent_tools.py

````python
"""全场景生活消费决策智能体的工具函数与 Function Calling 定义。

工具层职责：
1. 从 products.json 搜索符合品类、标签和预算的商品；
2. 从 discount_rules.json 匹配平台优惠、满减、凑单和会员权益；
3. 参考一般个人与家庭的生活消费结构生成分场景预算建议；
4. 向 Agent 提供严格符合 OpenAI tools JSON Schema 的函数定义。

工具函数只返回结构化数据，不生成自然语言，便于模型继续推理并生成方案。
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# 使用绝对路径读取数据，避免 Flask 从不同工作目录启动时找不到文件。
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PRODUCTS_FILE_PATH = DATA_DIR / "products.json"
DISCOUNT_RULES_FILE_PATH = DATA_DIR / "discount_rules.json"

# 全生活消费场景的常用品类。搜索时会同时匹配分类、商品名、标签和描述。
PRODUCT_CATEGORIES = [
    "餐饮美食",
    "零食饮料",
    "商超日用",
    "生活用品",
    "家居生活",
    "数码配件",
    "数码家电",
    "服饰鞋包",
    "美妆个护",
    "健康医疗",
    "交通出行",
    "教育学习",
    "文体娱乐",
    "亲子宠物",
    "旅游住宿",
    "本地服务",
    "礼品文创",
]

# 常见口语表达与标准品类之间的映射，用于模糊搜索。
CATEGORY_ALIASES: Dict[str, str] = {
    "吃": "餐饮美食",
    "吃饭": "餐饮美食",
    "餐饮": "餐饮美食",
    "外卖": "餐饮美食",
    "聚餐": "餐饮美食",
    "买菜": "餐饮美食",
    "生鲜": "餐饮美食",
    "咖啡": "餐饮美食",
    "奶茶": "餐饮美食",
    "零食": "零食饮料",
    "饮料": "零食饮料",
    "食品": "零食饮料",
    "超市": "商超日用",
    "商超": "商超日用",
    "日用品": "生活用品",
    "日用百货": "生活用品",
    "洗护": "生活用品",
    "家居": "家居生活",
    "厨房": "家居生活",
    "床品": "家居生活",
    "数码": "数码配件",
    "电子产品": "数码配件",
    "手机配件": "数码配件",
    "家电": "数码家电",
    "电器": "数码家电",
    "小家电": "数码家电",
    "衣服": "服饰鞋包",
    "服装": "服饰鞋包",
    "穿搭": "服饰鞋包",
    "鞋子": "服饰鞋包",
    "包包": "服饰鞋包",
    "美妆": "美妆个护",
    "护肤": "美妆个护",
    "个护": "美妆个护",
    "药品": "健康医疗",
    "医疗": "健康医疗",
    "健康": "健康医疗",
    "保健品": "健康医疗",
    "交通": "交通出行",
    "出行": "交通出行",
    "通勤": "交通出行",
    "打车": "交通出行",
    "地铁": "交通出行",
    "学习": "教育学习",
    "课程": "教育学习",
    "教育": "教育学习",
    "图书": "教育学习",
    "娱乐": "文体娱乐",
    "电影": "文体娱乐",
    "健身": "文体娱乐",
    "运动": "文体娱乐",
    "宠物": "亲子宠物",
    "猫粮": "亲子宠物",
    "猫砂": "亲子宠物",
    "孩子": "亲子宠物",
    "儿童": "亲子宠物",
    "亲子": "亲子宠物",
    "旅游": "旅游住宿",
    "旅行": "旅游住宿",
    "酒店": "旅游住宿",
    "民宿": "旅游住宿",
    "门票": "旅游住宿",
    "保洁": "本地服务",
    "家政": "本地服务",
    "维修": "本地服务",
    "搬家": "本地服务",
    "礼物": "礼品文创",
    "礼品": "礼品文创",
    "文创": "礼品文创",
}

# 一般个人与家庭月均消费结构的参考权重，总和为 100。
# 该比例用于预算分配，实际金额会按用户选择的场景重新归一化。
LIFE_SPENDING_PROFILES: Dict[str, Dict[str, Any]] = {
    "餐饮美食": {
        "weight": 20,
        "suggestion": "优先安排日常三餐与家庭食材，减少高频外卖和非必要聚餐。",
    },
    "商超日用": {
        "weight": 12,
        "suggestion": "纸巾、清洁用品和食材可集中采购，关注量贩装与配送满减。",
    },
    "生活用品": {
        "weight": 6,
        "suggestion": "按实际消耗补充日用品，避免因促销囤积过多。",
    },
    "住房水电": {
        "weight": 16,
        "suggestion": "房租、物业和水电属于刚性支出，应优先留足并单独管理。",
    },
    "交通出行": {
        "weight": 10,
        "suggestion": "优先使用公共交通、月卡和通勤优惠，减少非必要打车。",
    },
    "数码家电": {
        "weight": 5,
        "suggestion": "先确认使用频率和售后需求，避免为低频功能支付溢价。",
    },
    "服饰鞋包": {
        "weight": 5,
        "suggestion": "优先补充高频穿着的基础款，结合季节和通勤场景购买。",
    },
    "美妆个护": {
        "weight": 4,
        "suggestion": "优先补充快用完的基础洗护，避免重复购买和过度囤货。",
    },
    "健康医疗": {
        "weight": 4,
        "suggestion": "常备基础健康用品，医疗支出以专业机构和医生建议为准。",
    },
    "零食饮料": {
        "weight": 3,
        "suggestion": "设置每周上限，优先购买分享装或家庭装，减少冲动消费。",
    },
    "教育学习": {
        "weight": 3,
        "suggestion": "优先选择与当前目标直接相关的课程和资料，避免付费后闲置。",
    },
    "文体娱乐": {
        "weight": 3,
        "suggestion": "为娱乐活动设置单次上限，优先使用团购、会员和城市公共文化资源。",
    },
    "亲子宠物": {
        "weight": 2,
        "suggestion": "优先保障食品、清洁和健康刚需，再安排玩具与体验型消费。",
    },
    "旅游住宿": {
        "weight": 2,
        "suggestion": "提前比较交通和住宿价格，为临时加价和餐饮留出弹性预算。",
    },
    "本地服务": {
        "weight": 1,
        "suggestion": "下单前确认服务范围、上门费和可能产生的附加费用。",
    },
    "礼品文创": {
        "weight": 2,
        "suggestion": "按关系和场景控制礼物预算，优先选择实用或有纪念意义的选项。",
    },
    "应急储蓄": {
        "weight": 2,
        "suggestion": "保留少量应急资金，用于临时医疗、维修或紧急出行。",
    },
}

# 兼容旧版本代码中的常量名。
STUDENT_SPENDING_PROFILES = LIFE_SPENDING_PROFILES

# 用户常用口语场景到标准预算场景的映射。
SCENE_ALIASES: Dict[str, str] = {
    "吃饭": "餐饮美食",
    "三餐": "餐饮美食",
    "餐饮": "餐饮美食",
    "外卖": "餐饮美食",
    "聚餐": "餐饮美食",
    "生鲜": "餐饮美食",
    "咖啡": "餐饮美食",
    "奶茶": "餐饮美食",
    "零食": "零食饮料",
    "饮料": "零食饮料",
    "超市": "商超日用",
    "商超": "商超日用",
    "日用品": "生活用品",
    "日用百货": "生活用品",
    "家居": "家居生活",
    "厨房": "家居生活",
    "数码": "数码家电",
    "家电": "数码家电",
    "衣服": "服饰鞋包",
    "服装": "服饰鞋包",
    "穿搭": "服饰鞋包",
    "美妆": "美妆个护",
    "护肤": "美妆个护",
    "健康": "健康医疗",
    "医疗": "健康医疗",
    "买药": "健康医疗",
    "交通": "交通出行",
    "出行": "交通出行",
    "通勤": "交通出行",
    "打车": "交通出行",
    "话费": "交通出行",
    "学习": "教育学习",
    "课程": "教育学习",
    "教育": "教育学习",
    "娱乐": "文体娱乐",
    "电影": "文体娱乐",
    "健身": "文体娱乐",
    "宠物": "亲子宠物",
    "亲子": "亲子宠物",
    "孩子": "亲子宠物",
    "旅游": "旅游住宿",
    "旅行": "旅游住宿",
    "酒店": "旅游住宿",
    "保洁": "本地服务",
    "家政": "本地服务",
    "维修": "本地服务",
    "搬家": "本地服务",
    "礼物": "礼品文创",
    "房租": "住房水电",
    "水电": "住房水电",
    "物业": "住房水电",
    "储蓄": "应急储蓄",
    "存钱": "应急储蓄",
}


# 严格采用 OpenAI Chat Completions tools 格式：
# {"type": "function", "function": {"name", "description", "parameters"}}。
AGENT_TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "按关键词、品类标签和价格区间搜索生活消费商品与本地服务。"
                "category 支持模糊输入，例如“耳机”“护肤”“生鲜”“宠物用品”“酒店”“保洁服务”。"
                "结果按价格升序返回。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": (
                            "商品或服务品类，可传餐饮美食、商超日用、家居生活、"
                            "数码家电、服饰鞋包、健康医疗、交通出行、教育学习、"
                            "文体娱乐、亲子宠物、旅游住宿、本地服务等；也可传"
                            "耳机、猫粮、酒店、保洁等具体关键词；不限制时传“全部”。"
                        ),
                    },
                    "budget_min": {
                        "type": "number",
                        "description": "最低预算，单位为元；没有下限时传 0。",
                        "minimum": 0,
                    },
                    "budget_max": {
                        "type": "number",
                        "description": "最高预算，单位为元，必须大于或等于 budget_min。",
                        "minimum": 0,
                    },
                },
                "required": ["category", "budget_min", "budget_max"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_discount",
            "description": (
                "根据商品或服务 ID 计算平台专属优惠、最优满减、会员权益或凑单规则、"
                "单品到手价和进一步凑单建议。通常应先调用 search_products，"
                "再把选中的商品 ID 列表传给本工具。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "products": {
                        "type": "array",
                        "description": "从 search_products 结果中选择的商品 ID 列表。",
                        "items": {
                            "type": "string",
                            "description": "商品唯一编号，例如 D001 或 S002。",
                        },
                        "minItems": 1,
                        "maxItems": 12,
                    }
                },
                "required": ["products"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "budget_allocation",
            "description": (
                "参考一般个人与家庭的生活消费比例，把总预算拆分到餐饮美食、"
                "商超日用、住房水电、交通出行、数码家电、服饰鞋包、健康医疗、"
                "教育学习、文体娱乐、亲子宠物、旅游住宿、本地服务等场景。"
                "适合个人预算、家庭预算、旅行预算和阶段性消费规划。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "total_budget": {
                        "type": "number",
                        "description": "需要分配的总预算，单位为元，必须大于 0。",
                        "exclusiveMinimum": 0,
                    },
                    "scenes": {
                        "type": "array",
                        "description": (
                            "需要分配预算的消费场景列表，例如餐饮美食、商超日用、"
                            "住房水电、交通出行、健康医疗、教育学习、文体娱乐、"
                            "亲子宠物、旅游住宿、本地服务、礼品文创、应急储蓄。"
                        ),
                        "items": {
                            "type": "string",
                            "description": "消费场景名称，支持吃饭、日用品、护肤等口语表达。",
                        },
                        "minItems": 1,
                        "maxItems": 20,
                    },
                },
                "required": ["total_budget", "scenes"],
                "additionalProperties": False,
            },
        },
    },
]

def _load_json_file(file_path: Path, data_name: str) -> Any:
    """读取 JSON 数据文件，并给出明确的错误信息。"""

    try:
        with file_path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    except FileNotFoundError as error:
        raise RuntimeError(f"{data_name}文件不存在：{file_path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{data_name} JSON 格式错误：{error.msg}") from error


def _load_product_catalog() -> List[Dict[str, Any]]:
    """读取并校验商品数据。"""

    catalog_data = _load_json_file(PRODUCTS_FILE_PATH, "商品数据")
    if not isinstance(catalog_data, dict):
        raise RuntimeError("商品数据根节点必须是 JSON 对象")

    products = catalog_data.get("products", [])
    if not isinstance(products, list):
        raise RuntimeError("商品数据缺少 products 数组")

    required_fields = {
        "id",
        "name",
        "category",
        "price",
        "platform",
        "rating",
        "tags",
        "description",
    }
    for index, product in enumerate(products):
        if not isinstance(product, dict):
            raise RuntimeError(f"第 {index + 1} 个商品必须是 JSON 对象")
        missing_fields = required_fields - set(product)
        if missing_fields:
            missing_text = "、".join(sorted(missing_fields))
            raise RuntimeError(f"商品 {product.get('id', index + 1)} 缺少字段：{missing_text}")

    return products


def _load_discount_rules() -> Dict[str, Any]:
    """读取并校验优惠规则数据。"""

    rules = _load_json_file(DISCOUNT_RULES_FILE_PATH, "优惠规则")
    if not isinstance(rules, dict):
        raise RuntimeError("优惠规则根节点必须是 JSON 对象")
    return rules


def _normalize_category(category: str) -> str:
    """把常见口语品类转换为标准品类；无法映射时保留原文。"""

    normalized_category = category.strip()
    return CATEGORY_ALIASES.get(normalized_category, normalized_category)


def _product_search_text(product: Dict[str, Any]) -> str:
    """拼接商品的可搜索文本。"""

    tags = product.get("tags", [])
    tag_text = " ".join(str(tag) for tag in tags) if isinstance(tags, list) else str(tags)
    return " ".join(
        [
            str(product.get("category", "")),
            str(product.get("name", "")),
            str(product.get("description", "")),
            tag_text,
        ]
    ).lower()


def search_products(
    category: str,
    budget_min: float,
    budget_max: float,
) -> List[Dict[str, Any]]:
    """按模糊品类、标签和价格区间搜索商品。

    匹配规则：
    - “全部”返回所有商品；
    - 先尝试常见口语品类映射，再对分类、商品名、标签和描述做模糊匹配；
    - 支持空格、中文逗号和顿号分隔的多个关键词，命中任意关键词即可；
    - 最终严格按价格升序排列。

    Args:
        category: 品类或具体搜索关键词。
        budget_min: 最低预算，包含边界。
        budget_max: 最高预算，包含边界。

    Returns:
        List[Dict[str, Any]]: 商品列表，字段与 products.json 保持一致。

    Raises:
        ValueError: 参数不合法时抛出。
        RuntimeError: 商品数据无法读取时抛出。
    """

    if not isinstance(category, str) or not category.strip():
        raise ValueError("category 必须是非空字符串")

    try:
        minimum_price = float(budget_min)
        maximum_price = float(budget_max)
    except (TypeError, ValueError) as error:
        raise ValueError("budget_min 和 budget_max 必须是数字") from error

    if minimum_price < 0 or maximum_price < 0:
        raise ValueError("预算不能小于 0")
    if minimum_price > maximum_price:
        raise ValueError("budget_min 不能大于 budget_max")

    normalized_query = _normalize_category(category)
    if normalized_query.lower() in {"全部", "不限", "任意", "all"}:
        keywords = []
    else:
        keywords = [
            keyword.lower()
            for keyword in re.split(r"[\s,，、/]+", normalized_query)
            if keyword.strip()
        ]

    products = _load_product_catalog()
    matched_products: List[Dict[str, Any]] = []

    for product in products:
        price = float(product.get("price", 0))
        if not minimum_price <= price <= maximum_price:
            continue

        if not keywords:
            matched_products.append(dict(product))
            continue

        searchable_text = _product_search_text(product)
        if any(keyword in searchable_text for keyword in keywords):
            matched_products.append(dict(product))

    # 用户要求按价格升序；同价时评分高、ID 稳定的商品排前面。
    matched_products.sort(
        key=lambda item: (
            float(item.get("price", 0)),
            -float(item.get("rating", 0)),
            str(item.get("id", "")),
        )
    )
    return matched_products


def _is_rule_eligible(
    rule: Dict[str, Any],
    subtotal: float,
    selected_products: Sequence[Dict[str, Any]],
) -> bool:
    """判断满减或凑单规则是否适用于当前订单。"""

    threshold = float(rule.get("threshold", 0))
    if subtotal < threshold:
        return False

    required_category = rule.get("category")
    if required_category:
        return any(
            product.get("category") == required_category
            for product in selected_products
        )

    allowed_platforms = rule.get("platforms")
    if isinstance(allowed_platforms, list) and allowed_platforms:
        return any(
            product.get("platform") in allowed_platforms
            for product in selected_products
        )

    return True


def _select_best_rule(
    rules: Sequence[Dict[str, Any]],
    subtotal: float,
    selected_products: Sequence[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """从所有可用规则中选择优惠金额最大的规则。"""

    eligible_rules = [
        rule
        for rule in rules
        if isinstance(rule, dict)
        and _is_rule_eligible(rule, subtotal, selected_products)
    ]
    if not eligible_rules:
        return None

    # 优先比较实际减免金额；金额相同时选择门槛更高的规则。
    return max(
        eligible_rules,
        key=lambda rule: (
            float(rule.get("reduce", 0)),
            float(rule.get("threshold", 0)),
        ),
    )


def _calculate_platform_offer(
    subtotal: float,
    platform_offer: Dict[str, Any],
) -> float:
    """计算单个平台订单可享受的平台专属优惠金额。"""

    min_spend = float(platform_offer.get("min_spend", 0))
    if subtotal < min_spend:
        return 0.0

    offer_type = platform_offer.get("type")
    if offer_type == "rate":
        rate = min(1.0, max(0.0, float(platform_offer.get("rate", 1.0))))
        raw_discount = subtotal * (1.0 - rate)
        max_discount = float(platform_offer.get("max_discount", raw_discount))
        return round(min(raw_discount, max_discount), 2)

    if offer_type == "threshold":
        threshold = float(platform_offer.get("threshold", 0))
        if subtotal >= threshold:
            return round(float(platform_offer.get("reduce", 0)), 2)

    return 0.0

def _calculate_member_discount(
    total: float,
    member_rules: Sequence[Dict[str, Any]],
) -> Tuple[float, Optional[Dict[str, Any]]]:
    """从会员权益或平台券中选出实际优惠金额最高的一项。"""

    best_discount = 0.0
    best_rule: Optional[Dict[str, Any]] = None

    for rule in member_rules:
        if not isinstance(rule, dict):
            continue

        min_spend = float(rule.get("min_spend", 0))
        if total < min_spend:
            continue

        rule_type = rule.get("type")
        discount = 0.0
        if rule_type == "rate":
            rate = min(1.0, max(0.0, float(rule.get("rate", 1.0))))
            discount = total * (1.0 - rate)
            max_discount = float(rule.get("max_discount", discount))
            discount = min(discount, max_discount)
        elif rule_type == "threshold":
            threshold = float(rule.get("threshold", 0))
            if total >= threshold:
                discount = float(rule.get("reduce", 0))

        discount = round(max(0.0, discount), 2)
        if discount > best_discount:
            best_discount = discount
            best_rule = rule

    return best_discount, best_rule


def _calculate_order_breakdown(
    selected_products: Sequence[Dict[str, Any]],
    discount_rules: Dict[str, Any],
) -> Dict[str, Any]:
    """计算订单在平台分组、满减和会员权益后的最终价格。"""

    full_rules = discount_rules.get("full_reduction", [])
    bundle_rules = discount_rules.get("bundle_rules", [])
    combined_rules = [
        rule
        for rule in list(full_rules) + list(bundle_rules)
        if isinstance(rule, dict)
    ]
    platform_offers = discount_rules.get("platform_offers", {})
    member_rules = discount_rules.get(
        "member_discounts",
        discount_rules.get("student_discounts", []),
    )

    if not isinstance(platform_offers, dict):
        platform_offers = {}
    if not isinstance(member_rules, list):
        member_rules = []

    # 满减和平台优惠通常按平台订单计算，因此先按 platform 分组。
    platform_groups: Dict[str, List[Dict[str, Any]]] = {}
    for product in selected_products:
        platform = str(product.get("platform", "其他"))
        platform_groups.setdefault(platform, []).append(product)

    original_total = round(
        sum(float(product.get("price", 0)) for product in selected_products),
        2,
    )
    platform_breakdown: List[Dict[str, Any]] = []
    total_before_member = 0.0
    platform_discount_total = 0.0
    full_reduction_total = 0.0

    for platform, products in platform_groups.items():
        platform_subtotal = round(
            sum(float(product.get("price", 0)) for product in products),
            2,
        )
        platform_offer = platform_offers.get(platform, {})
        platform_discount = (
            _calculate_platform_offer(platform_subtotal, platform_offer)
            if isinstance(platform_offer, dict)
            else 0.0
        )
        subtotal_after_platform = round(
            max(0.0, platform_subtotal - platform_discount),
            2,
        )

        best_rule = _select_best_rule(
            rules=combined_rules,
            subtotal=subtotal_after_platform,
            selected_products=products,
        )
        full_reduction = (
            round(float(best_rule.get("reduce", 0)), 2)
            if best_rule
            else 0.0
        )

        platform_final = round(
            max(0.0, subtotal_after_platform - full_reduction),
            2,
        )
        total_before_member = round(total_before_member + platform_final, 2)
        platform_discount_total = round(
            platform_discount_total + platform_discount,
            2,
        )
        full_reduction_total = round(
            full_reduction_total + full_reduction,
            2,
        )

        platform_breakdown.append(
            {
                "platform": platform,
                "subtotal": platform_subtotal,
                "platform_offer": (
                    platform_offer.get("name", "")
                    if isinstance(platform_offer, dict)
                    else ""
                ),
                "platform_discount": platform_discount,
                "best_reduction_rule": (
                    {
                        "id": best_rule.get("id"),
                        "name": best_rule.get("name"),
                        "threshold": float(best_rule.get("threshold", 0)),
                        "reduce": full_reduction,
                    }
                    if best_rule
                    else None
                ),
                "subtotal_after_reduction": platform_final,
            }
        )

    member_discount, member_rule = _calculate_member_discount(
        total=total_before_member,
        member_rules=member_rules,
    )
    final_total = round(max(0.0, total_before_member - member_discount), 2)

    return {
        "original_total": original_total,
        "platform_discount_total": platform_discount_total,
        "full_reduction_total": full_reduction_total,
        "member_discount": member_discount,
        "member_rule": (
            {
                "id": member_rule.get("id"),
                "name": member_rule.get("name"),
                "discount": member_discount,
            }
            if member_rule
            else None
        ),
        "final_total": final_total,
        "platform_breakdown": platform_breakdown,
    }


def _allocate_order_discounts_to_items(
    selected_products: Sequence[Dict[str, Any]],
    breakdown: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """将订单级优惠按商品价格比例分摊，生成单品到手价。"""

    original_total = float(breakdown["original_total"])
    total_discount = round(
        original_total - float(breakdown["final_total"]),
        2,
    )

    item_details: List[Dict[str, Any]] = []
    allocated_discount = 0.0
    for index, product in enumerate(selected_products):
        price = round(float(product.get("price", 0)), 2)
        if index == len(selected_products) - 1:
            # 最后一件商品吸收四舍五入差额，保证优惠分摊总额准确。
            discount_share = round(total_discount - allocated_discount, 2)
        elif original_total > 0:
            discount_share = round(total_discount * price / original_total, 2)
        else:
            discount_share = 0.0

        allocated_discount = round(allocated_discount + discount_share, 2)
        item_details.append(
            {
                "id": product.get("id"),
                "name": product.get("name"),
                "category": product.get("category"),
                "platform": product.get("platform"),
                "price": price,
                "discount": discount_share,
                "final_price": round(max(0.0, price - discount_share), 2),
            }
        )

    return item_details

def _build_bundle_suggestions(
    selected_products: Sequence[Dict[str, Any]],
    current_final_total: float,
    catalog: Sequence[Dict[str, Any]],
    discount_rules: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """基于下一档满减或凑单门槛生成可执行的加购建议。"""

    current_subtotal = round(
        sum(float(product.get("price", 0)) for product in selected_products),
        2,
    )
    all_rules = [
        rule
        for rule in list(discount_rules.get("full_reduction", []))
        + list(discount_rules.get("bundle_rules", []))
        if isinstance(rule, dict)
    ]
    next_thresholds = sorted(
        {
            float(rule.get("threshold", 0))
            for rule in all_rules
            if float(rule.get("threshold", 0)) > current_subtotal
        }
    )
    if not next_thresholds:
        return []

    next_threshold = next_thresholds[0]
    gap_to_threshold = round(next_threshold - current_subtotal, 2)
    selected_ids = {str(product.get("id")) for product in selected_products}
    selected_platforms = {str(product.get("platform")) for product in selected_products}
    selected_categories = {str(product.get("category")) for product in selected_products}

    candidates = [
        product
        for product in catalog
        if str(product.get("id")) not in selected_ids
    ]
    scored_candidates: List[Tuple[Tuple[int, int, int, float], Dict[str, Any]]] = []
    for candidate in candidates:
        projected_products = list(selected_products) + [candidate]
        projected_breakdown = _calculate_order_breakdown(
            projected_products,
            discount_rules,
        )
        projected_final = float(projected_breakdown["final_total"])
        additional_payment = round(projected_final - current_final_total, 2)
        scoring_key = (
            0 if float(candidate.get("price", 0)) >= gap_to_threshold else 1,
            0 if str(candidate.get("platform")) in selected_platforms else 1,
            0 if str(candidate.get("category")) in selected_categories else 1,
            additional_payment,
        )
        scored_candidates.append((scoring_key, candidate))

    scored_candidates.sort(key=lambda item: item[0])

    suggestions: List[Dict[str, Any]] = []
    for _, candidate in scored_candidates[:2]:
        projected_products = list(selected_products) + [candidate]
        projected_breakdown = _calculate_order_breakdown(
            projected_products,
            discount_rules,
        )
        projected_final = float(projected_breakdown["final_total"])
        additional_payment = round(projected_final - current_final_total, 2)
        suggestions.append(
            {
                "suggested_product": {
                    "id": candidate.get("id"),
                    "name": candidate.get("name"),
                    "price": float(candidate.get("price", 0)),
                    "platform": candidate.get("platform"),
                },
                "current_subtotal": current_subtotal,
                "next_threshold": next_threshold,
                "gap_to_threshold": gap_to_threshold,
                "projected_final_total": projected_final,
                "additional_payment": additional_payment,
                "note": (
                    f"当前商品原价合计 {current_subtotal:.2f} 元，距下一档 "
                    f"{next_threshold:.0f} 元还差 {gap_to_threshold:.2f} 元；"
                    f"加购{candidate.get('name')}后预计实付 {projected_final:.2f} 元。"
                ),
            }
        )

    return suggestions


def calculate_discount(products: Sequence[Any]) -> Dict[str, Any]:
    """计算最优优惠、到手价和凑单建议。

    计算流程：
    1. 按 platform 对商品分组；
    2. 每个平台先匹配平台专属优惠；
    3. 再匹配可用满减和凑单规则中减免金额最高的一项；
    4. 汇总订单后匹配会员权益或平台券中优惠最大的一项；
    5. 按商品价格比例分摊优惠，输出单品到手价；
    6. 查找下一档门槛，生成同平台、同品类优先的凑单建议。

    Args:
        products: 商品 ID 列表；兼容包含 id/product_id 的字典列表。

    Returns:
        Dict[str, Any]: 优惠明细、平台明细、单品到手价和凑单建议。

    Raises:
        ValueError: 参数或商品 ID 不合法时抛出。
        RuntimeError: 数据文件无法读取时抛出。
    """

    if not isinstance(products, Sequence) or isinstance(products, (str, bytes)):
        raise ValueError("products 必须是商品 ID 数组")
    if not products:
        raise ValueError("products 不能为空")

    catalog = _load_product_catalog()
    discount_rules = _load_discount_rules()
    product_map = {
        str(product.get("id")): product
        for product in catalog
        if product.get("id")
    }

    selected_products: List[Dict[str, Any]] = []
    for product_reference in products:
        product_id = ""
        if isinstance(product_reference, str):
            product_id = product_reference.strip()
        elif isinstance(product_reference, Mapping):
            product_id = str(
                product_reference.get("id")
                or product_reference.get("product_id")
                or ""
            ).strip()

        if not product_id or product_id not in product_map:
            raise ValueError(f"未找到商品：{product_reference}")

        selected_products.append(product_map[product_id])

    breakdown = _calculate_order_breakdown(selected_products, discount_rules)
    item_details = _allocate_order_discounts_to_items(selected_products, breakdown)
    bundle_suggestions = _build_bundle_suggestions(
        selected_products=selected_products,
        current_final_total=float(breakdown["final_total"]),
        catalog=catalog,
        discount_rules=discount_rules,
    )

    return {
        "items": item_details,
        "original_total": breakdown["original_total"],
        "platform_discount_total": breakdown["platform_discount_total"],
        "full_reduction_total": breakdown["full_reduction_total"],
        "member_discount": breakdown["member_discount"],
        "member_rule": breakdown["member_rule"],
        "final_total": breakdown["final_total"],
        "saved_total": round(
            float(breakdown["original_total"]) - float(breakdown["final_total"]),
            2,
        ),
        "platform_breakdown": breakdown["platform_breakdown"],
        "bundle_suggestions": bundle_suggestions,
    }

def _resolve_budget_scene(scene: str) -> str:
    """将口语场景转换为标准预算场景。"""

    normalized_scene = scene.strip()
    if normalized_scene in LIFE_SPENDING_PROFILES:
        return normalized_scene

    for alias, standard_scene in SCENE_ALIASES.items():
        if alias in normalized_scene or normalized_scene in alias:
            return standard_scene

    for standard_scene in LIFE_SPENDING_PROFILES:
        if standard_scene in normalized_scene or normalized_scene in standard_scene:
            return standard_scene

    return normalized_scene


def budget_allocation(total_budget: float, scenes: Sequence[str]) -> Dict[str, Any]:
    """参考一般个人与家庭的生活消费比例生成分场景预算分配。

    当用户只指定部分场景时，会按这些场景的参考权重重新归一化，
    保证全部分配金额之和严格等于总预算。

    Args:
        total_budget: 总预算，单位为元。
        scenes: 消费场景列表；为空时使用完整的参考消费结构。

    Returns:
        Dict[str, Any]: 各场景金额、占比、参考比例和消费建议。

    Raises:
        ValueError: 总预算或场景列表不合法时抛出。
    """

    try:
        normalized_total_budget = float(total_budget)
    except (TypeError, ValueError) as error:
        raise ValueError("total_budget 必须是数字") from error

    if normalized_total_budget <= 0:
        raise ValueError("total_budget 必须大于 0")

    if isinstance(scenes, str):
        raw_scenes = [
            item.strip()
            for item in re.split(r"[,，、/]+", scenes)
            if item.strip()
        ]
    elif isinstance(scenes, Sequence):
        raw_scenes = [str(item).strip() for item in scenes if str(item).strip()]
    else:
        raise ValueError("scenes 必须是消费场景数组")

    normalized_scenes: List[str] = []
    for scene in raw_scenes:
        standard_scene = _resolve_budget_scene(scene)
        if standard_scene and standard_scene not in normalized_scenes:
            normalized_scenes.append(standard_scene)

    if not normalized_scenes:
        normalized_scenes = list(LIFE_SPENDING_PROFILES.keys())

    weights: List[float] = []
    for scene in normalized_scenes:
        profile = LIFE_SPENDING_PROFILES.get(scene)
        # 新场景采用相对保守的 5% 权重参与归一化。
        weights.append(float(profile["weight"]) if profile else 5.0)

    total_weight = sum(weights)
    allocations: List[Dict[str, Any]] = []
    allocated_amount = 0.0

    for index, scene in enumerate(normalized_scenes):
        ratio = weights[index] / total_weight
        amount = round(normalized_total_budget * ratio, 2)
        if index == len(normalized_scenes) - 1:
            amount = round(normalized_total_budget - allocated_amount, 2)

        allocated_amount = round(allocated_amount + amount, 2)
        profile = LIFE_SPENDING_PROFILES.get(scene, {})
        allocations.append(
            {
                "scene": scene,
                "reference_ratio": round(weights[index] / 100.0, 4),
                "allocated_ratio": round(ratio, 4),
                "amount": amount,
                "suggestion": profile.get(
                    "suggestion",
                    "作为弹性预算使用，建议单笔消费前先确认是否属于必要支出。",
                ),
            }
        )

    tips = [
        "比例参考一般个人与家庭的生活消费结构；指定场景时会按相对权重重新归一化。",
        "优先保障餐饮、住房、日用和健康等刚需，再安排娱乐、旅行等弹性支出。",
        "建议每周复盘实际花费，把未使用金额结转到下一周期或应急储蓄。",
    ]
    if normalized_total_budget <= 500:
        tips.insert(0, "预算较紧，建议优先自己做饭、使用公共交通，并暂停非刚需购物。")

    return {
        "total_budget": round(normalized_total_budget, 2),
        "reference_structure": {
            scene: profile["weight"]
            for scene, profile in LIFE_SPENDING_PROFILES.items()
        },
        "allocations": allocations,
        "tips": tips,
    }


# 工具名到实际 Python 函数的映射。
TOOL_FUNCTIONS: Dict[str, Callable[..., Any]] = {
    "search_products": search_products,
    "calculate_discount": calculate_discount,
    "budget_allocation": budget_allocation,
}


def execute_agent_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """执行模型选择的工具，并把异常转换为结构化错误。"""

    tool_function = TOOL_FUNCTIONS.get(tool_name)
    if tool_function is None:
        return {"error": f"未知工具：{tool_name}"}
    if not isinstance(arguments, dict):
        return {"error": "工具参数必须是 JSON 对象"}

    try:
        return tool_function(**arguments)
    except (TypeError, ValueError, RuntimeError) as error:
        logger.warning("工具 %s 执行失败：%s", tool_name, error)
        return {"error": f"工具 {tool_name} 执行失败：{error}"}
    except Exception as error:  # pragma: no cover - 最后一道安全兜底
        logger.exception("工具 %s 发生未预期异常", tool_name)
        return {"error": f"工具 {tool_name} 发生未预期异常：{error}"}
````


## 16. utils/env_utils.py

````python
"""环境变量读取工具。

所有敏感配置均从 .env 或部署平台注入的环境变量中读取，
源代码中不保存任何真实密钥。
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# 当前文件位于 <项目根目录>/utils/env_utils.py，
# 因此向上两级可以稳定定位到项目根目录，不依赖启动命令所在目录。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


def load_environment() -> bool:
    """加载项目根目录下的 .env 文件。

    Returns:
        bool: 成功找到并读取 .env 时返回 True，否则返回 False。

    Notes:
        override=False 表示系统中已有的环境变量优先级更高，
        可避免本地 .env 意外覆盖容器或部署平台注入的生产配置。
    """

    return load_dotenv(dotenv_path=ENV_FILE_PATH, override=False)


def get_env(
    variable_name: str,
    default: Optional[str] = None,
    required: bool = False,
) -> str:
    """读取字符串类型的环境变量。

    Args:
        variable_name: 环境变量名称。
        default: 环境变量不存在时使用的默认值。
        required: 是否为必填变量；为 True 且变量不存在时抛出异常。

    Returns:
        str: 去除首尾空格后的环境变量值。

    Raises:
        RuntimeError: 必填环境变量不存在或值为空时抛出。
    """

    raw_value = os.getenv(variable_name)

    # 未配置时优先使用显式默认值；required=True 则直接给出清晰错误。
    if raw_value is None or not raw_value.strip():
        if required:
            raise RuntimeError(f"缺少必需的环境变量：{variable_name}")
        return (default or "").strip()

    return raw_value.strip()


def get_bool_env(variable_name: str, default: bool = False) -> bool:
    """读取布尔类型环境变量。

    支持 true、1、yes、on（不区分大小写）作为真值，
    其他非空内容统一视为 False。
    """

    raw_value = get_env(variable_name)
    if not raw_value:
        return default

    return raw_value.lower() in {"true", "1", "yes", "on"}


def get_openai_api_key() -> str:
    """安全获取 OpenAI API 密钥。

    该函数不提供默认值，因此缺少配置时会立即报错，
    防止后续调用外部接口时使用无效或伪造的密钥。
    """

    return get_env("OPENAI_API_KEY", required=True)
````


## 17. data/__init__.py

````python
"""模拟数据包。

集中导出全生活消费场景的商户样例数据，便于业务层进行本地开发和接口联调。
真实项目中可将该层替换为数据库访问代码，同时保持服务层接口不变。
"""

from .mock_merchants import CAMPUS_MERCHANTS, LIFE_MERCHANTS

__all__ = ["CAMPUS_MERCHANTS", "LIFE_MERCHANTS"]
````


## 18. data/discount_rules.json

````json
{
  "full_reduction": [
    {
      "id": "FR_30_5",
      "name": "平台满30减5",
      "threshold": 30,
      "reduce": 5,
      "description": "单个平台订单满30元减5元。"
    },
    {
      "id": "FR_60_10",
      "name": "生活消费满60减10",
      "threshold": 60,
      "reduce": 10,
      "description": "单个平台订单满60元减10元。"
    },
    {
      "id": "FR_100_20",
      "name": "家庭采购满100减20",
      "threshold": 100,
      "reduce": 20,
      "description": "单个平台订单满100元减20元，适合家庭集中采购。"
    },
    {
      "id": "FR_200_45",
      "name": "品质生活满200减45",
      "threshold": 200,
      "reduce": 45,
      "description": "单个平台订单满200元减45元。"
    },
    {
      "id": "FR_300_70",
      "name": "大额采购满300减70",
      "threshold": 300,
      "reduce": 70,
      "description": "单个平台订单满300元减70元，适合家电、旅行和家庭集中采购。"
    }
  ],
  "bundle_rules": [
    {
      "id": "BUNDLE_FOOD_59_8",
      "name": "餐饮美食凑单满59减8",
      "threshold": 59,
      "reduce": 8,
      "category": "餐饮美食",
      "description": "餐饮美食订单满59元减8元，适合聚餐和家庭用餐。"
    },
    {
      "id": "BUNDLE_SNACK_59_8",
      "name": "零食饮料凑单满59减8",
      "threshold": 59,
      "reduce": 8,
      "category": "零食饮料",
      "description": "零食饮料订单满59元减8元，适合居家囤货。"
    },
    {
      "id": "BUNDLE_LIFE_79_12",
      "name": "商超日用凑单满79减12",
      "threshold": 79,
      "reduce": 12,
      "category": "生活用品",
      "description": "生活用品订单满79元减12元。"
    },
    {
      "id": "BUNDLE_HOME_99_15",
      "name": "家居生活满99减15",
      "threshold": 99,
      "reduce": 15,
      "category": "家居生活",
      "description": "家居生活订单满99元减15元。"
    },
    {
      "id": "BUNDLE_DIGITAL_150_25",
      "name": "数码家电凑单满150减25",
      "threshold": 150,
      "reduce": 25,
      "category": "数码家电",
      "description": "数码家电订单满150元减25元，适合耳机、小家电组合购买。"
    },
    {
      "id": "BUNDLE_TRAVEL_199_30",
      "name": "旅行住宿满199减30",
      "threshold": 199,
      "reduce": 30,
      "category": "旅游住宿",
      "description": "旅行住宿订单满199元减30元，适合周末出游。"
    }
  ],
  "member_discounts": [
    {
      "id": "MEMBER_95",
      "name": "生活会员95折",
      "type": "rate",
      "rate": 0.95,
      "min_spend": 30,
      "max_discount": 20,
      "description": "开通生活会员后，订单满30元享95折，最多优惠20元。"
    },
    {
      "id": "NEW_USER_99_15",
      "name": "新客专享满99减15",
      "type": "threshold",
      "threshold": 99,
      "reduce": 15,
      "min_spend": 99,
      "description": "新用户首单满99元减15元。"
    }
  ],
  "platform_offers": {
    "淘宝": {
      "id": "TAOBAO_LIFE_98",
      "name": "淘宝生活频道98折",
      "type": "rate",
      "rate": 0.98,
      "min_spend": 50,
      "max_discount": 10,
      "description": "淘宝生活频道订单满50元享98折，最多优惠10元。"
    },
    "拼多多": {
      "id": "PDD_LIFE_97",
      "name": "拼多多百亿补贴97折",
      "type": "rate",
      "rate": 0.97,
      "min_spend": 39,
      "max_discount": 12,
      "description": "拼多多百亿补贴订单满39元享97折，最多优惠12元。"
    },
    "京东": {
      "id": "JD_LIFE_98",
      "name": "京东生活会员98折",
      "type": "rate",
      "rate": 0.98,
      "min_spend": 59,
      "max_discount": 15,
      "description": "京东生活会员订单满59元享98折，最多优惠15元。"
    },
    "美团": {
      "id": "MEITUAN_LIFE_95",
      "name": "美团团购95折",
      "type": "rate",
      "rate": 0.95,
      "min_spend": 50,
      "max_discount": 12,
      "description": "美团团购订单满50元享95折，最多优惠12元。"
    },
    "携程": {
      "id": "CTRIP_TRAVEL_95",
      "name": "携程旅行95折",
      "type": "rate",
      "rate": 0.95,
      "min_spend": 199,
      "max_discount": 40,
      "description": "携程指定旅行产品满199元享95折，最多优惠40元。"
    }
  }
}
````


## 19. data/mock_merchants.py

````python
"""全生活消费场景的模拟商户数据。

数据字段说明：
- merchant_id：商户唯一编号；
- name：商户名称；
- category：消费分类；
- average_price：人均消费金额，单位为元；
- rating：综合评分，满分 5 分；
- distance_meters：距离用户的步行距离，单位为米；
- tags：用于辅助决策的特征标签；
- business_hours：营业时间。

该文件仅用于基础框架演示，不包含真实用户或商户隐私数据。
"""

from typing import Any, Dict, Tuple

LIFE_MERCHANTS: Tuple[Dict[str, Any], ...] = (
    {
        "merchant_id": "M001",
        "name": "社区家常菜馆",
        "category": "餐饮美食",
        "average_price": 32.0,
        "rating": 4.7,
        "distance_meters": 260,
        "tags": ["家常菜", "出餐快", "适合家庭"],
        "business_hours": "10:00-22:00",
    },
    {
        "merchant_id": "M002",
        "name": "商圈轻食餐厅",
        "category": "餐饮美食",
        "average_price": 45.0,
        "rating": 4.6,
        "distance_meters": 620,
        "tags": ["低卡", "健康", "工作餐"],
        "business_hours": "09:00-21:30",
    },
    {
        "merchant_id": "M003",
        "name": "城市咖啡角",
        "category": "餐饮美食",
        "average_price": 24.0,
        "rating": 4.5,
        "distance_meters": 340,
        "tags": ["咖啡", "下午茶", "可办公"],
        "business_hours": "08:00-22:00",
    },
    {
        "merchant_id": "M004",
        "name": "社区生鲜超市",
        "category": "商超日用",
        "average_price": 65.0,
        "rating": 4.6,
        "distance_meters": 420,
        "tags": ["生鲜", "日用品", "家庭采购"],
        "business_hours": "07:30-22:30",
    },
    {
        "merchant_id": "M005",
        "name": "邻里生活百货",
        "category": "商超日用",
        "average_price": 38.0,
        "rating": 4.4,
        "distance_meters": 280,
        "tags": ["日用百货", "营业时间长", "配送"],
        "business_hours": "08:00-23:00",
    },
    {
        "merchant_id": "M006",
        "name": "数码生活体验店",
        "category": "数码家电",
        "average_price": 280.0,
        "rating": 4.6,
        "distance_meters": 850,
        "tags": ["数码", "小家电", "售后"],
        "business_hours": "10:00-21:00",
    },
    {
        "merchant_id": "M007",
        "name": "城市服饰集合店",
        "category": "服饰鞋包",
        "average_price": 180.0,
        "rating": 4.4,
        "distance_meters": 760,
        "tags": ["通勤穿搭", "基础款", "可试穿"],
        "business_hours": "10:00-22:00",
    },
    {
        "merchant_id": "M008",
        "name": "安心大药房",
        "category": "健康医疗",
        "average_price": 58.0,
        "rating": 4.7,
        "distance_meters": 390,
        "tags": ["常用药品", "健康用品", "药师咨询"],
        "business_hours": "08:00-22:00",
    },
    {
        "merchant_id": "M009",
        "name": "城市书店与阅读空间",
        "category": "教育学习",
        "average_price": 50.0,
        "rating": 4.8,
        "distance_meters": 540,
        "tags": ["图书", "阅读", "文创"],
        "business_hours": "09:00-21:00",
    },
    {
        "merchant_id": "M010",
        "name": "社区电影院",
        "category": "文体娱乐",
        "average_price": 45.0,
        "rating": 4.5,
        "distance_meters": 680,
        "tags": ["电影", "周末活动", "双人优惠"],
        "business_hours": "10:00-23:30",
    },
    {
        "merchant_id": "M011",
        "name": "邻里健身中心",
        "category": "文体娱乐",
        "average_price": 35.0,
        "rating": 4.4,
        "distance_meters": 610,
        "tags": ["健身", "月卡", "器械"],
        "business_hours": "07:00-23:00",
    },
    {
        "merchant_id": "M012",
        "name": "萌宠生活馆",
        "category": "亲子宠物",
        "average_price": 95.0,
        "rating": 4.6,
        "distance_meters": 720,
        "tags": ["宠物用品", "洗护", "猫狗"],
        "business_hours": "09:00-21:00",
    },
    {
        "merchant_id": "M013",
        "name": "亲子成长中心",
        "category": "亲子宠物",
        "average_price": 120.0,
        "rating": 4.7,
        "distance_meters": 930,
        "tags": ["亲子活动", "益智", "周末"],
        "business_hours": "09:00-20:00",
    },
    {
        "merchant_id": "M014",
        "name": "城市周边旅行服务社",
        "category": "旅游住宿",
        "average_price": 450.0,
        "rating": 4.5,
        "distance_meters": 1100,
        "tags": ["周边游", "酒店", "门票"],
        "business_hours": "09:00-20:00",
    },
    {
        "merchant_id": "M015",
        "name": "到家保洁服务站",
        "category": "本地服务",
        "average_price": 130.0,
        "rating": 4.5,
        "distance_meters": 500,
        "tags": ["保洁", "家政", "上门服务"],
        "business_hours": "08:00-20:00",
    },
    {
        "merchant_id": "M016",
        "name": "社区维修服务点",
        "category": "本地服务",
        "average_price": 75.0,
        "rating": 4.3,
        "distance_meters": 450,
        "tags": ["家电维修", "上门检测", "便民"],
        "business_hours": "09:00-19:00",
    },
)

# 兼容旧代码与旧文档中的变量名，后续可逐步迁移到 LIFE_MERCHANTS。
CAMPUS_MERCHANTS = LIFE_MERCHANTS
````


## 20. data/products.json

````json
{
  "products": [
    {
      "id": "D001",
      "name": "入耳式有线耳机",
      "category": "数码配件",
      "price": 29.9,
      "platform": "淘宝",
      "rating": 4.5,
      "tags": [
        "耳机",
        "有线",
        "高性价比"
      ],
      "description": "带麦克风线控，适合线上会议和日常听歌。"
    },
    {
      "id": "D002",
      "name": "真无线蓝牙耳机",
      "category": "数码配件",
      "price": 89.0,
      "platform": "拼多多",
      "rating": 4.4,
      "tags": [
        "耳机",
        "蓝牙",
        "通勤"
      ],
      "description": "半入耳设计，续航约20小时，适合居家和通勤使用。"
    },
    {
      "id": "D003",
      "name": "32GB USB3.0 U盘",
      "category": "数码配件",
      "price": 24.9,
      "platform": "京东",
      "rating": 4.7,
      "tags": [
        "U盘",
        "存储",
        "学习资料"
      ],
      "description": "读取速度快，适合保存工作文件、学习资料和打印资料。"
    },
    {
      "id": "D004",
      "name": "10000mAh充电宝",
      "category": "数码配件",
      "price": 79.0,
      "platform": "淘宝",
      "rating": 4.6,
      "tags": [
        "充电宝",
        "便携",
        "居家"
      ],
      "description": "双向快充，机身轻便，适合办公室和短途出行。"
    },
    {
      "id": "D005",
      "name": "Type-C快充数据线1.5米",
      "category": "数码配件",
      "price": 12.9,
      "platform": "拼多多",
      "rating": 4.5,
      "tags": [
        "数据线",
        "快充",
        "手机配件"
      ],
      "description": "加长编织线身，支持常见安卓手机和轻薄本充电。"
    },
    {
      "id": "D006",
      "name": "桌面手机支架",
      "category": "数码配件",
      "price": 9.9,
      "platform": "淘宝",
      "rating": 4.4,
      "tags": [
        "手机支架",
        "桌面",
        "线上会议"
      ],
      "description": "可调节角度，适合居家追剧、线上会议和视频通话。"
    },
    {
      "id": "D007",
      "name": "无线静音鼠标",
      "category": "数码配件",
      "price": 39.9,
      "platform": "京东",
      "rating": 4.6,
      "tags": [
        "鼠标",
        "无线",
        "静音"
      ],
      "description": "静音按键设计，适合办公室和居家学习使用。"
    },
    {
      "id": "D008",
      "name": "便携蓝牙键盘",
      "category": "数码配件",
      "price": 69.0,
      "platform": "拼多多",
      "rating": 4.3,
      "tags": [
        "键盘",
        "蓝牙",
        "便携"
      ],
      "description": "紧凑布局，可连接手机和平板，适合移动记笔记。"
    },
    {
      "id": "D009",
      "name": "主动降噪蓝牙耳机",
      "category": "数码配件",
      "price": 149.0,
      "platform": "京东",
      "rating": 4.7,
      "tags": [
        "耳机",
        "降噪",
        "专注"
      ],
      "description": "支持主动降噪和通透模式，适合居家、通勤和安静办公环境。"
    },
    {
      "id": "D010",
      "name": "轻量半入耳蓝牙耳机",
      "category": "数码配件",
      "price": 59.9,
      "platform": "拼多多",
      "rating": 4.2,
      "tags": [
        "耳机",
        "蓝牙",
        "轻量",
        "高性价比"
      ],
      "description": "轻量半入耳设计，支持蓝牙连接，适合预算有限的日常听歌和线上会议。"
    },
    {
      "id": "D011",
      "name": "运动蓝牙耳机",
      "category": "数码配件",
      "price": 95.0,
      "platform": "淘宝",
      "rating": 4.5,
      "tags": [
        "耳机",
        "蓝牙",
        "运动",
        "防汗"
      ],
      "description": "挂耳式运动设计，支持蓝牙连接和防汗，适合跑步、通勤和学习使用。"
    },
    {
      "id": "B001",
      "name": "氨基酸洗面奶",
      "category": "美妆个护",
      "price": 29.9,
      "platform": "淘宝",
      "rating": 4.6,
      "tags": [
        "洗面奶",
        "温和",
        "清洁"
      ],
      "description": "温和清洁不紧绷，适合日常早晚洁面。"
    },
    {
      "id": "B002",
      "name": "补水保湿面膜10片",
      "category": "美妆个护",
      "price": 39.9,
      "platform": "拼多多",
      "rating": 4.4,
      "tags": [
        "面膜",
        "补水",
        "护肤"
      ],
      "description": "轻薄服帖，适合换季补水和熬夜后基础护理。"
    },
    {
      "id": "B003",
      "name": "滋润口红",
      "category": "美妆个护",
      "price": 49.9,
      "platform": "京东",
      "rating": 4.5,
      "tags": [
        "口红",
        "彩妆",
        "日常"
      ],
      "description": "日常显色色号，滋润不拔干，适合通勤和聚会活动。"
    },
    {
      "id": "B004",
      "name": "清爽防晒霜SPF50",
      "category": "美妆个护",
      "price": 59.9,
      "platform": "淘宝",
      "rating": 4.6,
      "tags": [
        "防晒",
        "清爽",
        "户外活动"
      ],
      "description": "清爽易推开，适合户外活动、运动和日常通勤。"
    },
    {
      "id": "B005",
      "name": "去屑洗发水500ml",
      "category": "美妆个护",
      "price": 32.9,
      "platform": "拼多多",
      "rating": 4.4,
      "tags": [
        "洗发水",
        "去屑",
        "大容量"
      ],
      "description": "清洁头皮并减少头屑，大容量适合家庭长期使用。"
    },
    {
      "id": "B006",
      "name": "清香沐浴露500ml",
      "category": "美妆个护",
      "price": 27.9,
      "platform": "京东",
      "rating": 4.5,
      "tags": [
        "沐浴露",
        "清香",
        "洗护"
      ],
      "description": "泡沫细腻易冲洗，适合日常洗护。"
    },
    {
      "id": "B007",
      "name": "保湿护手霜",
      "category": "美妆个护",
      "price": 15.9,
      "platform": "淘宝",
      "rating": 4.6,
      "tags": [
        "护手霜",
        "保湿",
        "便携"
      ],
      "description": "小支便携，适合秋冬季节随身补涂。"
    },
    {
      "id": "B008",
      "name": "温和卸妆水300ml",
      "category": "美妆个护",
      "price": 35.9,
      "platform": "拼多多",
      "rating": 4.3,
      "tags": [
        "卸妆水",
        "温和",
        "彩妆"
      ],
      "description": "可卸除日常防晒和淡妆，使用后不黏腻。"
    },
    {
      "id": "B009",
      "name": "新手基础彩妆套装",
      "category": "美妆个护",
      "price": 79.9,
      "platform": "京东",
      "rating": 4.2,
      "tags": [
        "彩妆",
        "套装",
        "新手"
      ],
      "description": "包含底妆和基础眼妆用品，适合新手聚会活动使用。"
    },
    {
      "id": "S001",
      "name": "红烧牛肉泡面5连包",
      "category": "零食饮料",
      "price": 19.9,
      "platform": "拼多多",
      "rating": 4.7,
      "tags": [
        "泡面",
        "速食",
        "夜宵"
      ],
      "description": "经典口味五连包，适合居家夜宵和应急加餐。"
    },
    {
      "id": "S002",
      "name": "纯牛奶250ml×12盒",
      "category": "零食饮料",
      "price": 39.9,
      "platform": "京东",
      "rating": 4.8,
      "tags": [
        "牛奶",
        "早餐",
        "整箱"
      ],
      "description": "整箱装常温纯牛奶，适合早餐和日常补充蛋白质。"
    },
    {
      "id": "S003",
      "name": "原味薯片3连包",
      "category": "零食饮料",
      "price": 15.9,
      "platform": "淘宝",
      "rating": 4.4,
      "tags": [
        "薯片",
        "零食",
        "分享"
      ],
      "description": "小包装组合，适合居家追剧和朋友分享。"
    },
    {
      "id": "S004",
      "name": "早餐饼干2斤",
      "category": "零食饮料",
      "price": 12.9,
      "platform": "拼多多",
      "rating": 4.3,
      "tags": [
        "饼干",
        "早餐",
        "囤货"
      ],
      "description": "独立小包方便携带，适合早八赶课和课间加餐。"
    },
    {
      "id": "S005",
      "name": "即食燕麦片1kg",
      "category": "零食饮料",
      "price": 25.9,
      "platform": "京东",
      "rating": 4.6,
      "tags": [
        "燕麦",
        "早餐",
        "健康"
      ],
      "description": "热水冲泡即可食用，适合居家早餐和轻食搭配。"
    },
    {
      "id": "S006",
      "name": "矿泉水550ml×24瓶",
      "category": "零食饮料",
      "price": 24.9,
      "platform": "淘宝",
      "rating": 4.5,
      "tags": [
        "矿泉水",
        "整箱",
        "居家"
      ],
      "description": "整箱饮用水，适合居家、户外活动和聚会活动储备。"
    },
    {
      "id": "S007",
      "name": "无糖乌龙茶500ml×6瓶",
      "category": "零食饮料",
      "price": 19.9,
      "platform": "拼多多",
      "rating": 4.4,
      "tags": [
        "茶饮",
        "无糖",
        "解腻"
      ],
      "description": "无糖茶饮组合装，适合通勤和聚餐后饮用。"
    },
    {
      "id": "S008",
      "name": "每日坚果20小包",
      "category": "零食饮料",
      "price": 29.9,
      "platform": "京东",
      "rating": 4.6,
      "tags": [
        "坚果",
        "健康",
        "课间"
      ],
      "description": "独立小包装，方便课间补充能量和控制食用量。"
    },
    {
      "id": "S009",
      "name": "辣条混合装20包",
      "category": "零食饮料",
      "price": 9.9,
      "platform": "淘宝",
      "rating": 4.3,
      "tags": [
        "辣条",
        "零食",
        "居家"
      ],
      "description": "多种口味混合装，适合居家分享和休闲零食储备。"
    },
    {
      "id": "L001",
      "name": "抽纸3层24包",
      "category": "生活用品",
      "price": 29.9,
      "platform": "拼多多",
      "rating": 4.7,
      "tags": [
        "纸巾",
        "抽纸",
        "居家囤货"
      ],
      "description": "原生木浆抽纸整箱装，适合家庭长期使用。"
    },
    {
      "id": "L002",
      "name": "洗衣液2kg",
      "category": "生活用品",
      "price": 24.9,
      "platform": "京东",
      "rating": 4.6,
      "tags": [
        "洗衣液",
        "清洁",
        "大容量"
      ],
      "description": "低泡易漂洗，适合手洗和居家公共洗衣机。"
    },
    {
      "id": "L003",
      "name": "晴雨两用折叠伞",
      "category": "生活用品",
      "price": 19.9,
      "platform": "淘宝",
      "rating": 4.4,
      "tags": [
        "雨伞",
        "防晒",
        "便携"
      ],
      "description": "轻量折叠设计，晴天防晒、雨天挡雨，适合随身携带。"
    },
    {
      "id": "L004",
      "name": "软毛牙刷牙膏套装",
      "category": "生活用品",
      "price": 16.9,
      "platform": "拼多多",
      "rating": 4.5,
      "tags": [
        "牙刷",
        "牙膏",
        "洗漱"
      ],
      "description": "软毛牙刷搭配牙膏，满足居家日常洗漱需求。"
    },
    {
      "id": "L005",
      "name": "纯棉毛巾3条装",
      "category": "生活用品",
      "price": 19.9,
      "platform": "淘宝",
      "rating": 4.4,
      "tags": [
        "毛巾",
        "纯棉",
        "居家"
      ],
      "description": "吸水柔软的纯棉毛巾，三条装方便换洗。"
    },
    {
      "id": "L006",
      "name": "桌面收纳盒",
      "category": "生活用品",
      "price": 14.9,
      "platform": "拼多多",
      "rating": 4.3,
      "tags": [
        "收纳",
        "桌面",
        "居家"
      ],
      "description": "分区收纳文具和杂物，让居家桌面更整洁。"
    },
    {
      "id": "L007",
      "name": "防滑衣架20个",
      "category": "生活用品",
      "price": 12.9,
      "platform": "淘宝",
      "rating": 4.4,
      "tags": [
        "衣架",
        "防滑",
        "居家"
      ],
      "description": "轻薄防滑设计，适合居家衣柜和晾晒衣物。"
    },
    {
      "id": "L008",
      "name": "居家小垃圾桶",
      "category": "生活用品",
      "price": 15.9,
      "platform": "京东",
      "rating": 4.5,
      "tags": [
        "垃圾桶",
        "桌面",
        "居家"
      ],
      "description": "带盖小容量垃圾桶，适合书桌旁和居家床位使用。"
    },
    {
      "id": "L009",
      "name": "不锈钢保温杯",
      "category": "生活用品",
      "price": 39.9,
      "platform": "淘宝",
      "rating": 4.7,
      "tags": [
        "保温杯",
        "水杯",
        "通勤"
      ],
      "description": "长效保温保冷，容量适中，适合通勤和专注携带。"
    },
    {
      "id": "G001",
      "name": "简约定制笔记本",
      "category": "礼品文创",
      "price": 9.9,
      "platform": "拼多多",
      "rating": 4.6,
      "tags": [
        "笔记本",
        "学习",
        "文创"
      ],
      "description": "简约主题封面，内页顺滑，适合课堂记录和送礼。"
    },
    {
      "id": "G002",
      "name": "商务钢笔礼盒",
      "category": "礼品文创",
      "price": 39.9,
      "platform": "淘宝",
      "rating": 4.5,
      "tags": [
        "钢笔",
        "礼盒",
        "生日礼物"
      ],
      "description": "含钢笔、墨囊和包装盒，适合生日或毕业赠礼。"
    },
    {
      "id": "G003",
      "name": "桌面励志摆件",
      "category": "礼品文创",
      "price": 19.9,
      "platform": "拼多多",
      "rating": 4.3,
      "tags": [
        "摆件",
        "桌面",
        "礼物"
      ],
      "description": "小巧桌面装饰，适合送给朋友或布置书桌。"
    },
    {
      "id": "G004",
      "name": "文创帆布包",
      "category": "礼品文创",
      "price": 29.9,
      "platform": "淘宝",
      "rating": 4.6,
      "tags": [
        "帆布包",
        "实用",
        "文创"
      ],
      "description": "大容量帆布托特包，适合通勤、购物和日常出行。"
    },
    {
      "id": "G005",
      "name": "复古手账套装",
      "category": "礼品文创",
      "price": 35.9,
      "platform": "京东",
      "rating": 4.7,
      "tags": [
        "手账",
        "文具",
        "礼物"
      ],
      "description": "含手账本、贴纸和胶带，适合记录日常生活和送礼。"
    },
    {
      "id": "G006",
      "name": "古风书签礼盒",
      "category": "礼品文创",
      "price": 15.9,
      "platform": "淘宝",
      "rating": 4.5,
      "tags": [
        "书签",
        "礼盒",
        "文创"
      ],
      "description": "多款古风书签组合，适合读书爱好者和小型伴手礼。"
    },
    {
      "id": "G007",
      "name": "香薰蜡烛礼盒",
      "category": "礼品文创",
      "price": 49.9,
      "platform": "拼多多",
      "rating": 4.4,
      "tags": [
        "香薰",
        "蜡烛",
        "生日礼物"
      ],
      "description": "淡香型香薰蜡烛组合，适合居家氛围布置和生日赠礼。"
    },
    {
      "id": "G008",
      "name": "定制照片相框",
      "category": "礼品文创",
      "price": 29.9,
      "platform": "京东",
      "rating": 4.6,
      "tags": [
        "相框",
        "定制",
        "纪念礼物"
      ],
      "description": "可放入生活合照或生活照片，适合纪念日和毕业礼物。"
    },
    {
      "id": "G009",
      "name": "毕业纪念册",
      "category": "礼品文创",
      "price": 59.9,
      "platform": "淘宝",
      "rating": 4.8,
      "tags": [
        "纪念册",
        "毕业",
        "礼物"
      ],
      "description": "可书写留言的纪念册，适合集体纪念和毕业留念。"
    },
    {
      "id": "F001",
      "name": "双人火锅套餐",
      "category": "餐饮美食",
      "price": 158.0,
      "platform": "美团",
      "rating": 4.7,
      "tags": [
        "火锅",
        "双人餐",
        "周末聚餐"
      ],
      "description": "含锅底、荤素拼盘和饮品，适合朋友或情侣聚餐。"
    },
    {
      "id": "F002",
      "name": "家庭披萨套餐",
      "category": "餐饮美食",
      "price": 99.0,
      "platform": "饿了么",
      "rating": 4.5,
      "tags": [
        "披萨",
        "家庭餐",
        "外卖"
      ],
      "description": "含大份披萨、小食和饮料，适合家庭简餐或朋友分享。"
    },
    {
      "id": "F003",
      "name": "工作日轻食午餐券",
      "category": "餐饮美食",
      "price": 29.9,
      "platform": "美团",
      "rating": 4.6,
      "tags": [
        "午餐",
        "轻食",
        "工作餐"
      ],
      "description": "可选沙拉、鸡胸肉和谷物饭，适合工作日快速用餐。"
    },
    {
      "id": "F004",
      "name": "咖啡饮品兑换券",
      "category": "餐饮美食",
      "price": 19.9,
      "platform": "美团",
      "rating": 4.5,
      "tags": [
        "咖啡",
        "饮品",
        "下午茶"
      ],
      "description": "可用于指定咖啡或茶饮，适合通勤和下午茶场景。"
    },
    {
      "id": "F005",
      "name": "生鲜蔬菜周套餐",
      "category": "餐饮美食",
      "price": 69.0,
      "platform": "京东到家",
      "rating": 4.4,
      "tags": [
        "生鲜",
        "蔬菜",
        "家庭采购"
      ],
      "description": "包含多种当季蔬菜，适合家庭一周基础食材补充。"
    },
    {
      "id": "F006",
      "name": "家庭米面粮油组合",
      "category": "餐饮美食",
      "price": 129.0,
      "platform": "京东",
      "rating": 4.7,
      "tags": [
        "粮油",
        "家庭采购",
        "囤货"
      ],
      "description": "大米、面粉和食用油基础组合，适合家庭日常储备。"
    },
    {
      "id": "W001",
      "name": "基础纯棉T恤",
      "category": "服饰鞋包",
      "price": 59.9,
      "platform": "淘宝",
      "rating": 4.5,
      "tags": [
        "T恤",
        "纯棉",
        "日常穿搭"
      ],
      "description": "版型简洁，适合通勤、休闲和叠穿。"
    },
    {
      "id": "W002",
      "name": "通勤双肩包",
      "category": "服饰鞋包",
      "price": 129.0,
      "platform": "京东",
      "rating": 4.6,
      "tags": [
        "双肩包",
        "通勤",
        "电脑包"
      ],
      "description": "带独立电脑隔层，适合上班、短途出行和日常使用。"
    },
    {
      "id": "W003",
      "name": "轻量运动鞋",
      "category": "服饰鞋包",
      "price": 199.0,
      "platform": "拼多多",
      "rating": 4.4,
      "tags": [
        "运动鞋",
        "轻量",
        "跑步"
      ],
      "description": "缓震鞋底和透气鞋面，适合日常步行与轻度运动。"
    },
    {
      "id": "W004",
      "name": "保暖针织外套",
      "category": "服饰鞋包",
      "price": 159.0,
      "platform": "淘宝",
      "rating": 4.5,
      "tags": [
        "外套",
        "保暖",
        "秋冬"
      ],
      "description": "柔软针织面料，适合换季通勤和日常外搭。"
    },
    {
      "id": "W005",
      "name": "居家防滑拖鞋",
      "category": "服饰鞋包",
      "price": 29.9,
      "platform": "拼多多",
      "rating": 4.3,
      "tags": [
        "拖鞋",
        "防滑",
        "居家"
      ],
      "description": "轻便防滑，适合家庭日常和浴室使用。"
    },
    {
      "id": "A001",
      "name": "迷你电饭煲",
      "category": "数码家电",
      "price": 159.0,
      "platform": "京东",
      "rating": 4.6,
      "tags": [
        "电饭煲",
        "小家电",
        "租房"
      ],
      "description": "小容量多功能设计，适合独居、租房和小家庭使用。"
    },
    {
      "id": "A002",
      "name": "家用空气炸锅",
      "category": "数码家电",
      "price": 199.0,
      "platform": "拼多多",
      "rating": 4.5,
      "tags": [
        "空气炸锅",
        "厨房电器",
        "家庭"
      ],
      "description": "操作简单，适合日常快手烹饪和家庭加餐。"
    },
    {
      "id": "A003",
      "name": "便携蓝牙音箱",
      "category": "数码家电",
      "price": 99.0,
      "platform": "淘宝",
      "rating": 4.4,
      "tags": [
        "音箱",
        "蓝牙",
        "户外"
      ],
      "description": "小巧便携，适合居家听歌、露营和短途出游。"
    },
    {
      "id": "A004",
      "name": "手持挂烫机",
      "category": "数码家电",
      "price": 129.0,
      "platform": "京东",
      "rating": 4.5,
      "tags": [
        "挂烫机",
        "衣物护理",
        "通勤"
      ],
      "description": "快速预热，适合通勤衣物除皱和日常护理。"
    },
    {
      "id": "J001",
      "name": "多功能不粘锅",
      "category": "家居生活",
      "price": 129.0,
      "platform": "京东",
      "rating": 4.6,
      "tags": [
        "锅具",
        "厨房",
        "租房"
      ],
      "description": "煎炒煮一体，适合独居和家庭日常烹饪。"
    },
    {
      "id": "J002",
      "name": "家用保温电热水壶",
      "category": "家居生活",
      "price": 79.9,
      "platform": "淘宝",
      "rating": 4.5,
      "tags": [
        "电热水壶",
        "厨房",
        "保温"
      ],
      "description": "自动断电和保温功能，满足家庭日常饮水需求。"
    },
    {
      "id": "J003",
      "name": "全棉四件套",
      "category": "家居生活",
      "price": 199.0,
      "platform": "拼多多",
      "rating": 4.5,
      "tags": [
        "床品",
        "四件套",
        "换新"
      ],
      "description": "亲肤棉质面料，适合卧室换季和乔迁布置。"
    },
    {
      "id": "J004",
      "name": "折叠收纳柜",
      "category": "家居生活",
      "price": 89.0,
      "platform": "京东",
      "rating": 4.4,
      "tags": [
        "收纳",
        "储物",
        "租房"
      ],
      "description": "多层折叠结构，适合小户型、租房和杂物整理。"
    },
    {
      "id": "J005",
      "name": "家用净水壶",
      "category": "家居生活",
      "price": 99.0,
      "platform": "淘宝",
      "rating": 4.5,
      "tags": [
        "净水壶",
        "饮水",
        "家庭"
      ],
      "description": "过滤水垢和杂质，适合租房及家庭日常饮水。"
    },
    {
      "id": "X001",
      "name": "电子体温计",
      "category": "健康医疗",
      "price": 29.9,
      "platform": "京东",
      "rating": 4.7,
      "tags": [
        "体温计",
        "健康监测",
        "家庭"
      ],
      "description": "快速测温，适合家庭日常健康监测。"
    },
    {
      "id": "X002",
      "name": "家庭急救包",
      "category": "健康医疗",
      "price": 49.9,
      "platform": "淘宝",
      "rating": 4.6,
      "tags": [
        "急救",
        "家庭",
        "常备"
      ],
      "description": "含基础消毒、包扎和固定用品，适合家庭应急储备。"
    },
    {
      "id": "X003",
      "name": "复合维生素60片",
      "category": "健康医疗",
      "price": 69.0,
      "platform": "京东",
      "rating": 4.5,
      "tags": [
        "维生素",
        "营养",
        "日常补充"
      ],
      "description": "日常营养补充产品，使用前请按说明并结合个人情况选择。"
    },
    {
      "id": "X004",
      "name": "医用外科口罩50只",
      "category": "健康医疗",
      "price": 24.9,
      "platform": "拼多多",
      "rating": 4.7,
      "tags": [
        "口罩",
        "防护",
        "家庭"
      ],
      "description": "独立包装，适合家庭日常防护和出行备用。"
    },
    {
      "id": "X005",
      "name": "颈椎热敷贴",
      "category": "健康医疗",
      "price": 39.9,
      "platform": "淘宝",
      "rating": 4.4,
      "tags": [
        "热敷",
        "颈肩",
        "居家护理"
      ],
      "description": "温热敷贴，适合久坐后居家放松，不替代医疗诊疗。"
    },
    {
      "id": "T001",
      "name": "共享单车月卡",
      "category": "交通出行",
      "price": 16.8,
      "platform": "美团",
      "rating": 4.6,
      "tags": [
        "单车",
        "月卡",
        "通勤"
      ],
      "description": "适合短距离通勤和接驳，使用范围以平台规则为准。"
    },
    {
      "id": "T002",
      "name": "地铁10次乘车券",
      "category": "交通出行",
      "price": 30.0,
      "platform": "支付宝",
      "rating": 4.7,
      "tags": [
        "地铁",
        "通勤",
        "乘车券"
      ],
      "description": "适合日常通勤，覆盖城市地铁基础出行需求。"
    },
    {
      "id": "T003",
      "name": "网约车20元券包",
      "category": "交通出行",
      "price": 15.9,
      "platform": "滴滴出行",
      "rating": 4.3,
      "tags": [
        "打车",
        "优惠券",
        "出行"
      ],
      "description": "含多张小额打车券，适合雨天、夜间和赶时间出行。"
    },
    {
      "id": "T004",
      "name": "加油200元券包",
      "category": "交通出行",
      "price": 189.0,
      "platform": "易捷",
      "rating": 4.5,
      "tags": [
        "加油",
        "自驾",
        "用车"
      ],
      "description": "适合自驾通勤和家庭用车，具体适用站点以平台为准。"
    },
    {
      "id": "E001",
      "name": "在线课程月卡",
      "category": "教育学习",
      "price": 99.0,
      "platform": "京东",
      "rating": 4.4,
      "tags": [
        "在线课程",
        "技能提升",
        "学习"
      ],
      "description": "可学习平台指定课程，适合职业技能和兴趣提升。"
    },
    {
      "id": "E002",
      "name": "电子书平台月卡",
      "category": "教育学习",
      "price": 25.0,
      "platform": "淘宝",
      "rating": 4.6,
      "tags": [
        "电子书",
        "阅读",
        "会员"
      ],
      "description": "适合日常阅读和知识拓展，具体书库以平台说明为准。"
    },
    {
      "id": "E003",
      "name": "A4打印纸500张",
      "category": "教育学习",
      "price": 24.9,
      "platform": "京东",
      "rating": 4.7,
      "tags": [
        "打印纸",
        "办公",
        "居家学习"
      ],
      "description": "适合家庭打印、办公资料和孩子作业使用。"
    },
    {
      "id": "E004",
      "name": "英语口语练习课程",
      "category": "教育学习",
      "price": 129.0,
      "platform": "拼多多",
      "rating": 4.3,
      "tags": [
        "英语",
        "口语",
        "课程"
      ],
      "description": "包含情景练习和发音训练，适合业余时间自主学习。"
    },
    {
      "id": "R001",
      "name": "电影双人票",
      "category": "文体娱乐",
      "price": 79.9,
      "platform": "美团",
      "rating": 4.6,
      "tags": [
        "电影",
        "双人",
        "约会"
      ],
      "description": "适合情侣、朋友或家人周末观影，具体影院以平台为准。"
    },
    {
      "id": "R002",
      "name": "健身房月卡",
      "category": "文体娱乐",
      "price": 199.0,
      "platform": "美团",
      "rating": 4.4,
      "tags": [
        "健身",
        "月卡",
        "运动"
      ],
      "description": "可在指定门店使用，适合建立短期运动习惯。"
    },
    {
      "id": "R003",
      "name": "家庭桌游套装",
      "category": "文体娱乐",
      "price": 89.0,
      "platform": "淘宝",
      "rating": 4.7,
      "tags": [
        "桌游",
        "家庭",
        "聚会"
      ],
      "description": "适合家庭聚会和朋友互动，包含多种基础玩法。"
    },
    {
      "id": "R004",
      "name": "城市博物馆通票",
      "category": "文体娱乐",
      "price": 60.0,
      "platform": "携程",
      "rating": 4.8,
      "tags": [
        "博物馆",
        "城市游",
        "文化"
      ],
      "description": "覆盖多个合作场馆，适合周末城市文化游览。"
    },
    {
      "id": "P001",
      "name": "全价猫粮2kg",
      "category": "亲子宠物",
      "price": 89.0,
      "platform": "京东",
      "rating": 4.6,
      "tags": [
        "猫粮",
        "宠物",
        "囤货"
      ],
      "description": "适合成年猫日常喂养，换粮时请循序渐进。"
    },
    {
      "id": "P002",
      "name": "豆腐猫砂10L",
      "category": "亲子宠物",
      "price": 39.9,
      "platform": "拼多多",
      "rating": 4.5,
      "tags": [
        "猫砂",
        "宠物",
        "清洁"
      ],
      "description": "结团和吸味表现稳定，适合猫咪家庭日常清洁。"
    },
    {
      "id": "P003",
      "name": "宠物互动玩具",
      "category": "亲子宠物",
      "price": 29.9,
      "platform": "淘宝",
      "rating": 4.4,
      "tags": [
        "宠物玩具",
        "互动",
        "猫狗"
      ],
      "description": "适合日常陪伴和互动，使用时请注意宠物安全。"
    },
    {
      "id": "P004",
      "name": "儿童益智积木",
      "category": "亲子宠物",
      "price": 79.0,
      "platform": "京东",
      "rating": 4.7,
      "tags": [
        "儿童",
        "积木",
        "亲子"
      ],
      "description": "适合亲子互动和动手能力培养，请按年龄说明使用。"
    },
    {
      "id": "P005",
      "name": "亲子乐园双人票",
      "category": "亲子宠物",
      "price": 99.0,
      "platform": "美团",
      "rating": 4.5,
      "tags": [
        "亲子",
        "乐园",
        "周末"
      ],
      "description": "适合家长带孩子周末游玩，具体场次以平台为准。"
    },
    {
      "id": "V001",
      "name": "城市周边酒店1晚",
      "category": "旅游住宿",
      "price": 399.0,
      "platform": "携程",
      "rating": 4.6,
      "tags": [
        "酒店",
        "周边游",
        "周末"
      ],
      "description": "适合周末短途住宿，房型和日期以平台库存为准。"
    },
    {
      "id": "V002",
      "name": "景区成人门票",
      "category": "旅游住宿",
      "price": 88.0,
      "platform": "飞猪",
      "rating": 4.7,
      "tags": [
        "景区",
        "门票",
        "出游"
      ],
      "description": "适合城市周边景点游玩，使用日期以票面规则为准。"
    },
    {
      "id": "V003",
      "name": "旅行收纳套装",
      "category": "旅游住宿",
      "price": 49.9,
      "platform": "淘宝",
      "rating": 4.5,
      "tags": [
        "旅行收纳",
        "行李",
        "出游"
      ],
      "description": "分类整理衣物和随身用品，提升短途出行效率。"
    },
    {
      "id": "V004",
      "name": "周末民宿双人套餐",
      "category": "旅游住宿",
      "price": 499.0,
      "platform": "美团",
      "rating": 4.5,
      "tags": [
        "民宿",
        "双人",
        "度假"
      ],
      "description": "含指定民宿住宿和早餐，适合周末放松。"
    },
    {
      "id": "V005",
      "name": "机场接送服务券",
      "category": "旅游住宿",
      "price": 120.0,
      "platform": "高德",
      "rating": 4.4,
      "tags": [
        "接送机",
        "旅行",
        "交通"
      ],
      "description": "适合机场往返接驳，需提前预约并确认服务范围。"
    },
    {
      "id": "LS001",
      "name": "家政保洁2小时",
      "category": "本地服务",
      "price": 129.0,
      "platform": "美团",
      "rating": 4.5,
      "tags": [
        "保洁",
        "家政",
        "家庭"
      ],
      "description": "适合日常家庭清洁，服务内容和范围以商家说明为准。"
    },
    {
      "id": "LS002",
      "name": "空调清洗服务",
      "category": "本地服务",
      "price": 99.0,
      "platform": "京东服务",
      "rating": 4.6,
      "tags": [
        "空调清洗",
        "家电服务",
        "家庭"
      ],
      "description": "上门清洗单台空调，具体型号和加价规则以平台为准。"
    },
    {
      "id": "LS003",
      "name": "洗衣鞋洗护券",
      "category": "本地服务",
      "price": 49.9,
      "platform": "美团",
      "rating": 4.5,
      "tags": [
        "洗鞋",
        "衣物洗护",
        "本地服务"
      ],
      "description": "适合运动鞋和日常衣物洗护，特殊材质可能需补差价。"
    },
    {
      "id": "LS004",
      "name": "家电维修上门检测",
      "category": "本地服务",
      "price": 59.0,
      "platform": "美团",
      "rating": 4.3,
      "tags": [
        "维修",
        "家电",
        "上门服务"
      ],
      "description": "含上门检测，维修配件费用需另行确认。"
    },
    {
      "id": "LS005",
      "name": "同城搬家基础套餐",
      "category": "本地服务",
      "price": 299.0,
      "platform": "货拉拉",
      "rating": 4.4,
      "tags": [
        "搬家",
        "同城",
        "租房"
      ],
      "description": "适合基础同城搬家，楼层和里程费用以平台报价为准。"
    },
    {
      "id": "CS001",
      "name": "家庭清洁用品组合",
      "category": "商超日用",
      "price": 69.0,
      "platform": "京东",
      "rating": 4.7,
      "tags": [
        "清洁",
        "家庭采购",
        "组合装"
      ],
      "description": "含清洁剂、抹布和手套，适合家庭日常清洁。"
    },
    {
      "id": "CS002",
      "name": "抽纸24包整箱",
      "category": "商超日用",
      "price": 49.9,
      "platform": "拼多多",
      "rating": 4.6,
      "tags": [
        "抽纸",
        "家庭装",
        "囤货"
      ],
      "description": "家庭量贩装，适合客厅、卧室和厨房日常使用。"
    },
    {
      "id": "CS003",
      "name": "洗衣液家庭组合装",
      "category": "商超日用",
      "price": 79.0,
      "platform": "京东",
      "rating": 4.5,
      "tags": [
        "洗衣液",
        "家庭装",
        "洗护"
      ],
      "description": "大容量组合装，适合家庭日常衣物清洁。"
    },
    {
      "id": "CS004",
      "name": "加厚垃圾袋100只",
      "category": "商超日用",
      "price": 19.9,
      "platform": "淘宝",
      "rating": 4.4,
      "tags": [
        "垃圾袋",
        "日用",
        "家庭"
      ],
      "description": "加厚防漏设计，适合厨房和客厅日常使用。"
    },
    {
      "id": "CS005",
      "name": "家庭洗漱补充装组合",
      "category": "商超日用",
      "price": 59.9,
      "platform": "拼多多",
      "rating": 4.5,
      "tags": [
        "洗漱",
        "补充装",
        "家庭"
      ],
      "description": "含洗手液和沐浴露补充装，适合家庭日常消耗。"
    }
  ]
}
````


## 21. index.html

````html
<!DOCTYPE html>
<html lang="zh-CN" class="scroll-smooth">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="全场景生活消费决策智能体：智能咨询、预算管理与消费复盘。" />
  <title>全场景生活消费决策智能体</title>

  <!-- 单文件页面使用 Tailwind Play CDN；业务 CSS 和全部 JavaScript 均内嵌。 -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: {
              50: "#eff6ff", 100: "#dbeafe", 200: "#bfdbfe", 300: "#93c5fd",
              400: "#60a5fa", 500: "#3b82f6", 600: "#2563eb", 700: "#1d4ed8",
              800: "#1e40af", 900: "#1e3a8a"
            }
          },
          boxShadow: {
            soft: "0 18px 45px -22px rgba(37, 99, 235, 0.28)",
            card: "0 16px 38px -24px rgba(15, 23, 42, 0.22)"
          },
          fontFamily: {
            sans: ["Inter", "PingFang SC", "Microsoft YaHei", "system-ui", "sans-serif"]
          }
        }
      }
    };
  </script>

  <style>
    :root { --brand: #2563eb; --brand-dark: #1d4ed8; --ink: #0f172a; --muted: #64748b; }
    * { box-sizing: border-box; }
    html, body { min-height: 100%; }
    body {
      color: var(--ink);
      background:
        radial-gradient(circle at 8% 2%, rgba(96, 165, 250, 0.18), transparent 28rem),
        radial-gradient(circle at 92% 12%, rgba(191, 219, 254, 0.42), transparent 30rem),
        #f8fbff;
      font-family: Inter, "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
    }
    button, input, textarea, select { font: inherit; }
    button:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible {
      outline: 3px solid rgba(59, 130, 246, 0.25); outline-offset: 2px;
    }
    .page-section { animation: pageIn 260ms ease-out; }
    .nav-tab { position: relative; transition: color 180ms ease, background-color 180ms ease, transform 180ms ease; }
    .nav-tab:hover { transform: translateY(-1px); }
    .nav-tab.active { color: #1d4ed8; background: #eff6ff; }
    .nav-tab.active::after {
      content: ""; position: absolute; left: 22%; right: 22%; bottom: 2px;
      height: 2px; border-radius: 999px; background: linear-gradient(90deg, #60a5fa, #2563eb);
    }
    .soft-card {
      border: 1px solid rgba(226, 232, 240, 0.9);
      background: rgba(255, 255, 255, 0.92);
      box-shadow: 0 16px 38px -24px rgba(15, 23, 42, 0.22);
      backdrop-filter: blur(16px);
    }
    .chat-scroll, .records-scroll { scrollbar-width: thin; scrollbar-color: #bfdbfe transparent; }
    .chat-scroll::-webkit-scrollbar, .records-scroll::-webkit-scrollbar { width: 7px; }
    .chat-scroll::-webkit-scrollbar-thumb, .records-scroll::-webkit-scrollbar-thumb {
      border-radius: 999px; background: #bfdbfe;
    }
    .message-row { animation: messageIn 240ms ease-out both; }
    .typing-dots { display: inline-flex; gap: 4px; align-items: center; }
    .typing-dots span {
      width: 6px; height: 6px; border-radius: 999px; background: #60a5fa;
      animation: typing 1.1s infinite ease-in-out;
    }
    .typing-dots span:nth-child(2) { animation-delay: 120ms; }
    .typing-dots span:nth-child(3) { animation-delay: 240ms; }
    .spinner {
      width: 16px; height: 16px; border: 2px solid rgba(255, 255, 255, 0.35);
      border-top-color: #ffffff; border-radius: 999px; animation: spin 700ms linear infinite;
    }
    .plan-card { transition: transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease; }
    .plan-card:hover {
      transform: translateY(-4px); border-color: #93c5fd;
      box-shadow: 0 22px 45px -24px rgba(37, 99, 235, 0.4);
    }
    .prompt-chip { transition: transform 180ms ease, border-color 180ms ease, background-color 180ms ease; }
    .prompt-chip:hover { transform: translateY(-2px); border-color: #93c5fd; background: #eff6ff; }
    .primary-button {
      background: linear-gradient(135deg, #3b82f6, #2563eb 55%, #1d4ed8);
      box-shadow: 0 10px 22px -12px rgba(37, 99, 235, 0.8);
      transition: transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease;
    }
    .primary-button:hover:not(:disabled) {
      transform: translateY(-1px); box-shadow: 0 14px 28px -12px rgba(37, 99, 235, 0.9);
    }
    .primary-button:active:not(:disabled) { transform: translateY(0); }
    .primary-button:disabled { cursor: not-allowed; opacity: 0.62; }
    .period-button { transition: all 180ms ease; }
    .period-button.active {
      color: #ffffff; background: linear-gradient(135deg, #3b82f6, #2563eb);
      box-shadow: 0 8px 18px -10px rgba(37, 99, 235, 0.85);
    }
    .status-dot {
      width: 8px; height: 8px; border-radius: 999px; background: #94a3b8;
      box-shadow: 0 0 0 4px rgba(148, 163, 184, 0.12);
    }
    .status-dot.online { background: #22c55e; box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.14); }
    .status-dot.error { background: #ef4444; box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.14); }
    .budget-progress { transition: width 500ms cubic-bezier(0.22, 1, 0.36, 1), background-color 240ms ease; }
    .record-row { transition: background-color 180ms ease, transform 180ms ease; }
    .record-row:hover { background: #f8fbff; transform: translateX(2px); }
    .toast {
      width: min(360px, calc(100vw - 32px)); border-radius: 16px;
      border: 1px solid rgba(226, 232, 240, 0.95); background: rgba(255, 255, 255, 0.97);
      padding: 13px 15px; box-shadow: 0 20px 50px -24px rgba(15, 23, 42, 0.45);
      opacity: 0; transform: translateY(-10px) scale(0.98);
      transition: opacity 200ms ease, transform 200ms ease; pointer-events: none;
    }
    .toast.show { opacity: 1; transform: translateY(0) scale(1); pointer-events: auto; }
    .toast-error { border-color: #fecaca; background: #fff7f7; }
    .toast-success { border-color: #bbf7d0; background: #f7fff9; }
    .toast-info { border-color: #bfdbfe; background: #f7fbff; }
    .chart-wrap canvas { width: 100%; height: 100%; }
    @keyframes spin { to { transform: rotate(360deg); } }
    @keyframes typing {
      0%, 60%, 100% { transform: translateY(0); opacity: 0.38; }
      30% { transform: translateY(-4px); opacity: 1; }
    }
    @keyframes pageIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes messageIn { from { opacity: 0; transform: translateY(7px); } to { opacity: 1; transform: translateY(0); } }
    .project-modal {
      opacity: 0; transition: opacity 220ms ease;
    }
    .project-modal.is-open { opacity: 1; }
    .project-modal-dialog {
      transform: translateY(14px) scale(0.985);
      transition: transform 240ms cubic-bezier(0.22, 1, 0.36, 1);
    }
    .project-modal.is-open .project-modal-dialog {
      transform: translateY(0) scale(1);
    }
    body.modal-open { overflow: hidden; }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        scroll-behavior: auto !important; animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important; transition-duration: 0.01ms !important;
      }
    }
    .page-loader {
      position: fixed; inset: 0; z-index: 90; display: flex; align-items: center;
      justify-content: center; background: rgba(248, 251, 255, 0.96);
      backdrop-filter: blur(12px); transition: opacity 320ms ease, visibility 320ms ease;
    }
    .page-loader.is-hidden { opacity: 0; visibility: hidden; pointer-events: none; }
    .loader-ring {
      width: 42px; height: 42px; border: 3px solid #dbeafe; border-top-color: #2563eb;
      border-radius: 999px; animation: spin 800ms linear infinite;
    }
  </style>
</head>
<body class="min-h-screen antialiased">
  <!-- 首屏加载动画：应用初始化完成后淡出 -->
  <div id="page-loader" class="page-loader" role="status" aria-live="polite">
    <div class="text-center">
      <div class="mx-auto loader-ring"></div>
      <p class="mt-4 text-sm font-semibold text-slate-600">正在加载生活消费智能体...</p>
      <p class="mt-1 text-xs text-slate-400">初始化对话、预算和消费复盘数据</p>
    </div>
  </div>
  <!-- 全局消息提示容器 -->
  <div id="toast-container" class="fixed right-4 top-4 z-[100] flex flex-col gap-2" aria-live="polite"></div>

  <!-- 顶部导航：三个页面通过原生 JavaScript 切换，不刷新页面 -->
  <header class="sticky top-0 z-40 border-b border-white/70 bg-white/80 backdrop-blur-xl">
    <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
      <a href="#chat" class="group flex items-center gap-3" aria-label="返回智能咨询首页">
        <div class="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 text-white shadow-lg shadow-blue-200 transition-transform duration-200 group-hover:-rotate-3 group-hover:scale-105">
          <svg viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 18.75 5.1 20.1a.6.6 0 0 1-.82-.68l.65-3.25A8.25 8.25 0 1 1 8.25 18.75Z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.5 9.75h7M8.5 13.25h4.5" />
          </svg>
        </div>
        <div>
          <p class="text-[11px] font-semibold uppercase tracking-[0.2em] text-blue-500">Life Wallet AI</p>
          <h1 class="text-base font-bold tracking-tight text-slate-900 sm:text-lg">全场景生活消费决策智能体</h1>
        </div>
      </a>

      <nav class="flex flex-1 items-center justify-end gap-1 overflow-x-auto rounded-2xl border border-slate-200/80 bg-white/70 p-1 sm:flex-none" aria-label="主导航">
        <button type="button" class="nav-tab active inline-flex items-center gap-2 whitespace-nowrap rounded-xl px-3 py-2 text-sm font-semibold text-slate-500 sm:px-4" data-page="chat">智能咨询</button>
        <button type="button" class="nav-tab inline-flex items-center gap-2 whitespace-nowrap rounded-xl px-3 py-2 text-sm font-semibold text-slate-500 sm:px-4" data-page="budget">预算管理</button>
        <button type="button" class="nav-tab inline-flex items-center gap-2 whitespace-nowrap rounded-xl px-3 py-2 text-sm font-semibold text-slate-500 sm:px-4" data-page="review">消费复盘</button>
        <button id="project-intro-button" type="button" class="ml-1 whitespace-nowrap rounded-xl border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-bold text-blue-700 transition hover:border-blue-300 hover:bg-blue-100">作品介绍</button>
        <button id="share-project-button" type="button" class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-bold text-emerald-700 transition hover:border-emerald-300 hover:bg-emerald-100" title="复制项目网址">
          <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 12.75 7.5 13.5a3.18 3.18 0 0 1-4.5-4.5l3-3a3.18 3.18 0 0 1 4.5 0m5.25 5.25.75-.75a3.18 3.18 0 0 1 4.5 4.5l-3 3a3.18 3.18 0 0 1-4.5 0M8.25 15.75l7.5-7.5" /></svg>
+          <span>分享网址</span>
+        </button>
      </nav>
    </div>
  </header>

  <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
    <!-- ==================== 智能咨询页 ==================== -->
    <section id="chat-page" class="page-section" data-page-section="chat">
      <div class="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <p class="text-xs font-bold uppercase tracking-[0.22em] text-blue-500">AI Consultation</p>
          <h2 class="mt-1 text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">全场景生活消费决策</h2>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-500">基于自然语言理解与 Function Calling，覆盖日常选购、家庭采购、预算规划、旅行安排与本地服务等生活消费场景。</p>
        </div>
        <div class="inline-flex items-center gap-2 self-start rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 sm:self-auto">
          <span class="h-2 w-2 rounded-full bg-blue-500"></span>
          Function Calling 自主决策
        </div>
      </div>

      <div class="grid gap-5 lg:grid-cols-[1.02fr_0.98fr]">
        <!-- 左侧对话区域 -->
        <section class="soft-card flex min-h-[650px] flex-col overflow-hidden rounded-3xl">
          <div class="border-b border-slate-100 px-5 py-4 sm:px-6">
            <div class="flex items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <div class="relative grid h-10 w-10 place-items-center rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-200">
                  <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 3.75a5.25 5.25 0 0 0-5.25 5.25v1.5L4.5 13.5h3v2.25A2.25 2.25 0 0 0 9.75 18h.75m1.5-14.25a5.25 5.25 0 0 1 5.25 5.25v1.5l2.25 3h-3v2.25A2.25 2.25 0 0 1 14.25 18h-.75" />
                  </svg>
                  <span class="absolute -right-0.5 -top-0.5 h-3 w-3 rounded-full border-2 border-white bg-emerald-400"></span>
                </div>
                <div>
                  <h3 class="font-bold text-slate-900">全场景生活消费决策智能体</h3>
                  <div class="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
                    <span id="api-status-dot" class="status-dot"></span>
                    <span id="api-status-text">正在检测运行模式</span>
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button id="clear-chat-history" type="button" class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-400 transition hover:border-red-200 hover:bg-red-50 hover:text-red-500" title="清空本地对话记录" aria-label="清空本地对话记录">清空</button>
                <button id="focus-api-config" type="button" class="rounded-xl border border-slate-200 bg-white p-2 text-slate-400 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600" title="可选：连接 Flask 后端" aria-label="可选：连接 Flask 后端">
                  <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9.6 3.75h4.8l.55 2.2c.5.23.97.52 1.39.86l2.13-.7 2.4 4.16-1.63 1.58c.03.32.05.65.05.98s-.02.66-.05.98l1.63 1.58-2.4 4.16-2.13-.7c-.42.34-.89.63-1.39.86l-.55 2.2H9.6l-.55-2.2c-.5-.23-.97-.52-1.39-.86l-2.13.7-2.4-4.16 1.63-1.58A7.2 7.2 0 0 1 4.71 12c0-.33.02-.66.05-.98L3.13 9.44l2.4-4.16 2.13.7c.42-.34.89-.63 1.39-.86l.55-2.2Z" />
                    <circle cx="12" cy="12" r="2.4" />
                  </svg>
                </button>
              </div>
            </div>

            <div id="api-config-panel" class="mt-4 hidden rounded-2xl border border-blue-100 bg-blue-50/70 p-3">
              <label for="api-base-url" class="text-[11px] font-bold uppercase tracking-wider text-blue-700">可选：Flask 后端接口地址</label>
              <div class="mt-2 flex gap-2">
                <input id="api-base-url" type="url" class="min-w-0 flex-1 rounded-xl border border-blue-200 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-blue-400" value="" placeholder="自动使用当前网站地址" />
                <button id="save-api-url" type="button" class="rounded-xl bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white transition hover:bg-blue-700">保存</button>
              </div>
              <p id="api-mode-hint" class="mt-2 text-[11px] leading-5 text-blue-600/80">通过网址访问时自动使用当前网站的同源后端；直接打开本地文件时使用本地演示模式。</p>
            </div>
          </div>

          <div id="chat-messages" class="chat-scroll flex-1 space-y-4 overflow-y-auto bg-gradient-to-b from-white to-slate-50/60 px-4 py-5 sm:px-6" aria-live="polite">
            <div id="welcome-message" class="message-row flex items-start gap-3">
              <div class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-blue-100 text-blue-600">
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h8M8 14h5m-8.5 5.5-1.2.7a.5.5 0 0 1-.74-.53l.43-2.16A8.25 8.25 0 1 1 7.5 19Z" />
                </svg>
              </div>
              <div class="max-w-[86%]">
                <div class="rounded-2xl rounded-tl-md border border-slate-100 bg-white px-4 py-3 text-sm leading-6 text-slate-700 shadow-sm">
                  您好，我是全场景生活消费决策智能体。请说明预算、目标品类、使用场景与偏好，我将调用商品检索和优惠计算工具生成可执行方案；如关键信息不足，我会先向您确认必要条件。
                </div>
                <p class="mt-1.5 text-[10px] text-slate-400">刚刚</p>
              </div>
            </div>
          </div>

          <div class="border-t border-slate-100 bg-white p-4 sm:p-5">
            <div id="scenario-panel" class="mb-4 rounded-2xl border border-blue-100 bg-blue-50/60 p-3">
              <div class="mb-2 flex items-center justify-between gap-3">
                <div>
                  <p class="text-xs font-bold text-blue-800">典型生活场景</p>
                  <p class="mt-0.5 text-[10px] text-blue-600/75">从家庭采购到旅行安排，选择预设问题可快速体验。</p>
                </div>
                <span class="rounded-full bg-white px-2 py-1 text-[10px] font-bold text-blue-600">5 个场景</span>
              </div>
              <div class="flex gap-2 overflow-x-auto pb-1">
                <button type="button" class="scenario-chip min-w-[235px] rounded-xl border border-blue-100 bg-white px-3 py-2.5 text-left transition hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-sm" data-scenario="一家三口本周生活采购预算500元，帮我分配并推荐商品">
                  <span class="block text-[10px] font-bold text-blue-500">家庭采购</span>
                  <span class="mt-1 block text-xs font-semibold leading-5 text-slate-700">一家三口本周生活采购预算500元，帮我分配并推荐商品</span>
                </button>
                <button type="button" class="scenario-chip min-w-[235px] rounded-xl border border-blue-100 bg-white px-3 py-2.5 text-left transition hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-sm" data-scenario="预算1000元，帮我安排一个周末周边游，包含吃住行">
                  <span class="block text-[10px] font-bold text-blue-500">出游规划</span>
                  <span class="mt-1 block text-xs font-semibold leading-5 text-slate-700">预算1000元，帮我安排一个周末周边游，包含吃住行</span>
                </button>
                <button type="button" class="scenario-chip min-w-[235px] rounded-xl border border-blue-100 bg-white px-3 py-2.5 text-left transition hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-sm" data-scenario="租房想用300元改善厨房，推荐实用的小家电和用品">
                  <span class="block text-[10px] font-bold text-blue-500">居家生活</span>
                  <span class="mt-1 block text-xs font-semibold leading-5 text-slate-700">租房想用300元改善厨房，推荐实用的小家电和用品</span>
                </button>
                <button type="button" class="scenario-chip min-w-[235px] rounded-xl border border-blue-100 bg-white px-3 py-2.5 text-left transition hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-sm" data-scenario="给父母买200元以内的健康用品，注重实用">
                  <span class="block text-[10px] font-bold text-blue-500">健康关怀</span>
                  <span class="mt-1 block text-xs font-semibold leading-5 text-slate-700">给父母买200元以内的健康用品，注重实用</span>
                </button>
                <button type="button" class="scenario-chip min-w-[235px] rounded-xl border border-blue-100 bg-white px-3 py-2.5 text-left transition hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-sm" data-scenario="每天通勤，预算100元，帮我选交通方案并规划月度支出">
                  <span class="block text-[10px] font-bold text-blue-500">通勤出行</span>
                  <span class="mt-1 block text-xs font-semibold leading-5 text-slate-700">每天通勤，预算100元，帮我选交通方案并规划月度支出</span>
                </button>
              </div>
            </div>

            <form id="chat-form" class="flex items-end gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-2 transition focus-within:border-blue-300 focus-within:bg-white focus-within:shadow-md focus-within:shadow-blue-100/50">
              <label for="chat-input" class="sr-only">输入消费问题</label>
              <textarea id="chat-input" rows="1" maxlength="2000" class="max-h-32 min-h-[44px] flex-1 resize-none bg-transparent px-3 py-2.5 text-sm leading-6 text-slate-700 outline-none placeholder:text-slate-400" placeholder="描述预算、消费场景和偏好，例如：1000元安排周末周边游，Enter 发送"></textarea>
              <button id="send-button" type="submit" class="primary-button inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-xl px-4 text-sm font-bold text-white" aria-label="发送消息">
                <span id="send-label">发送</span>
                <svg id="send-icon" viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12 15-7.5-4.2 15-3.3-6-7.5-1.5Z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="m12 13.5 3.6-3.6" />
                </svg>
                <span id="send-spinner" class="spinner hidden" aria-hidden="true"></span>
              </button>
            </form>
            <p class="mt-2 text-center text-[10px] text-slate-400">AI 建议仅供决策参考，请结合商品库存、服务规则和个人实际情况审慎消费。</p>
          </div>
        </section>
        <!-- 右侧方案展示区域 -->
        <aside class="soft-card flex min-h-[650px] flex-col overflow-hidden rounded-3xl">
          <div class="border-b border-slate-100 px-5 py-4 sm:px-6">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-[11px] font-bold uppercase tracking-[0.18em] text-blue-500">Recommendation</p>
                <h3 class="mt-1 text-lg font-bold text-slate-900">智能消费方案</h3>
              </div>
              <span class="rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">2–3 套方案</span>
            </div>
            <div class="mt-4 flex flex-wrap items-center gap-2">
              <span class="text-xs font-semibold text-slate-400">调用工具</span>
              <div id="used-tools" class="flex flex-wrap gap-1.5">
                <span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-500">暂无</span>
              </div>
            </div>
          </div>

          <div class="chat-scroll flex-1 overflow-y-auto bg-slate-50/60 p-4 sm:p-5">
            <div id="plans-empty" class="flex h-full min-h-[420px] flex-col items-center justify-center rounded-2xl border border-dashed border-blue-100 bg-white/60 px-8 text-center">
              <div class="grid h-16 w-16 place-items-center rounded-3xl bg-blue-100 text-blue-600">
                <svg viewBox="0 0 24 24" class="h-8 w-8" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 7.5h15v10.75A1.75 1.75 0 0 1 17.75 20H6.25a1.75 1.75 0 0 1-1.75-1.75V7.5Zm3-3h9M8.25 12h7.5m-7.5 3.5h4.5" />
                </svg>
              </div>
              <h4 class="mt-4 font-bold text-slate-800">方案输出区</h4>
              <p class="mt-2 max-w-xs text-sm leading-6 text-slate-400">提交需求后，系统将展示商品或预算清单、预计总价、方案优势及智能体推荐依据。</p>
            </div>
            <div id="plans-container" class="hidden space-y-4"></div>
          </div>
        </aside>
      </div>
    </section>

    <!-- ==================== 预算管理页 ==================== -->
    <section id="budget-page" class="page-section hidden" data-page-section="budget">
      <div class="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <p class="text-xs font-bold uppercase tracking-[0.22em] text-blue-500">Budget Planner</p>
          <h2 class="mt-1 text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">预算管理</h2>
          <p class="mt-2 text-sm leading-6 text-slate-500">按月度或周度管理预算，可回看历史周期，逐期查看预算、支出和消费明细。</p>
        </div>
        <div class="flex gap-2">
          <button id="seed-expenses" type="button" class="rounded-xl border border-blue-100 bg-blue-50 px-3.5 py-2 text-sm font-semibold text-blue-700 transition hover:border-blue-200 hover:bg-blue-100">载入示例记录</button>
          <button id="clear-expenses" type="button" class="rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm font-semibold text-slate-500 transition hover:border-red-200 hover:bg-red-50 hover:text-red-600">清空记录</button>
        </div>
      </div>
      <section class="soft-card mb-5 overflow-hidden rounded-2xl">
        <div class="flex flex-col gap-4 p-4 sm:p-5 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex items-start gap-3">
            <span class="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-blue-50 text-blue-600">
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3.75v3m10.5-3v3M4.5 8.25h15M5.25 5.25h13.5A1.5 1.5 0 0 1 20.25 6.75v12A1.5 1.5 0 0 1 18.75 20.25H5.25a1.5 1.5 0 0 1-1.5-1.5v-12a1.5 1.5 0 0 1 1.5-1.5Zm2.25 6h2.25m3 0h2.25m-7.5 3h2.25m3 0h2.25" />
              </svg>
            </span>
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <p class="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-500">Period Navigator</p>
                <span id="budget-period-context" class="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-600">当前周期</span>
              </div>
              <h3 id="budget-period-title" class="mt-1 text-lg font-black tracking-tight text-slate-900">当前月份</h3>
              <p id="budget-period-range" class="mt-0.5 text-xs text-slate-400">正在读取周期范围</p>
            </div>
          </div>
          <div class="w-full lg:max-w-[560px]">
            <div class="mb-2 flex items-center justify-end gap-2">
              <span class="text-[10px] font-semibold text-slate-400">查看粒度</span>
              <div class="inline-flex rounded-lg bg-slate-100 p-1" role="group" aria-label="切换月度或周度查看">
                <button type="button" class="period-button active rounded-md px-3 py-1 text-[11px] font-bold text-slate-500" data-period="monthly">月度</button>
                <button type="button" class="period-button rounded-md px-3 py-1 text-[11px] font-bold text-slate-500" data-period="weekly">周度</button>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button id="previous-period" type="button" class="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-slate-200 bg-white text-slate-500 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-40" aria-label="查看上一周期">
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m14.5 6.5-5.5 5.5 5.5 5.5" /></svg>
              </button>
              <label for="budget-period-select" class="sr-only">选择要查看的月份或周度</label>
              <select id="budget-period-select" class="min-w-0 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm font-bold text-slate-700 outline-none transition focus:border-blue-300 focus:bg-white"></select>
              <button id="next-period" type="button" class="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-slate-200 bg-white text-slate-500 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700 disabled:cursor-not-allowed disabled:opacity-40" aria-label="查看下一周期">
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m9.5 6.5 5.5 5.5-5.5 5.5" /></svg>
              </button>
            </div>
            <div class="mt-2 flex items-center justify-between gap-3">
              <p class="text-[10px] leading-4 text-slate-400">可回看近 24 个月或 26 周，更早的有记录周期会自动加入列表。</p>
              <button id="back-to-current-period" type="button" class="shrink-0 rounded-lg px-2 py-1 text-[11px] font-bold text-blue-600 transition hover:bg-blue-50 disabled:cursor-not-allowed disabled:text-slate-300">回到当前</button>
            </div>
          </div>
        </div>
      </section>

      <div class="mb-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div class="soft-card rounded-2xl p-5">
          <div class="flex items-center justify-between">
            <p id="budget-card-label" class="text-sm font-semibold text-slate-500">所选周期预算</p>
            <span class="grid h-9 w-9 place-items-center rounded-xl bg-blue-50 text-blue-600">
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 7.5A2.25 2.25 0 0 1 6.75 5.25h10.5A2.25 2.25 0 0 1 19.5 7.5v9A2.25 2.25 0 0 1 17.25 18.75H6.75a2.25 2.25 0 0 1-2.25-2.25v-9Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 10.5h3.75v3h-3.75a1.5 1.5 0 0 1 0-3Z" /></svg>
            </span>
          </div>
          <p id="budget-total" class="mt-4 text-3xl font-black tracking-tight text-slate-900">¥6,000.00</p>
          <p id="budget-card-hint" class="mt-1 text-xs text-slate-400">每个周期可单独设置预算</p>
        </div>
        <div class="soft-card rounded-2xl p-5">
          <div class="flex items-center justify-between">
            <p class="text-sm font-semibold text-slate-500">已消费</p>
            <span class="grid h-9 w-9 place-items-center rounded-xl bg-amber-50 text-amber-600">
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5v10.5H3.75V6.75Zm0 4.5h16.5M7.5 15h3" /></svg>
            </span>
          </div>
          <p id="budget-spent" class="mt-4 text-3xl font-black tracking-tight text-slate-900">¥0.00</p>
          <p id="budget-record-count" class="mt-1 text-xs text-slate-400">0 笔记录</p>
        </div>
        <div class="soft-card rounded-2xl p-5">
          <div class="flex items-center justify-between">
            <p class="text-sm font-semibold text-slate-500">预算剩余</p>
            <span id="remaining-icon" class="grid h-9 w-9 place-items-center rounded-xl bg-emerald-50 text-emerald-600">
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m3.75-9.75a3 3 0 0 0-3-2.25h-1.5a2.25 2.25 0 0 0 0 4.5h1.5a2.25 2.25 0 0 1 0 4.5h-1.5a3 3 0 0 1-3-2.25" /></svg>
            </span>
          </div>
          <p id="budget-remaining" class="mt-4 text-3xl font-black tracking-tight text-slate-900">¥6,000.00</p>
          <p id="budget-status" class="mt-1 text-xs text-emerald-600">额度充足</p>
        </div>
        <div class="soft-card rounded-2xl p-5">
          <div class="flex items-center justify-between">
            <p class="text-sm font-semibold text-slate-500">预算使用率</p>
            <span class="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-700" id="budget-percent">0%</span>
          </div>
          <div class="mt-5 h-2.5 overflow-hidden rounded-full bg-slate-100">
            <div id="budget-progress" class="budget-progress h-full rounded-full bg-blue-500" style="width: 0%"></div>
          </div>
          <p class="mt-3 text-xs leading-5 text-slate-400">建议将使用率控制在 80% 以内</p>
        </div>
      </div>

      <div id="budget-alert" class="mb-5 hidden rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">
        已超出预算，请暂停非必要消费并检查近期支出。
      </div>
      <div class="grid gap-5 xl:grid-cols-[0.92fr_1.08fr]">
        <div class="space-y-5">
          <section class="soft-card rounded-3xl p-5 sm:p-6">
            <div class="flex items-center justify-between gap-4">
              <div>
                <h3 class="text-lg font-bold text-slate-900">设置预算</h3>
                <p id="budget-editor-hint" class="mt-1 text-xs text-slate-400">保存后仅更新当前所选周期。</p>
              </div>
            </div>
            <div class="mt-5 flex gap-2">
              <div class="relative flex-1">
                <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm font-bold text-slate-400">¥</span>
                <input id="budget-input" type="number" min="0.01" step="0.01" class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-8 pr-3 text-sm font-semibold text-slate-700 outline-none transition focus:border-blue-300 focus:bg-white" placeholder="输入预算金额" />
              </div>
              <button id="save-budget" type="button" class="primary-button rounded-xl px-5 py-3 text-sm font-bold text-white">保存预算</button>
            </div>
          </section>

          <section class="soft-card rounded-3xl p-5 sm:p-6">
            <h3 class="text-lg font-bold text-slate-900">新增消费记录</h3>
            <p class="mt-1 text-xs text-slate-400">记录后会立即更新剩余预算和消费复盘。</p>
            <form id="expense-form" class="mt-5 space-y-4">
              <div class="grid gap-4 sm:grid-cols-2">
                <div>
                  <label for="expense-name" class="text-xs font-semibold text-slate-500">消费名称</label>
                  <input id="expense-name" required maxlength="40" class="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-blue-300 focus:bg-white" placeholder="例如：周末聚餐" />
                </div>
                <div>
                  <label for="expense-amount" class="text-xs font-semibold text-slate-500">金额</label>
                  <div class="relative mt-1.5">
                    <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm font-bold text-slate-400">¥</span>
                    <input id="expense-amount" type="number" required min="0.01" step="0.01" class="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-8 pr-3 text-sm text-slate-700 outline-none transition focus:border-blue-300 focus:bg-white" placeholder="0.00" />
                  </div>
                </div>
                <div>
                  <label for="expense-category" class="text-xs font-semibold text-slate-500">消费分类</label>
                  <select id="expense-category" class="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-blue-300 focus:bg-white">
                    <option>餐饮美食</option><option>零食饮料</option><option>商超日用</option><option>生活用品</option><option>家居生活</option><option>数码家电</option><option>服饰鞋包</option><option>美妆个护</option><option>健康医疗</option><option>交通出行</option><option>教育学习</option><option>文体娱乐</option><option>亲子宠物</option><option>旅游住宿</option><option>本地服务</option><option>礼品文创</option><option>应急储蓄</option><option>其他</option>
                  </select>
                </div>
                <div>
                  <label for="expense-date" class="text-xs font-semibold text-slate-500">日期</label>
                  <input id="expense-date" type="date" required class="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-blue-300 focus:bg-white" />
                </div>
              </div>
              <button type="submit" class="primary-button w-full rounded-xl px-5 py-3 text-sm font-bold text-white">添加消费记录</button>
            </form>
          </section>
        </div>

        <section class="soft-card flex min-h-[500px] flex-col overflow-hidden rounded-3xl">
          <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4 sm:px-6">
            <div>
              <h3 class="text-lg font-bold text-slate-900">消费明细</h3>
              <p id="records-period-label" class="mt-1 text-xs text-slate-400">所选周期记录</p>
            </div>
            <span id="records-total" class="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">合计 ¥0.00</span>
          </div>
          <div id="expense-list" class="records-scroll flex-1 overflow-y-auto p-4 sm:p-5"></div>
        </section>
      </div>
    </section>
    <!-- ==================== 消费复盘页 ==================== -->
    <section id="review-page" class="page-section hidden" data-page-section="review">
      <div class="mb-5">
        <p class="text-xs font-bold uppercase tracking-[0.22em] text-blue-500">Periodic Review</p>
        <h2 class="mt-1 text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">消费复盘</h2>
        <p id="review-page-description" class="mt-2 text-sm leading-6 text-slate-500">复盘周期与预算管理同步，可分析当月、本周以及历史月份或周度的消费结构。</p>
      </div>

      <section class="soft-card mb-5 overflow-hidden rounded-2xl">
        <div class="flex flex-col gap-4 p-4 sm:p-5 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex items-start gap-3">
            <span class="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-violet-50 text-violet-600">
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5V10.5m5 9V6.75m5 12.75V8.25m5 11.25V4.5M3 19.5h18" />
              </svg>
            </span>
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <p class="text-[11px] font-bold uppercase tracking-[0.16em] text-violet-500">Review Period</p>
                <span id="review-period-context" class="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-600">当前周期</span>
              </div>
              <h3 id="review-period-title" class="mt-1 text-lg font-black tracking-tight text-slate-900">当前月份</h3>
              <p id="review-period-range" class="mt-0.5 text-xs text-slate-400">正在读取复盘周期</p>
            </div>
          </div>
          <div class="w-full lg:max-w-[560px]">
            <div class="mb-2 flex items-center justify-end gap-2">
              <span class="text-[10px] font-semibold text-slate-400">复盘粒度</span>
              <div class="inline-flex rounded-lg bg-slate-100 p-1" role="group" aria-label="切换月度或周度复盘">
                <button type="button" class="period-button active rounded-md px-3 py-1 text-[11px] font-bold text-slate-500" data-period="monthly">月度</button>
                <button type="button" class="period-button rounded-md px-3 py-1 text-[11px] font-bold text-slate-500" data-period="weekly">周度</button>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button id="review-previous-period" type="button" class="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-slate-200 bg-white text-slate-500 transition hover:border-violet-200 hover:bg-violet-50 hover:text-violet-700 disabled:cursor-not-allowed disabled:opacity-40" aria-label="复盘上一周期">
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m14.5 6.5-5.5 5.5 5.5 5.5" /></svg>
              </button>
              <label for="review-period-select" class="sr-only">选择要复盘的月份或周度</label>
              <select id="review-period-select" class="min-w-0 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm font-bold text-slate-700 outline-none transition focus:border-violet-300 focus:bg-white"></select>
              <button id="review-next-period" type="button" class="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-slate-200 bg-white text-slate-500 transition hover:border-violet-200 hover:bg-violet-50 hover:text-violet-700 disabled:cursor-not-allowed disabled:opacity-40" aria-label="复盘下一周期">
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m9.5 6.5 5.5 5.5-5.5 5.5" /></svg>
              </button>
            </div>
            <div class="mt-2 flex items-center justify-between gap-3">
              <p class="text-[10px] leading-4 text-slate-400">与预算管理共用周期选择，切换页面后仍会保留当前复盘范围。</p>
              <button id="review-back-to-current-period" type="button" class="shrink-0 rounded-lg px-2 py-1 text-[11px] font-bold text-violet-600 transition hover:bg-violet-50 disabled:cursor-not-allowed disabled:text-slate-300">回到当前</button>
            </div>
          </div>
        </div>
      </section>

      <div class="mb-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div class="soft-card rounded-2xl p-5">
          <p id="review-total-label" class="text-sm font-semibold text-slate-500">本周期总支出</p>
          <p id="review-total" class="mt-4 text-3xl font-black tracking-tight text-slate-900">¥0.00</p>
          <p id="review-total-detail" class="mt-1 text-xs text-slate-400">按所选周期统计</p>
        </div>
        <div class="soft-card rounded-2xl p-5">
          <p class="text-sm font-semibold text-slate-500">消费笔数</p>
          <p id="review-count" class="mt-4 text-3xl font-black tracking-tight text-slate-900">0</p>
          <p id="review-count-detail" class="mt-1 text-xs text-slate-400">当前周期有效记录</p>
        </div>
        <div class="soft-card rounded-2xl p-5">
          <p class="text-sm font-semibold text-slate-500">最高支出分类</p>
          <p id="review-top-category" class="mt-4 truncate text-2xl font-black tracking-tight text-slate-900">暂无</p>
          <p id="review-top-amount" class="mt-1 text-xs text-slate-400">暂无消费</p>
        </div>
        <div class="soft-card rounded-2xl p-5">
          <p id="review-budget-label" class="text-sm font-semibold text-slate-500">周期预算状态</p>
          <p id="review-budget-status" class="mt-4 text-2xl font-black tracking-tight text-emerald-600">暂无数据</p>
          <p id="review-budget-detail" class="mt-1 text-xs text-slate-400">所选周期预算</p>
        </div>
      </div>

      <div class="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <section class="soft-card rounded-3xl p-5 sm:p-6">
          <div class="flex items-center justify-between gap-4">
            <div>
              <h3 class="text-lg font-bold text-slate-900">消费分类占比</h3>
              <p class="mt-1 text-xs text-slate-400">使用原生 Canvas 绘制，无需额外图表库。</p>
            </div>
            <span id="review-period-badge" class="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">所选周期</span>
          </div>
          <div class="mt-5 grid gap-6 md:grid-cols-[1fr_0.9fr] md:items-center">
            <div class="chart-wrap mx-auto h-[290px] w-full max-w-[360px]">
              <canvas id="category-chart" aria-label="所选周期消费分类饼图" role="img"></canvas>
            </div>
            <div id="category-legend" class="space-y-3"></div>
          </div>
        </section>

        <section class="soft-card flex flex-col rounded-3xl p-5 sm:p-6">
          <div class="flex items-center gap-3">
            <div class="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 text-white shadow-lg shadow-blue-200">
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 18h6m-7.5 3h9M12 3a6 6 0 0 0-3.6 10.8c.54.4.85 1.03.85 1.7H14.75c0-.67.31-1.3.85-1.7A6 6 0 0 0 12 3Z" />
              </svg>
            </div>
            <div>
              <h3 id="review-insight-title" class="text-lg font-bold text-slate-900">周期总结建议</h3>
              <p id="review-insight-subtitle" class="mt-0.5 text-xs text-slate-400">依据所选周期记录自动生成</p>
            </div>
          </div>
          <div id="review-advice" class="mt-5 flex-1 space-y-3"></div>
          <div class="mt-5 rounded-2xl border border-blue-100 bg-blue-50/70 p-4">
            <p id="review-action-label" class="text-xs font-bold uppercase tracking-wider text-blue-700">周期行动建议</p>
            <p id="review-action" class="mt-2 text-sm leading-6 text-blue-900/80">先添加几条消费记录，系统会根据你的分类占比给出更具体的建议。</p>
          </div>
        </section>
      </div>
    </section>
  </main>

  <!-- ==================== 作品说明 ==================== -->
  <footer class="mt-10 border-t border-slate-200/80 bg-white/70">
    <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div class="grid gap-6 lg:grid-cols-[1.05fr_1.35fr]">
        <section>
          <div class="flex items-center gap-3">
            <div class="grid h-10 w-10 place-items-center rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-200">
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3.75 4.5 7.5v4.75c0 4.4 3.05 7.15 7.5 8 4.45-.85 7.5-3.6 7.5-8V7.5L12 3.75Z" /><path stroke-linecap="round" stroke-linejoin="round" d="m9 12 2 2 4-4" /></svg>
            </div>
            <div>
              <p class="text-[10px] font-bold uppercase tracking-[0.2em] text-blue-500">Competition Showcase</p>
              <h2 class="text-lg font-black text-slate-900">作品说明</h2>
            </div>
          </div>
          <p class="mt-4 text-sm leading-7 text-slate-500">全场景生活消费决策智能体面向全国人工智能应用创新大赛演示场景，以真实生活消费问题为牵引，展示大模型在需求理解、工具调用、跨平台比价和预算规划中的综合应用能力。</p>
          <div class="mt-4 flex flex-wrap gap-2">
            <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold text-slate-600">全国人工智能应用创新大赛</span>
            <span class="rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[11px] font-semibold text-blue-700">AI Agent 应用</span>
            <span class="rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-[11px] font-semibold text-emerald-700">全生活消费场景</span>
          </div>
        </section>

        <div class="grid gap-4 sm:grid-cols-2">
          <section class="rounded-2xl border border-slate-200 bg-white p-4">
            <h3 class="text-sm font-bold text-slate-800">技术栈</h3>
            <p class="mt-2 text-xs leading-6 text-slate-500">Python Flask · OpenAI Function Calling · HTML5 · Tailwind CSS · 原生 JavaScript · LocalStorage · Canvas</p>
          </section>
          <section class="rounded-2xl border border-slate-200 bg-white p-4">
            <h3 class="text-sm font-bold text-slate-800">核心创新点</h3>
            <ul class="mt-2 space-y-1.5 text-xs leading-5 text-slate-500">
              <li>· 自然语言需求拆解与自主工具调用</li>
              <li>· 多平台商品检索及最优优惠计算</li>
              <li>· 对话式方案修改与预算闭环管理</li>
            </ul>
          </section>
        </div>
      </div>
      <div class="mt-6 flex flex-col justify-between gap-2 border-t border-slate-100 pt-4 text-[11px] text-slate-400 sm:flex-row">
        <p>本作品中的商品、价格、优惠与消费记录均为演示模拟数据。</p>
        <p>全场景生活消费决策智能体 · 2026</p>
      </div>
    </div>
  </footer>

  <!-- ==================== 项目介绍弹窗 ==================== -->
  <div id="project-intro-modal" class="project-modal fixed inset-0 z-[80] hidden" role="dialog" aria-modal="true" aria-labelledby="project-intro-title">
    <button id="project-intro-backdrop" type="button" class="absolute inset-0 bg-slate-950/45 backdrop-blur-sm" aria-label="关闭项目介绍"></button>
    <div class="relative flex min-h-full items-center justify-center p-4 sm:p-6">
      <div class="project-modal-dialog relative max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-3xl border border-white/80 bg-white shadow-2xl shadow-slate-950/25">
        <div class="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-slate-100 bg-white/95 px-5 py-4 backdrop-blur-xl sm:px-7">
          <div>
            <p class="text-[10px] font-bold uppercase tracking-[0.24em] text-blue-500">National AI Application Innovation Competition</p>
            <h2 id="project-intro-title" class="mt-1 text-xl font-black tracking-tight text-slate-900 sm:text-2xl">全场景生活消费决策智能体</h2>
          </div>
          <button id="project-intro-close" type="button" class="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-slate-100 text-xl text-slate-500 transition hover:bg-slate-200 hover:text-slate-800" aria-label="关闭项目介绍">×</button>
        </div>

        <div class="p-5 sm:p-7">
          <div class="rounded-2xl border border-blue-100 bg-gradient-to-r from-blue-50 via-white to-cyan-50 p-4 sm:p-5">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p class="text-xs font-bold text-blue-700">面向真实全生活消费场景的 AI Agent 应用</p>
                <p class="mt-1 text-sm leading-6 text-slate-600">通过自然语言交互，联动商品检索、优惠计算与预算管理工具，为个人和家庭提供可解释、可执行、可复盘的消费决策支持。</p>
              </div>
              <span class="self-start rounded-full bg-blue-600 px-3 py-1.5 text-[11px] font-bold text-white sm:self-auto">比赛演示版</span>
            </div>
          </div>

          <div class="mt-5 grid gap-4 md:grid-cols-2">
            <section class="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
              <div class="flex items-center gap-2">
                <span class="grid h-8 w-8 place-items-center rounded-xl bg-blue-100 text-sm font-black text-blue-700">01</span>
                <h3 class="font-bold text-slate-900">项目背景</h3>
              </div>
              <p class="mt-3 text-sm leading-6 text-slate-500">日常消费场景丰富但信息分散，商品价格、平台优惠、预算约束和实际需求往往需要跨平台反复比较，缺少覆盖多场景的一体化智能决策工具。</p>
            </section>
            <section class="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
              <div class="flex items-center gap-2">
                <span class="grid h-8 w-8 place-items-center rounded-xl bg-amber-100 text-sm font-black text-amber-700">02</span>
                <h3 class="font-bold text-slate-900">核心痛点</h3>
              </div>
              <ul class="mt-3 space-y-1.5 text-sm leading-6 text-slate-500">
                <li>· 多平台价格与优惠规则复杂，人工比价成本高</li>
                <li>· 预算规划缺乏数据支撑，容易出现非理性消费</li>
                <li>· 消费记录与复盘割裂，难以形成持续优化闭环</li>
              </ul>
            </section>
            <section class="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
              <div class="flex items-center gap-2">
                <span class="grid h-8 w-8 place-items-center rounded-xl bg-emerald-100 text-sm font-black text-emerald-700">03</span>
                <h3 class="font-bold text-slate-900">Agent 能力</h3>
              </div>
              <div class="mt-3 grid gap-2 sm:grid-cols-2">
                <span class="rounded-xl bg-white px-3 py-2 text-xs font-semibold text-slate-600">自然语言需求理解</span>
                <span class="rounded-xl bg-white px-3 py-2 text-xs font-semibold text-slate-600">Function Calling 工具调用</span>
                <span class="rounded-xl bg-white px-3 py-2 text-xs font-semibold text-slate-600">多平台商品比价</span>
                <span class="rounded-xl bg-white px-3 py-2 text-xs font-semibold text-slate-600">最优满减与凑单计算</span>
                <span class="rounded-xl bg-white px-3 py-2 text-xs font-semibold text-slate-600">预算分配与消费复盘</span>
                <span class="rounded-xl bg-white px-3 py-2 text-xs font-semibold text-slate-600">模糊需求主动追问</span>
              </div>
            </section>
            <section class="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
              <div class="flex items-center gap-2">
                <span class="grid h-8 w-8 place-items-center rounded-xl bg-violet-100 text-sm font-black text-violet-700">04</span>
                <h3 class="font-bold text-slate-900">适用人群</h3>
              </div>
              <p class="mt-3 text-sm leading-6 text-slate-500">面向个人消费者、家庭采购者、通勤上班族、旅行与本地生活用户，以及关注智能消费决策应用的研究与评审人员。</p>
            </section>
          </div>

          <div class="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p class="text-xs leading-5 text-slate-400">演示数据均为模拟内容，可随时通过预算管理页编辑或清空。</p>
            <div class="flex gap-2">
              <button id="intro-view-scenarios" type="button" class="rounded-xl border border-blue-200 bg-white px-4 py-2.5 text-sm font-bold text-blue-700 transition hover:bg-blue-50">查看典型场景</button>
              <button id="intro-start-demo" type="button" class="primary-button rounded-xl px-5 py-2.5 text-sm font-bold text-white">开始体验</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script id="local-demo-data" type="application/json">{"products":[{"id":"D001","name":"入耳式有线耳机","category":"数码配件","price":29.9,"platform":"淘宝","rating":4.5,"tags":["耳机","有线","高性价比"],"description":"带麦克风线控，适合线上会议和日常听歌。"},{"id":"D002","name":"真无线蓝牙耳机","category":"数码配件","price":89.0,"platform":"拼多多","rating":4.4,"tags":["耳机","蓝牙","通勤"],"description":"半入耳设计，续航约20小时，适合居家和通勤使用。"},{"id":"D003","name":"32GB USB3.0 U盘","category":"数码配件","price":24.9,"platform":"京东","rating":4.7,"tags":["U盘","存储","学习资料"],"description":"读取速度快，适合保存工作文件、学习资料和打印资料。"},{"id":"D004","name":"10000mAh充电宝","category":"数码配件","price":79.0,"platform":"淘宝","rating":4.6,"tags":["充电宝","便携","居家"],"description":"双向快充，机身轻便，适合办公室和短途出行。"},{"id":"D005","name":"Type-C快充数据线1.5米","category":"数码配件","price":12.9,"platform":"拼多多","rating":4.5,"tags":["数据线","快充","手机配件"],"description":"加长编织线身，支持常见安卓手机和轻薄本充电。"},{"id":"D006","name":"桌面手机支架","category":"数码配件","price":9.9,"platform":"淘宝","rating":4.4,"tags":["手机支架","桌面","线上会议"],"description":"可调节角度，适合居家追剧、线上会议和视频通话。"},{"id":"D007","name":"无线静音鼠标","category":"数码配件","price":39.9,"platform":"京东","rating":4.6,"tags":["鼠标","无线","静音"],"description":"静音按键设计，适合办公室和居家学习使用。"},{"id":"D008","name":"便携蓝牙键盘","category":"数码配件","price":69.0,"platform":"拼多多","rating":4.3,"tags":["键盘","蓝牙","便携"],"description":"紧凑布局，可连接手机和平板，适合移动记笔记。"},{"id":"D009","name":"主动降噪蓝牙耳机","category":"数码配件","price":149.0,"platform":"京东","rating":4.7,"tags":["耳机","降噪","专注"],"description":"支持主动降噪和通透模式，适合居家、通勤和安静办公环境。"},{"id":"D010","name":"轻量半入耳蓝牙耳机","category":"数码配件","price":59.9,"platform":"拼多多","rating":4.2,"tags":["耳机","蓝牙","轻量","高性价比"],"description":"轻量半入耳设计，支持蓝牙连接，适合预算有限的日常听歌和线上会议。"},{"id":"D011","name":"运动蓝牙耳机","category":"数码配件","price":95.0,"platform":"淘宝","rating":4.5,"tags":["耳机","蓝牙","运动","防汗"],"description":"挂耳式运动设计，支持蓝牙连接和防汗，适合跑步、通勤和学习使用。"},{"id":"B001","name":"氨基酸洗面奶","category":"美妆个护","price":29.9,"platform":"淘宝","rating":4.6,"tags":["洗面奶","温和","清洁"],"description":"温和清洁不紧绷，适合日常早晚洁面。"},{"id":"B002","name":"补水保湿面膜10片","category":"美妆个护","price":39.9,"platform":"拼多多","rating":4.4,"tags":["面膜","补水","护肤"],"description":"轻薄服帖，适合换季补水和熬夜后基础护理。"},{"id":"B003","name":"滋润口红","category":"美妆个护","price":49.9,"platform":"京东","rating":4.5,"tags":["口红","彩妆","日常"],"description":"日常显色色号，滋润不拔干，适合通勤和聚会活动。"},{"id":"B004","name":"清爽防晒霜SPF50","category":"美妆个护","price":59.9,"platform":"淘宝","rating":4.6,"tags":["防晒","清爽","户外活动"],"description":"清爽易推开，适合户外活动、运动和日常通勤。"},{"id":"B005","name":"去屑洗发水500ml","category":"美妆个护","price":32.9,"platform":"拼多多","rating":4.4,"tags":["洗发水","去屑","大容量"],"description":"清洁头皮并减少头屑，大容量适合家庭长期使用。"},{"id":"B006","name":"清香沐浴露500ml","category":"美妆个护","price":27.9,"platform":"京东","rating":4.5,"tags":["沐浴露","清香","洗护"],"description":"泡沫细腻易冲洗，适合日常洗护。"},{"id":"B007","name":"保湿护手霜","category":"美妆个护","price":15.9,"platform":"淘宝","rating":4.6,"tags":["护手霜","保湿","便携"],"description":"小支便携，适合秋冬季节随身补涂。"},{"id":"B008","name":"温和卸妆水300ml","category":"美妆个护","price":35.9,"platform":"拼多多","rating":4.3,"tags":["卸妆水","温和","彩妆"],"description":"可卸除日常防晒和淡妆，使用后不黏腻。"},{"id":"B009","name":"新手基础彩妆套装","category":"美妆个护","price":79.9,"platform":"京东","rating":4.2,"tags":["彩妆","套装","新手"],"description":"包含底妆和基础眼妆用品，适合新手聚会活动使用。"},{"id":"S001","name":"红烧牛肉泡面5连包","category":"零食饮料","price":19.9,"platform":"拼多多","rating":4.7,"tags":["泡面","速食","夜宵"],"description":"经典口味五连包，适合居家夜宵和应急加餐。"},{"id":"S002","name":"纯牛奶250ml×12盒","category":"零食饮料","price":39.9,"platform":"京东","rating":4.8,"tags":["牛奶","早餐","整箱"],"description":"整箱装常温纯牛奶，适合早餐和日常补充蛋白质。"},{"id":"S003","name":"原味薯片3连包","category":"零食饮料","price":15.9,"platform":"淘宝","rating":4.4,"tags":["薯片","零食","分享"],"description":"小包装组合，适合居家追剧和朋友分享。"},{"id":"S004","name":"早餐饼干2斤","category":"零食饮料","price":12.9,"platform":"拼多多","rating":4.3,"tags":["饼干","早餐","囤货"],"description":"独立小包方便携带，适合早八赶课和课间加餐。"},{"id":"S005","name":"即食燕麦片1kg","category":"零食饮料","price":25.9,"platform":"京东","rating":4.6,"tags":["燕麦","早餐","健康"],"description":"热水冲泡即可食用，适合居家早餐和轻食搭配。"},{"id":"S006","name":"矿泉水550ml×24瓶","category":"零食饮料","price":24.9,"platform":"淘宝","rating":4.5,"tags":["矿泉水","整箱","居家"],"description":"整箱饮用水，适合居家、户外活动和聚会活动储备。"},{"id":"S007","name":"无糖乌龙茶500ml×6瓶","category":"零食饮料","price":19.9,"platform":"拼多多","rating":4.4,"tags":["茶饮","无糖","解腻"],"description":"无糖茶饮组合装，适合通勤和聚餐后饮用。"},{"id":"S008","name":"每日坚果20小包","category":"零食饮料","price":29.9,"platform":"京东","rating":4.6,"tags":["坚果","健康","课间"],"description":"独立小包装，方便课间补充能量和控制食用量。"},{"id":"S009","name":"辣条混合装20包","category":"零食饮料","price":9.9,"platform":"淘宝","rating":4.3,"tags":["辣条","零食","居家"],"description":"多种口味混合装，适合居家分享和休闲零食储备。"},{"id":"L001","name":"抽纸3层24包","category":"生活用品","price":29.9,"platform":"拼多多","rating":4.7,"tags":["纸巾","抽纸","居家囤货"],"description":"原生木浆抽纸整箱装，适合家庭长期使用。"},{"id":"L002","name":"洗衣液2kg","category":"生活用品","price":24.9,"platform":"京东","rating":4.6,"tags":["洗衣液","清洁","大容量"],"description":"低泡易漂洗，适合手洗和居家公共洗衣机。"},{"id":"L003","name":"晴雨两用折叠伞","category":"生活用品","price":19.9,"platform":"淘宝","rating":4.4,"tags":["雨伞","防晒","便携"],"description":"轻量折叠设计，晴天防晒、雨天挡雨，适合随身携带。"},{"id":"L004","name":"软毛牙刷牙膏套装","category":"生活用品","price":16.9,"platform":"拼多多","rating":4.5,"tags":["牙刷","牙膏","洗漱"],"description":"软毛牙刷搭配牙膏，满足居家日常洗漱需求。"},{"id":"L005","name":"纯棉毛巾3条装","category":"生活用品","price":19.9,"platform":"淘宝","rating":4.4,"tags":["毛巾","纯棉","居家"],"description":"吸水柔软的纯棉毛巾，三条装方便换洗。"},{"id":"L006","name":"桌面收纳盒","category":"生活用品","price":14.9,"platform":"拼多多","rating":4.3,"tags":["收纳","桌面","居家"],"description":"分区收纳文具和杂物，让居家桌面更整洁。"},{"id":"L007","name":"防滑衣架20个","category":"生活用品","price":12.9,"platform":"淘宝","rating":4.4,"tags":["衣架","防滑","居家"],"description":"轻薄防滑设计，适合居家衣柜和晾晒衣物。"},{"id":"L008","name":"居家小垃圾桶","category":"生活用品","price":15.9,"platform":"京东","rating":4.5,"tags":["垃圾桶","桌面","居家"],"description":"带盖小容量垃圾桶，适合书桌旁和居家床位使用。"},{"id":"L009","name":"不锈钢保温杯","category":"生活用品","price":39.9,"platform":"淘宝","rating":4.7,"tags":["保温杯","水杯","通勤"],"description":"长效保温保冷，容量适中，适合通勤和专注携带。"},{"id":"G001","name":"简约定制笔记本","category":"礼品文创","price":9.9,"platform":"拼多多","rating":4.6,"tags":["笔记本","学习","文创"],"description":"简约主题封面，内页顺滑，适合课堂记录和送礼。"},{"id":"G002","name":"商务钢笔礼盒","category":"礼品文创","price":39.9,"platform":"淘宝","rating":4.5,"tags":["钢笔","礼盒","生日礼物"],"description":"含钢笔、墨囊和包装盒，适合生日或毕业赠礼。"},{"id":"G003","name":"桌面励志摆件","category":"礼品文创","price":19.9,"platform":"拼多多","rating":4.3,"tags":["摆件","桌面","礼物"],"description":"小巧桌面装饰，适合送给朋友或布置书桌。"},{"id":"G004","name":"文创帆布包","category":"礼品文创","price":29.9,"platform":"淘宝","rating":4.6,"tags":["帆布包","实用","文创"],"description":"大容量帆布托特包，适合通勤、购物和日常出行。"},{"id":"G005","name":"复古手账套装","category":"礼品文创","price":35.9,"platform":"京东","rating":4.7,"tags":["手账","文具","礼物"],"description":"含手账本、贴纸和胶带，适合记录日常生活和送礼。"},{"id":"G006","name":"古风书签礼盒","category":"礼品文创","price":15.9,"platform":"淘宝","rating":4.5,"tags":["书签","礼盒","文创"],"description":"多款古风书签组合，适合读书爱好者和小型伴手礼。"},{"id":"G007","name":"香薰蜡烛礼盒","category":"礼品文创","price":49.9,"platform":"拼多多","rating":4.4,"tags":["香薰","蜡烛","生日礼物"],"description":"淡香型香薰蜡烛组合，适合居家氛围布置和生日赠礼。"},{"id":"G008","name":"定制照片相框","category":"礼品文创","price":29.9,"platform":"京东","rating":4.6,"tags":["相框","定制","纪念礼物"],"description":"可放入生活合照或生活照片，适合纪念日和毕业礼物。"},{"id":"G009","name":"毕业纪念册","category":"礼品文创","price":59.9,"platform":"淘宝","rating":4.8,"tags":["纪念册","毕业","礼物"],"description":"可书写留言的纪念册，适合集体纪念和毕业留念。"},{"id":"F001","name":"双人火锅套餐","category":"餐饮美食","price":158.0,"platform":"美团","rating":4.7,"tags":["火锅","双人餐","周末聚餐"],"description":"含锅底、荤素拼盘和饮品，适合朋友或情侣聚餐。"},{"id":"F002","name":"家庭披萨套餐","category":"餐饮美食","price":99.0,"platform":"饿了么","rating":4.5,"tags":["披萨","家庭餐","外卖"],"description":"含大份披萨、小食和饮料，适合家庭简餐或朋友分享。"},{"id":"F003","name":"工作日轻食午餐券","category":"餐饮美食","price":29.9,"platform":"美团","rating":4.6,"tags":["午餐","轻食","工作餐"],"description":"可选沙拉、鸡胸肉和谷物饭，适合工作日快速用餐。"},{"id":"F004","name":"咖啡饮品兑换券","category":"餐饮美食","price":19.9,"platform":"美团","rating":4.5,"tags":["咖啡","饮品","下午茶"],"description":"可用于指定咖啡或茶饮，适合通勤和下午茶场景。"},{"id":"F005","name":"生鲜蔬菜周套餐","category":"餐饮美食","price":69.0,"platform":"京东到家","rating":4.4,"tags":["生鲜","蔬菜","家庭采购"],"description":"包含多种当季蔬菜，适合家庭一周基础食材补充。"},{"id":"F006","name":"家庭米面粮油组合","category":"餐饮美食","price":129.0,"platform":"京东","rating":4.7,"tags":["粮油","家庭采购","囤货"],"description":"大米、面粉和食用油基础组合，适合家庭日常储备。"},{"id":"W001","name":"基础纯棉T恤","category":"服饰鞋包","price":59.9,"platform":"淘宝","rating":4.5,"tags":["T恤","纯棉","日常穿搭"],"description":"版型简洁，适合通勤、休闲和叠穿。"},{"id":"W002","name":"通勤双肩包","category":"服饰鞋包","price":129.0,"platform":"京东","rating":4.6,"tags":["双肩包","通勤","电脑包"],"description":"带独立电脑隔层，适合上班、短途出行和日常使用。"},{"id":"W003","name":"轻量运动鞋","category":"服饰鞋包","price":199.0,"platform":"拼多多","rating":4.4,"tags":["运动鞋","轻量","跑步"],"description":"缓震鞋底和透气鞋面，适合日常步行与轻度运动。"},{"id":"W004","name":"保暖针织外套","category":"服饰鞋包","price":159.0,"platform":"淘宝","rating":4.5,"tags":["外套","保暖","秋冬"],"description":"柔软针织面料，适合换季通勤和日常外搭。"},{"id":"W005","name":"居家防滑拖鞋","category":"服饰鞋包","price":29.9,"platform":"拼多多","rating":4.3,"tags":["拖鞋","防滑","居家"],"description":"轻便防滑，适合家庭日常和浴室使用。"},{"id":"A001","name":"迷你电饭煲","category":"数码家电","price":159.0,"platform":"京东","rating":4.6,"tags":["电饭煲","小家电","租房"],"description":"小容量多功能设计，适合独居、租房和小家庭使用。"},{"id":"A002","name":"家用空气炸锅","category":"数码家电","price":199.0,"platform":"拼多多","rating":4.5,"tags":["空气炸锅","厨房电器","家庭"],"description":"操作简单，适合日常快手烹饪和家庭加餐。"},{"id":"A003","name":"便携蓝牙音箱","category":"数码家电","price":99.0,"platform":"淘宝","rating":4.4,"tags":["音箱","蓝牙","户外"],"description":"小巧便携，适合居家听歌、露营和短途出游。"},{"id":"A004","name":"手持挂烫机","category":"数码家电","price":129.0,"platform":"京东","rating":4.5,"tags":["挂烫机","衣物护理","通勤"],"description":"快速预热，适合通勤衣物除皱和日常护理。"},{"id":"J001","name":"多功能不粘锅","category":"家居生活","price":129.0,"platform":"京东","rating":4.6,"tags":["锅具","厨房","租房"],"description":"煎炒煮一体，适合独居和家庭日常烹饪。"},{"id":"J002","name":"家用保温电热水壶","category":"家居生活","price":79.9,"platform":"淘宝","rating":4.5,"tags":["电热水壶","厨房","保温"],"description":"自动断电和保温功能，满足家庭日常饮水需求。"},{"id":"J003","name":"全棉四件套","category":"家居生活","price":199.0,"platform":"拼多多","rating":4.5,"tags":["床品","四件套","换新"],"description":"亲肤棉质面料，适合卧室换季和乔迁布置。"},{"id":"J004","name":"折叠收纳柜","category":"家居生活","price":89.0,"platform":"京东","rating":4.4,"tags":["收纳","储物","租房"],"description":"多层折叠结构，适合小户型、租房和杂物整理。"},{"id":"J005","name":"家用净水壶","category":"家居生活","price":99.0,"platform":"淘宝","rating":4.5,"tags":["净水壶","饮水","家庭"],"description":"过滤水垢和杂质，适合租房及家庭日常饮水。"},{"id":"X001","name":"电子体温计","category":"健康医疗","price":29.9,"platform":"京东","rating":4.7,"tags":["体温计","健康监测","家庭"],"description":"快速测温，适合家庭日常健康监测。"},{"id":"X002","name":"家庭急救包","category":"健康医疗","price":49.9,"platform":"淘宝","rating":4.6,"tags":["急救","家庭","常备"],"description":"含基础消毒、包扎和固定用品，适合家庭应急储备。"},{"id":"X003","name":"复合维生素60片","category":"健康医疗","price":69.0,"platform":"京东","rating":4.5,"tags":["维生素","营养","日常补充"],"description":"日常营养补充产品，使用前请按说明并结合个人情况选择。"},{"id":"X004","name":"医用外科口罩50只","category":"健康医疗","price":24.9,"platform":"拼多多","rating":4.7,"tags":["口罩","防护","家庭"],"description":"独立包装，适合家庭日常防护和出行备用。"},{"id":"X005","name":"颈椎热敷贴","category":"健康医疗","price":39.9,"platform":"淘宝","rating":4.4,"tags":["热敷","颈肩","居家护理"],"description":"温热敷贴，适合久坐后居家放松，不替代医疗诊疗。"},{"id":"T001","name":"共享单车月卡","category":"交通出行","price":16.8,"platform":"美团","rating":4.6,"tags":["单车","月卡","通勤"],"description":"适合短距离通勤和接驳，使用范围以平台规则为准。"},{"id":"T002","name":"地铁10次乘车券","category":"交通出行","price":30.0,"platform":"支付宝","rating":4.7,"tags":["地铁","通勤","乘车券"],"description":"适合日常通勤，覆盖城市地铁基础出行需求。"},{"id":"T003","name":"网约车20元券包","category":"交通出行","price":15.9,"platform":"滴滴出行","rating":4.3,"tags":["打车","优惠券","出行"],"description":"含多张小额打车券，适合雨天、夜间和赶时间出行。"},{"id":"T004","name":"加油200元券包","category":"交通出行","price":189.0,"platform":"易捷","rating":4.5,"tags":["加油","自驾","用车"],"description":"适合自驾通勤和家庭用车，具体适用站点以平台为准。"},{"id":"E001","name":"在线课程月卡","category":"教育学习","price":99.0,"platform":"京东","rating":4.4,"tags":["在线课程","技能提升","学习"],"description":"可学习平台指定课程，适合职业技能和兴趣提升。"},{"id":"E002","name":"电子书平台月卡","category":"教育学习","price":25.0,"platform":"淘宝","rating":4.6,"tags":["电子书","阅读","会员"],"description":"适合日常阅读和知识拓展，具体书库以平台说明为准。"},{"id":"E003","name":"A4打印纸500张","category":"教育学习","price":24.9,"platform":"京东","rating":4.7,"tags":["打印纸","办公","居家学习"],"description":"适合家庭打印、办公资料和孩子作业使用。"},{"id":"E004","name":"英语口语练习课程","category":"教育学习","price":129.0,"platform":"拼多多","rating":4.3,"tags":["英语","口语","课程"],"description":"包含情景练习和发音训练，适合业余时间自主学习。"},{"id":"R001","name":"电影双人票","category":"文体娱乐","price":79.9,"platform":"美团","rating":4.6,"tags":["电影","双人","约会"],"description":"适合情侣、朋友或家人周末观影，具体影院以平台为准。"},{"id":"R002","name":"健身房月卡","category":"文体娱乐","price":199.0,"platform":"美团","rating":4.4,"tags":["健身","月卡","运动"],"description":"可在指定门店使用，适合建立短期运动习惯。"},{"id":"R003","name":"家庭桌游套装","category":"文体娱乐","price":89.0,"platform":"淘宝","rating":4.7,"tags":["桌游","家庭","聚会"],"description":"适合家庭聚会和朋友互动，包含多种基础玩法。"},{"id":"R004","name":"城市博物馆通票","category":"文体娱乐","price":60.0,"platform":"携程","rating":4.8,"tags":["博物馆","城市游","文化"],"description":"覆盖多个合作场馆，适合周末城市文化游览。"},{"id":"P001","name":"全价猫粮2kg","category":"亲子宠物","price":89.0,"platform":"京东","rating":4.6,"tags":["猫粮","宠物","囤货"],"description":"适合成年猫日常喂养，换粮时请循序渐进。"},{"id":"P002","name":"豆腐猫砂10L","category":"亲子宠物","price":39.9,"platform":"拼多多","rating":4.5,"tags":["猫砂","宠物","清洁"],"description":"结团和吸味表现稳定，适合猫咪家庭日常清洁。"},{"id":"P003","name":"宠物互动玩具","category":"亲子宠物","price":29.9,"platform":"淘宝","rating":4.4,"tags":["宠物玩具","互动","猫狗"],"description":"适合日常陪伴和互动，使用时请注意宠物安全。"},{"id":"P004","name":"儿童益智积木","category":"亲子宠物","price":79.0,"platform":"京东","rating":4.7,"tags":["儿童","积木","亲子"],"description":"适合亲子互动和动手能力培养，请按年龄说明使用。"},{"id":"P005","name":"亲子乐园双人票","category":"亲子宠物","price":99.0,"platform":"美团","rating":4.5,"tags":["亲子","乐园","周末"],"description":"适合家长带孩子周末游玩，具体场次以平台为准。"},{"id":"V001","name":"城市周边酒店1晚","category":"旅游住宿","price":399.0,"platform":"携程","rating":4.6,"tags":["酒店","周边游","周末"],"description":"适合周末短途住宿，房型和日期以平台库存为准。"},{"id":"V002","name":"景区成人门票","category":"旅游住宿","price":88.0,"platform":"飞猪","rating":4.7,"tags":["景区","门票","出游"],"description":"适合城市周边景点游玩，使用日期以票面规则为准。"},{"id":"V003","name":"旅行收纳套装","category":"旅游住宿","price":49.9,"platform":"淘宝","rating":4.5,"tags":["旅行收纳","行李","出游"],"description":"分类整理衣物和随身用品，提升短途出行效率。"},{"id":"V004","name":"周末民宿双人套餐","category":"旅游住宿","price":499.0,"platform":"美团","rating":4.5,"tags":["民宿","双人","度假"],"description":"含指定民宿住宿和早餐，适合周末放松。"},{"id":"V005","name":"机场接送服务券","category":"旅游住宿","price":120.0,"platform":"高德","rating":4.4,"tags":["接送机","旅行","交通"],"description":"适合机场往返接驳，需提前预约并确认服务范围。"},{"id":"LS001","name":"家政保洁2小时","category":"本地服务","price":129.0,"platform":"美团","rating":4.5,"tags":["保洁","家政","家庭"],"description":"适合日常家庭清洁，服务内容和范围以商家说明为准。"},{"id":"LS002","name":"空调清洗服务","category":"本地服务","price":99.0,"platform":"京东服务","rating":4.6,"tags":["空调清洗","家电服务","家庭"],"description":"上门清洗单台空调，具体型号和加价规则以平台为准。"},{"id":"LS003","name":"洗衣鞋洗护券","category":"本地服务","price":49.9,"platform":"美团","rating":4.5,"tags":["洗鞋","衣物洗护","本地服务"],"description":"适合运动鞋和日常衣物洗护，特殊材质可能需补差价。"},{"id":"LS004","name":"家电维修上门检测","category":"本地服务","price":59.0,"platform":"美团","rating":4.3,"tags":["维修","家电","上门服务"],"description":"含上门检测，维修配件费用需另行确认。"},{"id":"LS005","name":"同城搬家基础套餐","category":"本地服务","price":299.0,"platform":"货拉拉","rating":4.4,"tags":["搬家","同城","租房"],"description":"适合基础同城搬家，楼层和里程费用以平台报价为准。"},{"id":"CS001","name":"家庭清洁用品组合","category":"商超日用","price":69.0,"platform":"京东","rating":4.7,"tags":["清洁","家庭采购","组合装"],"description":"含清洁剂、抹布和手套，适合家庭日常清洁。"},{"id":"CS002","name":"抽纸24包整箱","category":"商超日用","price":49.9,"platform":"拼多多","rating":4.6,"tags":["抽纸","家庭装","囤货"],"description":"家庭量贩装，适合客厅、卧室和厨房日常使用。"},{"id":"CS003","name":"洗衣液家庭组合装","category":"商超日用","price":79.0,"platform":"京东","rating":4.5,"tags":["洗衣液","家庭装","洗护"],"description":"大容量组合装，适合家庭日常衣物清洁。"},{"id":"CS004","name":"加厚垃圾袋100只","category":"商超日用","price":19.9,"platform":"淘宝","rating":4.4,"tags":["垃圾袋","日用","家庭"],"description":"加厚防漏设计，适合厨房和客厅日常使用。"},{"id":"CS005","name":"家庭洗漱补充装组合","category":"商超日用","price":59.9,"platform":"拼多多","rating":4.5,"tags":["洗漱","补充装","家庭"],"description":"含洗手液和沐浴露补充装，适合家庭日常消耗。"}],"discountRules":{"full_reduction":[{"id":"FR_30_5","name":"平台满30减5","threshold":30,"reduce":5,"description":"单个平台订单满30元减5元。"},{"id":"FR_60_10","name":"生活消费满60减10","threshold":60,"reduce":10,"description":"单个平台订单满60元减10元。"},{"id":"FR_100_20","name":"家庭采购满100减20","threshold":100,"reduce":20,"description":"单个平台订单满100元减20元，适合家庭集中采购。"},{"id":"FR_200_45","name":"品质生活满200减45","threshold":200,"reduce":45,"description":"单个平台订单满200元减45元。"},{"id":"FR_300_70","name":"大额采购满300减70","threshold":300,"reduce":70,"description":"单个平台订单满300元减70元，适合家电、旅行和家庭集中采购。"}],"bundle_rules":[{"id":"BUNDLE_FOOD_59_8","name":"餐饮美食凑单满59减8","threshold":59,"reduce":8,"category":"餐饮美食","description":"餐饮美食订单满59元减8元，适合聚餐和家庭用餐。"},{"id":"BUNDLE_SNACK_59_8","name":"零食饮料凑单满59减8","threshold":59,"reduce":8,"category":"零食饮料","description":"零食饮料订单满59元减8元，适合居家囤货。"},{"id":"BUNDLE_LIFE_79_12","name":"商超日用凑单满79减12","threshold":79,"reduce":12,"category":"生活用品","description":"生活用品订单满79元减12元。"},{"id":"BUNDLE_HOME_99_15","name":"家居生活满99减15","threshold":99,"reduce":15,"category":"家居生活","description":"家居生活订单满99元减15元。"},{"id":"BUNDLE_DIGITAL_150_25","name":"数码家电凑单满150减25","threshold":150,"reduce":25,"category":"数码家电","description":"数码家电订单满150元减25元，适合耳机、小家电组合购买。"},{"id":"BUNDLE_TRAVEL_199_30","name":"旅行住宿满199减30","threshold":199,"reduce":30,"category":"旅游住宿","description":"旅行住宿订单满199元减30元，适合周末出游。"}],"member_discounts":[{"id":"MEMBER_95","name":"生活会员95折","type":"rate","rate":0.95,"min_spend":30,"max_discount":20,"description":"开通生活会员后，订单满30元享95折，最多优惠20元。"},{"id":"NEW_USER_99_15","name":"新客专享满99减15","type":"threshold","threshold":99,"reduce":15,"min_spend":99,"description":"新用户首单满99元减15元。"}],"platform_offers":{"淘宝":{"id":"TAOBAO_LIFE_98","name":"淘宝生活频道98折","type":"rate","rate":0.98,"min_spend":50,"max_discount":10,"description":"淘宝生活频道订单满50元享98折，最多优惠10元。"},"拼多多":{"id":"PDD_LIFE_97","name":"拼多多百亿补贴97折","type":"rate","rate":0.97,"min_spend":39,"max_discount":12,"description":"拼多多百亿补贴订单满39元享97折，最多优惠12元。"},"京东":{"id":"JD_LIFE_98","name":"京东生活会员98折","type":"rate","rate":0.98,"min_spend":59,"max_discount":15,"description":"京东生活会员订单满59元享98折，最多优惠15元。"},"美团":{"id":"MEITUAN_LIFE_95","name":"美团团购95折","type":"rate","rate":0.95,"min_spend":50,"max_discount":12,"description":"美团团购订单满50元享95折，最多优惠12元。"},"携程":{"id":"CTRIP_TRAVEL_95","name":"携程旅行95折","type":"rate","rate":0.95,"min_spend":199,"max_discount":40,"description":"携程指定旅行产品满199元享95折，最多优惠40元。"}}}}</script>

  <script>
    /**
     * 全场景生活消费决策智能体前端逻辑
     * 模块：状态管理、导航切换、API 配置、智能咨询、预算管理、消费复盘。
     */
    (() => {
      "use strict";

      const STORAGE_KEYS = {
        apiBaseUrl: "life-agent-api-base-url",
        budgets: "life-agent-budgets",
        budgetPeriod: "life-agent-budget-period",
        expenses: "life-agent-expenses",
        chatHistory: "life-agent-chat-history",
        projectIntroSeen: "life-agent-project-intro-seen",
        demoSeeded: "life-agent-demo-seeded"
      };
      const LEGACY_STORAGE_KEYS = {
        apiBaseUrl: "campus-agent-api-base-url",
        budgets: "campus-agent-budgets",
        budgetPeriod: "campus-agent-budget-period",
        expenses: "campus-agent-expenses",
        chatHistory: "campus-agent-chat-history",
        projectIntroSeen: "campus-agent-project-intro-seen",
        demoSeeded: "campus-agent-demo-seeded"
      };
      const DEFAULT_BUDGETS = { monthly: 6000, weekly: 1500 };
      const IS_FILE_MODE = window.location.protocol === "file:";
      const DEFAULT_API_BASE_URL = IS_FILE_MODE
        ? "http://127.0.0.1:5000"
        : window.location.origin;
      const REQUEST_TIMEOUT_MS = 60000;
      const API_ENDPOINTS = { chat: "/api/agent/chat" };
      const CATEGORY_COLORS = {
        "餐饮美食": "#2563eb", "零食饮料": "#38bdf8", "商超日用": "#14b8a6",
        "生活用品": "#10b981", "家居生活": "#0d9488", "数码配件": "#8b5cf6",
        "数码家电": "#7c3aed", "服饰鞋包": "#ec4899", "美妆个护": "#f472b6",
        "健康医疗": "#ef4444", "交通出行": "#f59e0b", "教育学习": "#6366f1",
        "文体娱乐": "#f97316", "亲子宠物": "#84cc16", "旅游住宿": "#06b6d4",
        "本地服务": "#64748b", "礼品文创": "#d946ef", "应急储蓄": "#22c55e",
        "其他": "#94a3b8"
      };

      // 内嵌演示引擎：直接打开 index.html 时无需 Flask 后端即可完成核心演示。
      const LOCAL_DEMO_DATA = JSON.parse(document.getElementById("local-demo-data").textContent);
      const LOCAL_PRODUCTS = LOCAL_DEMO_DATA.products;
      const LOCAL_DISCOUNT_RULES = LOCAL_DEMO_DATA.discountRules;
      const LOCAL_CATEGORY_RULES = [
        {
          category: "餐饮美食",
          keywords: ["吃饭", "三餐", "午餐", "晚餐", "早餐", "外卖", "聚餐", "火锅", "披萨", "咖啡", "奶茶", "生鲜", "买菜", "粮油", "餐厅", "餐饮"]
        },
        {
          category: "数码配件",
          keywords: ["耳机", "蓝牙", "充电宝", "数据线", "U盘", "鼠标", "键盘", "数码", "手机支架", "音箱"]
        },
        {
          category: "数码家电",
          keywords: ["电饭煲", "空气炸锅", "挂烫机", "家电", "小家电", "厨房电器"]
        },
        {
          category: "美妆个护",
          keywords: ["洗面奶", "面膜", "口红", "防晒", "洗发水", "沐浴露", "护手霜", "卸妆", "彩妆", "护肤", "美妆", "洗护"]
        },
        {
          category: "零食饮料",
          keywords: ["零食", "泡面", "牛奶", "薯片", "饼干", "燕麦", "矿泉水", "茶饮", "坚果", "辣条", "饮料"]
        },
        {
          category: "商超日用",
          keywords: ["超市", "商超", "抽纸", "家庭装", "清洁用品", "家庭采购", "垃圾袋", "洗漱补充装"]
        },
        {
          category: "生活用品",
          keywords: ["纸巾", "洗衣液", "雨伞", "牙刷", "毛巾", "衣架", "垃圾桶", "保温杯", "日用品", "清洁用品", "日用百货"]
        },
        {
          category: "家居生活",
          keywords: ["锅", "水壶", "四件套", "收纳柜", "净水壶", "床品", "厨房", "家居", "租房", "乔迁", "新家"]
        },
        {
          category: "服饰鞋包",
          keywords: ["衣服", "T恤", "运动鞋", "鞋子", "双肩包", "外套", "拖鞋", "穿搭", "服饰", "鞋包"]
        },
        {
          category: "健康医疗",
          keywords: ["体温计", "急救", "维生素", "口罩", "热敷", "药品", "健康", "医疗", "父母", "老人", "护理"]
        },
        {
          category: "交通出行",
          keywords: ["地铁", "公交", "单车", "打车", "网约车", "加油", "通勤", "交通", "出行", "自驾"]
        },
        {
          category: "教育学习",
          keywords: ["课程", "电子书", "打印纸", "学习", "培训", "考试", "教育", "阅读"]
        },
        {
          category: "文体娱乐",
          keywords: ["电影", "健身", "桌游", "博物馆", "娱乐", "运动", "演出", "周末活动"]
        },
        {
          category: "亲子宠物",
          keywords: ["猫粮", "猫砂", "宠物", "猫咪", "狗狗", "儿童", "亲子", "积木", "孩子", "带娃"]
        },
        {
          category: "旅游住宿",
          keywords: ["酒店", "民宿", "景区", "门票", "旅行", "旅游", "周边游", "出游", "度假", "周末游"]
        },
        {
          category: "本地服务",
          keywords: ["保洁", "家政", "清洗", "维修", "洗鞋", "搬家", "上门服务", "本地服务"]
        },
        {
          category: "礼品文创",
          keywords: ["礼物", "礼品", "生日", "送礼", "纪念日", "节日", "笔记本", "钢笔", "摆件", "帆布包", "手账", "书签", "香薰", "相框", "纪念册", "文创"]
        }
      ];
      const LOCAL_CATEGORY_SWAPS = {
        "餐饮美食": "商超日用",
        "数码配件": "数码家电",
        "数码家电": "家居生活",
        "礼品文创": "健康医疗",
        "健康医疗": "文体娱乐",
        "美妆个护": "服饰鞋包",
        "生活用品": "家居生活",
        "家居生活": "商超日用",
        "零食饮料": "餐饮美食",
        "服饰鞋包": "生活用品",
        "交通出行": "旅游住宿",
        "教育学习": "文体娱乐",
        "文体娱乐": "旅游住宿",
        "亲子宠物": "生活用品",
        "旅游住宿": "文体娱乐",
        "本地服务": "家居生活",
        "商超日用": "生活用品"
      };

      const state = {
        activePage: "chat",
        apiBaseUrl: DEFAULT_API_BASE_URL,
        executionMode: "detecting",
        isSending: false,
        budgetPeriod: "monthly",
        budgets: { ...DEFAULT_BUDGETS, periods: {} },
        selectedBudgetDate: null,
        expenses: [],
        chatHistory: []
      };

      const $ = (selector, scope = document) => scope.querySelector(selector);
      const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));
      const currencyFormatter = new Intl.NumberFormat("zh-CN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });

      /** 将 HTML 特殊字符转义，避免接口数据或用户输入被当作 HTML 执行。 */
      function escapeHtml(value) {
        return String(value ?? "")
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#039;");
      }

      function formatCurrency(value) {
        const number = Number(value);
        return Number.isFinite(number) ? `¥${currencyFormatter.format(number)}` : "¥0.00";
      }

      function localDateString(date = new Date()) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        return `${year}-${month}-${day}`;
      }

      function formatDateLabel(dateString) {
        const date = new Date(`${dateString}T00:00:00`);
        if (Number.isNaN(date.getTime())) return dateString || "未知日期";
        return date.toLocaleDateString("zh-CN", { month: "long", day: "numeric" });
      }

      function generateId() {
        if (window.crypto && typeof window.crypto.randomUUID === "function") {
          return window.crypto.randomUUID();
        }
        return `expense-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      }

      /** 构造跨月度、跨周度的生活消费演示数据，覆盖常见消费分类。 */
      function buildDemoMonthlyExpenses() {
        const now = new Date();
        const demoItems = [
          ["工作日午餐", 35, "餐饮美食", 0],
          ["周末家庭聚餐", 128, "餐饮美食", 2],
          ["超市日用采购", 186, "商超日用", 4],
          ["月度房租", 3200, "住房水电", 5],
          ["水电燃气", 180, "住房水电", 6],
          ["地铁公交充值", 50, "交通出行", 8],
          ["网约车", 26, "交通出行", 9],
          ["在线课程", 99, "教育学习", 11],
          ["电影双人票", 79.9, "文体娱乐", 12],
          ["宠物猫粮", 89, "亲子宠物", 13],
          ["家庭清洁用品", 79.9, "生活用品", 15],
          ["日常洗护", 45, "美妆个护", 17],
          ["家庭常备药品", 58, "健康医疗", 18],
          ["周末咖啡", 19.9, "餐饮美食", 19],
          ["上月房租", 3200, "住房水电", 35],
          ["上月超市采购", 155, "商超日用", 38],
          ["上月交通充值", 50, "交通出行", 41],
          ["上月家庭聚餐", 168, "餐饮美食", 45],
          ["上月电影双人票", 79.9, "文体娱乐", 49],
          ["上月学习资料", 99, "教育学习", 52],
          ["上月宠物用品", 129, "亲子宠物", 56],
          ["上月健康用品", 65, "健康医疗", 60]
        ];
        return demoItems.map(([name, amount, category, offset], index) => {
          const date = new Date(
            now.getFullYear(),
            now.getMonth(),
            now.getDate() - offset
          );
          return {
            id: `demo-${Date.now()}-${index}`,
            name,
            amount,
            category,
            date: localDateString(date)
          };
        });
      }

      function readStorageValue(key, legacyKey = null) {
        try {
          const currentValue = localStorage.getItem(key);
          if (currentValue !== null) return currentValue;
          if (!legacyKey) return null;
          const legacyValue = localStorage.getItem(legacyKey);
          if (legacyValue !== null) {
            localStorage.setItem(key, legacyValue);
            localStorage.removeItem(legacyKey);
          }
          return legacyValue;
        } catch (error) {
          console.warn("读取本地存储失败", error);
          return null;
        }
      }

      function readJsonStorage(key, fallbackValue, legacyKey = null) {
        try {
          const rawValue = readStorageValue(key, legacyKey);
          return rawValue ? JSON.parse(rawValue) : fallbackValue;
        } catch (error) {
          console.warn("读取本地存储失败", error);
          return fallbackValue;
        }
      }

      function writeJsonStorage(key, value) {
        try {
          localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
          console.warn("写入本地存储失败", error);
          showToast("浏览器本地存储不可用，数据可能无法保存。", "error");
        }
      }

      function loadPersistedState() {
        const savedBudgets = readJsonStorage(STORAGE_KEYS.budgets, DEFAULT_BUDGETS, LEGACY_STORAGE_KEYS.budgets);
        const savedExpenses = readJsonStorage(STORAGE_KEYS.expenses, [], LEGACY_STORAGE_KEYS.expenses);
        const savedPeriod = readStorageValue(STORAGE_KEYS.budgetPeriod, LEGACY_STORAGE_KEYS.budgetPeriod);
        const savedApiBaseUrl = readStorageValue(STORAGE_KEYS.apiBaseUrl, LEGACY_STORAGE_KEYS.apiBaseUrl);
        const savedChatHistory = readJsonStorage(STORAGE_KEYS.chatHistory, [], LEGACY_STORAGE_KEYS.chatHistory);

        if (savedBudgets && typeof savedBudgets === "object") {
          state.budgets.monthly = Number(savedBudgets.monthly) > 0 ? Number(savedBudgets.monthly) : DEFAULT_BUDGETS.monthly;
          state.budgets.weekly = Number(savedBudgets.weekly) > 0 ? Number(savedBudgets.weekly) : DEFAULT_BUDGETS.weekly;
          if (savedBudgets.periods && typeof savedBudgets.periods === "object" && !Array.isArray(savedBudgets.periods)) {
            state.budgets.periods = Object.fromEntries(
              Object.entries(savedBudgets.periods)
                .filter(([, value]) => Number.isFinite(Number(value)) && Number(value) > 0)
                .map(([key, value]) => [key, Math.round(Number(value) * 100) / 100])
            );
          }
        }
        if (savedPeriod === "monthly" || savedPeriod === "weekly") {
          state.budgetPeriod = savedPeriod;
        }
        // 旧版本只有一个月度/周度预算值，将其迁移到对应的当前周期。
        const currentMonthlyKey = getPeriodBudgetKey("monthly");
        const currentWeeklyKey = getPeriodBudgetKey("weekly");
        if (!state.budgets.periods[currentMonthlyKey]) {
          state.budgets.periods[currentMonthlyKey] = state.budgets.monthly;
        }
        if (!state.budgets.periods[currentWeeklyKey]) {
          state.budgets.periods[currentWeeklyKey] = state.budgets.weekly;
        }
        state.selectedBudgetDate = localDateString(getPeriodStart(state.budgetPeriod));
        if (savedApiBaseUrl) {
          // 网页部署模式下，旧版本保存的 localhost 地址会指向访问者自己的电脑，
          // 因此自动改用当前网站的同源接口地址。
          const savedUsesLoopback = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?\/?$/i.test(savedApiBaseUrl);
          state.apiBaseUrl = (!IS_FILE_MODE && savedUsesLoopback)
            ? DEFAULT_API_BASE_URL
            : savedApiBaseUrl.replace(
              /^http:\/\/localhost:5000\/?$/i,
              DEFAULT_API_BASE_URL
            );
          localStorage.setItem(STORAGE_KEYS.apiBaseUrl, state.apiBaseUrl);
        } else if (!IS_FILE_MODE) {
          state.apiBaseUrl = DEFAULT_API_BASE_URL;
        }
        if (Array.isArray(savedExpenses)) {
          state.expenses = savedExpenses.filter((item) => (
            item && typeof item.name === "string" && Number.isFinite(Number(item.amount))
          )).map((item) => ({
            id: item.id || generateId(),
            name: item.name,
            amount: Number(item.amount),
            category: item.category || "其他",
            date: item.date || localDateString()
          }));
        }
        if (Array.isArray(savedChatHistory)) {
          state.chatHistory = savedChatHistory
            .filter((item) => item && ["user", "assistant"].includes(item.role) && typeof item.content === "string")
            .slice(-40)
            .map((item) => ({
              id: item.id || generateId(),
              role: item.role,
              content: item.content,
              timestamp: item.timestamp || new Date().toISOString(),
              plans: Array.isArray(item.plans) ? item.plans : [],
              usedTools: Array.isArray(item.usedTools) ? item.usedTools : [],
              requiresInput: Boolean(item.requiresInput),
              suggestedReplies: Array.isArray(item.suggestedReplies) ? item.suggestedReplies.slice(0, 3) : []
            }));
        }

        // 首次演示自动载入月度模拟消费数据；用户主动清空后不会再次强制覆盖。
        const demoWasSeeded = readStorageValue(STORAGE_KEYS.demoSeeded, LEGACY_STORAGE_KEYS.demoSeeded) === "true";
        if (!state.expenses.length && !demoWasSeeded) {
          state.expenses = buildDemoMonthlyExpenses();
          writeJsonStorage(STORAGE_KEYS.expenses, state.expenses);
          localStorage.setItem(STORAGE_KEYS.demoSeeded, "true");
        }
      }

      function saveChatHistory() {
        writeJsonStorage(STORAGE_KEYS.chatHistory, state.chatHistory.slice(-40));
      }

      function saveExpenses() {
        writeJsonStorage(STORAGE_KEYS.expenses, state.expenses);
      }

      function saveBudgets() {
        writeJsonStorage(STORAGE_KEYS.budgets, state.budgets);
        localStorage.setItem(STORAGE_KEYS.budgetPeriod, state.budgetPeriod);
      }
      /** 顶部全局 Toast 提示。 */
      function showToast(message, type = "info") {
        const container = $("#toast-container");
        if (!container) return;

        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        const iconColor = type === "error" ? "text-red-500" : type === "success" ? "text-emerald-500" : "text-blue-500";
        toast.innerHTML = `
          <div class="flex items-start gap-3">
            <span class="mt-0.5 ${iconColor}">
              <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                ${type === "error"
                  ? '<path stroke-linecap="round" stroke-linejoin="round" d="M12 8.25v4.5m0 3h.01M10.3 3.9 2.4 17.6A1.5 1.5 0 0 0 3.7 20h16.6a1.5 1.5 0 0 0 1.3-2.4L13.7 3.9a1.95 1.95 0 0 0-3.4 0Z" />'
                  : '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15.75 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />'}
              </svg>
            </span>
            <p class="flex-1 text-sm leading-6 text-slate-700">${escapeHtml(message)}</p>
            <button type="button" class="text-slate-300 transition hover:text-slate-500" aria-label="关闭提示">×</button>
          </div>
        `;
        container.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add("show"));
        const removeToast = () => {
          toast.classList.remove("show");
          window.setTimeout(() => toast.remove(), 220);
        };
        $("button", toast).addEventListener("click", removeToast);
        window.setTimeout(removeToast, 4200);
      }

      function setApiStatus(status, text) {
        const dot = $("#api-status-dot");
        const label = $("#api-status-text");
        dot.classList.remove("online", "error");
        if (status === "online") dot.classList.add("online");
        if (status === "error") dot.classList.add("error");
        label.textContent = text;
      }

      function normalizeApiBaseUrl(rawValue) {
        let trimmedValue = String(rawValue || "").trim().replace(/\/+$/, "");
        if (!trimmedValue) throw new Error("接口地址不能为空");
        trimmedValue = trimmedValue.replace(
          /^http:\/\/localhost:5000\/?$/i,
          DEFAULT_API_BASE_URL
        );
        let parsedUrl;
        try {
          parsedUrl = new URL(trimmedValue);
        } catch (error) {
          throw new Error("请输入完整接口地址，例如 http://127.0.0.1:5000");
        }
        if (!["http:", "https:"].includes(parsedUrl.protocol)) {
          throw new Error("接口地址必须以 http:// 或 https:// 开头");
        }
        return parsedUrl.toString().replace(/\/+$/, "");
      }

      /** 页面切换：不刷新，仅控制 section 显示和导航激活状态。 */
      function showPage(pageName, updateHash = true) {
        const validPages = ["chat", "budget", "review"];
        if (!validPages.includes(pageName)) pageName = "chat";
        state.activePage = pageName;

        $$("[data-page-section]").forEach((section) => {
          section.classList.toggle("hidden", section.dataset.pageSection !== pageName);
        });
        $$(".nav-tab").forEach((button) => {
          button.classList.toggle("active", button.dataset.page === pageName);
        });

        if (updateHash) {
          const targetHash = `#${pageName}`;
          if (window.location.hash !== targetHash) {
            window.history.replaceState(null, "", targetHash);
          }
        }
        if (pageName === "budget") renderBudgetPage();
        if (pageName === "review") renderReviewPage();
        window.scrollTo({ top: 0, behavior: "smooth" });
      }

      function initNavigation() {
        $$(".nav-tab").forEach((button) => {
          button.addEventListener("click", () => showPage(button.dataset.page));
        });
        const initialPage = window.location.hash.replace("#", "") || "chat";
        showPage(initialPage, false);
        window.addEventListener("hashchange", () => {
          const pageName = window.location.hash.replace("#", "") || "chat";
          showPage(pageName, false);
        });
      }

      function initApiConfiguration() {
        const input = $("#api-base-url");
        input.value = state.apiBaseUrl;
        $("#save-api-url").addEventListener("click", () => {
          try {
            state.apiBaseUrl = normalizeApiBaseUrl(input.value);
            input.value = state.apiBaseUrl;
            localStorage.setItem(STORAGE_KEYS.apiBaseUrl, state.apiBaseUrl);
            setApiStatus("online", state.executionMode === "local" ? "本地演示模式 · 无需后端" : "等待后端连接");
            showToast("接口地址已保存。", "success");
          } catch (error) {
            showToast(error.message, "error");
          }
        });
        $("#focus-api-config").addEventListener("click", () => {
          const panel = $("#api-config-panel");
          panel.classList.toggle("hidden");
          if (!panel.classList.contains("hidden")) {
            panel.scrollIntoView({ behavior: "smooth", block: "center" });
            input.focus({ preventScroll: true });
            input.select();
          }
        });
      }
            function formatMessageTime(timestamp) {
        const date = new Date(timestamp);
        return Number.isNaN(date.getTime())
          ? new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
          : date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
      }

      /** 根据统一消息对象创建 DOM，供实时对话和历史恢复共同使用。 */
      function createMessageElement(message) {
        const isUser = message.role === "user";
        const row = document.createElement("div");
        row.className = `message-row flex items-start gap-3 ${isUser ? "justify-end" : ""}`;
        const avatar = isUser ? "" : `
          <div class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-blue-100 text-blue-600">
            <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h8M8 14h5m-8.5 5.5-1.2.7a.5.5 0 0 1-.74-.53l.43-2.16A8.25 8.25 0 1 1 7.5 19Z" />
            </svg>
          </div>`;
        const bubbleClass = isUser
          ? "rounded-2xl rounded-tr-md bg-blue-600 px-4 py-3 text-sm leading-6 text-white shadow-lg shadow-blue-200/60"
          : "rounded-2xl rounded-tl-md border border-slate-100 bg-white px-4 py-3 text-sm leading-6 text-slate-700 shadow-sm";
        const suggestions = Array.isArray(message.suggestedReplies) ? message.suggestedReplies : [];
        const suggestionHtml = !isUser && suggestions.length
          ? `<div class="mt-2 flex flex-wrap gap-2">
              ${suggestions.map((reply) => `<button type="button" data-suggested-reply="${escapeHtml(reply)}" class="prompt-chip rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-[11px] font-semibold text-blue-700 hover:bg-blue-100">${escapeHtml(reply)}</button>`).join("")}
            </div>`
          : "";
        const inputBadge = !isUser && message.requiresInput
          ? '<span class="mb-1 inline-flex rounded-full bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-600">需要补充信息</span>'
          : "";

        row.innerHTML = `
          ${avatar}
          <div class="max-w-[86%]">
            ${inputBadge}
            <div class="${bubbleClass} whitespace-pre-wrap break-words">${escapeHtml(message.content)}</div>
            <p class="mt-1.5 text-[10px] text-slate-400 ${isUser ? "text-right" : ""}">${formatMessageTime(message.timestamp)}</p>
            ${suggestionHtml}
          </div>
        `;
        return row;
      }

      function renderChatMessage(message) {
        const container = $("#chat-messages");
        container.appendChild(createMessageElement(message));
        container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
      }

      /** 追加消息并持久化，页面刷新后可完整恢复。 */
      function appendMessage(role, text, metadata = {}) {
        const message = {
          id: generateId(),
          role,
          content: String(text),
          timestamp: new Date().toISOString(),
          plans: Array.isArray(metadata.plans) ? metadata.plans : [],
          usedTools: Array.isArray(metadata.usedTools) ? metadata.usedTools : [],
          requiresInput: Boolean(metadata.requiresInput),
          suggestedReplies: Array.isArray(metadata.suggestedReplies) ? metadata.suggestedReplies.slice(0, 3) : []
        };
        state.chatHistory.push(message);
        state.chatHistory = state.chatHistory.slice(-40);
        saveChatHistory();
        $("#welcome-message")?.classList.add("hidden");
        renderChatMessage(message);
        return message;
      }

      /** 恢复本地对话历史，并用最后一条 assistant 消息恢复右侧方案。 */
      function restoreChatHistory() {
        const messages = state.chatHistory;
        if (!messages.length) {
          $("#welcome-message")?.classList.remove("hidden");
          renderPlans([]);
          renderUsedTools([]);
          return;
        }

        $("#welcome-message")?.classList.add("hidden");
        messages.forEach(renderChatMessage);
        const lastAssistant = [...messages].reverse().find((message) => message.role === "assistant");
        renderPlans(lastAssistant?.plans || [], Boolean(lastAssistant?.requiresInput));
        renderUsedTools(lastAssistant?.usedTools || []);
      }

      /** 为模型截取最近上下文，并把上一轮方案压缩进 assistant 内容。 */
      function buildApiHistory() {
        return state.chatHistory.slice(-10).map((message) => {
          let content = message.content;
          if (message.role === "assistant" && message.plans?.length) {
            const compactPlans = message.plans.map((plan) => ({
              name: plan.name,
              desc: plan.desc,
              items: plan.items,
              total_price: plan.total_price,
              advantage: plan.advantage
            }));
            content += `\n[上一轮方案上下文]${JSON.stringify(compactPlans)}`;
          }
          return { role: message.role, content: content.slice(0, 5000) };
        });
      }

      function clearChatHistory() {
        if (state.isSending) {
          showToast("正在生成方案，请稍后再清空对话。", "info");
          return;
        }
        if (!state.chatHistory.length) {
          showToast("当前没有可清空的对话记录。", "info");
          return;
        }
        if (!window.confirm("确认清空本地对话历史和右侧方案吗？")) return;
        state.chatHistory = [];
        saveChatHistory();
        $$("#chat-messages .message-row:not(#welcome-message)").forEach((row) => row.remove());
        $("#typing-indicator")?.remove();
        const welcome = $("#welcome-message");
        if (welcome) {
          welcome.classList.remove("hidden");
          $("#chat-messages").prepend(welcome);
        }
        renderPlans([]);
        renderUsedTools([]);
        showToast("对话历史已清空。", "success");
      }

      function setChatLoading(isLoading) {
        const button = $("#send-button");
        const input = $("#chat-input");
        const spinner = $("#send-spinner");
        const icon = $("#send-icon");
        const label = $("#send-label");
        button.disabled = isLoading;
        input.disabled = isLoading;
        spinner.classList.toggle("hidden", !isLoading);
        icon.classList.toggle("hidden", isLoading);
        label.textContent = isLoading ? "思考中" : "发送";

        const existingIndicator = $("#typing-indicator");
        if (isLoading && !existingIndicator) {
          const container = $("#chat-messages");
          const indicator = document.createElement("div");
          indicator.id = "typing-indicator";
          indicator.className = "message-row flex items-start gap-3";
          indicator.innerHTML = `
            <div class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-blue-100 text-blue-600">
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M8 10h8M8 14h5m-8.5 5.5-1.2.7a.5.5 0 0 1-.74-.53l.43-2.16A8.25 8.25 0 1 1 7.5 19Z" /></svg>
            </div>
            <div class="rounded-2xl rounded-tl-md border border-slate-100 bg-white px-4 py-4 shadow-sm">
              <span class="typing-dots" aria-label="正在生成方案"><span></span><span></span><span></span></span>
            </div>`;
          container.appendChild(indicator);
          container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
        }
        if (!isLoading && existingIndicator) existingIndicator.remove();
      }
      function itemName(item, index) {
        if (typeof item === "string") return item;
        return item?.name || item?.title || item?.product_name || `商品 ${index + 1}`;
      }

      function itemPrice(item) {
        if (!item || typeof item === "string") return 0;
        const value = item.final_price ?? item.price ?? item.unit_price ?? 0;
        return Number(value) || 0;
      }

      function itemQuantity(item) {
        if (!item || typeof item === "string") return 1;
        return Math.max(1, Number(item.quantity) || 1);
      }

      /** 前端侧再次兼容后端/模型字段别名，形成稳定的方案展示结构。 */
      function normalizePlanForFrontend(plan, index) {
        if (!plan || typeof plan !== "object") return null;
        const rawItems = Array.isArray(plan.items)
          ? plan.items
          : (Array.isArray(plan.products) ? plan.products : []);
        const items = rawItems.map((item, itemIndex) => {
          if (typeof item === "string") {
            return { id: `item-${itemIndex}`, name: item, quantity: 1, price: 0, final_price: 0 };
          }
          const price = Number(item?.final_price ?? item?.price ?? item?.unit_price ?? 0) || 0;
          return {
            id: item?.id ?? item?.product_id ?? `item-${itemIndex}`,
            name: item?.name ?? item?.title ?? item?.product_name ?? `商品 ${itemIndex + 1}`,
            quantity: Math.max(1, Number(item?.quantity) || 1),
            price,
            final_price: price,
            platform: item?.platform || ""
          };
        });
        let totalPrice = Number(plan.total_price ?? plan.total ?? plan.price ?? 0) || 0;
        if (totalPrice <= 0) {
          totalPrice = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
        }
        return {
          name: plan.name || plan.title || `方案 ${index + 1}`,
          desc: plan.desc || plan.description || "",
          items,
          total_price: Math.round(totalPrice * 100) / 100,
          advantage: plan.advantage || plan.reason || plan.recommendation_reason || ""
        };
      }

      /** 将后端 plans 渲染为 2-3 张带推荐理由的方案卡片。 */
      function renderPlans(plans, requiresInput = false) {
        const emptyState = $("#plans-empty");
        const container = $("#plans-container");
        const validPlans = Array.isArray(plans)
          ? plans.map(normalizePlanForFrontend).filter(Boolean).slice(0, 3)
          : [];

        if (!validPlans.length) {
          container.innerHTML = "";
          container.classList.add("hidden");
          emptyState.classList.remove("hidden");
          const emptyTitle = requiresInput ? "等待补充关键信息" : "暂未生成结构化方案";
          const emptyText = requiresInput
            ? "请在左侧回答预算或品类偏好，Assistant 会继续生成方案。"
            : "可以查看左侧回复，或补充预算和场景后重新咨询。";
          emptyState.innerHTML = `
            <div class="grid h-16 w-16 place-items-center rounded-3xl ${requiresInput ? "bg-amber-50 text-amber-500" : "bg-blue-50 text-blue-500"}">
              <svg viewBox="0 0 24 24" class="h-8 w-8" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 3h.01M10.3 3.9 2.4 17.6A1.5 1.5 0 0 0 3.7 20h16.6a1.5 1.5 0 0 0 1.3-2.4L13.7 3.9a1.95 1.95 0 0 0-3.4 0Z" /></svg>
            </div>
            <h4 class="mt-4 font-bold text-slate-800">${emptyTitle}</h4>
            <p class="mt-2 max-w-xs text-sm leading-6 text-slate-400">${emptyText}</p>`;
          return;
        }

        emptyState.classList.add("hidden");
        container.classList.remove("hidden");
        container.innerHTML = validPlans.map((plan, planIndex) => {
          const items = Array.isArray(plan?.items) ? plan.items : [];
          const itemRows = items.length
            ? items.map((item, itemIndex) => {
                const name = itemName(item, itemIndex);
                const price = itemPrice(item);
                const quantity = itemQuantity(item);
                return `
                  <div class="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2.5">
                    <div class="min-w-0">
                      <p class="truncate text-xs font-semibold text-slate-700">${escapeHtml(name)}</p>
                      <p class="mt-0.5 text-[10px] text-slate-400">数量 ${quantity}</p>
                    </div>
                    <span class="shrink-0 text-xs font-bold text-slate-600">${formatCurrency(price * quantity)}</span>
                  </div>`;
              }).join("")
            : '<div class="rounded-xl border border-dashed border-slate-200 px-3 py-4 text-center text-xs text-slate-400">该方案为预算分配建议，无具体商品清单</div>';

          const totalPrice = Number(plan?.total_price ?? 0);
          const reason = plan?.advantage || plan?.desc || "由智能体结合预算与工具结果生成。";
          const badgeText = planIndex === 0 ? "首选推荐" : `备选方案 ${planIndex + 1}`;
          const badgeClass = planIndex === 0 ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-500";
          const cardClass = planIndex === 0
            ? "border-blue-200 bg-gradient-to-br from-blue-50/90 to-white ring-1 ring-blue-100"
            : "border-slate-200 bg-white";

          return `
            <article class="plan-card rounded-2xl border p-4 ${cardClass}">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <span class="inline-flex rounded-full px-2.5 py-1 text-[10px] font-black tracking-wide ${badgeClass}">${badgeText}</span>
                  <h4 class="mt-2 truncate text-base font-black text-slate-900">${escapeHtml(plan?.name || `方案 ${planIndex + 1}`)}</h4>
                  <p class="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">${escapeHtml(plan?.desc || "")}</p>
                </div>
                <div class="shrink-0 text-right">
                  <p class="text-[10px] font-semibold uppercase tracking-wider text-slate-400">预计总价</p>
                  <p class="mt-1 text-xl font-black text-blue-700">${formatCurrency(totalPrice)}</p>
                </div>
              </div>
              <div class="mt-4 space-y-2">${itemRows}</div>
              <div class="mt-3 flex flex-wrap gap-1.5">
                <span class="rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-[10px] font-bold text-blue-700">AI 自主决策</span>
                <span class="rounded-full border border-cyan-200 bg-cyan-50 px-2.5 py-1 text-[10px] font-bold text-cyan-700">多平台比价</span>
                <span class="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[10px] font-bold text-emerald-700">最优优惠计算</span>
              </div>
              <div class="mt-3 rounded-xl border border-blue-100 bg-blue-50/80 p-3">
                <p class="text-[10px] font-black uppercase tracking-wider text-blue-600">推荐理由</p>
                <p class="mt-1 text-xs leading-5 text-blue-900/80">${escapeHtml(reason)}</p>
              </div>
            </article>`;
        }).join("");
      }

      function renderUsedTools(tools) {
        const container = $("#used-tools");
        const uniqueTools = Array.isArray(tools) ? [...new Set(tools.filter(Boolean))] : [];
        if (!uniqueTools.length) {
          container.innerHTML = '<span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-500">暂无</span>';
          return;
        }
        container.innerHTML = uniqueTools.map((tool) => (
          `<span class="rounded-full border border-blue-100 bg-blue-50 px-2.5 py-1 text-[11px] font-semibold text-blue-700">${escapeHtml(tool)}</span>`
        )).join("");
      }
      /** ---------- 本地演示 Agent：无需 Flask 后端即可直接运行 ---------- */
      function localRound(value) {
        return Math.round((Number(value) || 0) * 100) / 100;
      }

      const LOCAL_SCENE_BUNDLES = [
        {
          id: "family",
          label: "家庭采购",
          pattern: /(家庭采购|一家.{0,4}口|家庭消费|家庭.{0,4}预算|生活采购|囤货|年货)/,
          categories: ["商超日用", "餐饮美食", "生活用品", "亲子宠物"],
          ratios: [0.42, 0.28, 0.2, 0.1],
          valueRatios: [0.5, 0.25, 0.18, 0.07],
          suggestions: ["再便宜一点", "增加生鲜预算", "减少零食预算"]
        },
        {
          id: "travel",
          label: "周边出游",
          pattern: /(周边游|周末游|短途旅行|旅游|出游|度假|两天一夜|三天两夜)/,
          categories: ["旅游住宿", "交通出行", "餐饮美食", "文体娱乐"],
          ratios: [0.43, 0.17, 0.25, 0.15],
          valueRatios: [0.36, 0.2, 0.3, 0.14],
          suggestions: ["改成一日游", "提高住宿预算", "再省一点"]
        },
        {
          id: "home",
          label: "居家改善",
          pattern: /(租房|乔迁|新家|改善厨房|厨房改造|家居升级|布置房间)/,
          categories: ["家居生活", "数码家电", "生活用品"],
          ratios: [0.5, 0.35, 0.15],
          valueRatios: [0.45, 0.4, 0.15],
          suggestions: ["只买必需品", "增加小家电预算", "换一套更便宜的"]
        },
        {
          id: "health",
          label: "健康关怀",
          pattern: /(健康用品|家庭健康|给.{0,8}(父母|爸妈|老人).{0,8}(健康|营养|护理)|体检|营养补充)/,
          categories: ["健康医疗", "生活用品", "餐饮美食"],
          ratios: [0.55, 0.2, 0.25],
          valueRatios: [0.6, 0.22, 0.18],
          suggestions: ["再实用一点", "控制在150元内", "换一份健康礼盒"]
        },
        {
          id: "commute",
          label: "通勤出行",
          pattern: /(通勤|上下班|每日出行|交通方案|月度出行)/,
          categories: ["交通出行", "数码配件", "餐饮美食"],
          ratios: [0.6, 0.15, 0.25],
          valueRatios: [0.7, 0.1, 0.2],
          suggestions: ["更省钱一点", "增加打车预算", "按一周规划"]
        },
        {
          id: "date",
          label: "约会纪念",
          pattern: /(约会|纪念日|情侣|二人世界)/,
          categories: ["餐饮美食", "文体娱乐", "礼品文创"],
          ratios: [0.45, 0.35, 0.2],
          valueRatios: [0.55, 0.3, 0.15],
          suggestions: ["更浪漫一点", "再省一点", "换一个约会方案"]
        },
        {
          id: "child",
          label: "亲子周末",
          pattern: /(亲子|带孩子|儿童周末|遛娃)/,
          categories: ["亲子宠物", "文体娱乐", "餐饮美食"],
          ratios: [0.4, 0.35, 0.25],
          valueRatios: [0.45, 0.3, 0.25],
          suggestions: ["更省钱一点", "增加亲子活动", "改到半天"]
        },
        {
          id: "gift",
          label: "送礼关怀",
          pattern: /(送礼|礼物|生日|节日礼物|给.{0,8}(父母|爸妈|朋友|对象).{0,8}(买|挑|推荐))/,
          categories: ["礼品文创", "健康医疗", "数码配件"],
          ratios: [0.45, 0.3, 0.25],
          valueRatios: [0.55, 0.25, 0.2],
          suggestions: ["更实用一点", "再便宜一点", "换一份礼物"]
        }
      ];

      function localParseBudget(text) {
        const patterns = [
          /(?:预算|控制在|不超过|最多|以内|左右)\s*(?:为|是)?\s*(\d+(?:\.\d+)?)\s*元?/i,
          /(\d+(?:\.\d+)?)\s*元(?:以内|左右|以下)?/i,
          /(\d+(?:\.\d+)?)\s*块(?:钱)?/i
        ];
        for (const pattern of patterns) {
          const match = text.match(pattern);
          if (match) return Number(match[1]);
        }
        return null;
      }

      function localDetectCategories(text) {
        const categories = [];
        LOCAL_CATEGORY_RULES.forEach((rule) => {
          if (rule.keywords.some((keyword) => text.includes(keyword))) {
            categories.push(rule.category);
          }
        });

        if (/(男生|男性)/.test(text) && /(礼物|生日|送)/.test(text)) {
          categories.push("数码配件", "文体娱乐");
        }
        if (/(女生|女性)/.test(text) && /(礼物|生日|送)/.test(text)) {
          categories.push("美妆个护", "礼品文创");
        }
        return [...new Set(categories)];
      }

      function localDetectScene(text) {
        return LOCAL_SCENE_BUNDLES.find((scene) => scene.pattern.test(text)) || null;
      }

      function localShouldUseSceneBundle(scene, text) {
        if (!scene) return false;
        if (["family", "travel", "home", "health", "commute", "date", "child"].includes(scene.id)) {
          return true;
        }
        return scene.id === "gift" && /(礼物|送礼|生日|节日)/.test(text);
      }

      function localExtractKeywords(text) {
        const keywords = [];
        const addKeyword = (keyword) => {
          if (!keywords.includes(keyword)) keywords.push(keyword);
        };
        LOCAL_CATEGORY_RULES.forEach((rule) => {
          rule.keywords.forEach((keyword) => {
            if (text.includes(keyword)) addKeyword(keyword);
          });
        });

        if (/(男生|男性)/.test(text)) {
          ["键盘", "鼠标", "充电宝", "钢笔", "保温杯", "耳机", "实用"].forEach(addKeyword);
        }
        if (/(女生|女性)/.test(text)) {
          ["香薰", "手账", "口红", "面膜", "相框", "礼盒"].forEach(addKeyword);
        }
        if (/实用/.test(text)) {
          ["实用", "充电宝", "保温杯", "键盘", "家庭", "耐用"].forEach(addKeyword);
        }
        if (/性价比|划算|省钱/.test(text)) {
          ["经济实惠", "平价", "高性价比", "耐用"].forEach(addKeyword);
        }
        if (/健康|父母|老人/.test(text)) {
          ["健康", "家庭", "护理", "营养"].forEach(addKeyword);
        }
        return keywords;
      }

      function localSearchProducts(categories, keywords, budget) {
        return LOCAL_PRODUCTS
          .filter((product) => product.price <= budget)
          .filter((product) => !categories.length || categories.includes(product.category))
          .map((product) => {
            const searchable = `${product.name} ${product.category} ${product.description} ${product.tags.join(" ")}`;
            const keywordMatches = keywords.filter((keyword) => searchable.includes(keyword)).length;
            const score =
              Number(product.rating) * 22 +
              keywordMatches * 28 +
              Math.max(0, budget - product.price) * 0.08 -
              product.price * 0.035;
            return { product, score, keywordMatches };
          })
          .sort((a, b) => b.score - a.score || a.product.price - b.product.price)
          .map((item) => item.product);
      }

      function localApplyMemberDiscount(total, rules) {
        const memberRules = Array.isArray(rules) ? rules : [];
        let bestDiscount = 0;
        let bestRule = null;
        memberRules.forEach((rule) => {
          if (total < Number(rule.min_spend || 0)) return;
          let discount = 0;
          if (rule.type === "rate") {
            discount = total * (1 - Math.min(1, Math.max(0, Number(rule.rate) || 1)));
            discount = Math.min(discount, Number(rule.max_discount ?? discount));
          } else if (rule.type === "threshold" && total >= Number(rule.threshold || 0)) {
            discount = Number(rule.reduce || 0);
          }
          discount = localRound(Math.max(0, discount));
          if (discount > bestDiscount) {
            bestDiscount = discount;
            bestRule = rule;
          }
        });
        return { discount: bestDiscount, rule: bestRule };
      }

      function localBuildDiscountedPlan(name, products, description, budget) {
        const baseTotal = localRound(
          products.reduce((sum, product) => sum + Number(product.price), 0)
        );
        const platformOffer = LOCAL_DISCOUNT_RULES.platform_offers?.[products[0]?.platform];
        let platformDiscount = 0;
        if (platformOffer && baseTotal >= Number(platformOffer.min_spend || 0)) {
          if (platformOffer.type === "rate") {
            platformDiscount = Math.min(
              baseTotal * (1 - Number(platformOffer.rate || 1)),
              Number(platformOffer.max_discount ?? baseTotal)
            );
          } else if (platformOffer.type === "threshold" && baseTotal >= Number(platformOffer.threshold || 0)) {
            platformDiscount = Number(platformOffer.reduce || 0);
          }
        }
        platformDiscount = localRound(Math.max(0, platformDiscount));

        const fullRules = [...(LOCAL_DISCOUNT_RULES.full_reduction || [])]
          .sort((a, b) => Number(a.threshold) - Number(b.threshold));
        const matchedRule = [...fullRules]
          .reverse()
          .find((rule) => baseTotal >= Number(rule.threshold) && (
            !rule.category || products.some((product) => product.category === rule.category)
          ));
        const reduction = matchedRule ? Number(matchedRule.reduce) : 0;
        const afterReduction = Math.max(0, baseTotal - platformDiscount - reduction);
        const memberRules = LOCAL_DISCOUNT_RULES.member_discounts || LOCAL_DISCOUNT_RULES.student_discounts || [];
        const memberResult = localApplyMemberDiscount(afterReduction, memberRules);
        const finalTotal = localRound(Math.max(0, afterReduction - memberResult.discount));
        const totalDiscount = localRound(baseTotal - finalTotal);

        const items = products.map((product, index) => {
          const previousDiscounts = products.slice(0, index).reduce(
            (sum, item) => sum + localRound(totalDiscount * Number(item.price) / baseTotal),
            0
          );
          const share = index === products.length - 1
            ? localRound(totalDiscount - previousDiscounts)
            : localRound(totalDiscount * Number(product.price) / baseTotal);
          return {
            id: product.id,
            name: product.name,
            quantity: 1,
            price: Number(product.price),
            final_price: localRound(Number(product.price) - share),
            platform: product.platform
          };
        });

        const discountText = totalDiscount > 0
          ? `已计算平台优惠、满减与会员权益，预计优惠约 ¥${totalDiscount.toFixed(2)}`
          : "当前组合未达到额外优惠门槛";
        return {
          name,
          desc: description,
          items,
          total_price: finalTotal,
          advantage: `${discountText}，最终控制在 ¥${budget.toFixed(2)} 预算内。`
        };
      }

      function localBuildShoppingResponse(userInput, budget, categories, keywords, contextText = userInput) {
        let candidates = localSearchProducts(categories, keywords, budget);
        if (!candidates.length && categories.length) {
          candidates = localSearchProducts([], keywords, budget);
        }

        if (!candidates.length) {
          return {
            answer: `当前本地商品库中没有找到预算 ¥${budget.toFixed(2)} 内的匹配项。可以适当提高预算、放宽品类，或改为让我先做预算分配。`,
            plans: [],
            requires_input: true,
            suggested_replies: ["预算提高到300元", "先帮我规划预算", "换一个消费方向"],
            used_tools: ["search_products"]
          };
        }

        const plans = [];
        const giftIntent = categories.includes("礼品文创") && /(礼物|生日|送|送礼)/.test(contextText);
        let first = candidates[0];
        if (giftIntent) {
          const premiumCandidates = candidates
            .filter((product) => product.price >= budget * 0.25)
            .sort((a, b) => b.rating - a.rating || b.price - a.price);
          if (premiumCandidates.length) first = premiumCandidates[0];
        }

        plans.push(localBuildDiscountedPlan(
          "首选品质方案",
          [first],
          `结合评分、价格和“${userInput}”的需求匹配度，优先推荐${first.category}类选择。`,
          budget
        ));

        if (candidates.length > 1) {
          const second = candidates.find((product) => product.id !== first.id) || candidates[1];
          plans.push(localBuildDiscountedPlan(
            "备选性价比方案",
            [second],
            "在相同预算下提供另一种选择，适合更关注价格、平台差异或使用频率的场景。",
            budget
          ));
        }

        const categoryText = categories.length ? categories.join("、") : first.category;
        return {
          answer: `已围绕“${userInput}”完成筛选。当前按 ${categoryText} 品类、¥${budget.toFixed(2)} 预算进行比较，并综合评分、价格和平台优惠生成 ${plans.length} 套方案。`,
          plans: plans.slice(0, 3),
          requires_input: false,
          suggested_replies: ["再便宜一点", "换个消费方向", "重新规划预算"],
          used_tools: ["search_products", "calculate_discount"]
        };
      }

      function localBudgetWeight(scene) {
        const weights = {
          "餐饮美食": 20, "商超日用": 12, "生活用品": 6, "住房水电": 16,
          "交通出行": 10, "数码家电": 5, "服饰鞋包": 5, "美妆个护": 4,
          "健康医疗": 4, "零食饮料": 3, "教育学习": 3, "文体娱乐": 3,
          "亲子宠物": 2, "旅游住宿": 2, "本地服务": 1, "礼品文创": 2,
          "应急储蓄": 2, "数码配件": 4
        };
        return weights[scene] || 4;
      }

      function localBuildBudgetItems(scenes, totalBudget, mode) {
        const weights = scenes.map((scene) => {
          const base = localBudgetWeight(scene);
          if (mode === "cautious" && ["文体娱乐", "数码家电", "服饰鞋包", "美妆个护", "礼品文创", "零食饮料", "旅游住宿"].includes(scene)) {
            return base * 0.65;
          }
          if (mode === "cautious" && ["应急储蓄", "住房水电", "健康医疗"].includes(scene)) {
            return base * 1.15;
          }
          return base;
        });
        const totalWeight = weights.reduce((sum, weight) => sum + weight, 0) || 1;
        let allocated = 0;
        return scenes.map((scene, index) => {
          const amount = index === scenes.length - 1
            ? localRound(totalBudget - allocated)
            : localRound(totalBudget * weights[index] / totalWeight);
          allocated = localRound(allocated + amount);
          return {
            id: `budget-${scene}`,
            name: `${scene}预算`,
            quantity: 1,
            price: amount,
            final_price: amount
          };
        });
      }

      function localBuildBudgetResponse(totalBudget, categories = [], scene = null) {
        let scenes = categories.length ? [...new Set(categories)] : [];
        if (scene) scenes = [...scene.categories];
        if (!scenes.length) {
          scenes = ["餐饮美食", "商超日用", "住房水电", "交通出行", "文体娱乐", "应急储蓄"];
        }
        scenes = scenes.slice(0, 8);
        if (!scenes.includes("应急储蓄")) {
          if (scenes.length >= 8) scenes[scenes.length - 1] = "应急储蓄";
          else scenes.push("应急储蓄");
        }

        const plans = [
          {
            name: "稳健保障方案",
            desc: "优先覆盖日常刚需和应急空间，压缩非必要弹性支出。",
            items: localBuildBudgetItems(scenes, totalBudget, "cautious"),
            total_price: localRound(totalBudget),
            advantage: "住房、餐饮、日用品和应急资金优先，适合希望稳定控制月度支出的用户。"
          },
          {
            name: "均衡生活方案",
            desc: "在保障基本生活的同时，为娱乐、购物和体验型消费保留空间。",
            items: localBuildBudgetItems(scenes, totalBudget, "balanced"),
            total_price: localRound(totalBudget),
            advantage: "刚需与体验消费更均衡，适合收入稳定、希望兼顾生活质量的用户。"
          }
        ];

        return {
          answer: `已将 ¥${totalBudget.toFixed(2)} 按 ${scenes.join("、")} 等场景生成 2 套预算方案。建议先锁定住房、餐饮和日用等刚性支出，再安排弹性消费。`,
          plans,
          requires_input: false,
          suggested_replies: ["减少娱乐预算", "增加餐饮预算", "再省一点"],
          used_tools: ["budget_allocation"]
        };
      }

      function localPickSceneProduct(category, targetBudget, keywords, usedIds) {
        const candidates = localSearchProducts([category], keywords, targetBudget)
          .filter((product) => !usedIds.has(product.id));
        if (!candidates.length) return null;
        const qualityCandidates = candidates.filter((product) =>
          Number(product.price) >= targetBudget * 0.18 && Number(product.rating) >= 4.2
        );
        const pool = qualityCandidates.length ? qualityCandidates : candidates;
        return [...pool].sort((a, b) =>
          Number(b.rating) - Number(a.rating) ||
          Number(b.price) - Number(a.price)
        )[0];
      }

      function localBuildScenePlan(scene, scheme, budget, keywords) {
        const usedIds = new Set();
        const items = [];
        let allocated = 0;

        scene.categories.forEach((category, index) => {
          const ratio = scheme.ratios[index] ?? 0;
          const target = localRound(budget * ratio);
          const product = localPickSceneProduct(category, target, keywords, usedIds);
          if (product) {
            usedIds.add(product.id);
            items.push({
              id: product.id,
              name: product.name,
              quantity: 1,
              price: Number(product.price),
              final_price: Number(product.price),
              platform: product.platform
            });
            allocated = localRound(allocated + Number(product.price));
          } else if (target > 0) {
            items.push({
              id: `scene-${scheme.id}-${category}`,
              name: `${category}预算`,
              quantity: 1,
              price: target,
              final_price: target
            });
            allocated = localRound(allocated + target);
          }
        });

        const remaining = localRound(budget - allocated);
        if (remaining > 0.01) {
          items.push({
            id: `scene-${scheme.id}-buffer`,
            name: "灵活备用金",
            quantity: 1,
            price: remaining,
            final_price: remaining
          });
        }

        return {
          name: scheme.name,
          desc: `覆盖${scene.categories.join("、")}，按 ${scheme.note} 控制预算。`,
          items,
          total_price: budget,
          advantage: `${scheme.advantage} 实际商品之外未用完的额度会进入灵活备用金，整体不超过 ¥${budget.toFixed(2)}。`
        };
      }

      function localBuildSceneResponse(userInput, budget, scene) {
        const keywords = localExtractKeywords(userInput);
        const plans = [
          localBuildScenePlan(scene, {
            id: "balanced",
            name: "均衡体验方案",
            ratios: scene.ratios,
            note: "体验与预算平衡",
            advantage: `优先兼顾${scene.label}的核心体验，适合希望一次安排完整的用户。`
          }, budget, keywords),
          localBuildScenePlan(scene, {
            id: "value",
            name: "预算优先方案",
            ratios: scene.valueRatios,
            note: "刚需优先、弹性压缩",
            advantage: `保留${scene.label}的必要环节，同时为后续临时支出留出更多空间。`
          }, budget, keywords)
        ];

        return {
          answer: `已识别为“${scene.label}”场景，并围绕 ${scene.categories.join("、")} 生成 2 套方案。方案会优先选择预算内匹配度较高的商品或服务，未使用额度自动留作灵活备用金。`,
          plans,
          requires_input: false,
          suggested_replies: scene.suggestions,
          used_tools: ["budget_allocation", "search_products"]
        };
      }

      function localAgentReply(userInput, history) {
        const historyText = history.map((message) => message.content).join("\n");
        const historyUserText = history
          .filter((message) => message.role === "user")
          .map((message) => message.content)
          .join("\n");

        const currentBudget = localParseBudget(userInput);
        const historyBudgets = [...historyUserText.matchAll(/(\d+(?:\.\d+)?)\s*(?:元|块)/g)]
          .map((match) => Number(match[1]));
        const planTotals = [...historyText.matchAll(/"total_price"\s*:\s*(\d+(?:\.\d+)?)/g)]
          .map((match) => Number(match[1]));
        const lastAssistantMessage = [...history]
          .reverse()
          .find((message) => message.role === "assistant");
        const lastAssistantPlanTotals = [
          ...(lastAssistantMessage?.content || "").matchAll(/"total_price"\s*:\s*(\d+(?:\.\d+)?)/g)
        ].map((match) => Number(match[1]));
        const lastRecommendedPlanTotal = lastAssistantPlanTotals[0] ?? planTotals[0] ?? null;
        let budget = currentBudget ?? historyBudgets.at(-1) ?? lastRecommendedPlanTotal ?? null;

        let categories = localDetectCategories(userInput);
        const historyCategories = localDetectCategories(historyText);
        if (!categories.length && historyCategories.length) {
          categories = historyCategories.slice(-1);
        }
        const scene = localDetectScene(userInput) || localDetectScene(historyUserText);
        const wantsCheaper = /(再便宜|便宜一点|更便宜|降低预算|省一点|省钱)/.test(userInput);
        const wantsCategoryChange = /(换个品类|换一种|换个方向|换一个方案|换一份)/.test(userInput);
        if (wantsCheaper && budget) {
          const cheaperBase = lastRecommendedPlanTotal ?? budget;
          budget = Math.max(10, localRound(cheaperBase * 0.75));
        }
        if (wantsCategoryChange && !localDetectCategories(userInput).length && categories.length) {
          const previousCategory = categories.at(-1);
          categories = [LOCAL_CATEGORY_SWAPS[previousCategory] || "商超日用"];
        }

        const wantsBudgetPlanning = /(怎么分配|预算.*(规划|安排|分配)|(家庭|月度|周度|生活|旅行|出游|采购).{0,6}预算|生活费|规划.*(支出|消费)|预算.*怎么用)/.test(userInput);

        if (wantsBudgetPlanning) {
          if (!budget) {
            return {
              answer: "请补充本次预算金额，并说明是家庭、旅行还是日常支出，例如“家庭月度预算6000元怎么分配”。",
              plans: [],
              requires_input: true,
              suggested_replies: ["家庭月度预算6000元", "旅行预算1000元怎么分配", "一周生活费500元怎么安排"],
              used_tools: []
            };
          }
          if (scene && localShouldUseSceneBundle(scene, `${historyUserText} ${userInput}`)) {
            return localBuildSceneResponse(userInput, budget, scene);
          }
          return localBuildBudgetResponse(budget, categories, scene);
        }

        if (scene && budget && localShouldUseSceneBundle(scene, `${historyUserText} ${userInput}`)) {
          return localBuildSceneResponse(userInput, budget, scene);
        }

        if (!budget && !categories.length) {
          return {
            answer: "请补充两个关键信息：一是预算范围，二是想购买的品类或使用场景。例如“预算300元改善租房厨房”或“家庭月度预算6000元怎么分配”。",
            plans: [],
            requires_input: true,
            suggested_replies: ["预算300元改善厨房", "家庭月预算6000元", "1000元周末周边游"],
            used_tools: []
          };
        }

        if (!budget) {
          return {
            answer: `已识别到你想了解“${categories.join("、")}”。请补充预算范围，我会继续筛选并计算优惠。`,
            plans: [],
            requires_input: true,
            suggested_replies: ["预算100元以内", "预算300元左右", "预算1000元以内"],
            used_tools: []
          };
        }

        if (!categories.length) {
          return {
            answer: `已识别预算 ¥${budget.toFixed(2)}。请补充想购买的品类或消费场景，例如餐饮美食、家居生活、数码家电、健康医疗、旅游住宿或本地服务。`,
            plans: [],
            requires_input: true,
            suggested_replies: ["餐饮美食", "家居生活", "旅游住宿"],
            used_tools: []
          };
        }

        const keywords = localExtractKeywords(`${historyUserText} ${userInput}`);
        const response = localBuildShoppingResponse(
          userInput,
          budget,
          categories,
          keywords,
          `${historyUserText} ${userInput}`
        );
        if (wantsCheaper) {
          response.answer = `已按你的要求将预算下调至约 ¥${budget.toFixed(2)}。${response.answer}`;
        }
        if (wantsCategoryChange) {
          response.answer = `已切换到${categories.join("、")}方向。${response.answer}`;
        }
        return response;
      }

      function setExecutionMode(mode) {
        state.executionMode = mode;
        const hint = $("#api-mode-hint");
        if (mode === "local") {
          setApiStatus("online", "本地演示模式 · 无需后端");
          if (hint) hint.textContent = "当前直接使用内嵌生活消费商品、服务与优惠数据，无需启动后端或配置 API Key。";
        } else {
          setApiStatus("online", "后端服务已连接");
          if (hint) hint.textContent = "当前使用 Flask Agent 后端服务。";
        }
      }

      async function initializeExecutionMode() {
        if (IS_FILE_MODE) {
          setExecutionMode("local");
          return;
        }
        const controller = new AbortController();
        const timer = window.setTimeout(() => controller.abort(), 1500);
        try {
          const response = await fetch(`${state.apiBaseUrl}/health`, {
            cache: "no-store",
            signal: controller.signal
          });
          if (!response.ok) {
            setExecutionMode("local");
            return;
          }
          const healthPayload = await response.json();
          const keyConfigured = healthPayload?.config_status?.openai_api_key_configured;
          setExecutionMode(keyConfigured === false ? "local" : "backend");
        } catch (error) {
          setExecutionMode("local");
        } finally {
          window.clearTimeout(timer);
        }
      }
      /** 兼容后端顶层字段与 data 包裹结构，并统一默认值。 */
      function normalizeAgentPayload(payload) {
        const data = payload?.data && typeof payload.data === "object" ? payload.data : payload;
        const answer = data?.answer ?? data?.message ?? payload?.answer;
        if (typeof answer !== "string" || !answer.trim()) {
          throw new Error("后端返回格式不完整，缺少 answer 字段。");
        }
        const plans = Array.isArray(data?.plans)
          ? data.plans
          : (Array.isArray(data?.recommendations) ? data.recommendations : []);
        const suggestions = data?.suggested_replies ?? data?.suggestedReplies ?? data?.suggestions ?? [];
        return {
          answer: answer.trim(),
          plans,
          used_tools: Array.isArray(data?.used_tools) ? data.used_tools : [],
          requires_input: Boolean(data?.requires_input ?? data?.requiresInput),
          suggested_replies: Array.isArray(suggestions) ? suggestions.filter((item) => typeof item === "string").slice(0, 3) : []
        };
      }

      class ApiRequestError extends Error {
        constructor(message, kind = "unknown", status = 0) {
          super(message);
          this.name = "ApiRequestError";
          this.kind = kind;
          this.status = status;
        }
      }

      /**
       * 浏览器出于安全限制不会直接暴露 CORS 错误。
       * 使用 no-cors 请求探测服务器是否可达：
       * - 请求成功但普通请求失败：优先判定为 CORS 配置问题；
       * - 请求失败：判定为后端未启动或连接被拒绝。
       */
      async function detectNetworkFailureKind(baseUrl) {
        const controller = new AbortController();
        const timer = window.setTimeout(() => controller.abort(), 3000);
        try {
          await fetch(`${baseUrl}/health`, {
            mode: "no-cors",
            cache: "no-store",
            signal: controller.signal
          });
          return "cors";
        } catch (error) {
          return "connection";
        } finally {
          window.clearTimeout(timer);
        }
      }

      /** 调用后端 /api/agent/chat，携带最近对话上下文并设置 60 秒超时。 */
      async function requestAgentReply(userInput, history) {
        const controller = new AbortController();
        const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
        const endpoint = `${state.apiBaseUrl}${API_ENDPOINTS.chat}`;
        console.info(`[API] POST ${endpoint}`, {
          userInputLength: userInput.length,
          historyMessages: history.length
        });

        try {
          const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_input: userInput, history }),
            signal: controller.signal
          });

          const rawText = await response.text();
          let payload = null;
          if (rawText) {
            try {
              payload = JSON.parse(rawText);
            } catch (error) {
              payload = null;
            }
          }

          console.info(`[API] ${response.status} ${response.statusText}`, payload ?? rawText);

          if (!response.ok) {
            const backendMessage =
              payload?.answer ||
              payload?.message ||
              payload?.detail ||
              response.statusText ||
              "请求失败";

            console.error("[API] 请求失败", {
              url: endpoint,
              status: response.status,
              statusText: response.statusText,
              response: payload ?? rawText
            });

            if (response.status === 404) {
              throw new ApiRequestError(
                "接口路径不匹配，请检查前后端路由是否一致",
                "http_404",
                404
              );
            }
            if (response.status === 500) {
              throw new ApiRequestError(
                "后端服务内部错误，请查看终端报错信息",
                "http_500",
                response.status
              );
            }
            throw new ApiRequestError(
              backendMessage,
              "http_error",
              response.status
            );
          }

          if (!payload) {
            throw new ApiRequestError(
              "后端返回内容格式异常，请检查终端日志。",
              "invalid_response",
              response.status
            );
          }

          return normalizeAgentPayload(payload);
        } catch (error) {
          let normalizedError = error;

          if (error instanceof TypeError) {
            const failureKind = await detectNetworkFailureKind(state.apiBaseUrl);
            normalizedError = failureKind === "cors"
              ? new ApiRequestError(
                  "跨域配置异常，请检查后端 CORS 设置并重启服务",
                  "cors"
                )
              : new ApiRequestError(
                  "后端服务未启动，请先运行 start.bat",
                  "connection"
                );
          }

          console.error("[API] 请求异常", {
            url: endpoint,
            name: normalizedError.name,
            kind: normalizedError.kind,
            status: normalizedError.status,
            message: normalizedError.message,
            error: normalizedError
          });
          throw normalizedError;
        } finally {
          window.clearTimeout(timeoutId);
        }
      }

      async function handleChatSubmit(event) {
        event.preventDefault();
        if (state.isSending) return;

        const input = $("#chat-input");
        const userInput = input.value.trim();
        if (!userInput) {
          showToast("请先输入消费问题。", "error");
          input.focus();
          return;
        }

        state.isSending = true;
        const historyForRequest = buildApiHistory();
        appendMessage("user", userInput);
        input.value = "";
        input.style.height = "auto";
        setChatLoading(true);

        try {
          let payload;

          if (state.executionMode === "local") {
            payload = localAgentReply(userInput, historyForRequest);
          } else {
            try {
              payload = await requestAgentReply(userInput, historyForRequest);
            } catch (backendError) {
              const canFallback =
                ["connection", "cors", "http_404", "http_500", "invalid_response"].includes(backendError.kind) ||
                Number(backendError.status) >= 500;
              if (!canFallback) throw backendError;

              console.warn("[Agent] 后端不可用，自动切换本地演示模式", backendError);
              setExecutionMode("local");
              payload = localAgentReply(userInput, historyForRequest);
              showToast("后端服务不可用，已自动切换为本地演示模式。", "info");
            }
          }

          appendMessage("assistant", payload.answer, {
            plans: payload.plans,
            usedTools: payload.used_tools,
            requiresInput: payload.requires_input,
            suggestedReplies: payload.suggested_replies
          });
          renderPlans(payload.plans, payload.requires_input);
          renderUsedTools(payload.used_tools);

          if (state.executionMode === "local") {
            setApiStatus(
              "online",
              payload.requires_input
                ? "本地演示模式 · 等待补充信息"
                : "本地演示模式 · 方案已生成"
            );
          } else {
            setApiStatus(
              "online",
              payload.requires_input
                ? "后端已连接 · 等待补充信息"
                : "后端已连接 · 方案已生成"
            );
          }
        } catch (error) {
          let friendlyMessage = "智能体服务暂时不可用，请稍后重试。";

          if (error instanceof ApiRequestError) {
            friendlyMessage = error.message;
          } else if (error.name === "AbortError") {
            friendlyMessage = "请求超时，请确认后端服务已启动后重试。";
          } else if (error.message) {
            friendlyMessage = error.message;
          }

          console.error("[Chat] 请求处理失败", {
            name: error.name,
            kind: error.kind || "unknown",
            status: error.status || 0,
            message: error.message,
            error
          });
          setApiStatus("error", "连接异常");
          appendMessage("assistant", `抱歉，${friendlyMessage}`);
          showToast(friendlyMessage, "error");
        } finally {
          state.isSending = false;
          setChatLoading(false);
          input.focus();
        }
      }

      function initChat() {
        const form = $("#chat-form");
        const input = $("#chat-input");
        const messages = $("#chat-messages");

        form.addEventListener("submit", handleChatSubmit);
        input.addEventListener("keydown", (event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            form.requestSubmit();
          }
        });
        input.addEventListener("input", () => {
          input.style.height = "auto";
          input.style.height = `${Math.min(input.scrollHeight, 128)}px`;
        });
        $$(".prompt-chip").forEach((button) => {
          button.addEventListener("click", () => {
            if (state.isSending) return;
            input.value = button.dataset.prompt || "";
            input.dispatchEvent(new Event("input"));
            form.requestSubmit();
          });
        });
        $$(".scenario-chip").forEach((button) => {
          button.addEventListener("click", () => {
            if (state.isSending) return;
            input.value = button.dataset.scenario || "";
            input.dispatchEvent(new Event("input"));
            input.focus();
            showToast("典型场景问题已填入输入框，可直接发送。", "info");
          });
        });
        messages.addEventListener("click", (event) => {
          const suggestion = event.target.closest("[data-suggested-reply]");
          if (!suggestion || state.isSending) return;
          input.value = suggestion.dataset.suggestedReply || "";
          input.dispatchEvent(new Event("input"));
          form.requestSubmit();
        });
        $("#clear-chat-history").addEventListener("click", clearChatHistory);
        restoreChatHistory();
      }
      /** 返回指定月份或周度的起始日期；周度以周一为第一天。 */
      function getPeriodStart(period, anchorDate = new Date()) {
        let anchor;
        if (anchorDate instanceof Date) {
          anchor = new Date(anchorDate);
        } else {
          anchor = new Date(`${anchorDate}T00:00:00`);
        }
        if (Number.isNaN(anchor.getTime())) anchor = new Date();

        if (period === "weekly") {
          const start = new Date(anchor.getFullYear(), anchor.getMonth(), anchor.getDate());
          const dayOffset = (start.getDay() + 6) % 7;
          start.setDate(start.getDate() - dayOffset);
          return start;
        }
        return new Date(anchor.getFullYear(), anchor.getMonth(), 1);
      }

      /** 返回周期起止日期，结束日期不包含在区间内。 */
      function getPeriodRange(period, anchorDate = new Date()) {
        const start = getPeriodStart(period, anchorDate);
        const end = new Date(start);
        if (period === "weekly") {
          end.setDate(start.getDate() + 7);
        } else {
          end.setMonth(start.getMonth() + 1);
        }
        return { start, end };
      }

      function getPeriodBudgetKey(period, anchorDate = new Date()) {
        return `${period}:${localDateString(getPeriodStart(period, anchorDate))}`;
      }

      function getSelectedBudgetStart() {
        return getPeriodStart(
          state.budgetPeriod,
          state.selectedBudgetDate || new Date()
        );
      }

      function getSelectedBudgetRange() {
        return getPeriodRange(state.budgetPeriod, getSelectedBudgetStart());
      }

      function getBudgetForPeriod(period, anchorDate = new Date()) {
        const key = getPeriodBudgetKey(period, anchorDate);
        const amount = Number(state.budgets.periods?.[key]);
        return Number.isFinite(amount) && amount > 0 ? amount : 0;
      }

      function isCurrentBudgetPeriod() {
        const selectedKey = getPeriodBudgetKey(state.budgetPeriod, getSelectedBudgetStart());
        const currentKey = getPeriodBudgetKey(state.budgetPeriod, new Date());
        return selectedKey === currentKey;
      }

      function formatMonthTitle(date) {
        return `${date.getFullYear()}年${date.getMonth() + 1}月`;
      }

      function formatShortDate(date) {
        return `${date.getMonth() + 1}月${date.getDate()}日`;
      }

      function formatPeriodTitle(period, startDate) {
        if (period === "monthly") return formatMonthTitle(startDate);
        const range = getPeriodRange("weekly", startDate);
        const inclusiveEnd = new Date(range.end);
        inclusiveEnd.setDate(inclusiveEnd.getDate() - 1);
        const endYear = inclusiveEnd.getFullYear() !== startDate.getFullYear()
          ? `${inclusiveEnd.getFullYear()}年`
          : "";
        return `${startDate.getFullYear()}年${formatShortDate(startDate)} - ${endYear}${formatShortDate(inclusiveEnd)}`;
      }

      function formatPeriodRangeLabel(period, startDate) {
        const range = getPeriodRange(period, startDate);
        const inclusiveEnd = new Date(range.end);
        inclusiveEnd.setDate(inclusiveEnd.getDate() - 1);
        if (period === "monthly") {
          return `${startDate.getFullYear()}年${startDate.getMonth() + 1}月1日 - ${inclusiveEnd.getDate()}日`;
        }
        const endYear = inclusiveEnd.getFullYear() !== startDate.getFullYear()
          ? `${inclusiveEnd.getFullYear()}年`
          : "";
        return `${startDate.getFullYear()}年${formatShortDate(startDate)} - ${endYear}${formatShortDate(inclusiveEnd)}`;
      }

      function countExpensesInPeriod(period, startDate) {
        const range = getPeriodRange(period, startDate);
        return filterExpensesByRange(state.expenses, range).length;
      }

      function getAvailablePeriodDates(period) {
        const currentStart = getPeriodStart(period);
        const dates = new Map();
        const addDate = (value) => {
          const date = getPeriodStart(period, value);
          if (date <= currentStart) dates.set(localDateString(date), date);
        };

        const rollingCount = period === "monthly" ? 24 : 26;
        for (let index = 0; index < rollingCount; index += 1) {
          const date = new Date(currentStart);
          if (period === "monthly") {
            date.setMonth(currentStart.getMonth() - index);
          } else {
            date.setDate(currentStart.getDate() - index * 7);
          }
          addDate(date);
        }

        state.expenses.forEach((expense) => addDate(expense.date));
        Object.keys(state.budgets.periods || {})
          .filter((key) => key.startsWith(`${period}:`))
          .forEach((key) => addDate(key.slice(period.length + 1)));
        addDate(getSelectedBudgetStart());

        return [...dates.values()].sort((a, b) => b.getTime() - a.getTime());
      }

      function refreshPeriodSelect(selectSelector = "#budget-period-select") {
        const select = $(selectSelector);
        if (!select) return;
        const selectedStart = getSelectedBudgetStart();
        const currentKey = localDateString(getPeriodStart(state.budgetPeriod));
        const options = getAvailablePeriodDates(state.budgetPeriod).map((date) => {
          const dateKey = localDateString(date);
          const count = countExpensesInPeriod(state.budgetPeriod, date);
          const suffix = [
            dateKey === currentKey ? "当前" : "历史",
            count > 0 ? `${count} 笔` : "无记录"
          ].join(" · ");
          return `<option value="${dateKey}">${escapeHtml(formatPeriodTitle(state.budgetPeriod, date))} · ${suffix}</option>`;
        });
        select.innerHTML = options.join("");
        const selectedValue = localDateString(selectedStart);
        select.value = selectedValue;
        if (select.value !== selectedValue) {
          select.insertAdjacentHTML(
            "afterbegin",
            `<option value="${selectedValue}">${escapeHtml(formatPeriodTitle(state.budgetPeriod, selectedStart))} · 历史</option>`
          );
          select.value = selectedValue;
        }
      }

      function renderActivePeriodPage() {
        if (state.activePage === "review") {
          renderReviewPage();
        } else {
          renderBudgetPage();
        }
      }

      function shiftSelectedBudgetPeriod(offset) {
        const selectedStart = getSelectedBudgetStart();
        const next = new Date(selectedStart);
        if (state.budgetPeriod === "monthly") {
          next.setMonth(next.getMonth() + offset);
        } else {
          next.setDate(next.getDate() + offset * 7);
        }
        const currentStart = getPeriodStart(state.budgetPeriod);
        if (next > currentStart) return;
        state.selectedBudgetDate = localDateString(next);
        syncExpenseDateToPeriod();
        renderActivePeriodPage();
      }

      function setSelectedBudgetPeriod(dateValue) {
        state.selectedBudgetDate = localDateString(getPeriodStart(state.budgetPeriod, dateValue));
        syncExpenseDateToPeriod();
        renderActivePeriodPage();
      }

      function getSuggestedExpenseDate() {
        return isCurrentBudgetPeriod()
          ? localDateString()
          : localDateString(getSelectedBudgetStart());
      }

      function syncExpenseDateToPeriod() {
        const expenseDate = $("#expense-date");
        if (expenseDate) expenseDate.value = getSuggestedExpenseDate();
      }

      function filterExpensesByRange(expenses, range) {
        const startDate = localDateString(range.start);
        const endDate = localDateString(range.end);
        return expenses.filter((expense) => expense.date >= startDate && expense.date < endDate);
      }

      function renderExpenseList(expenses) {
        const container = $("#expense-list");
        if (!expenses.length) {
          container.innerHTML = `
            <div class="flex h-full min-h-[380px] flex-col items-center justify-center text-center">
              <div class="grid h-16 w-16 place-items-center rounded-3xl bg-blue-50 text-blue-500">
                <svg viewBox="0 0 24 24" class="h-8 w-8" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 7.5h15v10.75A1.75 1.75 0 0 1 17.75 20H6.25a1.75 1.75 0 0 1-1.75-1.75V7.5Zm3-3h9M8.25 12h7.5m-7.5 3.5h4.5" /></svg>
              </div>
              <h4 class="mt-4 font-bold text-slate-700">该周期暂无消费记录</h4>
              <p class="mt-2 max-w-xs text-sm leading-6 text-slate-400">可切换其他月份或周度查看历史记录，也可以为当前所选周期添加消费。</p>
            </div>`;
          return;
        }

        container.innerHTML = expenses.map((expense) => {
          const color = CATEGORY_COLORS[expense.category] || CATEGORY_COLORS["其他"];
          return `
            <div class="record-row flex items-center gap-3 rounded-2xl border border-transparent px-3 py-3 hover:border-slate-100">
              <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-sm font-black" style="background:${color}18;color:${color}">
                ${escapeHtml(expense.category.slice(0, 1))}
              </span>
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-bold text-slate-700">${escapeHtml(expense.name)}</p>
                <div class="mt-1 flex items-center gap-2 text-[11px] text-slate-400">
                  <span>${escapeHtml(expense.category)}</span>
                  <span>·</span>
                  <span>${escapeHtml(formatDateLabel(expense.date))}</span>
                </div>
              </div>
              <p class="shrink-0 text-sm font-black text-slate-800">-${formatCurrency(expense.amount)}</p>
              <button type="button" data-delete-expense="${escapeHtml(expense.id)}" class="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-300 transition hover:bg-red-50 hover:text-red-500" aria-label="删除这条消费记录">
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m6 7.5.75 11.25h10.5L18 7.5M9 7.5V5.25h6V7.5M4.5 7.5h15" /></svg>
              </button>
            </div>`;
        }).join("");
      }

      /** 实时计算并刷新所选周期预算、使用率与消费明细。 */
      function renderBudgetPage() {
        const period = state.budgetPeriod;
        const selectedStart = getSelectedBudgetStart();
        const range = getSelectedBudgetRange();
        const budget = getBudgetForPeriod(period, selectedStart);
        const hasBudget = budget > 0;
        const activeExpenses = filterExpensesByRange(state.expenses, range)
          .sort((a, b) => b.date.localeCompare(a.date));
        const spent = activeExpenses.reduce((sum, expense) => sum + expense.amount, 0);
        const remaining = budget - spent;
        const percent = hasBudget ? (spent / budget) * 100 : 0;
        const isOverspent = hasBudget && remaining < 0;
        const isCurrent = isCurrentBudgetPeriod();
        const periodTitle = formatPeriodTitle(period, selectedStart);

        $("#budget-period-title").textContent = periodTitle;
        $("#budget-period-range").textContent = formatPeriodRangeLabel(period, selectedStart);
        const context = $("#budget-period-context");
        context.textContent = isCurrent ? "当前周期" : "历史周期";
        context.className = `rounded-full px-2 py-0.5 text-[10px] font-bold ${isCurrent ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-600"}`;

        $("#budget-card-label").textContent = period === "monthly" ? "所选月份预算" : "所选周预算";
        $("#budget-card-hint").textContent = hasBudget ? "该周期预算已单独保存" : "该周期尚未设置预算";
        $("#budget-editor-hint").textContent = period === "monthly"
          ? "保存后仅更新当前所选月份。"
          : "保存后仅更新当前所选周度。";
        $("#budget-total").textContent = hasBudget ? formatCurrency(budget) : "未设置";
        $("#budget-spent").textContent = formatCurrency(spent);
        $("#budget-record-count").textContent = `${activeExpenses.length} 笔记录`;
        $("#budget-remaining").textContent = hasBudget ? formatCurrency(Math.abs(remaining)) : "—";
        $("#budget-remaining").style.color = isOverspent ? "#dc2626" : "#0f172a";
        $("#budget-status").textContent = !hasBudget
          ? "尚未设置预算"
          : (isOverspent ? `已超出 ${formatCurrency(Math.abs(remaining))}` : (percent >= 80 ? "接近预算上限" : "额度充足"));
        $("#budget-status").style.color = !hasBudget
          ? "#64748b"
          : (isOverspent ? "#dc2626" : (percent >= 80 ? "#d97706" : "#059669"));
        $("#budget-percent").textContent = hasBudget ? `${Math.round(percent)}%` : "—";
        $("#budget-percent").style.color = isOverspent ? "#dc2626" : "#1d4ed8";

        const progress = $("#budget-progress");
        progress.style.width = `${hasBudget ? Math.min(100, Math.max(0, percent)) : 0}%`;
        progress.style.backgroundColor = isOverspent ? "#ef4444" : (percent >= 80 ? "#f59e0b" : "#3b82f6");

        const icon = $("#remaining-icon");
        icon.style.backgroundColor = isOverspent ? "#fef2f2" : "#ecfdf5";
        icon.style.color = isOverspent ? "#dc2626" : "#059669";
        $("#budget-alert").classList.toggle("hidden", !isOverspent);

        $("#records-period-label").textContent = `${periodTitle}消费记录`;
        $("#records-total").textContent = `合计 ${formatCurrency(spent)}`;
        $("#budget-input").value = hasBudget ? budget.toFixed(2) : "";
        $("#previous-period").disabled = false;
        $("#next-period").disabled = isCurrent;
        $("#back-to-current-period").disabled = isCurrent;
        $$(".period-button").forEach((button) => {
          button.classList.toggle("active", button.dataset.period === period);
        });
        refreshPeriodSelect("#budget-period-select");
        renderExpenseList(activeExpenses);
      }

      function initBudgetPage() {
        const budgetInput = $("#budget-input");
        const expenseForm = $("#expense-form");
        const expenseDate = $("#expense-date");
        if (!state.selectedBudgetDate) {
          state.selectedBudgetDate = localDateString(getPeriodStart(state.budgetPeriod));
        }
        expenseDate.value = getSuggestedExpenseDate();

        $$(".period-button").forEach((button) => {
          button.addEventListener("click", () => {
            state.budgetPeriod = button.dataset.period === "weekly" ? "weekly" : "monthly";
            state.selectedBudgetDate = localDateString(getPeriodStart(state.budgetPeriod));
            saveBudgets();
            syncExpenseDateToPeriod();
            renderActivePeriodPage();
          });
        });

        $("#previous-period").addEventListener("click", () => shiftSelectedBudgetPeriod(-1));
        $("#next-period").addEventListener("click", () => shiftSelectedBudgetPeriod(1));
        $("#back-to-current-period").addEventListener("click", () => {
          state.selectedBudgetDate = localDateString(getPeriodStart(state.budgetPeriod));
          syncExpenseDateToPeriod();
          renderActivePeriodPage();
        });
        $("#budget-period-select").addEventListener("change", (event) => {
          setSelectedBudgetPeriod(event.target.value);
        });

        $("#save-budget").addEventListener("click", () => {
          const nextBudget = Number(budgetInput.value);
          if (!Number.isFinite(nextBudget) || nextBudget <= 0) {
            showToast("预算金额必须大于 0。", "error");
            budgetInput.focus();
            return;
          }
          const selectedStart = getSelectedBudgetStart();
          const periodKey = getPeriodBudgetKey(state.budgetPeriod, selectedStart);
          const roundedBudget = Math.round(nextBudget * 100) / 100;
          state.budgets.periods[periodKey] = roundedBudget;
          if (isCurrentBudgetPeriod()) {
            state.budgets[state.budgetPeriod] = roundedBudget;
          }
          saveBudgets();
          renderBudgetPage();
          showToast(`${formatPeriodTitle(state.budgetPeriod, selectedStart)}预算已保存。`, "success");
        });

        expenseForm.addEventListener("submit", (event) => {
          event.preventDefault();
          const name = $("#expense-name").value.trim();
          const amount = Number($("#expense-amount").value);
          const category = $("#expense-category").value;
          const date = expenseDate.value;

          if (!name) {
            showToast("请输入消费名称。", "error");
            return;
          }
          if (!Number.isFinite(amount) || amount <= 0) {
            showToast("消费金额必须大于 0。", "error");
            return;
          }
          if (!date) {
            showToast("请选择消费日期。", "error");
            return;
          }

          state.expenses.push({
            id: generateId(),
            name,
            amount: Math.round(amount * 100) / 100,
            category,
            date
          });
          // 新记录可能属于其他日期，自动切换到对应月份或周度，确保立即可见。
          state.selectedBudgetDate = localDateString(getPeriodStart(state.budgetPeriod, date));
          saveExpenses();
          renderBudgetPage();
          if (state.activePage === "review") renderReviewPage();
          expenseForm.reset();
          expenseDate.value = getSuggestedExpenseDate();
          showToast("消费记录已添加。", "success");
          $("#expense-name").focus();
        });

        $("#expense-list").addEventListener("click", (event) => {
          const deleteButton = event.target.closest("[data-delete-expense]");
          if (!deleteButton) return;
          const expenseId = deleteButton.dataset.deleteExpense;
          const expense = state.expenses.find((item) => item.id === expenseId);
          if (!expense) return;
          if (!window.confirm(`确认删除“${expense.name}”这条记录吗？`)) return;
          state.expenses = state.expenses.filter((item) => item.id !== expenseId);
          saveExpenses();
          renderBudgetPage();
          showToast("消费记录已删除。", "success");
        });

        $("#seed-expenses").addEventListener("click", () => {
          if (state.expenses.length && !window.confirm("将追加一组包含历史周期的演示消费数据，是否继续？")) return;
          state.expenses.push(...buildDemoMonthlyExpenses());
          saveExpenses();
          localStorage.setItem(STORAGE_KEYS.demoSeeded, "true");
          renderBudgetPage();
          showToast("演示消费数据已载入，可切换月份和周度查看。", "success");
        });

        $("#clear-expenses").addEventListener("click", () => {
          if (!state.expenses.length) {
            showToast("当前没有可清空的消费记录。", "info");
            return;
          }
          if (!window.confirm("确认清空全部消费记录吗？该操作不可撤销。")) return;
          state.expenses = [];
          saveExpenses();
          localStorage.setItem(STORAGE_KEYS.demoSeeded, "true");
          renderBudgetPage();
          showToast("全部消费记录已清空。", "success");
        });
      }

      function aggregateByCategory(expenses) {
        const totals = new Map();
        expenses.forEach((expense) => {
          const amount = Number(expense.amount) || 0;
          const category = expense.category || "其他";
          totals.set(category, (totals.get(category) || 0) + amount);
        });
        return [...totals.entries()]
          .map(([category, amount]) => ({ category, amount: Math.round(amount * 100) / 100 }))
          .sort((a, b) => b.amount - a.amount);
      }

      function renderCategoryLegend(categoryData, total) {
        const container = $("#category-legend");
        if (!categoryData.length || total <= 0) {
          container.innerHTML = '<p class="rounded-xl bg-slate-50 px-3 py-4 text-center text-xs leading-5 text-slate-400">所选周期暂无消费记录，添加记录后这里会显示各分类金额与占比。</p>';
          return;
        }

        container.innerHTML = categoryData.map((item) => {
          const percent = total > 0 ? (item.amount / total) * 100 : 0;
          const color = CATEGORY_COLORS[item.category] || CATEGORY_COLORS["其他"];
          return `
            <div class="flex items-center gap-3 rounded-xl px-1 py-1.5">
              <span class="h-2.5 w-2.5 shrink-0 rounded-full" style="background:${color}"></span>
              <span class="min-w-0 flex-1 truncate text-xs font-semibold text-slate-600">${escapeHtml(item.category)}</span>
              <span class="text-xs font-bold text-slate-700">${formatCurrency(item.amount)}</span>
              <span class="w-10 text-right text-[10px] text-slate-400">${percent.toFixed(1)}%</span>
            </div>`;
        }).join("");
      }

      function drawCategoryChart(categoryData) {
        const canvas = $("#category-chart");
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        const width = Math.max(260, Math.round(rect.width || 300));
        const height = Math.max(240, Math.round(rect.height || 290));
        const pixelRatio = Math.min(2, window.devicePixelRatio || 1);
        canvas.width = Math.round(width * pixelRatio);
        canvas.height = Math.round(height * pixelRatio);
        const context = canvas.getContext("2d");
        if (!context) return;
        context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
        context.clearRect(0, 0, width, height);

        const total = categoryData.reduce((sum, item) => sum + Number(item.amount || 0), 0);
        const centerX = width / 2;
        const centerY = height / 2;
        const outerRadius = Math.min(width, height) * 0.38;
        const innerRadius = outerRadius * 0.52;

        if (!categoryData.length || total <= 0) {
          context.beginPath();
          context.arc(centerX, centerY, outerRadius, 0, Math.PI * 2);
          context.fillStyle = "#e2e8f0";
          context.fill();
          context.beginPath();
          context.arc(centerX, centerY, innerRadius, 0, Math.PI * 2);
          context.fillStyle = "#ffffff";
          context.fill();
          context.fillStyle = "#94a3b8";
          context.font = "600 13px sans-serif";
          context.textAlign = "center";
          context.textBaseline = "middle";
          context.fillText("暂无数据", centerX, centerY);
          return;
        }

        let startAngle = -Math.PI / 2;
        categoryData.forEach((item) => {
          const angle = (Number(item.amount) / total) * Math.PI * 2;
          context.beginPath();
          context.moveTo(centerX, centerY);
          context.arc(centerX, centerY, outerRadius, startAngle, startAngle + angle);
          context.closePath();
          context.fillStyle = CATEGORY_COLORS[item.category] || CATEGORY_COLORS["其他"];
          context.fill();
          context.strokeStyle = "rgba(255,255,255,0.92)";
          context.lineWidth = 2;
          context.stroke();
          startAngle += angle;
        });

        context.beginPath();
        context.arc(centerX, centerY, innerRadius, 0, Math.PI * 2);
        context.fillStyle = "#ffffff";
        context.fill();
        context.fillStyle = "#0f172a";
        context.font = "800 20px sans-serif";
        context.textAlign = "center";
        context.textBaseline = "middle";
        context.fillText(formatCurrency(total), centerX, centerY - 7);
        context.fillStyle = "#94a3b8";
        context.font = "600 11px sans-serif";
        context.fillText("所选周期总支出", centerX, centerY + 16);
      }

      /** 根据所选周期的分类结构生成总结与行动建议。 */
      function buildReviewInsights(categoryData, total, budget, periodTitle) {
        const hasBudget = budget > 0;
        if (!total) {
          return {
            advice: [`${periodTitle}暂无消费记录，添加记录后即可自动分析分类占比和预算使用情况。`],
            action: `先记录${periodTitle}的餐饮、商超、交通和本地服务支出，再回来查看消费结构。`,
            topText: "暂无",
            topAmount: "暂无消费",
            budgetStatus: hasBudget ? "暂无支出" : "未设置预算",
            budgetDetail: hasBudget
              ? `${periodTitle}预算 ${formatCurrency(budget)}`
              : `${periodTitle}尚未设置预算`
          };
        }

        const top = categoryData[0];
        const topPercent = (top.amount / total) * 100;
        const budgetPercent = hasBudget ? (total / budget) * 100 : 0;
        const remaining = budget - total;
        const foodTotal = categoryData
          .filter((item) => ["餐饮美食", "零食饮料", "商超日用"].includes(item.category))
          .reduce((sum, item) => sum + item.amount, 0);
        const foodPercent = (foodTotal / total) * 100;
        const advice = [
          `${periodTitle}支出最高的是“${top.category}”，共 ${formatCurrency(top.amount)}，占总支出的 ${topPercent.toFixed(1)}%。`,
          hasBudget
            ? `${periodTitle}预算使用率为 ${budgetPercent.toFixed(1)}%，${remaining >= 0 ? `仍有 ${formatCurrency(remaining)} 额度` : `已超出 ${formatCurrency(Math.abs(remaining))}`}。`
            : `${periodTitle}尚未设置预算，建议先在预算管理中补充该周期预算。`
        ];

        let action = "当前消费结构较均衡，继续保持记录习惯，并为非必要支出设置单次上限。";
        if (!hasBudget) {
          action = `建议先在预算管理中为${periodTitle}设置预算，再结合消费结构制定下一周期调整目标。`;
        } else if (remaining < 0) {
          action = "本周期已经超支，建议暂停娱乐、旅行和非刚需购物，优先保障餐饮、住房与日用品。";
        } else if (top.category === "餐饮美食" && topPercent >= 35) {
          action = "餐饮外食占比较高，建议增加家庭做饭或工作餐团购，并比较外卖满减与配送费。";
        } else if (top.category === "零食饮料" && topPercent >= 20) {
          action = "零食饮料占比较高，建议设置每周上限，优先购买整箱或分享装。";
        } else if (top.category === "文体娱乐" && topPercent >= 25) {
          action = "文体娱乐支出偏高，建议提前设定单次活动预算，优先使用团购、会员和公共文化资源。";
        } else if (foodPercent >= 60) {
          action = "餐饮支出占主体，建议比较家庭做饭、工作餐团购和外卖满减，稳定日常餐饮预算。";
        }

        return {
          advice,
          action,
          topText: top.category,
          topAmount: `${formatCurrency(top.amount)} · ${topPercent.toFixed(1)}%`,
          budgetStatus: !hasBudget
            ? "未设置预算"
            : (remaining >= 0 ? `剩余 ${formatCurrency(remaining)}` : `超支 ${formatCurrency(Math.abs(remaining))}`),
          budgetDetail: !hasBudget
            ? `${periodTitle}尚未设置预算`
            : `${periodTitle}预算 ${formatCurrency(budget)} · 已用 ${budgetPercent.toFixed(1)}%`
        };
      }

      function renderReviewPage() {
        const period = state.budgetPeriod;
        const selectedStart = getSelectedBudgetStart();
        const range = getSelectedBudgetRange();
        const periodExpenses = filterExpensesByRange(state.expenses, range)
          .sort((a, b) => b.date.localeCompare(a.date));
        const total = periodExpenses.reduce((sum, expense) => sum + expense.amount, 0);
        const categoryData = aggregateByCategory(periodExpenses);
        const periodBudget = getBudgetForPeriod(period, selectedStart);
        const hasBudget = periodBudget > 0;
        const periodTitle = formatPeriodTitle(period, selectedStart);
        const isCurrent = isCurrentBudgetPeriod();
        const insights = buildReviewInsights(categoryData, total, periodBudget, periodTitle);
        const periodLabel = period === "monthly" ? "月度" : "周度";

        $("#review-period-title").textContent = periodTitle;
        $("#review-period-range").textContent = formatPeriodRangeLabel(period, selectedStart);
        const context = $("#review-period-context");
        context.textContent = isCurrent ? "当前周期" : "历史周期";
        context.className = `rounded-full px-2 py-0.5 text-[10px] font-bold ${isCurrent ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-600"}`;
        $("#review-period-badge").textContent = isCurrent
          ? (period === "monthly" ? "本月" : "本周")
          : (period === "monthly" ? "历史月份" : "历史周度");
        $("#review-total-label").textContent = period === "monthly" ? "月度总支出" : "周度总支出";
        $("#review-total-detail").textContent = `按 ${formatPeriodRangeLabel(period, selectedStart)} 统计`;
        $("#review-count-detail").textContent = `${periodLabel}有效记录`;
        $("#review-budget-label").textContent = `${periodLabel}预算状态`;
        $("#review-insight-title").textContent = `${periodLabel}总结建议`;
        $("#review-insight-subtitle").textContent = `依据 ${periodTitle} 记录自动生成`;
        $("#review-action-label").textContent = `${periodLabel}行动建议`;
        $("#category-chart").setAttribute("aria-label", `${periodTitle}消费分类饼图`);

        $("#review-total").textContent = formatCurrency(total);
        $("#review-count").textContent = String(periodExpenses.length);
        $("#review-top-category").textContent = insights.topText;
        $("#review-top-amount").textContent = insights.topAmount;
        $("#review-budget-status").textContent = insights.budgetStatus;
        $("#review-budget-status").style.color = !hasBudget
          ? "#64748b"
          : (total > periodBudget ? "#dc2626" : "#059669");
        $("#review-budget-detail").textContent = insights.budgetDetail;
        $("#review-action").textContent = insights.action;

        const adviceContainer = $("#review-advice");
        const adviceItems = [...insights.advice];
        if (periodExpenses.length) {
          adviceItems.push(`${periodTitle}共记录 ${periodExpenses.length} 笔消费，平均每笔约 ${formatCurrency(total / periodExpenses.length)}。`);
        }
        adviceContainer.innerHTML = adviceItems.map((text, index) => `
          <div class="flex gap-3 rounded-2xl border border-slate-100 bg-slate-50/70 p-3.5">
            <span class="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-blue-100 text-[11px] font-black text-blue-700">${index + 1}</span>
            <p class="text-xs leading-6 text-slate-600">${escapeHtml(text)}</p>
          </div>
        `).join("");

        $("#review-previous-period").disabled = false;
        $("#review-next-period").disabled = isCurrent;
        $("#review-back-to-current-period").disabled = isCurrent;
        $$(".period-button").forEach((button) => {
          button.classList.toggle("active", button.dataset.period === period);
        });
        refreshPeriodSelect("#review-period-select");
        renderCategoryLegend(categoryData, total);
        requestAnimationFrame(() => drawCategoryChart(categoryData));
      }

      function initReviewPage() {
        let resizeTimer = null;
        $("#review-previous-period").addEventListener("click", () => shiftSelectedBudgetPeriod(-1));
        $("#review-next-period").addEventListener("click", () => shiftSelectedBudgetPeriod(1));
        $("#review-back-to-current-period").addEventListener("click", () => {
          state.selectedBudgetDate = localDateString(getPeriodStart(state.budgetPeriod));
          syncExpenseDateToPeriod();
          renderReviewPage();
        });
        $("#review-period-select").addEventListener("change", (event) => {
          setSelectedBudgetPeriod(event.target.value);
        });
        window.addEventListener("resize", () => {
          if (state.activePage !== "review") return;
          window.clearTimeout(resizeTimer);
          resizeTimer = window.setTimeout(renderReviewPage, 120);
        });
      }

      /** 初始化全部模块。 */
      function getSharePageUrl() {
        const shareUrl = new URL(window.location.href);
        shareUrl.hash = "";
        return shareUrl.toString();
      }

      async function copyTextToClipboard(textValue) {
        try {
          if (navigator.clipboard && window.isSecureContext) {
            // 某些浏览器会在等待剪贴板授权时长期挂起，超时后自动使用兼容复制方式。
            await Promise.race([
              navigator.clipboard.writeText(textValue),
              new Promise((_, reject) => window.setTimeout(() => reject(new Error("clipboard-timeout")), 1500))
            ]);
            return true;
          }
        } catch (error) {
          console.warn("系统剪贴板写入失败，尝试兼容复制方式", error);
        }

        try {
          const input = document.createElement("textarea");
          input.value = textValue;
          input.setAttribute("readonly", "");
          input.style.position = "fixed";
          input.style.opacity = "0";
          document.body.appendChild(input);
          input.select();
          const copied = document.execCommand("copy");
          input.remove();
          return copied;
        } catch (error) {
          console.warn("兼容复制方式失败", error);
          return false;
        }
      }

      function initShareProject() {
        const button = $("#share-project-button");
        if (!button) return;
        button.addEventListener("click", async () => {
          if (IS_FILE_MODE) {
            showToast("当前是本地文件模式。启动网页服务或完成云端部署后，即可复制网址分享。", "info");
            return;
          }

          const shareUrl = getSharePageUrl();
          const loopbackHosts = ["localhost", "127.0.0.1", "::1"];
          const copied = await copyTextToClipboard(shareUrl);
          if (!copied) {
            window.prompt("请复制以下项目网址进行分享：", shareUrl);
            return;
          }
          if (loopbackHosts.includes(window.location.hostname)) {
            showToast("本机网址已复制。局域网分享需使用电脑 IP，公网分享请完成云端部署。", "info");
          } else {
            showToast("项目网址已复制，可以发送给其他人直接打开。", "success");
          }
        });
      }

      /** 项目介绍弹窗：首次访问自动展示，也可通过导航栏重复打开。 */
      function initProjectIntro() {
        const modal = $("#project-intro-modal");
        const closeButton = $("#project-intro-close");
        const backdrop = $("#project-intro-backdrop");
        let hideTimer = null;

        const openModal = () => {
          window.clearTimeout(hideTimer);
          modal.classList.remove("hidden");
          // 强制触发一次布局，确保透明度过渡在首次打开时生效。
          void modal.offsetWidth;
          modal.classList.add("is-open");
          document.body.classList.add("modal-open");
          window.setTimeout(() => closeButton.focus(), 80);
        };

        const closeModal = () => {
          modal.classList.remove("is-open");
          document.body.classList.remove("modal-open");
          localStorage.setItem(STORAGE_KEYS.projectIntroSeen, "true");
          hideTimer = window.setTimeout(() => modal.classList.add("hidden"), 220);
        };

        $("#project-intro-button").addEventListener("click", openModal);
        closeButton.addEventListener("click", closeModal);
        backdrop.addEventListener("click", closeModal);
        $("#intro-start-demo").addEventListener("click", closeModal);
        $("#intro-view-scenarios").addEventListener("click", () => {
          closeModal();
          showPage("chat");
          window.setTimeout(() => {
            $("#scenario-panel")?.scrollIntoView({ behavior: "smooth", block: "center" });
            $(".scenario-chip")?.focus({ preventScroll: true });
          }, 260);
        });
        document.addEventListener("keydown", (event) => {
          if (event.key === "Escape" && !modal.classList.contains("hidden")) closeModal();
        });

        if (readStorageValue(STORAGE_KEYS.projectIntroSeen, LEGACY_STORAGE_KEYS.projectIntroSeen) !== "true") {
          window.setTimeout(openModal, 900);
        }
      }

      function hidePageLoader() {
        const loader = $("#page-loader");
        if (!loader) return;
        window.setTimeout(() => {
          loader.classList.add("is-hidden");
          window.setTimeout(() => loader.remove(), 360);
        }, 320);
      }

      function initApp() {
        loadPersistedState();
        initApiConfiguration();
        initializeExecutionMode();
        initChat();
        initBudgetPage();
        initReviewPage();
        initShareProject();
        initProjectIntro();
        initNavigation();
        renderBudgetPage();
        if (state.activePage === "review") renderReviewPage();
        hidePageLoader();
      }

      window.addEventListener("unhandledrejection", (event) => {
        console.error("未处理的异步异常", event.reason);
        showToast("页面发生异常，请刷新后重试。", "error");
      });

      initApp();
    })();
  </script>
</body>
</html>
````


## 22. README.md

````markdown
# 全场景生活消费决策智能体

**在线体验：[https://shy194376.github.io/life-wallet-ai/](https://shy194376.github.io/life-wallet-ai/)**

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
````


## 23. 操作启动说明书.md

````markdown
# 全场景生活消费决策智能体 - 操作启动说明书

**适用项目：** 全国人工智能应用创新大赛参赛作品  
**文档版本：** V1.2  
**适用系统：** Windows 10 / Windows 11  
**项目目录：** `C:\Users\S\Desktop\人工智能大赛`  
**在线体验网址：** https://shy194376.github.io/life-wallet-ai/

---

## 一、说明书用途

本说明书用于指导参赛成员、演示人员和评审人员使用项目。

**推荐使用方式：直接双击 `index.html`。**

页面会自动启用本地演示模式，无需安装 Python、无需启动 Flask、无需填写 OpenAI API Key，即可体验智能咨询、商品推荐、优惠计算、预算管理和消费复盘。

Flask + OpenAI 后端仍然完整保留，仅在需要真实大模型 Agent 能力时选择性启动。

本说明书同时说明：

1. 零配置直接打开前端的方法
2. 可选后端模式的安装与启动方法
3. 功能演示流程
4. 常见问题排查方法

---

## 二、运行环境要求

### 直接打开 `index.html`

| 项目 | 要求 |
|---|---|
| 操作系统 | Windows 10 或 Windows 11 |
| 浏览器 | 新版 Chrome 或 Microsoft Edge |
| 网络 | 可访问 Tailwind CSS CDN |
| Python | 不需要 |
| OpenAI API Key | 不需要 |

### 可选：启动完整后端

| 项目 | 要求 |
|---|---|
| Python | Python 3.9 或更高版本 |
| 网络 | 可访问 OpenAI API |
| 密钥 | 有效的 OpenAI API Key |

如需启动后端，安装 Python 时请勾选：

```text
Add Python to PATH
```

如未安装 Python，请访问：

```text
https://www.python.org/downloads/
```

---

## 三、项目文件说明

| 文件或目录 | 用途 |
|---|---|
| `setup.bat` | 首次运行：自动创建虚拟环境并安装依赖 |
| `start.bat` | 日常运行：启动网页服务并显示本机、局域网访问地址 |
| `index.html` | 单页前端，可通过网址访问，也可直接双击打开 |
| `app.py` | Flask 主程序入口，同时托管页面和后端接口 |
| `requirements-deploy.txt` | 云端部署所需的 Gunicorn 依赖 |
| `render.yaml` | Render 公网部署配置 |
| `Dockerfile` | Docker 容器部署配置 |
| `Procfile` | 通用云平台启动配置 |
| `.env.example` | 环境变量模板 |
| `.env` | 用户私有配置，由 `setup.bat` 自动生成 |
| `requirements.txt` | Python 依赖及锁定版本 |
| `README.md` | 项目说明文档 |
| `PROJECT_SOURCE_CODE.md` | 全部交付源码汇总 |
| `data/` | 商品、优惠规则和模拟数据 |
| `services/` | Agent 与业务逻辑 |
| `utils/` | 工具函数和 Function Calling 工具定义 |

---

## 四、启动与使用流程

### 推荐方式：零配置直接使用

直接双击项目根目录中的：

```text
index.html
```

页面右上角状态显示：

```text
本地演示模式 · 无需后端
```

此时无需安装任何软件。内置 Agent 已包含：

- 104 个生活消费商品与服务
- 17 个生活消费分类
- 满减、会员权益与平台优惠规则
- 家庭采购、周末出游、租房改善、健康关怀和通勤出行等组合场景规划
- 模糊需求主动追问
- “再便宜一点”“换个品类”等方案修改
- 预算分配、消费记录和复盘分析

### 推荐方式：通过网址访问与分享

项目已经支持由一个网址同时提供前端页面和后端接口。

#### 同一局域网访问

1. 双击运行 `start.bat`。
2. 本机在浏览器打开：

```text
http://127.0.0.1:5000
```

3. 终端会显示类似下面的局域网地址：

```text
局域网分享：http://192.168.1.100:5000
```

4. 同一 Wi-Fi 或局域网内的其他设备打开该地址即可使用。
5. 如无法访问，请允许 Windows 防火墙放行 Python 或 5000 端口。

#### 分享给互联网用户

1. 将项目上传到 GitHub 仓库。
2. 登录 Render，选择 **New → Blueprint**。
3. 连接项目仓库，Render 会自动读取 `render.yaml`。
4. 配置 `OPENAI_API_KEY`，然后部署。
5. 部署成功后，平台会生成类似下面的 HTTPS 地址：

```text
https://life-wallet-ai.onrender.com
```

6. 将该网址发送给其他人，即可直接在浏览器中进入项目。
7. 页面右上角的“分享网址”按钮可一键复制当前访问地址。

未配置 OpenAI API Key 时，网址页面仍可使用内置本地演示 Agent。

### 可选后端第一步：运行 setup.bat

进入项目根目录，双击：

```text
setup.bat
```

脚本会自动完成：

1. 检测 Python 是否安装
2. 检查 Python 版本是否不低于 3.9
3. 创建 `venv` 虚拟环境
4. 激活虚拟环境
5. 升级 pip
6. 优先使用清华镜像安装 `requirements.txt`
7. 检测 `.env` 是否存在
8. 如不存在，则从 `.env.example` 自动复制
9. 自动打开记事本，提示填写 API Key

安装过程中请保持网络连接，并等待终端显示“环境初始化完成”。

### 可选后端第二步：填写 OpenAI 配置

如果脚本自动打开了记事本，请在 `.env` 中填写：

```dotenv
OPENAI_API_KEY=你的真实OpenAI_API_Key
OPENAI_BASE_URL=https://api.openai.com/v1
```

注意事项：

- 不要保留占位内容 `your_openai_api_key_here`
- 不要在密钥前后添加多余空格
- 不要将 `.env` 上传到公开代码仓库
- 如使用兼容 OpenAI 协议的服务，可修改 `OPENAI_BASE_URL`

填写完成后保存并关闭记事本。

### 可选后端第三步：运行 start.bat

双击：

```text
start.bat
```

启动成功后，终端窗口标题应显示：

```text
全场景生活消费决策智能体 - 网页服务
```

终端中应出现类似内容：

```text
Running on http://127.0.0.1:5000
```

请保持该窗口开启，不要关闭。

### 通过网址打开页面

在浏览器访问：

```text
http://127.0.0.1:5000
```

推荐使用 Microsoft Edge 或 Chrome。网页模式会自动使用当前网站地址作为接口，无需再单独打开 `index.html`。

---

## 五、后端启动验证

浏览器访问：

```text
http://127.0.0.1:5000/health
```

正常情况下应返回：

```json
{
  "status": "ok",
  "msg": "全场景生活消费Agent服务运行中",
  "server_time": "2026-10-26T19:00:00+08:00",
  "config_status": {
    "openai_api_key_configured": true,
    "env_file_loaded": true,
    "cors_enabled": true,
    "cors_origins": "*",
    "supports_credentials": false,
    "debug_mode": false,
    "host": "0.0.0.0",
    "port": 5000
  }
}
```

重点检查：

- `status` 应为 `ok`
- `server_time` 每次重启后应发生变化
- `openai_api_key_configured` 应为 `true`
- `env_file_loaded` 应为 `true`
- `cors_enabled` 应为 `true`

如果 `openai_api_key_configured` 为 `false`，说明 `.env` 未创建或 API Key 未正确填写。

---

## 六、前端功能操作说明

### 1. 项目介绍弹窗

首次打开页面会自动展示项目介绍，包含：

- 项目背景
- 核心痛点
- Agent 能力
- 适用人群

关闭后可通过顶部导航中的“作品介绍”按钮重新打开。

### 2. 智能咨询

在输入框中填写消费需求，例如：

```text
预算1000元，帮我安排一个周末周边游，包含吃住行
```

点击“发送”后，系统会：

1. 调用后端 Agent 接口
2. 自动解析预算、品类和场景
3. 调用商品搜索与优惠计算工具
4. 在右侧生成 2–3 套消费方案

如需求信息不足，Agent 会主动追问预算、品类或使用场景。

用户还可以继续修改方案，例如：

```text
再便宜一点
换个品类
预算降到100元
```

### 3. 典型场景测试

对话区域提供五个生活消费演示快捷场景：

- 一家三口本周生活采购预算500元，帮我分配并推荐商品
- 预算1000元，帮我安排一个周末周边游，包含吃住行
- 租房想用300元改善厨房，推荐实用的小家电和用品
- 给父母买200元以内的健康用品，注重实用
- 每天通勤，预算100元，帮我选交通方案并规划月度支出

点击后会自动填入输入框，不会自动发送，便于演示人员讲解后手动提交。

### 4. 预算管理

进入“预算管理”页面后可进行：

- 在月度与周度之间切换
- 通过上一周期、下一周期或下拉列表查看历史月份和历史周度
- 回看近 24 个月或 26 周；更早的有记录周期会自动加入列表
- 为每个月份或周度单独设置并保存预算
- 查看所选周期的支出、剩余额度、使用率和超支提示
- 新增、删除消费记录
- 清空全部记录或载入包含历史周期的演示数据
- 一键回到当前月份或本周

预算、各周期预算和消费记录保存在浏览器 LocalStorage 中。

### 5. 消费复盘

进入“消费复盘”页面后可查看：

- 与预算管理同步的月度或周度复盘周期
- 当月、本周以及历史月份和历史周度的复盘数据
- 所选周期总支出、消费笔数和最高支出分类
- 所选周期的预算使用状态和剩余额度
- 所选周期的消费分类饼图与分类明细
- 根据所选周期自动生成的总结、消费结构和行动建议
- 一键切换到上一周期、下一周期、当前周期，或通过下拉列表选择历史周期

首次使用时会自动载入一组覆盖当前与历史周期的演示消费数据。

---

## 七、典型比赛演示流程

建议按照以下顺序进行演示：

1. 打开项目介绍弹窗，介绍项目背景、痛点和 Agent 能力。
2. 点击“查看典型场景”，进入智能咨询页面。
3. 选择“预算1000元，帮我安排一个周末周边游，包含吃住行”并发送。
4. 讲解右侧方案卡片中的商品或预算清单、总价和推荐理由。
5. 继续输入“再便宜一点”，展示多轮方案修改能力。
6. 进入预算管理页，展示预算、消费记录和删除功能。
7. 进入消费复盘页，切换当月、本周或历史周期，展示分类饼图、预算状态和周期优化建议。
8. 打开 `/health` 页面，展示后端服务与配置状态。

---

## 八、日常启动与关闭

### 日常启动

如已完成首次初始化，只需：

1. 双击 `start.bat`
2. 等待后端启动
3. 双击 `index.html`

无需再次运行 `setup.bat`。

### 关闭服务

在 `start.bat` 后端窗口中按：

```text
Ctrl + C
```

或直接关闭该终端窗口。

---

## 九、前端接口地址配置

通过网址访问项目时，前端会自动使用当前网站的同源后端地址，例如：

```text
https://life-wallet-ai.onrender.com
```

访问者无需填写 `127.0.0.1:5000`，也不会请求访问者自己电脑上的地址。

只有在直接双击 `index.html` 的本地文件模式下，才需要在“后端接口地址”中填写：

```text
http://127.0.0.1:5000
```

系统会自动将旧版本保存的本机地址迁移到新的同源接口地址。

---

## 十、常见问题排查

### 问题 1：提示“后端服务未启动，请先运行 start.bat”

可能原因：

- 未运行 `start.bat`
- 后端窗口已关闭
- Flask 启动失败
- 5000 端口被占用

解决方法：

1. 双击运行 `start.bat`
2. 保持后端窗口开启
3. 访问 `http://127.0.0.1:5000/health`
4. 查看后端窗口中的完整报错信息

### 问题 2：提示“跨域配置异常，请检查后端 CORS 设置并重启服务”

解决方法：

1. 关闭后端窗口
2. 重新运行 `start.bat`
3. 浏览器按 `Ctrl + F5` 强制刷新
4. 确认使用的是项目提供的 `app.py`
5. 确认已安装 `flask-cors==4.0.0`

### 问题 3：提示“接口路径不匹配，请检查前后端路由是否一致”

可能原因：

- 前端请求路径不是 `/api/agent/chat`
- 后端不是最新版本
- 使用了错误的代理配置

解决方法：

1. 确认 `app.py` 同时包含：

```python
@flask_app.post("/api/agent/chat")
@flask_app.post("/api/chat")
def chat_with_agent():
    ...
```

2. 重启后端
3. 强制刷新浏览器

### 问题 4：提示“后端服务内部错误，请查看终端报错信息”

可能原因：

- OpenAI API Key 无效
- `OPENAI_BASE_URL` 配置错误
- 网络无法访问 OpenAI
- OpenAI 账户无模型权限
- Python 依赖损坏

解决方法：

1. 查看 `start.bat` 窗口中的完整堆栈
2. 检查 `.env` 文件
3. 访问 `/health` 检查 Key 配置状态
4. 确认账户可访问 `gpt-3.5-turbo-1106`
5. 重新运行 `setup.bat`

### 问题 5：Python 未检测到

重新安装 Python 3.9 或更高版本，安装时勾选：

```text
Add Python to PATH
```

### 问题 6：依赖安装失败

`setup.bat` 会优先使用清华镜像，失败时会尝试默认源。

如仍失败，请检查：

- 网络连接
- 代理设置
- 防火墙
- Python 是否为完整安装

### 问题 7：页面样式未加载

前端通过 Tailwind CSS CDN 加载样式，请确认网络可以访问：

```text
https://cdn.tailwindcss.com
```

---

## 十一、演示数据重置

如需重新展示首次弹窗和默认月度消费数据，可在浏览器开发者工具控制台执行：

```javascript
localStorage.removeItem("life-agent-project-intro-seen");
localStorage.removeItem("life-agent-demo-seeded");
localStorage.removeItem("life-agent-expenses");
localStorage.removeItem("life-agent-chat-history");
location.reload();
```

注意：

- 以上操作会清除本地对话、预算演示数据和消费记录
- 不会删除后端代码或 API 配置

---

## 十二、安全与部署说明

- `.env` 包含真实 API Key，严禁上传或公开分享
- `.gitignore` 已排除 `.env`、虚拟环境和本地运行产物
- 本项目已提供 `render.yaml`、`Dockerfile` 和 `Procfile` 用于云端部署
- 正式部署使用 Gunicorn，并自动读取平台注入的 `PORT`
- 页面和 API 使用同源地址，避免部署后误请求访问者本机
- 项目中的商品、服务、价格、优惠和消费记录均为模拟数据

---

## 十三、接口地址汇总

| 方法 | 地址 | 说明 |
|---|---|---|
| GET | `http://127.0.0.1:5000/` | 完整网页页面 |
| GET | `http://127.0.0.1:5000/health` | 健康检查、访问地址与配置状态 |
| GET | `http://127.0.0.1:5000/api/merchants` | 生活消费商户筛选 |
| POST | `http://127.0.0.1:5000/api/recommendations` | 基础预算推荐 |
| POST | `http://127.0.0.1:5000/api/chat` | Agent 对话接口别名 |
| POST | `http://127.0.0.1:5000/api/agent/chat` | Agent 对话主接口 |

---

## 十四、快速启动清单

- [ ] 已安装 Python 3.9+
- [ ] 已双击运行 `setup.bat`
- [ ] 已在 `.env` 中填写真实 `OPENAI_API_KEY`
- [ ] 已双击运行 `start.bat`
- [ ] `/health` 返回 HTTP 200
- [ ] 已打开 `http://127.0.0.1:5000`
- [ ] 页面显示本地演示或后端已连接状态
- [ ] 已完成一次典型场景测试
- [ ] 局域网分享时已获取终端显示的局域网地址
- [ ] 公网分享时已完成 Render 或 Docker 部署并获得 HTTPS 网址

完成以上步骤后，项目即可进入比赛演示状态。
````


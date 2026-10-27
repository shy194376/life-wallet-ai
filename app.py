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
    # 监听 0.0.0.0 便于本机、局域网和容器环境访问；生产环境关闭 debug。
    app.run(host="0.0.0.0", port=server_port, debug=False)
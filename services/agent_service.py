"""全场景生活消费决策智能体核心服务。

Agent 决策流程：
1. 需求理解：模型从自然语言中提取品类、预算、场景、人数和偏好；
2. 工具规划：模型根据需求选择 search_products、calculate_discount
   或 budget_allocation；
3. 自主调用：本模块解析模型返回的 tool_calls，执行对应工具，并把结构化
   结果写回对话；
4. 多轮推理：模型可以基于工具结果继续调用其他工具，最多循环 4 轮；
5. 方案输出：模型输出包含 answer 和 plans 的 JSON，本模块校验并补充
   used_tools，最终返回给 Flask 接口。

默认通过 DeepSeek 的 OpenAI 兼容接口调用，使用 tools/Function Calling：
client.chat.completions.create(
    model="deepseek-flash",
    temperature=0.45,
    tools=AGENT_TOOL_DEFINITIONS,
    tool_choice="auto",
    extra_body={"thinking": {"type": "disabled"}},
    ...
)
"""

import copy
import json
import logging
import re
import threading
import time
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from utils.agent_tools import AGENT_TOOL_DEFINITIONS, execute_agent_tool
from utils.env_utils import (
    get_bool_env,
    get_deepseek_api_key,
    get_env,
    get_openai_api_key,
)

# 默认使用 DeepSeek；可通过 LLM_PROVIDER 切换回 OpenAI 兼容服务。
logger = logging.getLogger(__name__)

DEFAULT_LLM_PROVIDER = "deepseek"
DEFAULT_DEEPSEEK_MODEL = "deepseek-flash"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo-1106"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = DEFAULT_OPENAI_MODEL
TEMPERATURE = 0.45
MAX_TOOL_ROUNDS = 4
OPENAI_REQUEST_TIMEOUT_SECONDS = 20.0
OPENAI_MAX_RETRIES = 1
AGENT_DEADLINE_SECONDS = 50.0
DEEPSEEK_CONNECT_TIMEOUT_SECONDS = 12.0
DEFAULT_DEEPSEEK_HEARTBEAT_SECONDS = 30.0
DEFAULT_DEEPSEEK_RECONNECT_SECONDS = 5.0
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

【多问题处理（强要求）】
1. 先识别本轮输入中的每一个独立问题，包括问号、编号、分号、换行以及“另外”“还有”“同时”等连接词引出的问题。
2. 用户一次提出多个问题时，必须全部回答，不能只回答第一个或最后一个；answer 使用“1.”“2.”等编号逐一回应，并明确每个问题对应的结论。
3. plans 应覆盖各个可执行问题，最多返回 3 个方案；方案 name 以“问题1 ·”“问题2 ·”开头，便于区分。问题多于 3 个时，其余问题在 answer 中用简洁文字回答。
4. 不同问题不得复用同一方案或同一核心商品凑数；若确实适合相同选择，也要说明共用原因。
5. 多问题中某个问题信息不足，只针对该问题追问或给出带假设的建议，不得阻塞其他已能回答的问题。

【追问与响应原则】
1. 只有整个请求既没有明确消费目标，也无法判断消费场景时才追问。
2. 追问要简短，最多提出 2 个最关键问题；用户已提供预算或品类时不要重复索要。
3. 如果用户只缺少预算但已有明确品类/场景，先按该品类的常见预算给出 1-2 个示例方案，明确写出价格假设，不要停下来只问预算。
4. 如果用户只缺少品类但已有预算，先给出预算分配框架和可选方向，再邀请细化。
5. 历史对话中已经出现的信息不要重复询问。
6. 涉及医疗、用药、投资理财等专业风险时，只提供一般消费信息和预算建议，不作诊断、处方或收益承诺。

【工具与方案】
1. 购买实物商品：调用 search_products；跨多个品类时，按品类分别检索。
2. 本地服务、旅行或体验类消费：优先检索可用的商品/服务券，并结合 budget_allocation 拆分交通、住宿、餐饮、门票等预算。
3. 周预算、月预算、家庭预算、旅行预算或生活支出规划：调用 budget_allocation。
4. 已选出商品或服务后：调用 calculate_discount 计算平台优惠、会员权益、到手价和凑单空间。
5. 综合场景要覆盖用户真正关心的核心环节，不要只返回一件商品；预算规划类方案可以用“交通预算”“住宿预算”等预算项作为 plans.items。
6. 不得编造商品、价格、优惠、库存或商家规则；本地数据不足时明确说明可提供通用决策框架。
7. 优先给出 2 个差异化方案，数据不足时可给 1 个；total_price 必须与 items 的价格逻辑一致，且不得超出用户预算。
8. 方案名称、描述和推荐理由必须结合本轮场景与用户偏好，不要每次套用同一组固定标题和话术。
9. 信息充分时直接给结论，不要为了追问而中断回答；信息不足时采用“先给可用方案，再说明假设”的方式。

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


def _looks_like_placeholder_secret(value: str) -> bool:
    """识别示例密钥，避免把 .env 占位内容当成真实配置。"""

    normalized = (value or "").strip().lower()
    return not normalized or any(
        marker in normalized
        for marker in ("your_", "replace_", "example", "placeholder", "<your")
    )


def _get_llm_config(require_api_key: bool = True) -> Dict[str, Any]:
    """读取当前大模型提供方配置。

    默认使用 DeepSeek。DEEPSEEK_API_KEY 只从环境变量读取，
    不会写入日志或返回给前端。
    """

    provider = get_env("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).strip().lower()
    if provider not in {"deepseek", "openai"}:
        raise AgentServiceError(
            "LLM_PROVIDER 仅支持 deepseek 或 openai，请检查 .env 配置。",
            status_code=503,
        )

    if provider == "deepseek":
        try:
            api_key = get_deepseek_api_key() if require_api_key else ""
            if require_api_key and _looks_like_placeholder_secret(api_key):
                raise RuntimeError("DEEPSEEK_API_KEY 仍是占位内容")
        except RuntimeError as error:
            raise AgentServiceError(
                "智能体服务尚未配置有效的 DEEPSEEK_API_KEY，请在 .env 中填写 DeepSeek API Key 后重启服务。",
                status_code=503,
            ) from error
        return {
            "provider": "deepseek",
            "api_key": api_key,
            "base_url": get_env(
                "DEEPSEEK_BASE_URL",
                DEFAULT_DEEPSEEK_BASE_URL,
            ).rstrip("/"),
            "model": get_env("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL),
            # DeepSeek 默认可能启用思考模式；智能咨询优先低延迟，因此显式关闭。
            "extra_body": {"thinking": {"type": "disabled"}},
        }

    try:
        api_key = get_openai_api_key() if require_api_key else ""
        if require_api_key and _looks_like_placeholder_secret(api_key):
            raise RuntimeError("OPENAI_API_KEY 仍是占位内容")
    except RuntimeError as error:
        raise AgentServiceError(
            "智能体服务尚未配置有效的 OPENAI_API_KEY，请在 .env 中填写密钥后重启服务。",
            status_code=503,
        ) from error
    return {
        "provider": "openai",
        "api_key": api_key,
        "base_url": get_env(
            "OPENAI_BASE_URL",
            DEFAULT_OPENAI_BASE_URL,
        ).rstrip("/"),
        "model": get_env("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
        "extra_body": None,
    }


def get_llm_runtime_status() -> Dict[str, Any]:
    """返回可安全展示到健康检查中的大模型运行状态。

    该函数只返回提供方、模型名、接口地址和密钥是否就绪，绝不返回密钥内容。
    deepseek_resident 为 True 表示当前确实由 DeepSeek 提供智能咨询服务。
    """

    provider = get_env("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).strip().lower()
    provider_supported = provider in {"deepseek", "openai"}

    if provider == "deepseek":
        api_key_name = "DEEPSEEK_API_KEY"
        fallback_model = get_env("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL)
        fallback_base_url = get_env(
            "DEEPSEEK_BASE_URL",
            DEFAULT_DEEPSEEK_BASE_URL,
        ).rstrip("/")
    elif provider == "openai":
        api_key_name = "OPENAI_API_KEY"
        fallback_model = get_env("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        fallback_base_url = get_env(
            "OPENAI_BASE_URL",
            DEFAULT_OPENAI_BASE_URL,
        ).rstrip("/")
    else:
        api_key_name = ""
        fallback_model = ""
        fallback_base_url = ""

    ready = False
    error_message = ""
    try:
        llm_config = _get_llm_config(require_api_key=True)
        ready = bool(llm_config.get("api_key"))
        model = str(llm_config.get("model") or fallback_model)
        base_url = str(llm_config.get("base_url") or fallback_base_url)
    except AgentServiceError as error:
        model = fallback_model
        base_url = fallback_base_url
        error_message = error.user_message

    if not provider_supported:
        error_message = "LLM_PROVIDER 仅支持 deepseek 或 openai，请检查服务端配置。"
        ready = False
    elif not ready and not error_message:
        error_message = "大模型 API Key 尚未配置。"

    connection_status = get_deepseek_connection_status()
    deepseek_connected = (
        provider == "deepseek"
        and ready
        and bool(connection_status.get("connected"))
    )
    connection_error = (
        str(connection_status.get("last_error") or "")
        if provider == "deepseek" and ready and not deepseek_connected
        else ""
    )

    return {
        "provider": provider,
        "provider_supported": provider_supported,
        "model": model,
        "base_url": base_url,
        "api_key_name": api_key_name,
        "api_key_configured": ready,
        "ready": ready,
        "deepseek_connected": deepseek_connected,
        "deepseek_connecting": bool(
            connection_status.get("checking")
            or (ready and not connection_status.get("last_check_at"))
        ),
        "deepseek_last_check_at": connection_status.get("last_check_at"),
        "deepseek_last_success_at": connection_status.get("last_success_at"),
        "deepseek_last_error": connection_status.get("last_error") or "",
        "deepseek_resident": deepseek_connected,
        "error": error_message if not ready else connection_error,
    }


def _get_provider_tool_definitions(provider: str) -> List[Dict[str, Any]]:
    """按提供方生成工具定义；DeepSeek 使用严格 JSON Schema 模式。"""

    tool_definitions = copy.deepcopy(AGENT_TOOL_DEFINITIONS)
    if provider == "deepseek":
        for tool_definition in tool_definitions:
            function_definition = tool_definition.get("function")
            if isinstance(function_definition, dict):
                function_definition["strict"] = True
    return tool_definitions


@lru_cache(maxsize=1)
def _create_llm_client() -> Tuple[Any, Dict[str, Any]]:
    """延迟创建模型客户端并返回提供方配置。"""

    try:
        from openai import OpenAI
    except ImportError as error:
        raise AgentServiceError(
            "智能体依赖尚未安装，请先执行 pip install -r requirements.txt。",
            status_code=503,
        ) from error

    llm_config = _get_llm_config(require_api_key=True)
    client = OpenAI(
        api_key=llm_config["api_key"],
        base_url=llm_config["base_url"],
        timeout=OPENAI_REQUEST_TIMEOUT_SECONDS,
        max_retries=OPENAI_MAX_RETRIES,
    )
    return client, llm_config


_CONNECTION_STATUS_LOCK = threading.Lock()
_CONNECTION_MONITOR_THREAD: Optional[threading.Thread] = None
_CONNECTION_STOP_EVENT = threading.Event()
_DEEPSEEK_CONNECTION_STATUS: Dict[str, Any] = {
    "connected": False,
    "checking": False,
    "last_check_at": None,
    "last_success_at": None,
    "last_error": "",
}


def _positive_float_env(variable_name: str, default: float) -> float:
    """读取正浮点环境变量，非法值回退到默认值。"""

    try:
        value = float(get_env(variable_name, str(default)))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _deepseek_heartbeat_seconds() -> float:
    return _positive_float_env(
        "DEEPSEEK_HEARTBEAT_SECONDS",
        DEFAULT_DEEPSEEK_HEARTBEAT_SECONDS,
    )


def _deepseek_reconnect_seconds() -> float:
    return _positive_float_env(
        "DEEPSEEK_RECONNECT_SECONDS",
        DEFAULT_DEEPSEEK_RECONNECT_SECONDS,
    )


def _get_connection_snapshot() -> Dict[str, Any]:
    with _CONNECTION_STATUS_LOCK:
        return dict(_DEEPSEEK_CONNECTION_STATUS)


def _update_connection_status(**changes: Any) -> None:
    with _CONNECTION_STATUS_LOCK:
        _DEEPSEEK_CONNECTION_STATUS.update(changes)


def _format_connection_error(error: Exception) -> str:
    """生成不含 API Key 的连接错误摘要。"""

    if isinstance(error, AgentServiceError):
        message = error.user_message
    else:
        message = f"{type(error).__name__}: {error}"
    return re.sub(r"sk-[A-Za-z0-9_-]+", "sk-***", message)[:300]


def get_deepseek_connection_status() -> Dict[str, Any]:
    """返回 DeepSeek 常驻连接状态，并识别心跳过期。"""

    status = _get_connection_snapshot()
    status["enabled"] = get_bool_env("DEEPSEEK_KEEPALIVE_ENABLED", True)
    status["heartbeat_seconds"] = _deepseek_heartbeat_seconds()
    status["reconnect_seconds"] = _deepseek_reconnect_seconds()

    last_success_at = status.get("last_success_at")
    if (
        status.get("connected")
        and isinstance(last_success_at, (int, float))
        and time.time() - float(last_success_at) > status["heartbeat_seconds"] * 3
    ):
        status["connected"] = False
        status["last_error"] = "DeepSeek 心跳超时，正在自动重连。"
    return status


def _deepseek_connection_monitor_loop() -> None:
    """持续探测 DeepSeek，保持连接池活跃并在断线后自动恢复。"""

    attempt = 0
    while not _CONNECTION_STOP_EVENT.is_set():
        previous_status = _get_connection_snapshot()
        _update_connection_status(checking=True, last_check_at=time.time())
        try:
            client, llm_config = _create_llm_client()
            if llm_config.get("provider") != "deepseek":
                raise AgentServiceError(
                    "DeepSeek 常驻连接要求 LLM_PROVIDER=deepseek。",
                    status_code=503,
                )
            client.models.list(timeout=DEEPSEEK_CONNECT_TIMEOUT_SECONDS)
            now = time.time()
            _update_connection_status(
                connected=True,
                checking=False,
                last_success_at=now,
                last_error="",
            )
            if not previous_status.get("connected"):
                logger.info(
                    "DeepSeek 自动连接成功：model=%s，心跳间隔=%.0f 秒",
                    llm_config.get("model"),
                    _deepseek_heartbeat_seconds(),
                )
            else:
                logger.debug("DeepSeek 心跳正常")
            attempt = 0
            delay = _deepseek_heartbeat_seconds()
        except Exception as error:
            message = _format_connection_error(error)
            _update_connection_status(
                connected=False,
                checking=False,
                last_error=message,
            )
            attempt += 1
            backoff = _deepseek_reconnect_seconds() * min(2 ** min(attempt - 1, 4), 8)
            delay = min(_deepseek_heartbeat_seconds(), backoff)
            logger.warning("DeepSeek 自动连接失败，%.0f 秒后重试：%s", delay, message)

        _CONNECTION_STOP_EVENT.wait(delay)


def start_deepseek_connection_monitor() -> bool:
    """启动唯一的 DeepSeek 后台连接保活线程。"""

    global _CONNECTION_MONITOR_THREAD

    if not get_bool_env("DEEPSEEK_KEEPALIVE_ENABLED", True):
        _update_connection_status(
            connected=False,
            checking=False,
            last_error="DeepSeek 后台保活已通过配置关闭。",
        )
        return False

    provider = get_env("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).strip().lower()
    if provider != "deepseek":
        _update_connection_status(
            connected=False,
            checking=False,
            last_error="当前 LLM_PROVIDER 不是 deepseek。",
        )
        return False

    with _CONNECTION_STATUS_LOCK:
        if (
            _CONNECTION_MONITOR_THREAD
            and _CONNECTION_MONITOR_THREAD.is_alive()
        ):
            return True

        _CONNECTION_STOP_EVENT.clear()
        _DEEPSEEK_CONNECTION_STATUS.update(
            checking=True,
            last_error="",
        )
        _CONNECTION_MONITOR_THREAD = threading.Thread(
            target=_deepseek_connection_monitor_loop,
            name="deepseek-keepalive",
            daemon=True,
        )
        _CONNECTION_MONITOR_THREAD.start()
        return True


def _create_openai_client() -> Any:
    """兼容旧调用方式，返回当前提供方的 OpenAI 兼容客户端。"""

    client, _ = _create_llm_client()
    return client


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
    model: str,
    extra_body: Optional[Dict[str, Any]] = None,
    timeout_seconds: Optional[float] = None,
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
                    "必须完整保留原回复中的全部问题及逐条回答，不能合并或删减。"
                    "顶层只能包含 answer、plans、requires_input、suggested_replies 四个字段，不要输出解释或代码围栏。"
                ),
            },
        ]
    )

    request_options: Dict[str, Any] = {
        "model": model,
        "temperature": TEMPERATURE,
        "messages": repair_messages,
        "response_format": {"type": "json_object"},
        "max_tokens": 1600,
    }
    if extra_body:
        request_options["extra_body"] = extra_body
    if timeout_seconds is not None:
        request_options["timeout"] = max(1.0, timeout_seconds)
    completion = client.chat.completions.create(**request_options)
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
    model: str,
    tool_definitions: List[Dict[str, Any]],
    extra_body: Optional[Dict[str, Any]] = None,
    started_at: Optional[float] = None,
) -> Dict[str, Any]:
    """执行 Agent 的多轮模型推理与工具调用循环。"""

    loop_started_at = started_at if started_at is not None else time.monotonic()
    for _ in range(MAX_TOOL_ROUNDS):
        elapsed_seconds = time.monotonic() - loop_started_at
        if elapsed_seconds >= AGENT_DEADLINE_SECONDS:
            raise AgentServiceError(
                "本次分析耗时较长，已停止继续扩展工具调用。请缩小问题范围或稍后重试。",
                status_code=503,
                used_tools=used_tools,
            )
        remaining_seconds = min(
            OPENAI_REQUEST_TIMEOUT_SECONDS,
            max(1.0, AGENT_DEADLINE_SECONDS - elapsed_seconds),
        )

        request_options: Dict[str, Any] = {
            "model": model,
            "temperature": TEMPERATURE,
            "messages": messages,
            "tools": tool_definitions,
            "tool_choice": "auto",
            "max_tokens": 1600,
            "timeout": remaining_seconds,
        }
        if extra_body:
            request_options["extra_body"] = extra_body
        completion = client.chat.completions.create(**request_options)

        if not completion.choices:
            raise AgentServiceError("智能体服务未返回有效结果，请稍后重试。")

        assistant_message = completion.choices[0].message
        tool_calls = assistant_message.tool_calls

        # 没有工具调用，说明模型已经准备生成最终方案。
        if not tool_calls:
            raw_content = assistant_message.content or ""
            parsed_result = _extract_json_object(raw_content)
            if parsed_result is None:
                repair_timeout = min(
                    OPENAI_REQUEST_TIMEOUT_SECONDS,
                    max(1.0, AGENT_DEADLINE_SECONDS - (time.monotonic() - loop_started_at)),
                )
                parsed_result = _request_structured_repair(
                    client=client,
                    messages=messages,
                    raw_content=raw_content,
                    model=model,
                    extra_body=extra_body,
                    timeout_seconds=repair_timeout,
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
        client: 可选的 OpenAI 兼容客户端。生产环境传 None，测试时可注入模拟客户端。

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
        if client is None:
            llm_client, llm_config = _create_llm_client()
        else:
            llm_client = client
            llm_config = _get_llm_config(require_api_key=False)

        normalized_history = _normalize_history(history)
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *normalized_history,
            {"role": "user", "content": normalized_input},
        ]
        return _run_tool_loop(
            client=llm_client,
            messages=messages,
            used_tools=used_tools,
            model=llm_config["model"],
            tool_definitions=_get_provider_tool_definitions(llm_config["provider"]),
            extra_body=llm_config.get("extra_body"),
            started_at=time.monotonic(),
        )
    except AgentServiceError:
        raise
    except Exception as error:
        # 完整异常只写入服务端日志，不向接口调用方泄露密钥或堆栈。
        logger.exception("DeepSeek 智能体请求异常")
        raise AgentServiceError(
            "抱歉，智能体服务暂时不可用，请稍后重试或检查 DeepSeek/OpenAI API 配置。",
            status_code=503,
            used_tools=used_tools,
        ) from error

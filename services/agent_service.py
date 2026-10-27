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
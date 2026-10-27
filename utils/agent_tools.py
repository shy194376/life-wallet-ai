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
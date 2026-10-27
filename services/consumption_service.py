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
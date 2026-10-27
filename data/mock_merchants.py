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

该文件仅用于基础功能体验，不包含真实用户或商户隐私数据。
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

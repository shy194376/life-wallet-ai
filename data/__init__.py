"""模拟数据包。

集中导出全生活消费场景的商户样例数据，便于业务层进行本地开发和接口联调。
真实项目中可将该层替换为数据库访问代码，同时保持服务层接口不变。
"""

from .mock_merchants import CAMPUS_MERCHANTS, LIFE_MERCHANTS

__all__ = ["CAMPUS_MERCHANTS", "LIFE_MERCHANTS"]
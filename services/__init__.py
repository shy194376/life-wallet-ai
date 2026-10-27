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
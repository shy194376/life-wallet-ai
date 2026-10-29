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


def get_deepseek_api_key() -> str:
    """安全获取 DeepSeek API 密钥。"""

    return get_env("DEEPSEEK_API_KEY", required=True)

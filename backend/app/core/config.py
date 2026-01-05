"""应用配置模块。"""

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AppConfig:
    """应用运行配置。

    Attributes:
        app_name: 应用名称。
        api_prefix: API 路由前缀。
        cors_origins: 允许的跨域来源列表。
    """

    app_name: str = "Argus 校园网钓鱼邮件智能过滤系统"
    api_prefix: str = "/api"
    cors_origins: List[str] = field(
        default_factory=lambda: [
            "http://localhost:10002",
            "http://127.0.0.1:10002",
        ]
    )

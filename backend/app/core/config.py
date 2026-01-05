"""应用配置模块。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from app.utils.environment import EnvReader


def _default_log_dir() -> Path:
    """获取默认日志目录。

    Returns:
        默认日志目录路径。
    """
    return Path(__file__).resolve().parents[3] / "logs"


@dataclass(frozen=True)
class AppConfig:
    """应用运行配置。

    Attributes:
        app_name: 应用名称。
        api_prefix: API 路由前缀。
        cors_origins: 允许的跨域来源列表。
        host: 服务监听地址。
        port: 服务监听端口。
        reload: 是否自动重载。
        log_level: 日志等级。
        log_dir: 日志目录。
        log_max_lines: 单个日志文件最大行数。
        database_url: 数据库连接字符串，仅从环境读取。
        api_key: API 密钥，仅从环境读取。
    """

    app_name: str = "Argus 校园网钓鱼邮件智能过滤系统"
    api_prefix: str = "/api"
    cors_origins: List[str] = field(
        default_factory=lambda: [
            "http://localhost:10002",
            "http://127.0.0.1:10002",
        ]
    )
    host: str = "0.0.0.0"
    port: int = 10003
    reload: bool = False
    log_level: str = "INFO"
    log_dir: Path = field(default_factory=_default_log_dir)
    log_max_lines: int = 1000
    database_url: str | None = None
    api_key: str | None = None


class AppConfigLoader:
    """应用配置加载器。"""

    def __init__(self, env_path: Path | None = None) -> None:
        """初始化配置加载器。

        Args:
            env_path: .env 文件路径。
        """
        self._env_path = env_path or self._default_env_path()
        self._env_reader = EnvReader()

    def load(self) -> AppConfig:
        """加载配置。

        Returns:
            应用配置。
        """
        log_dir = self._resolve_log_dir()

        return AppConfig(
            host=self._env_reader.get_str("HOST", "0.0.0.0"),
            port=self._env_reader.get_int("PORT", 10003),
            reload=self._env_reader.get_bool("RELOAD", False),
            log_level=self._env_reader.get_str("LOG_LEVEL", "INFO"),
            log_dir=log_dir,
            log_max_lines=self._env_reader.get_int("LOG_MAX_LINES", 1000),
            database_url=self._env_reader.get_str("DATABASE_URL"),
            api_key=self._env_reader.get_str("API_KEY"),
        )

    def _resolve_log_dir(self) -> Path:
        """解析日志目录。

        Returns:
            日志目录路径。
        """
        env_value = self._env_reader.get_str("LOG_DIR")
        if env_value:
            return Path(env_value)

        backend_root = self._env_path.parent
        return backend_root.parent / "logs"

    def _default_env_path(self) -> Path:
        """获取默认 .env 路径。

        Returns:
            .env 文件路径。
        """
        return Path(__file__).resolve().parents[2] / ".env"

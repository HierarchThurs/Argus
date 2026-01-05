"""环境变量读取工具。"""

from __future__ import annotations

import os


class EnvReader:
    """环境变量读取器。"""

    def get_str(self, key: str, default: str | None = None) -> str | None:
        """读取字符串配置。

        Args:
            key: 环境变量名。
            default: 默认值。

        Returns:
            配置值或默认值。
        """
        value = os.getenv(key)
        if value is None or value.strip() == "":
            return default
        return value

    def get_bool(self, key: str, default: bool = False) -> bool:
        """读取布尔配置。

        Args:
            key: 环境变量名。
            default: 默认值。

        Returns:
            布尔配置值。
        """
        value = self.get_str(key)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def get_int(self, key: str, default: int) -> int:
        """读取整数配置。

        Args:
            key: 环境变量名。
            default: 默认值。

        Returns:
            整数配置值。
        """
        value = self.get_str(key)
        if value is None:
            return default

        try:
            return int(value)
        except ValueError:
            return default

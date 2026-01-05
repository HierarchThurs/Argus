"""日志配置器。"""

from __future__ import annotations

import logging

from uvicorn.logging import DefaultFormatter

from app.core.config import AppConfig
from app.utils.logging.line_count_rotating_handler import LineCountRotatingFileHandler
from app.utils.logging.log_formatter import StandardFileFormatter


class LogConfigurator:
    """日志配置器。"""

    def __init__(self, config: AppConfig) -> None:
        """初始化配置器。

        Args:
            config: 应用配置。
        """
        self._config = config

    def configure(self) -> None:
        """应用日志配置。"""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(self._config.log_level)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            DefaultFormatter(
                fmt="%(levelprefix)s %(asctime)s | %(filename)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        file_handler = LineCountRotatingFileHandler(
            self._config.log_dir, self._config.log_max_lines
        )
        file_handler.setFormatter(StandardFileFormatter())

        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        self._configure_child_loggers()

    def _configure_child_loggers(self) -> None:
        """统一配置第三方日志。"""
        for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.setLevel(self._config.log_level)
            logger.propagate = True

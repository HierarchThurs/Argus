"""应用入口模块。"""

import logging

from fastapi import FastAPI

from app.core.app_factory import AppFactory
from app.core.config import AppConfig, AppConfigLoader
from app.core.container import AppContainer
from app.utils.logging.log_configurator import LogConfigurator


class BackendApplication:
    """应用启动器。

    该类负责组装依赖容器与工厂，并生成 FastAPI 应用实例。
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        """初始化启动器。

        Args:
            config: 可选的应用配置。
        """
        self._config = config or AppConfigLoader().load()
        LogConfigurator(self._config).configure()

        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.info("日志系统初始化完成，等级=%s", self._config.log_level)

        self._container = AppContainer(self._config)
        self._factory = AppFactory(self._container, self._config)
        self._app = self._factory.create_app()

    def get_app(self) -> FastAPI:
        """获取 FastAPI 应用实例。

        Returns:
            FastAPI 应用实例。
        """
        return self._app

    def get_config(self) -> AppConfig:
        """获取应用配置。

        Returns:
            应用配置实例。
        """
        return self._config


backend_application = BackendApplication()
app = backend_application.get_app()
config = backend_application.get_config()

"""应用入口模块。"""

from app.core.app_factory import AppFactory
from app.core.config import AppConfig
from app.core.container import AppContainer


config = AppConfig()
container = AppContainer(config)
factory = AppFactory(container, config)
app = factory.create_app()

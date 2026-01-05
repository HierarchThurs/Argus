"""依赖容器模块。"""

from app.core.config import AppConfig
from app.crud.user_crud import UserCrud
from app.routers.auth_router import AuthRouter
from app.services.auth_service import AuthService
from app.utils.logging.logger_factory import LoggerFactory
from app.utils.password_hasher import PasswordHasher
from app.utils.token_generator import TokenGenerator
from app.utils.validators import AuthValidator


class AppContainer:
    """应用依赖容器。

    该容器集中管理可复用的服务与工具类实例。
    """

    def __init__(self, config: AppConfig) -> None:
        """初始化依赖容器。

        Args:
            config: 应用配置。
        """
        self._config = config
        self._logger_factory = LoggerFactory()
        self.password_hasher = PasswordHasher()
        self.token_generator = TokenGenerator()
        self.validator = AuthValidator()
        self.user_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.user", "用户"
        )
        self.user_crud = UserCrud(self.password_hasher, self.user_crud_logger)
        self.auth_logger = self._logger_factory.create_logger("app.services.auth")
        self.auth_service = AuthService(
            self.user_crud,
            self.validator,
            self.password_hasher,
            self.token_generator,
            self.auth_logger,
        )
        self.auth_router_logger = self._logger_factory.create_logger("app.routers.auth")
        self.auth_router = AuthRouter(
            self.auth_service, self._config, self.auth_router_logger
        )

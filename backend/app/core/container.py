"""依赖容器模块。"""

from app.core.config import AppConfig
from app.core.database import DatabaseManager
from app.crud.user_crud import UserCrud
from app.crud.email_crud import EmailCrud
from app.crud.email_account_crud import EmailAccountCrud
from app.routers.auth_router import AuthRouter
from app.routers.email_account_router import EmailAccountRouter
from app.routers.email_router import EmailRouter
from app.services.auth_service import AuthService
from app.services.email_account_service import EmailAccountService
from app.services.email_service import EmailService
from app.utils.logging.logger_factory import LoggerFactory
from app.utils.password_hasher import PasswordHasher
from app.utils.token_generator import TokenGenerator
from app.utils.validators import AuthValidator
from app.utils.crypto.password_encryptor import PasswordEncryptor
from app.utils.phishing import MockPhishingDetector


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

        # 数据库管理器
        self.db_manager = DatabaseManager(config.get_database_url())

        # 工具类
        self.password_hasher = PasswordHasher()
        self.token_generator = TokenGenerator()
        self.validator = AuthValidator()
        self.password_encryptor = PasswordEncryptor()
        self.phishing_detector = MockPhishingDetector()

        # 初始化CRUD、服务、路由层
        self._init_user_layer()
        self._init_email_account_layer()
        self._init_email_layer()

    def _init_user_layer(self) -> None:
        """初始化用户相关的CRUD、服务和路由。"""
        # CRUD层
        self.user_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.user", "用户"
        )
        self.user_crud = UserCrud(
            self.db_manager, self.password_hasher, self.user_crud_logger
        )

        # 服务层
        self.auth_logger = self._logger_factory.create_logger("app.services.auth")
        self.auth_service = AuthService(
            self.user_crud,
            self.validator,
            self.password_hasher,
            self.token_generator,
            self.auth_logger,
        )

        # 路由层
        self.auth_router_logger = self._logger_factory.create_logger("app.routers.auth")
        self.auth_router = AuthRouter(
            self.auth_service, self._config, self.auth_router_logger
        )

    def _init_email_account_layer(self) -> None:
        """初始化邮箱账户相关的CRUD、服务和路由。"""
        # CRUD层
        self.email_account_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.email_account", "邮箱账户"
        )
        self.email_account_crud = EmailAccountCrud(
            self.db_manager,
            self.password_encryptor,
            self.email_account_crud_logger,
        )

        # 邮件CRUD（邮箱账户服务需要）
        self.email_crud_logger = self._logger_factory.create_crud_logger(
            "app.crud.email", "邮件"
        )
        self.email_crud = EmailCrud(
            self.db_manager,
            self.email_crud_logger,
        )

        # 服务层
        self.email_account_logger = self._logger_factory.create_logger(
            "app.services.email_account"
        )
        self.email_account_service = EmailAccountService(
            self.email_account_crud,
            self.email_crud,
            self.phishing_detector,
            self.email_account_logger,
        )

        # 路由层
        self.email_account_router_logger = self._logger_factory.create_logger(
            "app.routers.email_account"
        )
        self.email_account_router = EmailAccountRouter(
            self.email_account_service,
            self._config,
            self.email_account_router_logger,
        )

    def _init_email_layer(self) -> None:
        """初始化邮件相关的服务和路由。"""
        # 服务层
        self.email_logger = self._logger_factory.create_logger("app.services.email")
        self.email_service = EmailService(
            self.email_crud,
            self.email_account_crud,
            self.email_logger,
        )

        # 路由层
        self.email_router_logger = self._logger_factory.create_logger(
            "app.routers.email"
        )
        self.email_router = EmailRouter(
            self.email_service,
            self._config,
            self.email_router_logger,
        )

    async def close(self) -> None:
        """关闭容器中的资源。"""
        await self.db_manager.close()

"""认证路由层。"""

from fastapi import APIRouter

from app.core.config import AppConfig
from app.schemas.auth_schema import LoginRequest, LoginResponse
from app.services.auth_service import AuthService


class AuthRouter:
    """认证路由类。

    该类负责注册认证相关的 API 路由。
    """

    def __init__(self, auth_service: AuthService, config: AppConfig) -> None:
        """初始化认证路由。

        Args:
            auth_service: 认证服务。
            config: 应用配置。
        """
        self._auth_service = auth_service
        self._router = APIRouter(prefix=config.api_prefix, tags=["auth"])
        self._register_routes()

    @property
    def router(self) -> APIRouter:
        """对外暴露 FastAPI 路由对象。"""
        return self._router

    def _register_routes(self) -> None:
        """注册路由方法。"""
        self._router.post("/auth/login", response_model=LoginResponse)(self.login)

    async def login(self, request: LoginRequest) -> LoginResponse:
        """登录接口。

        Args:
            request: 登录请求数据。

        Returns:
            登录响应数据。
        """
        return await self._auth_service.login(request)

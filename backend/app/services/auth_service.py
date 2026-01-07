"""认证服务层。"""

import logging

from app.crud.user_crud import UserCrud
from app.middleware.jwt_auth import JWTAuthMiddleware
from app.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from app.utils.password_hasher import PasswordHasher
from app.utils.validators import AuthValidator


class AuthService:
    """认证服务类。

    该服务类负责登录流程编排与核心业务校验。
    """

    def __init__(
        self,
        user_crud: UserCrud,
        validator: AuthValidator,
        password_hasher: PasswordHasher,
        jwt_middleware: JWTAuthMiddleware,
        logger: logging.Logger,
    ) -> None:
        """初始化认证服务。

        Args:
            user_crud: 用户数据访问对象。
            validator: 登录校验器。
            password_hasher: 密码哈希工具。
            jwt_middleware: JWT认证中间件。
            logger: 日志记录器。
        """
        self._user_crud = user_crud
        self._validator = validator
        self._password_hasher = password_hasher
        self._jwt_middleware = jwt_middleware
        self._logger = logger

    async def login(self, request: LoginRequest) -> LoginResponse:
        """处理登录请求。

        Args:
            request: 登录请求模型。

        Returns:
            登录响应模型。
        """
        validation = self._validator.validate_login(
            request.student_id, request.password
        )
        if not validation.is_valid:
            self._logger.warning(
                "登录校验失败 student_id=%s message=%s",
                request.student_id,
                validation.message,
            )
            return LoginResponse(success=False, message=validation.message)

        user = await self._user_crud.get_by_student_id(request.student_id)
        if not user:
            self._logger.warning("登录失败，账号不存在 student_id=%s", request.student_id)
            return LoginResponse(success=False, message="账号或密码错误。")

        if not self._password_hasher.verify(request.password, user.password_hash):
            self._logger.warning("登录失败，密码错误 student_id=%s", request.student_id)
            return LoginResponse(success=False, message="账号或密码错误。")

        # 生成JWT令牌
        access_token = self._jwt_middleware.create_access_token(
            user_id=user.id,
            student_id=user.student_id,
            display_name=user.display_name,
        )
        refresh_token = self._jwt_middleware.create_refresh_token(
            user_id=user.id,
            student_id=user.student_id,
            display_name=user.display_name,
        )

        self._logger.info("登录成功 student_id=%s", request.student_id)
        return LoginResponse(
            success=True,
            message="登录成功。",
            token=access_token,
            refresh_token=refresh_token,
            user_id=user.id,
            student_id=user.student_id,
            display_name=user.display_name,
        )

    async def refresh_token(
        self, request: RefreshTokenRequest
    ) -> RefreshTokenResponse:
        """刷新访问令牌。

        Args:
            request: 刷新令牌请求模型。

        Returns:
            刷新令牌响应模型。
        """
        try:
            new_token = self._jwt_middleware.refresh_access_token(
                request.refresh_token
            )
            return RefreshTokenResponse(
                success=True,
                message="令牌刷新成功。",
                token=new_token,
            )
        except Exception as e:
            self._logger.warning("令牌刷新失败: %s", str(e))
            return RefreshTokenResponse(
                success=False,
                message="令牌刷新失败，请重新登录。",
            )

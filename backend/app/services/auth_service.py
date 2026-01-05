"""认证服务层。"""

from app.crud.user_crud import UserCrud
from app.schemas.auth_schema import LoginRequest, LoginResponse
from app.utils.password_hasher import PasswordHasher
from app.utils.token_generator import TokenGenerator
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
        token_generator: TokenGenerator,
    ) -> None:
        """初始化认证服务。

        Args:
            user_crud: 用户数据访问对象。
            validator: 登录校验器。
            password_hasher: 密码哈希工具。
            token_generator: 令牌生成工具。
        """
        self._user_crud = user_crud
        self._validator = validator
        self._password_hasher = password_hasher
        self._token_generator = token_generator

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
            return LoginResponse(success=False, message=validation.message)

        user = await self._user_crud.get_by_student_id(request.student_id)
        if not user:
            return LoginResponse(success=False, message="账号或密码错误。")

        if not self._password_hasher.verify(request.password, user.password_hash):
            return LoginResponse(success=False, message="账号或密码错误。")

        token = self._token_generator.generate()
        return LoginResponse(
            success=True,
            message="登录成功。",
            token=token,
            student_id=user.student_id,
            display_name=user.display_name,
        )

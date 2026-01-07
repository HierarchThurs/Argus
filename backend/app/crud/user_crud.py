"""用户数据访问层。"""

from typing import Optional

from sqlalchemy import select

from app.core.database import DatabaseManager
from app.entities.user_entity import UserEntity
from app.utils.logging.crud_logger import CrudLogger
from app.utils.password_hasher import PasswordHasher


class UserCrud:
    """用户CRUD操作类。

    提供用户数据的增删改查操作，使用异步数据库会话。
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        password_hasher: PasswordHasher,
        crud_logger: CrudLogger,
    ) -> None:
        """初始化用户CRUD。

        Args:
            db_manager: 数据库管理器实例。
            password_hasher: 密码哈希工具。
            crud_logger: CRUD日志记录器。
        """
        self._db_manager = db_manager
        self._password_hasher = password_hasher
        self._crud_logger = crud_logger

    async def get_by_student_id(self, student_id: str) -> Optional[UserEntity]:
        """根据学号获取用户。

        Args:
            student_id: 学号。

        Returns:
            用户实体或None（如果用户不存在）。
        """
        async with self._db_manager.get_session() as session:
            query = select(UserEntity).where(UserEntity.student_id == student_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user:
                self._crud_logger.log_read(
                    "查询到用户",
                    {"student_id": student_id, "found": True},
                )
            else:
                self._crud_logger.log_read(
                    "未查询到用户",
                    {"student_id": student_id, "found": False},
                )

            return user

    async def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        """根据ID获取用户。

        Args:
            user_id: 用户ID。

        Returns:
            用户实体或None（如果用户不存在）。
        """
        async with self._db_manager.get_session() as session:
            query = select(UserEntity).where(UserEntity.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user:
                self._crud_logger.log_read(
                    "根据ID查询到用户",
                    {"user_id": user_id, "found": True},
                )
            else:
                self._crud_logger.log_read(
                    "根据ID未查询到用户",
                    {"user_id": user_id, "found": False},
                )

            return user

    async def create(
        self, student_id: str, password: str, display_name: str
    ) -> UserEntity:
        """创建新用户。

        Args:
            student_id: 学号。
            password: 明文密码（将被哈希）。
            display_name: 显示名称。

        Returns:
            创建的用户实体。
        """
        async with self._db_manager.get_session() as session:
            user = UserEntity(
                student_id=student_id,
                password_hash=self._password_hasher.hash(password),
                display_name=display_name,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)

            self._crud_logger.log_create(
                "创建用户",
                {"student_id": student_id, "display_name": display_name},
            )

            return user

    async def update_password(self, user_id: int, new_password: str) -> bool:
        """更新用户密码。

        Args:
            user_id: 用户ID。
            new_password: 新密码（明文）。

        Returns:
            是否更新成功。
        """
        async with self._db_manager.get_session() as session:
            query = select(UserEntity).where(UserEntity.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                self._crud_logger.log_update(
                    "更新密码失败-用户不存在",
                    {"user_id": user_id, "success": False},
                )
                return False

            user.password_hash = self._password_hasher.hash(new_password)
            await session.flush()

            self._crud_logger.log_update(
                "更新用户密码",
                {"user_id": user_id, "success": True},
            )

            return True

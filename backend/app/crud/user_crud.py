"""用户数据访问层。"""

from typing import List, Optional

from app.entities.user_entity import UserEntity
from app.utils.logging.crud_logger import CrudLogger
from app.utils.password_hasher import PasswordHasher


class UserCrud:
    """用户 CRUD 类。

    当前实现使用内存作为数据源，便于后续替换为数据库实现。
    """

    def __init__(self, password_hasher: PasswordHasher, crud_logger: CrudLogger) -> None:
        """初始化用户 CRUD。

        Args:
            password_hasher: 密码哈希工具。
            crud_logger: CRUD 日志记录器。
        """
        self._password_hasher = password_hasher
        self._crud_logger = crud_logger
        self._users = self._seed_users()

    def _seed_users(self) -> List[UserEntity]:
        """初始化演示用户数据。

        Returns:
            用户实体列表。
        """
        default_user = UserEntity(
            student_id="20230001",
            password_hash=self._password_hasher.hash("Passw0rd!"),
            display_name="默认账号",
        )
        return [default_user]

    async def get_by_student_id(self, student_id: str) -> Optional[UserEntity]:
        """根据学号获取用户。

        Args:
            student_id: 学号。

        Returns:
            用户实体或 None。
        """
        for user in self._users:
            if user.student_id == student_id:
                self._crud_logger.log_read(
                    "查询到用户",
                    {"student_id": student_id, "found": True},
                )
                return user

        self._crud_logger.log_read(
            "未查询到用户",
            {"student_id": student_id, "found": False},
        )
        return None

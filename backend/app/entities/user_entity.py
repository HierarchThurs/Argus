"""用户实体定义。"""


class UserEntity:
    """用户实体。

    Attributes:
        student_id: 学号。
        password_hash: 密码哈希。
        display_name: 显示名称。
    """

    def __init__(self, student_id: str, password_hash: str, display_name: str) -> None:
        """初始化用户实体。

        Args:
            student_id: 学号。
            password_hash: 密码哈希。
            display_name: 显示名称。
        """
        self.student_id = student_id
        self.password_hash = password_hash
        self.display_name = display_name

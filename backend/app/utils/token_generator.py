"""令牌生成工具。"""

import uuid


class TokenGenerator:
    """轻量级令牌生成工具类。

    该类用于在登录成功后生成会话令牌，便于后续扩展鉴权逻辑。
    """

    def generate(self) -> str:
        """生成随机令牌。

        Returns:
            随机字符串令牌。
        """
        return uuid.uuid4().hex

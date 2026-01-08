"""发件人白名单匹配服务。

提供发件人邮箱地址规则匹配功能，支持多种匹配规则。
"""

import logging
from typing import List, Optional

from app.crud.sender_whitelist_crud import SenderWhitelistCrud
from app.entities.sender_whitelist_entity import SenderWhitelistEntity


class SenderWhitelistMatcher:
    """发件人白名单匹配器。

    支持四种匹配规则：
    - EMAIL: 精确匹配完整邮箱地址
    - DOMAIN: 精确匹配邮箱域名
    - DOMAIN-SUFFIX: 匹配邮箱域名后缀
    - DOMAIN-KEYWORD: 匹配邮箱域名中的关键词
    """

    # 规则类型常量
    RULE_EMAIL = "EMAIL"
    RULE_DOMAIN = "DOMAIN"
    RULE_DOMAIN_SUFFIX = "DOMAIN-SUFFIX"
    RULE_DOMAIN_KEYWORD = "DOMAIN-KEYWORD"

    def __init__(
        self,
        whitelist_crud: SenderWhitelistCrud,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """初始化发件人白名单匹配器。

        Args:
            whitelist_crud: 发件人白名单CRUD实例。
            logger: 日志记录器。
        """
        self._whitelist_crud = whitelist_crud
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._cached_rules: Optional[List[SenderWhitelistEntity]] = None

    async def refresh_rules(self) -> None:
        """刷新规则缓存。"""
        self._cached_rules = await self._whitelist_crud.get_all_active()
        self._logger.info(f"刷新发件人白名单规则缓存，共 {len(self._cached_rules)} 条规则")

    async def is_sender_whitelisted(self, sender_email: str) -> bool:
        """检查发件人邮箱是否在白名单中。

        Args:
            sender_email: 要检查的发件人邮箱地址。

        Returns:
            如果发件人在白名单中返回True，否则返回False。
        """
        if not sender_email:
            return False

        # 标准化邮箱地址
        sender_email = sender_email.lower().strip()

        # 提取域名
        domain = self.extract_domain(sender_email)
        if not domain:
            return False

        # 获取规则（使用缓存或重新加载）
        if self._cached_rules is None:
            await self.refresh_rules()

        rules = self._cached_rules or []

        for rule in rules:
            if self._match_rule(sender_email, domain, rule.rule_type, rule.rule_value):
                self._logger.debug(
                    f"发件人 '{sender_email}' 匹配白名单规则: {rule.rule_type}:{rule.rule_value}"
                )
                return True

        return False

    @staticmethod
    def extract_domain(email: str) -> Optional[str]:
        """从邮箱地址中提取域名部分。

        Args:
            email: 完整的邮箱地址。

        Returns:
            域名字符串，如果解析失败返回None。
        """
        try:
            if "@" in email:
                return email.split("@")[-1].lower()
            return None
        except Exception:
            return None

    def _match_rule(
        self, email: str, domain: str, rule_type: str, rule_value: str
    ) -> bool:
        """检查邮箱/域名是否匹配规则。

        Args:
            email: 完整的邮箱地址。
            domain: 邮箱域名。
            rule_type: 规则类型。
            rule_value: 规则值。

        Returns:
            是否匹配。
        """
        email = email.lower()
        domain = domain.lower()
        rule_value = rule_value.lower()

        if rule_type == self.RULE_EMAIL:
            # 精确匹配完整邮箱地址
            return email == rule_value

        elif rule_type == self.RULE_DOMAIN:
            # 精确匹配域名
            return domain == rule_value

        elif rule_type == self.RULE_DOMAIN_SUFFIX:
            # 后缀匹配
            # 例如: mail.qq.com 匹配 qq.com
            if domain == rule_value:
                return True
            if domain.endswith("." + rule_value):
                return True
            return False

        elif rule_type == self.RULE_DOMAIN_KEYWORD:
            # 关键词匹配
            return rule_value in domain

        return False

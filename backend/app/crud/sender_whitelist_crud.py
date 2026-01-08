"""发件人白名单规则数据访问层。"""

from typing import List, Optional

from sqlalchemy import select

from app.core.database import DatabaseManager
from app.entities.sender_whitelist_entity import SenderWhitelistEntity
from app.utils.logging.crud_logger import CrudLogger


class SenderWhitelistCrud:
    """发件人白名单CRUD操作类。

    提供发件人白名单规则的增删改查操作，使用异步数据库会话。
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        crud_logger: CrudLogger,
    ) -> None:
        """初始化发件人白名单CRUD。

        Args:
            db_manager: 数据库管理器实例。
            crud_logger: CRUD日志记录器。
        """
        self._db_manager = db_manager
        self._crud_logger = crud_logger

    async def create(
        self,
        rule_type: str,
        rule_value: str,
        description: Optional[str] = None,
    ) -> SenderWhitelistEntity:
        """创建发件人白名单规则。

        Args:
            rule_type: 规则类型（EMAIL/DOMAIN/DOMAIN-SUFFIX/DOMAIN-KEYWORD）。
            rule_value: 规则值。
            description: 规则描述。

        Returns:
            创建的发件人白名单规则实体。
        """
        async with self._db_manager.get_session() as session:
            rule = SenderWhitelistEntity(
                rule_type=rule_type,
                rule_value=rule_value,
                description=description,
            )
            session.add(rule)
            await session.flush()
            await session.refresh(rule)

            self._crud_logger.log_create(
                "创建发件人白名单规则",
                {"rule_type": rule_type, "rule_value": rule_value},
            )

            return rule

    async def get_all_active(self) -> List[SenderWhitelistEntity]:
        """获取所有启用的发件人白名单规则。

        Returns:
            启用的发件人白名单规则列表。
        """
        async with self._db_manager.get_session() as session:
            query = select(SenderWhitelistEntity).where(
                SenderWhitelistEntity.is_active == True
            )
            result = await session.execute(query)
            rules = list(result.scalars().all())

            self._crud_logger.log_read(
                "获取所有启用的发件人白名单规则",
                {"count": len(rules)},
            )

            return rules

    async def get_all(self) -> List[SenderWhitelistEntity]:
        """获取所有发件人白名单规则。

        Returns:
            发件人白名单规则列表。
        """
        async with self._db_manager.get_session() as session:
            query = select(SenderWhitelistEntity).order_by(
                SenderWhitelistEntity.created_at.desc()
            )
            result = await session.execute(query)
            rules = list(result.scalars().all())

            self._crud_logger.log_read(
                "获取所有发件人白名单规则",
                {"count": len(rules)},
            )

            return rules

    async def get_by_id(self, rule_id: int) -> Optional[SenderWhitelistEntity]:
        """根据ID获取发件人白名单规则。

        Args:
            rule_id: 规则ID。

        Returns:
            发件人白名单规则实体或None。
        """
        async with self._db_manager.get_session() as session:
            query = select(SenderWhitelistEntity).where(
                SenderWhitelistEntity.id == rule_id
            )
            result = await session.execute(query)
            rule = result.scalar_one_or_none()

            self._crud_logger.log_read(
                "根据ID查询发件人白名单规则",
                {"rule_id": rule_id, "found": rule is not None},
            )

            return rule

    async def update(
        self,
        rule_id: int,
        rule_type: Optional[str] = None,
        rule_value: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[SenderWhitelistEntity]:
        """更新发件人白名单规则。

        Args:
            rule_id: 规则ID。
            rule_type: 规则类型。
            rule_value: 规则值。
            description: 规则描述。
            is_active: 是否启用。

        Returns:
            更新后的规则实体，如果不存在返回None。
        """
        async with self._db_manager.get_session() as session:
            query = select(SenderWhitelistEntity).where(
                SenderWhitelistEntity.id == rule_id
            )
            result = await session.execute(query)
            rule = result.scalar_one_or_none()

            if not rule:
                self._crud_logger.log_update(
                    "更新发件人白名单规则失败-规则不存在",
                    {"rule_id": rule_id, "success": False},
                )
                return None

            if rule_type is not None:
                rule.rule_type = rule_type
            if rule_value is not None:
                rule.rule_value = rule_value
            if description is not None:
                rule.description = description
            if is_active is not None:
                rule.is_active = is_active

            await session.flush()
            await session.refresh(rule)

            self._crud_logger.log_update(
                "更新发件人白名单规则",
                {"rule_id": rule_id, "success": True},
            )

            return rule

    async def delete(self, rule_id: int) -> bool:
        """删除发件人白名单规则。

        Args:
            rule_id: 规则ID。

        Returns:
            是否删除成功。
        """
        async with self._db_manager.get_session() as session:
            query = select(SenderWhitelistEntity).where(
                SenderWhitelistEntity.id == rule_id
            )
            result = await session.execute(query)
            rule = result.scalar_one_or_none()

            if not rule:
                self._crud_logger.log_delete(
                    "删除发件人白名单规则失败-规则不存在",
                    {"rule_id": rule_id, "success": False},
                )
                return False

            await session.delete(rule)
            await session.flush()

            self._crud_logger.log_delete(
                "删除发件人白名单规则",
                {"rule_id": rule_id, "success": True},
            )

            return True

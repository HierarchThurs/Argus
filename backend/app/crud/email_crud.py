"""邮件数据访问层。"""

from typing import List, Optional

from sqlalchemy import select, desc

from app.core.database import DatabaseManager
from app.entities.email_entity import EmailEntity, PhishingLevel
from app.utils.logging.crud_logger import CrudLogger


class EmailCrud:
    """邮件CRUD操作类。

    提供邮件数据的增删改查操作，使用异步数据库会话。
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        crud_logger: CrudLogger,
    ) -> None:
        """初始化邮件CRUD。

        Args:
            db_manager: 数据库管理器实例。
            crud_logger: CRUD日志记录器。
        """
        self._db_manager = db_manager
        self._crud_logger = crud_logger

    async def get_by_account_id(
        self,
        account_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EmailEntity]:
        """获取指定邮箱账户的邮件列表。

        Args:
            account_id: 邮箱账户ID。
            limit: 返回数量限制。
            offset: 偏移量。

        Returns:
            邮件实体列表。
        """
        async with self._db_manager.get_session() as session:
            query = (
                select(EmailEntity)
                .where(EmailEntity.email_account_id == account_id)
                .order_by(desc(EmailEntity.received_at))
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(query)
            emails = result.scalars().all()

            self._crud_logger.log_read(
                "查询邮件列表",
                {"account_id": account_id, "count": len(emails)},
            )

            return list(emails)

    async def get_by_user_accounts(
        self,
        account_ids: List[int],
        limit: int = 50,
        offset: int = 0,
    ) -> List[EmailEntity]:
        """获取多个邮箱账户的聚合邮件列表。

        Args:
            account_ids: 邮箱账户ID列表。
            limit: 返回数量限制。
            offset: 偏移量。

        Returns:
            邮件实体列表。
        """
        if not account_ids:
            return []

        async with self._db_manager.get_session() as session:
            query = (
                select(EmailEntity)
                .where(EmailEntity.email_account_id.in_(account_ids))
                .order_by(desc(EmailEntity.received_at))
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(query)
            emails = result.scalars().all()

            self._crud_logger.log_read(
                "查询聚合邮件列表",
                {"account_ids": account_ids, "count": len(emails)},
            )

            return list(emails)

    async def get_by_id(self, email_id: int) -> Optional[EmailEntity]:
        """根据ID获取邮件。

        Args:
            email_id: 邮件ID。

        Returns:
            邮件实体或None。
        """
        async with self._db_manager.get_session() as session:
            query = select(EmailEntity).where(EmailEntity.id == email_id)
            result = await session.execute(query)
            email = result.scalar_one_or_none()

            if email:
                self._crud_logger.log_read(
                    "查询到邮件",
                    {"email_id": email_id, "found": True},
                )
            else:
                self._crud_logger.log_read(
                    "未查询到邮件",
                    {"email_id": email_id, "found": False},
                )

            return email

    async def get_by_message_id(
        self, account_id: int, message_id: str
    ) -> Optional[EmailEntity]:
        """根据邮件唯一标识获取邮件。

        Args:
            account_id: 邮箱账户ID。
            message_id: 邮件唯一标识。

        Returns:
            邮件实体或None。
        """
        async with self._db_manager.get_session() as session:
            query = select(EmailEntity).where(
                EmailEntity.email_account_id == account_id,
                EmailEntity.message_id == message_id,
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def create(
        self,
        email_account_id: int,
        message_id: str,
        subject: Optional[str],
        sender: str,
        recipients: Optional[str],
        content_text: Optional[str],
        content_html: Optional[str],
        received_at: Optional[str],
        is_sent: bool = False,
    ) -> EmailEntity:
        """创建邮件记录。

        Args:
            email_account_id: 邮箱账户ID。
            message_id: 邮件唯一标识。
            subject: 邮件主题。
            sender: 发件人。
            recipients: 收件人（JSON格式）。
            content_text: 纯文本内容。
            content_html: HTML内容。
            received_at: 接收时间。
            is_sent: 是否为发送的邮件。

        Returns:
            创建的邮件实体。
        """
        async with self._db_manager.get_session() as session:
            email = EmailEntity(
                email_account_id=email_account_id,
                message_id=message_id,
                subject=subject,
                sender=sender,
                recipients=recipients,
                content_text=content_text,
                content_html=content_html,
                received_at=received_at,
                is_sent=is_sent,
            )
            session.add(email)
            await session.flush()
            await session.refresh(email)

            self._crud_logger.log_create(
                "创建邮件",
                {"email_account_id": email_account_id, "subject": subject},
            )

            return email

    async def mark_as_read(self, email_id: int) -> bool:
        """标记邮件为已读。

        Args:
            email_id: 邮件ID。

        Returns:
            是否标记成功。
        """
        async with self._db_manager.get_session() as session:
            query = select(EmailEntity).where(EmailEntity.id == email_id)
            result = await session.execute(query)
            email = result.scalar_one_or_none()

            if not email:
                return False

            email.is_read = True
            await session.flush()

            self._crud_logger.log_update(
                "标记邮件已读",
                {"email_id": email_id},
            )

            return True

    async def update_phishing_result(
        self,
        email_id: int,
        phishing_level: PhishingLevel,
        phishing_score: float,
        phishing_reason: Optional[str] = None,
    ) -> bool:
        """更新邮件的钓鱼检测结果。

        Args:
            email_id: 邮件ID。
            phishing_level: 钓鱼危险等级。
            phishing_score: 钓鱼评分。
            phishing_reason: 钓鱼判定原因。

        Returns:
            是否更新成功。
        """
        async with self._db_manager.get_session() as session:
            query = select(EmailEntity).where(EmailEntity.id == email_id)
            result = await session.execute(query)
            email = result.scalar_one_or_none()

            if not email:
                return False

            email.phishing_level = phishing_level
            email.phishing_score = phishing_score
            email.phishing_reason = phishing_reason
            await session.flush()

            self._crud_logger.log_update(
                "更新钓鱼检测结果",
                {
                    "email_id": email_id,
                    "phishing_level": phishing_level.value,
                    "phishing_score": phishing_score,
                },
            )

            return True

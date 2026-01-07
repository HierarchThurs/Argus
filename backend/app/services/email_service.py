"""邮件服务层。"""

import logging
import json
from typing import List, Optional

from app.crud.email_crud import EmailCrud
from app.crud.email_account_crud import EmailAccountCrud
from app.schemas.email_schema import (
    EmailListResponse,
    EmailItem,
    EmailDetailResponse,
    EmailDetail,
    SendEmailRequest,
    SendEmailResponse,
    MarkAsReadResponse,
)
from app.utils.imap import SmtpClient, ImapConfigFactory


class EmailService:
    """邮件服务类。

    负责邮件的获取、发送等业务逻辑。
    """

    def __init__(
        self,
        email_crud: EmailCrud,
        email_account_crud: EmailAccountCrud,
        logger: logging.Logger,
    ) -> None:
        """初始化邮件服务。

        Args:
            email_crud: 邮件数据访问对象。
            email_account_crud: 邮箱账户数据访问对象。
            logger: 日志记录器。
        """
        self._email_crud = email_crud
        self._email_account_crud = email_account_crud
        self._logger = logger

    async def get_emails(
        self,
        user_id: int,
        account_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> EmailListResponse:
        """获取邮件列表。

        Args:
            user_id: 用户ID。
            account_id: 邮箱账户ID（可选，不指定则聚合所有邮箱）。
            limit: 返回数量限制。
            offset: 偏移量。

        Returns:
            邮件列表响应。
        """
        # 获取用户所有邮箱账户
        accounts = await self._email_account_crud.get_by_user_id(user_id)
        account_map = {acc.id: acc.email_address for acc in accounts}

        if not accounts:
            return EmailListResponse(success=True, emails=[], total=0)

        # 获取邮件
        if account_id:
            # 验证账户归属
            if account_id not in account_map:
                return EmailListResponse(success=True, emails=[], total=0)
            emails = await self._email_crud.get_by_account_id(account_id, limit, offset)
        else:
            # 聚合所有邮箱
            account_ids = list(account_map.keys())
            emails = await self._email_crud.get_by_user_accounts(
                account_ids, limit, offset
            )

        # 转换为响应模型
        items = [
            EmailItem(
                id=email.id,
                email_account_id=email.email_account_id,
                email_address=account_map.get(email.email_account_id),
                subject=email.subject,
                sender=email.sender,
                received_at=(
                    email.received_at.isoformat() if email.received_at else None
                ),
                is_read=email.is_read,
                phishing_level=email.phishing_level.value,
                phishing_score=email.phishing_score,
            )
            for email in emails
        ]

        return EmailListResponse(success=True, emails=items, total=len(items))

    async def get_email_detail(
        self, user_id: int, email_id: int
    ) -> EmailDetailResponse:
        """获取邮件详情。

        Args:
            user_id: 用户ID。
            email_id: 邮件ID。

        Returns:
            邮件详情响应。
        """
        # 获取邮件
        email = await self._email_crud.get_by_id(email_id)
        if not email:
            return EmailDetailResponse(success=False, email=None)

        # 验证邮件归属
        account = await self._email_account_crud.get_by_id(email.email_account_id)
        if not account or account.user_id != user_id:
            return EmailDetailResponse(success=False, email=None)

        # 标记为已读
        if not email.is_read:
            await self._email_crud.mark_as_read(email_id)

        detail = EmailDetail(
            id=email.id,
            email_account_id=email.email_account_id,
            email_address=account.email_address,
            message_id=email.message_id,
            subject=email.subject,
            sender=email.sender,
            recipients=email.recipients,
            content_text=email.content_text,
            content_html=email.content_html,
            received_at=(email.received_at.isoformat() if email.received_at else None),
            is_read=True,
            phishing_level=email.phishing_level.value,
            phishing_score=email.phishing_score,
            phishing_reason=email.phishing_reason,
        )

        return EmailDetailResponse(success=True, email=detail)

    async def send_email(
        self, user_id: int, request: SendEmailRequest
    ) -> SendEmailResponse:
        """发送邮件。

        Args:
            user_id: 用户ID。
            request: 发送邮件请求。

        Returns:
            发送邮件响应。
        """
        # 获取发件邮箱账户
        account = await self._email_account_crud.get_by_id(request.email_account_id)
        if not account or account.user_id != user_id:
            return SendEmailResponse(
                success=False,
                message="发件邮箱账户不存在。",
            )

        # 解密密码
        password = self._email_account_crud.decrypt_password(
            account.auth_password_encrypted
        )

        # 获取配置
        config = ImapConfigFactory.get_config_or_default(
            email_type=account.email_type,
            imap_host=account.imap_host,
            imap_port=account.imap_port,
            smtp_host=account.smtp_host,
            smtp_port=account.smtp_port,
            use_ssl=account.use_ssl,
        )

        # 发送邮件
        smtp_client = SmtpClient(config, self._logger)
        success = await smtp_client.send_email(
            username=account.email_address,
            password=password,
            to_addresses=request.to_addresses,
            subject=request.subject,
            content=request.content,
            content_html=request.content_html,
            cc_addresses=request.cc_addresses,
        )

        if success:
            self._logger.info(
                "发送邮件成功: from=%s, to=%s",
                account.email_address,
                request.to_addresses,
            )
            return SendEmailResponse(
                success=True,
                message="邮件发送成功。",
            )
        else:
            return SendEmailResponse(
                success=False,
                message="邮件发送失败，请稍后重试。",
            )

    async def mark_as_read(self, user_id: int, email_id: int) -> MarkAsReadResponse:
        """标记邮件为已读。

        Args:
            user_id: 用户ID。
            email_id: 邮件ID。

        Returns:
            标记已读响应。
        """
        # 获取邮件
        email = await self._email_crud.get_by_id(email_id)
        if not email:
            return MarkAsReadResponse(success=False, message="邮件不存在。")

        # 验证邮件归属
        account = await self._email_account_crud.get_by_id(email.email_account_id)
        if not account or account.user_id != user_id:
            return MarkAsReadResponse(success=False, message="邮件不存在。")

        # 标记已读
        await self._email_crud.mark_as_read(email_id)

        return MarkAsReadResponse(success=True, message="标记成功。")

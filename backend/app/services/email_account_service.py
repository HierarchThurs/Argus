"""邮箱账户服务层。"""

import logging
import json
from typing import List, Optional

from app.crud.email_account_crud import EmailAccountCrud
from app.crud.email_crud import EmailCrud
from app.entities.email_account_entity import EmailType, EmailAccountEntity
from app.entities.email_entity import PhishingLevel
from app.schemas.email_account_schema import (
    AddEmailAccountRequest,
    AddEmailAccountResponse,
    EmailAccountListResponse,
    EmailAccountItem,
    SyncEmailsResponse,
    DeleteEmailAccountResponse,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.utils.imap import ImapClient, ImapConfigFactory
from app.utils.phishing import PhishingDetectorInterface


class EmailAccountService:
    """邮箱账户服务类。

    负责邮箱账户的添加、同步、测试连接等业务逻辑。
    """

    def __init__(
        self,
        email_account_crud: EmailAccountCrud,
        email_crud: EmailCrud,
        phishing_detector: PhishingDetectorInterface,
        logger: logging.Logger,
    ) -> None:
        """初始化邮箱账户服务。

        Args:
            email_account_crud: 邮箱账户数据访问对象。
            email_crud: 邮件数据访问对象。
            phishing_detector: 钓鱼检测器。
            logger: 日志记录器。
        """
        self._email_account_crud = email_account_crud
        self._email_crud = email_crud
        self._phishing_detector = phishing_detector
        self._logger = logger

    async def add_email_account(
        self, user_id: int, request: AddEmailAccountRequest
    ) -> AddEmailAccountResponse:
        """添加邮箱账户。

        Args:
            user_id: 用户ID。
            request: 添加邮箱请求。

        Returns:
            添加邮箱响应。
        """
        # 检查邮箱是否已存在
        existing = await self._email_account_crud.get_by_email_address(
            user_id, request.email_address
        )
        if existing:
            return AddEmailAccountResponse(
                success=False,
                message="该邮箱已添加过。",
            )

        # 获取配置
        try:
            config = ImapConfigFactory.get_config_or_default(
                email_type=request.email_type,
                imap_host=request.imap_host,
                imap_port=request.imap_port,
                smtp_host=request.smtp_host,
                smtp_port=request.smtp_port,
                use_ssl=request.use_ssl,
            )
        except ValueError as e:
            return AddEmailAccountResponse(
                success=False,
                message=str(e),
            )

        # 测试连接
        imap_client = ImapClient(config, self._logger)
        connected = await imap_client.connect(
            request.email_address, request.auth_password
        )
        await imap_client.disconnect()

        if not connected:
            return AddEmailAccountResponse(
                success=False,
                message="邮箱连接失败，请检查邮箱地址和授权密码。",
            )

        # 创建账户
        account = await self._email_account_crud.create(
            user_id=user_id,
            email_address=request.email_address,
            email_type=request.email_type,
            auth_password=request.auth_password,
            imap_host=config.imap_host,
            imap_port=config.imap_port,
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            use_ssl=config.use_ssl,
        )

        self._logger.info(
            "添加邮箱成功: user_id=%s, email=%s", user_id, request.email_address
        )

        return AddEmailAccountResponse(
            success=True,
            message="邮箱添加成功。",
            account_id=account.id,
            email_address=account.email_address,
        )

    async def get_email_accounts(self, user_id: int) -> EmailAccountListResponse:
        """获取用户的邮箱账户列表。

        Args:
            user_id: 用户ID。

        Returns:
            邮箱账户列表响应。
        """
        accounts = await self._email_account_crud.get_by_user_id(user_id)

        items = [
            EmailAccountItem(
                id=account.id,
                email_address=account.email_address,
                email_type=account.email_type.value,
                is_active=account.is_active,
                last_sync_at=(
                    account.last_sync_at.isoformat() if account.last_sync_at else None
                ),
            )
            for account in accounts
        ]

        return EmailAccountListResponse(success=True, accounts=items)

    async def sync_emails(self, user_id: int, account_id: int) -> SyncEmailsResponse:
        """同步邮箱邮件。

        Args:
            user_id: 用户ID。
            account_id: 邮箱账户ID。

        Returns:
            同步邮件响应。
        """
        # 获取账户
        account = await self._email_account_crud.get_by_id(account_id)
        if not account or account.user_id != user_id:
            return SyncEmailsResponse(
                success=False,
                message="邮箱账户不存在。",
            )

        # 解密密码
        password = self._email_account_crud.decrypt_password(
            account.auth_password_encrypted
        )

        # 连接并获取邮件
        config = ImapConfigFactory.get_config_or_default(
            email_type=account.email_type,
            imap_host=account.imap_host,
            imap_port=account.imap_port,
            smtp_host=account.smtp_host,
            smtp_port=account.smtp_port,
            use_ssl=account.use_ssl,
        )

        imap_client = ImapClient(config, self._logger)
        connected = await imap_client.connect(account.email_address, password)

        if not connected:
            return SyncEmailsResponse(
                success=False,
                message="邮箱连接失败。",
            )

        try:
            emails = await imap_client.fetch_recent_emails(count=20)
            synced_count = 0

            self._logger.info("从IMAP获取到 %d 封邮件", len(emails))

            for email_msg in emails:
                self._logger.debug(
                    "处理邮件: message_id=%s, subject=%s",
                    email_msg.message_id[:50] if email_msg.message_id else "None",
                    email_msg.subject[:30] if email_msg.subject else "None",
                )

                # 检查邮件是否已存在
                existing = await self._email_crud.get_by_message_id(
                    account_id, email_msg.message_id
                )
                if existing:
                    self._logger.debug(
                        "邮件已存在，跳过: %s", email_msg.message_id[:50]
                    )
                    continue

                # 进行钓鱼检测
                phishing_result = await self._phishing_detector.detect(
                    subject=email_msg.subject,
                    sender=email_msg.sender,
                    content_text=email_msg.content_text,
                    content_html=email_msg.content_html,
                )

                # 转换钓鱼等级
                phishing_level_map = {
                    "NORMAL": PhishingLevel.NORMAL,
                    "SUSPICIOUS": PhishingLevel.SUSPICIOUS,
                    "HIGH_RISK": PhishingLevel.HIGH_RISK,
                }
                phishing_level = phishing_level_map.get(
                    phishing_result.level.value, PhishingLevel.NORMAL
                )

                # 创建邮件记录
                email_entity = await self._email_crud.create(
                    email_account_id=account_id,
                    message_id=email_msg.message_id,
                    subject=email_msg.subject,
                    sender=email_msg.sender,
                    recipients=json.dumps(email_msg.recipients),
                    content_text=email_msg.content_text,
                    content_html=email_msg.content_html,
                    received_at=email_msg.received_at,
                )

                # 更新钓鱼检测结果
                await self._email_crud.update_phishing_result(
                    email_id=email_entity.id,
                    phishing_level=phishing_level,
                    phishing_score=phishing_result.score,
                    phishing_reason=phishing_result.reason,
                )

                synced_count += 1
                self._logger.debug("邮件保存成功: id=%d", email_entity.id)

            # 更新最后同步时间
            await self._email_account_crud.update_last_sync(account_id)

            self._logger.info(
                "同步邮件成功: account_id=%s, synced=%d", account_id, synced_count
            )

            return SyncEmailsResponse(
                success=True,
                message=f"同步成功，获取{synced_count}封新邮件。",
                synced_count=synced_count,
            )

        finally:
            await imap_client.disconnect()

    async def delete_email_account(
        self, user_id: int, account_id: int
    ) -> DeleteEmailAccountResponse:
        """删除邮箱账户。

        Args:
            user_id: 用户ID。
            account_id: 邮箱账户ID。

        Returns:
            删除邮箱响应。
        """
        # 获取账户
        account = await self._email_account_crud.get_by_id(account_id)
        if not account or account.user_id != user_id:
            return DeleteEmailAccountResponse(
                success=False,
                message="邮箱账户不存在。",
            )

        # 软删除
        await self._email_account_crud.delete(account_id)

        self._logger.info("删除邮箱成功: account_id=%s", account_id)

        return DeleteEmailAccountResponse(
            success=True,
            message="邮箱删除成功。",
        )

    async def test_connection(
        self, request: TestConnectionRequest
    ) -> TestConnectionResponse:
        """测试邮箱连接。

        Args:
            request: 测试连接请求。

        Returns:
            测试连接响应。
        """
        try:
            config = ImapConfigFactory.get_config_or_default(
                email_type=request.email_type,
                imap_host=request.imap_host,
                imap_port=request.imap_port,
                use_ssl=request.use_ssl,
            )
        except ValueError as e:
            return TestConnectionResponse(
                success=False,
                message=str(e),
            )

        imap_client = ImapClient(config, self._logger)
        connected = await imap_client.connect(
            request.email_address, request.auth_password
        )
        await imap_client.disconnect()

        if connected:
            return TestConnectionResponse(
                success=True,
                message="连接成功。",
            )
        else:
            return TestConnectionResponse(
                success=False,
                message="连接失败，请检查邮箱地址和授权密码。",
            )

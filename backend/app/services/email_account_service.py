"""邮箱账户服务层。"""

from __future__ import annotations

import logging
from typing import List, Optional

from app.crud.email_account_crud import EmailAccountCrud
from app.crud.email_sync_crud import EmailSyncCrud
from app.crud.mailbox_crud import MailboxCrud
from app.entities.email_entity import PhishingLevel, PhishingStatus
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
from app.utils.imap import ImapClient, ImapConfigFactory, SmtpClient
from app.utils.imap.email_parser import EmailParser
from app.utils.imap.imap_models import MailboxInfo
from app.utils.phishing import PhishingDetectorInterface


class EmailAccountService:
    """邮箱账户服务类。

    负责邮箱账户的添加、同步、测试连接等业务逻辑。
    """

    def __init__(
        self,
        email_account_crud: EmailAccountCrud,
        mailbox_crud: MailboxCrud,
        email_sync_crud: EmailSyncCrud,
        phishing_detector: PhishingDetectorInterface,
        phishing_detection_service,  # 避免循环导入，使用类型提示的字符串形式
        logger: logging.Logger,
    ) -> None:
        """初始化邮箱账户服务。

        Args:
            email_account_crud: 邮箱账户数据访问对象。
            mailbox_crud: 邮箱文件夹数据访问对象。
            email_sync_crud: 邮件同步写入对象。
            phishing_detector: 钓鱼检测器。
            phishing_detection_service: 钓鱼检测服务（后台异步检测）。
            logger: 日志记录器。
        """
        self._email_account_crud = email_account_crud
        self._mailbox_crud = mailbox_crud
        self._email_sync_crud = email_sync_crud
        self._phishing_detector = phishing_detector
        self._phishing_detection_service = phishing_detection_service
        self._logger = logger
        self._email_parser = EmailParser(logger)

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
        imap_error = self._ensure_imap_available()
        if imap_error:
            return AddEmailAccountResponse(success=False, message=imap_error)

        smtp_error = self._ensure_smtp_available()
        if smtp_error:
            return AddEmailAccountResponse(success=False, message=smtp_error)

        existing = await self._email_account_crud.get_by_email_address(
            user_id, request.email_address
        )
        if existing:
            return AddEmailAccountResponse(
                success=False,
                message="该邮箱已添加过。",
            )

        try:
            config = ImapConfigFactory.get_config_or_default(
                email_type=request.email_type,
                imap_host=request.imap_host,
                imap_port=request.imap_port,
                smtp_host=request.smtp_host,
                smtp_port=request.smtp_port,
                use_ssl=request.use_ssl,
            )
        except ValueError as exc:
            return AddEmailAccountResponse(
                success=False,
                message=str(exc),
            )

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

        smtp_client = SmtpClient(config, self._logger)
        smtp_connected = await smtp_client.test_connection(
            request.email_address, request.auth_password
        )
        if not smtp_connected:
            return AddEmailAccountResponse(
                success=False,
                message="SMTP连接失败，请检查SMTP服务器和授权密码。",
            )

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
        imap_error = self._ensure_imap_available()
        if imap_error:
            return SyncEmailsResponse(success=False, message=imap_error)

        account = await self._email_account_crud.get_by_id(account_id)
        if not account or account.user_id != user_id:
            return SyncEmailsResponse(
                success=False,
                message="邮箱账户不存在。",
            )

        password = self._email_account_crud.decrypt_password(
            account.auth_password_encrypted
        )

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

        synced_total = 0
        try:
            mailboxes = await imap_client.list_mailboxes()
            if not mailboxes:
                mailboxes = [MailboxInfo(name="INBOX", delimiter=None, attributes=None)]

            for mailbox in mailboxes:
                if mailbox.attributes and "\\NOSELECT" in mailbox.attributes.upper():
                    continue

                status = await imap_client.get_mailbox_status(mailbox.name)
                mailbox_entity, uid_changed = await self._mailbox_crud.upsert_mailbox(
                    account_id=account_id,
                    name=mailbox.name,
                    delimiter=mailbox.delimiter,
                    attributes=mailbox.attributes,
                    uid_validity=status.uid_validity,
                )

                if uid_changed:
                    # UIDVALIDITY变化意味着UID游标失效，需清空文件夹映射后重新同步。
                    await self._mailbox_crud.reset_mailbox_messages(mailbox_entity.id)

                await imap_client.select_mailbox(mailbox.name)

                last_uid = mailbox_entity.last_uid or 0
                start_uid = last_uid + 1
                # 首次同步仅拉取最近50封邮件，避免一次性拉取全部历史邮件
                if last_uid == 0 and status.uid_next:
                    start_uid = max(status.uid_next - 50, 1)

                uids = await imap_client.fetch_uids_since(start_uid)
                if not uids:
                    await self._mailbox_crud.update_sync_state(
                        mailbox_entity.id, last_uid
                    )
                    continue

                uids = sorted(uids)
                # 收集所有新邮件的ID，用于后台异步检测
                new_email_ids = []

                for chunk in self._chunk_list(uids, 20):
                    # 分批拉取邮件与批量写入，避免单次内存占用过高。
                    fetched_emails = await imap_client.fetch_emails_by_uid(chunk)
                    payloads = self._build_payloads(fetched_emails, mailbox.name)
                    if not payloads:
                        continue

                    # 先保存邮件，不进行检测（默认为NORMAL），避免阻塞用户
                    # 钓鱼检测将在后台异步执行
                    for payload in payloads:
                        payload["phishing_level"] = PhishingLevel.NORMAL
                        payload["phishing_score"] = 0.0
                        payload["phishing_reason"] = None
                        payload["phishing_status"] = PhishingStatus.PENDING.value

                    synced_count, batch_email_ids = await self._email_sync_crud.save_mailbox_emails(
                        account_id=account_id,
                        mailbox_id=mailbox_entity.id,
                        payloads=payloads,
                    )
                    synced_total += synced_count

                    # 收集新邮件ID用于后台检测
                    new_email_ids.extend(batch_email_ids)

                    await self._mailbox_crud.update_sync_state(
                        mailbox_entity.id, max(chunk)
                    )

                # 启动后台异步检测任务（不等待完成）
                if new_email_ids:
                    self._logger.info(
                        "启动后台钓鱼检测任务: account_id=%d, mailbox=%s, count=%d",
                        account_id,
                        mailbox.name,
                        len(new_email_ids)
                    )
                    # 异步检测邮件，不阻塞主流程
                    await self._phishing_detection_service.detect_emails_async(new_email_ids)

            await self._email_account_crud.update_last_sync(account_id)

            return SyncEmailsResponse(
                success=True,
                message=f"同步成功，获取{synced_total}封新邮件。",
                synced_count=synced_total,
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
        account = await self._email_account_crud.get_by_id(account_id)
        if not account or account.user_id != user_id:
            return DeleteEmailAccountResponse(
                success=False,
                message="邮箱账户不存在。",
            )

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
        imap_error = self._ensure_imap_available()
        if imap_error:
            return TestConnectionResponse(success=False, message=imap_error)

        try:
            config = ImapConfigFactory.get_config_or_default(
                email_type=request.email_type,
                imap_host=request.imap_host,
                imap_port=request.imap_port,
                use_ssl=request.use_ssl,
            )
        except ValueError as exc:
            return TestConnectionResponse(
                success=False,
                message=str(exc),
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
        return TestConnectionResponse(
            success=False,
            message="连接失败，请检查邮箱地址和授权密码。",
        )

    def _build_payloads(
        self, fetched_emails, mailbox_name: str
    ) -> List[dict]:
        """构建同步写入的数据载荷。"""
        payloads: List[dict] = []
        for fetched in fetched_emails:
            parsed = self._email_parser.parse(fetched.raw_bytes)
            if not parsed:
                continue
            message_id = parsed.message_id or self._fallback_message_id(
                mailbox_name, fetched.uid
            )
            payloads.append(
                {
                    "uid": fetched.uid,
                    "flags": fetched.flags,
                    "internal_date": fetched.internal_date,
                    "size": fetched.size,
                    "message_id": message_id,
                    "subject": parsed.subject,
                    "sender_name": parsed.sender_name,
                    "sender_address": parsed.sender_address,
                    "recipients": parsed.recipients,
                    "content_text": parsed.content_text,
                    "content_html": parsed.content_html,
                    "snippet": parsed.snippet,
                    "received_at": parsed.received_at or fetched.internal_date,
                }
            )
        return payloads

    def _fallback_message_id(self, mailbox_name: str, uid: int) -> str:
        """生成缺失Message-ID时的替代值。"""
        message_id = f"missing-{mailbox_name}-{uid}"
        return message_id[:255]

    def _chunk_list(self, values: List[int], chunk_size: int) -> List[List[int]]:
        """将列表按指定大小切分为子列表。"""
        return [values[i : i + chunk_size] for i in range(0, len(values), chunk_size)]

    def _map_phishing_level(self, level: str) -> PhishingLevel:
        """映射钓鱼检测等级到数据库枚举。"""
        level_map = {
            "NORMAL": PhishingLevel.NORMAL,
            "SUSPICIOUS": PhishingLevel.SUSPICIOUS,
            "HIGH_RISK": PhishingLevel.HIGH_RISK,
        }
        return level_map.get(level, PhishingLevel.NORMAL)

    def _ensure_imap_available(self) -> Optional[str]:
        """确保IMAP依赖可用。"""
        if ImapClient is None:
            return "IMAP依赖未安装，请先安装aioimaplib。"
        return None

    def _ensure_smtp_available(self) -> Optional[str]:
        """确保SMTP依赖可用。"""
        if SmtpClient is None:
            return "SMTP依赖未安装，请先安装aiosmtplib。"
        return None

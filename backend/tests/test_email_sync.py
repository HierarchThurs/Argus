"""邮件同步与查询的单元测试。"""

from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.core.database import DatabaseManager
from app.crud.email_account_crud import EmailAccountCrud
from app.crud.email_crud import EmailCrud
from app.crud.email_sync_crud import EmailSyncCrud
from app.crud.mailbox_crud import MailboxCrud
from app.crud.user_crud import UserCrud
from app.entities.email_account_entity import EmailType
from app.entities.email_entity import PhishingLevel
from app.entities.email_recipient_entity import RecipientType
from app.utils.crypto.password_encryptor import PasswordEncryptor
from app.utils.imap.imap_models import ParsedRecipient
from app.utils.logging.logger_factory import LoggerFactory
from app.utils.password_hasher import PasswordHasher


class EmailSyncCrudTest(unittest.IsolatedAsyncioTestCase):
    """邮件同步与查询测试用例。"""

    async def asyncSetUp(self) -> None:
        """初始化测试数据库与依赖。"""
        self._temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self._temp_dir.name) / "test.db"
        test_db_url = os.getenv("TEST_DATABASE_URL")
        db_url = test_db_url or f"sqlite+aiosqlite:///{db_path}"

        try:
            self._db_manager = DatabaseManager(db_url)
        except ModuleNotFoundError:
            self._temp_dir.cleanup()
            self.skipTest("数据库驱动未安装，跳过数据库集成测试")
            return

        try:
            await asyncio.wait_for(self._db_manager.create_tables(), timeout=5)
        except asyncio.TimeoutError:
            await self._db_manager.close()
            self._temp_dir.cleanup()
            self.skipTest("数据库连接超时，跳过数据库集成测试")

        logger_factory = LoggerFactory()
        self._user_crud = UserCrud(
            self._db_manager,
            PasswordHasher(),
            logger_factory.create_crud_logger("test.user", "用户"),
        )
        self._email_account_crud = EmailAccountCrud(
            self._db_manager,
            PasswordEncryptor(),
            logger_factory.create_crud_logger("test.account", "邮箱账户"),
        )
        self._mailbox_crud = MailboxCrud(
            self._db_manager,
            logger_factory.create_crud_logger("test.mailbox", "邮箱文件夹"),
        )
        self._email_sync_crud = EmailSyncCrud(
            self._db_manager,
            logger_factory.create_crud_logger("test.sync", "邮件同步"),
        )
        self._email_crud = EmailCrud(
            self._db_manager,
            logger_factory.create_crud_logger("test.email", "邮件"),
        )

        self._user = await self._user_crud.create(
            student_id="2023001",
            password="test-pass",
            display_name="测试用户",
        )
        self._account = await self._email_account_crud.create(
            user_id=self._user.id,
            email_address="test@example.com",
            email_type=EmailType.QQ,
            auth_password="secret",
            imap_host="imap.qq.com",
            smtp_host="smtp.qq.com",
        )
        self._mailbox, _ = await self._mailbox_crud.upsert_mailbox(
            account_id=self._account.id,
            name="INBOX",
            delimiter="/",
            attributes=None,
            uid_validity=100,
        )

    async def asyncTearDown(self) -> None:
        """释放资源。"""
        await self._db_manager.close()
        self._temp_dir.cleanup()

    async def test_save_and_query_mailbox_emails(self) -> None:
        """验证同步写入与查询流程。"""
        now = datetime.now(timezone.utc)
        payloads = [
            {
                "uid": 1,
                "flags": ["\\Seen"],
                "internal_date": now,
                "size": 1234,
                "message_id": "<msg-1>",
                "subject": "测试邮件1",
                "sender_name": "Alice",
                "sender_address": "alice@example.com",
                "recipients": [
                    ParsedRecipient(
                        recipient_type=RecipientType.TO,
                        name="Bob",
                        address="bob@example.com",
                    )
                ],
                "content_text": "你好，这是测试邮件1",
                "content_html": None,
                "snippet": "你好，这是测试邮件1",
                "received_at": now,
                "phishing_level": PhishingLevel.NORMAL,
                "phishing_score": 0.1,
                "phishing_reason": "正常邮件",
            },
            {
                "uid": 2,
                "flags": [],
                "internal_date": now,
                "size": 2048,
                "message_id": "<msg-2>",
                "subject": "测试邮件2",
                "sender_name": "Carol",
                "sender_address": "carol@example.com",
                "recipients": [
                    ParsedRecipient(
                        recipient_type=RecipientType.CC,
                        name=None,
                        address="cc@example.com",
                    )
                ],
                "content_text": "你好，这是测试邮件2",
                "content_html": None,
                "snippet": "你好，这是测试邮件2",
                "received_at": now,
                "phishing_level": PhishingLevel.SUSPICIOUS,
                "phishing_score": 0.6,
                "phishing_reason": "包含可疑关键词",
            },
        ]

        inserted = await self._email_sync_crud.save_mailbox_emails(
            account_id=self._account.id,
            mailbox_id=self._mailbox.id,
            payloads=payloads,
        )
        self.assertEqual(inserted, 2)

        mailbox_messages = await self._email_crud.get_by_mailbox_ids(
            [self._mailbox.id], limit=10, offset=0
        )
        self.assertEqual(len(mailbox_messages), 2)
        self.assertTrue(mailbox_messages[0].message is not None)

        detail = await self._email_crud.get_by_id(mailbox_messages[0].id)
        self.assertIsNotNone(detail)
        self.assertIsNotNone(detail.message)
        self.assertIsNotNone(detail.message.body)

        inserted_again = await self._email_sync_crud.save_mailbox_emails(
            account_id=self._account.id,
            mailbox_id=self._mailbox.id,
            payloads=payloads,
        )
        self.assertEqual(inserted_again, 0)

    async def test_mark_as_read(self) -> None:
        """验证标记已读状态。"""
        now = datetime.now(timezone.utc)
        payloads = [
            {
                "uid": 10,
                "flags": [],
                "internal_date": now,
                "size": 512,
                "message_id": "<msg-10>",
                "subject": "未读邮件",
                "sender_name": "Dave",
                "sender_address": "dave@example.com",
                "recipients": [],
                "content_text": "测试标记已读",
                "content_html": None,
                "snippet": "测试标记已读",
                "received_at": now,
                "phishing_level": PhishingLevel.NORMAL,
                "phishing_score": 0.0,
                "phishing_reason": "正常邮件",
            }
        ]

        await self._email_sync_crud.save_mailbox_emails(
            account_id=self._account.id,
            mailbox_id=self._mailbox.id,
            payloads=payloads,
        )

        mailbox_messages = await self._email_crud.get_by_mailbox_ids(
            [self._mailbox.id], limit=10, offset=0
        )
        target = mailbox_messages[0]
        self.assertFalse(target.is_read)

        marked = await self._email_crud.mark_as_read(target.id)
        self.assertTrue(marked)

        refreshed = await self._email_crud.get_by_id(target.id)
        self.assertTrue(refreshed.is_read)

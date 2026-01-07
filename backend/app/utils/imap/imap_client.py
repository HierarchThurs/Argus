"""异步IMAP客户端模块。

基于aioimaplib封装的异步IMAP邮件客户端，支持增量同步与文件夹遍历。
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional

from aioimaplib import IMAP4_SSL

from app.utils.imap.imap_models import FetchedEmail, MailboxInfo, MailboxStatus
from app.utils.imap.imap_response_parser import ImapResponseParser


class ImapClient:
    """异步IMAP客户端类。

    提供连接、文件夹列表、增量UID同步等能力。
    """

    def __init__(self, config, logger: Optional[logging.Logger] = None):
        """初始化IMAP客户端。

        Args:
            config: IMAP配置。
            logger: 日志记录器。
        """
        self._config = config
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._client: Optional[IMAP4_SSL] = None
        self._selected_mailbox: Optional[str] = None

    async def connect(self, username: str, password: str) -> bool:
        """连接并登录IMAP服务器。

        Args:
            username: 用户名（通常是邮箱地址）。
            password: 授权密码。

        Returns:
            是否连接成功。
        """
        try:
            self._client = IMAP4_SSL(
                host=self._config.imap_host,
                port=self._config.imap_port,
            )
            await self._client.wait_hello_from_server()

            response = await self._client.login(username, password)
            if response.result != "OK":
                self._logger.warning("IMAP登录失败: %s", response)
                return False

            self._logger.info("IMAP连接成功: %s", username)
            return True
        except Exception as exc:
            self._logger.error("IMAP连接异常: %s", exc)
            return False

    async def disconnect(self) -> None:
        """断开IMAP连接。"""
        if self._client:
            try:
                await self._client.logout()
            except Exception as exc:
                self._logger.warning("IMAP断开连接异常: %s", exc)
            finally:
                self._client = None
                self._selected_mailbox = None

    async def list_mailboxes(self) -> List[MailboxInfo]:
        """获取邮箱文件夹列表。

        Returns:
            文件夹信息列表。
        """
        if not self._client:
            self._logger.error("IMAP未连接")
            return []

        response = await self._safe_list()
        if response.result != "OK":
            self._logger.warning("获取文件夹列表失败: %s", response)
            return []

        mailboxes = []
        for line in response.lines:
            if not isinstance(line, (bytes, bytearray)):
                continue
            info = self._parse_list_line(line.decode("utf-8", errors="ignore"))
            if info:
                mailboxes.append(info)

        return mailboxes

    async def get_mailbox_status(self, mailbox_name: str) -> MailboxStatus:
        """获取文件夹状态信息。

        Args:
            mailbox_name: 文件夹名称。

        Returns:
            文件夹状态。
        """
        if not self._client:
            self._logger.error("IMAP未连接")
            return MailboxStatus(None, None, None)

        response = await self._client.status(
            self._format_mailbox_name(mailbox_name),
            "(UIDVALIDITY UIDNEXT MESSAGES UNSEEN)",
        )
        if response.result != "OK":
            self._logger.warning("获取文件夹状态失败: %s", response)
            return MailboxStatus(None, None, None)

        line = ""
        for resp_line in response.lines:
            if isinstance(resp_line, (bytes, bytearray)):
                line = resp_line.decode("utf-8", errors="ignore")
                break

        uid_validity = self._parse_status_value(line, "UIDVALIDITY")
        uid_next = self._parse_status_value(line, "UIDNEXT")
        message_count = self._parse_status_value(line, "MESSAGES")

        return MailboxStatus(
            uid_validity=uid_validity,
            uid_next=uid_next,
            message_count=message_count,
        )

    async def select_mailbox(self, mailbox_name: str) -> bool:
        """选择文件夹用于后续操作。

        Args:
            mailbox_name: 文件夹名称。

        Returns:
            是否选择成功。
        """
        if not self._client:
            self._logger.error("IMAP未连接")
            return False

        response = await self._client.select(self._format_mailbox_name(mailbox_name))
        if response.result != "OK":
            self._logger.warning("选择文件夹失败: %s", response)
            return False

        self._selected_mailbox = mailbox_name
        return True

    async def fetch_uids_since(self, start_uid: int) -> List[int]:
        """获取指定UID之后的UID列表。

        Args:
            start_uid: 起始UID（包含）。

        Returns:
            UID列表。
        """
        if not self._client:
            self._logger.error("IMAP未连接")
            return []

        start_uid = max(start_uid, 1)
        # 注意：SEARCH UID <criteria> 返回的是SEQUENCE NUMBERS，不是UIDs！
        # 我们必须先获取这些sequence numbers，然后FETCH (UID)来获取真正的UID。
        response = await self._uid_command("SEARCH", None, "UID", f"{start_uid}:*")
        if response.result != "OK":
            self._logger.warning("UID搜索失败: %s", response)
            return []

        if not response.lines:
            return []

        line = response.lines[0]
        if isinstance(line, (bytes, bytearray)):
            line = line.decode("utf-8", errors="ignore")

        # 提取 Sequence Numbers
        seq_nums = [int(value) for value in str(line).split() if value.isdigit()]
        if not seq_nums:
            return []

        # 批量获取UID
        # 为了避免URL过长，应该分批处理，但这里假设差异不会太大
        # 使用逗号分隔Sequence Set
        seq_set = ",".join(map(str, seq_nums))

        fetched_response = await self._client.fetch(seq_set, "(UID)")
        if fetched_response.result != "OK":
            self._logger.warning("获取UID详情失败: %s", fetched_response)
            return []

        real_uids = []
        for line in fetched_response.lines:
            if isinstance(line, (bytes, bytearray)):
                line = line.decode("utf-8", errors="ignore")

            # 解析 FETCH 响应: * 118 FETCH (UID 146 ...)
            match = re.search(r"UID (\d+)", line)
            if match:
                real_uids.append(int(match.group(1)))

        return sorted(real_uids)

    async def fetch_emails_by_uid(self, uids: List[int]) -> List[FetchedEmail]:
        """按UID列表抓取邮件原始内容。

        Args:
            uids: UID列表。

        Returns:
            抓取到的邮件列表。
        """
        if not self._client:
            self._logger.error("IMAP未连接")
            return []

        emails: List[FetchedEmail] = []
        for uid in uids:
            fetched = await self._fetch_email(uid)
            if fetched:
                emails.append(fetched)
        return emails

    async def _fetch_email(self, uid: int) -> Optional[FetchedEmail]:
        """抓取单封邮件内容。

        Args:
            uid: 邮件UID。

        Returns:
            抓取到的邮件对象或None。
        """
        response = await self._uid_command(
            "FETCH",
            str(uid),
            "(UID FLAGS INTERNALDATE RFC822.SIZE BODY.PEEK[])",
        )
        if response.result != "OK":
            self._logger.warning("FETCH失败: uid=%s", uid)
            return None

        raw_email = ImapResponseParser.extract_literal_bytes(response.lines)
        if not raw_email:
            self._logger.warning("邮件内容为空: uid=%s", uid)
            return None

        flags, internal_date, size = ImapResponseParser.parse_flags_and_internal_date(
            response.lines
        )

        return FetchedEmail(
            uid=uid,
            flags=flags,
            internal_date=internal_date,
            size=size,
            raw_bytes=raw_email,
        )

    async def _safe_list(self):
        """兼容不同IMAP实现的LIST调用。"""
        try:
            return await self._client.list()
        except Exception:
            return await self._client.list('""', "*")

    async def _uid_command(self, command: str, *args):
        """执行UID命令，兼容部分客户端无UID方法的情况。"""
        command_upper = command.upper()
        if command_upper == "SEARCH":
            # aioimaplib的uid方法不支持SEARCH，改用SEARCH UID语法。
            return await self._client.search(*args)

        if hasattr(self._client, "uid"):
            return await self._client.uid(command, *args)

        if command_upper == "FETCH":
            return await self._client.fetch(*args)

        raise ValueError(f"不支持的UID命令: {command}")

    def _parse_list_line(self, line: str) -> Optional[MailboxInfo]:
        """解析LIST响应行。

        Args:
            line: LIST响应行文本。

        Returns:
            文件夹信息或None。
        """
        if not line:
            return None

        match = re.match(r"\((?P<attrs>[^)]*)\)\s+(?P<rest>.*)", line)
        if not match:
            return None

        attrs = match.group("attrs").strip()
        rest = match.group("rest").strip()

        delimiter = None
        name = rest
        if rest.startswith('"'):
            parts = rest.split('"')
            if len(parts) >= 3:
                delimiter = parts[1]
                name = '"'.join(parts[2:]).strip()
        elif " " in rest:
            delimiter, name = rest.split(" ", 1)

        name = name.strip().strip('"')
        if not name:
            return None

        return MailboxInfo(name=name, delimiter=delimiter, attributes=attrs or None)

    def _parse_status_value(self, line: str, key: str) -> Optional[int]:
        """从STATUS响应中解析数值。

        Args:
            line: STATUS响应文本。
            key: 字段名称。

        Returns:
            数值或None。
        """
        if not line:
            return None
        match = re.search(rf"{key} (\d+)", line)
        return int(match.group(1)) if match else None

    def _format_mailbox_name(self, mailbox_name: str) -> str:
        """格式化文件夹名称，处理包含空格的情况。

        Args:
            mailbox_name: 原始文件夹名称。

        Returns:
            格式化后的文件夹名称。
        """
        if not mailbox_name:
            return mailbox_name

        if mailbox_name.startswith('"') and mailbox_name.endswith('"'):
            return mailbox_name

        if " " in mailbox_name or '"' in mailbox_name:
            escaped = mailbox_name.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'

        return mailbox_name

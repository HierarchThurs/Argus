"""异步IMAP客户端模块。

基于aioimaplib封装的异步IMAP邮件客户端。
"""

import logging
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from aioimaplib import IMAP4_SSL

from app.utils.imap.imap_config import ImapConfig


@dataclass
class EmailMessage:
    """邮件消息数据类。

    Attributes:
        message_id: 邮件唯一标识。
        subject: 邮件主题。
        sender: 发件人。
        recipients: 收件人列表。
        content_text: 纯文本内容。
        content_html: HTML内容。
        received_at: 接收时间。
    """

    message_id: str
    subject: Optional[str]
    sender: str
    recipients: List[str]
    content_text: Optional[str]
    content_html: Optional[str]
    received_at: Optional[datetime]


class ImapClient:
    """异步IMAP客户端类。

    提供连接、登录、获取邮件等功能。
    """

    def __init__(self, config: ImapConfig, logger: Optional[logging.Logger] = None):
        """初始化IMAP客户端。

        Args:
            config: IMAP配置。
            logger: 日志记录器。
        """
        self._config = config
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._client: Optional[IMAP4_SSL] = None

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

        except Exception as e:
            self._logger.error("IMAP连接异常: %s", e)
            return False

    async def disconnect(self) -> None:
        """断开IMAP连接。"""
        if self._client:
            try:
                await self._client.logout()
            except Exception as e:
                self._logger.warning("IMAP断开连接异常: %s", e)
            finally:
                self._client = None

    async def fetch_recent_emails(self, count: int = 20) -> List[EmailMessage]:
        """获取最近的邮件。

        Args:
            count: 获取邮件数量。

        Returns:
            邮件消息列表。
        """
        if not self._client:
            self._logger.error("IMAP未连接")
            return []

        emails: List[EmailMessage] = []

        try:
            # 选择收件箱
            await self._client.select("INBOX")

            # 搜索所有邮件
            response = await self._client.search("ALL")
            if response.result != "OK":
                self._logger.warning("搜索邮件失败: %s", response)
                return []

            # 获取邮件ID列表
            message_ids = response.lines[0].decode().split()
            if not message_ids:
                return []

            # 取最近的count封邮件
            recent_ids = message_ids[-count:]

            # 逐个获取邮件
            for msg_id in reversed(recent_ids):
                try:
                    email_msg = await self._fetch_email(msg_id)
                    if email_msg:
                        emails.append(email_msg)
                except Exception as e:
                    self._logger.warning("获取邮件失败 id=%s: %s", msg_id, e)

        except Exception as e:
            self._logger.error("获取邮件列表异常: %s", e)

        return emails

    async def _fetch_email(self, msg_id: str) -> Optional[EmailMessage]:
        """获取单封邮件详情。

        Args:
            msg_id: IMAP邮件ID。

        Returns:
            邮件消息对象。
        """
        response = await self._client.fetch(msg_id, "(RFC822)")
        if response.result != "OK":
            self._logger.warning(
                "FETCH失败: msg_id=%s, result=%s", msg_id, response.result
            )
            return None

        # 调试: 输出 response.lines 的结构
        self._logger.debug(
            "FETCH response for msg_id=%s: lines_count=%d, lines_types=%s",
            msg_id,
            len(response.lines),
            [type(line).__name__ for line in response.lines],
        )
        for i, line in enumerate(response.lines):
            if isinstance(line, bytes):
                self._logger.debug(
                    "  line[%d] bytes len=%d, preview=%s",
                    i,
                    len(line),
                    line[:100] if len(line) > 100 else line,
                )
            else:
                self._logger.debug("  line[%d] = %s", i, repr(line)[:200])

        # 解析邮件内容 - aioimaplib 返回的格式:
        # response.lines 是一个列表，其中包含IMAP响应
        # 格式: b'* 102 FETCH (RFC822 {7950}\r\nReceived: from qq.com...'
        # 需要跳过IMAP协议头部分 "* 102 FETCH (RFC822 {7950}\r\n"
        raw_email = None

        # 合并所有 bytes 和 bytearray 类型的数据
        # aioimaplib 将 literal data 存储为 bytearray，普通行存储为 bytes
        all_bytes_list = []
        for line in response.lines:
            if isinstance(line, (bytes, bytearray)):
                all_bytes_list.append(
                    bytes(line) if isinstance(line, bytearray) else line
                )
        all_bytes = b"".join(all_bytes_list)

        if len(all_bytes) < 100:
            self._logger.warning(
                "邮件内容过短: msg_id=%s, length=%d", msg_id, len(all_bytes)
            )
            return None

        # 查找邮件开始的位置
        # IMAP响应头格式: * <num> FETCH (RFC822 {<size>}\r\n
        # 邮件内容通常以 "Received:" 开头

        # 方法1: 查找 ")\r\n" 后的 "Received:" (IMAP响应头结束标记)
        fetch_end = all_bytes.find(b"}\r\n")
        if fetch_end != -1:
            raw_email = all_bytes[fetch_end + 3 :]  # 跳过 "}\r\n"

        # 方法2: 如果方法1失败，直接查找常见邮件头
        if not raw_email or len(raw_email) < 50:
            for header in [b"Received:", b"From:", b"Date:", b"Message-ID:", b"X-"]:
                idx = all_bytes.find(header)
                if idx != -1:
                    raw_email = all_bytes[idx:]
                    break

        # 方法3: 查找第一个 \r\n 后的内容（跳过第一行IMAP响应头）
        if not raw_email or len(raw_email) < 50:
            first_crlf = all_bytes.find(b"\r\n")
            if first_crlf != -1 and first_crlf < 150:
                raw_email = all_bytes[first_crlf + 2 :]

        if not raw_email or len(raw_email) < 50:
            self._logger.warning(
                "无法解析邮件原始内容: msg_id=%s, total_bytes=%d",
                msg_id,
                len(all_bytes),
            )
            return None

        return self._parse_email(raw_email)

    def _parse_email(self, raw_email: bytes) -> Optional[EmailMessage]:
        """解析原始邮件。

        Args:
            raw_email: 原始邮件字节数据。

        Returns:
            解析后的邮件消息对象。
        """
        try:
            msg = email.message_from_bytes(raw_email)

            # 解析Message-ID
            message_id = msg.get("Message-ID", f"unknown-{datetime.now().timestamp()}")

            # 解析主题
            subject = self._decode_header(msg.get("Subject", ""))

            # 解析发件人
            sender = self._decode_header(msg.get("From", ""))

            # 解析收件人
            to_header = msg.get("To", "")
            recipients = [
                self._decode_header(addr.strip())
                for addr in to_header.split(",")
                if addr.strip()
            ]

            # 解析时间
            date_str = msg.get("Date")
            received_at = None
            if date_str:
                try:
                    received_at = parsedate_to_datetime(date_str)
                except Exception:
                    pass

            # 解析内容
            content_text = None
            content_html = None

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain" and not content_text:
                        payload = part.get_payload(decode=True)
                        if payload:
                            content_text = self._decode_content(payload, part)
                    elif content_type == "text/html" and not content_html:
                        payload = part.get_payload(decode=True)
                        if payload:
                            content_html = self._decode_content(payload, part)
            else:
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True)
                if payload:
                    content = self._decode_content(payload, msg)
                    if content_type == "text/html":
                        content_html = content
                    else:
                        content_text = content

            return EmailMessage(
                message_id=message_id,
                subject=subject,
                sender=sender,
                recipients=recipients,
                content_text=content_text,
                content_html=content_html,
                received_at=received_at,
            )

        except Exception as e:
            self._logger.error("解析邮件失败: %s", e)
            return None

    def _decode_header(self, header_value: str) -> str:
        """解码邮件头。

        Args:
            header_value: 邮件头原始值。

        Returns:
            解码后的字符串。
        """
        if not header_value:
            return ""

        try:
            decoded_parts = decode_header(header_value)
            result = []
            for content, charset in decoded_parts:
                if isinstance(content, bytes):
                    result.append(content.decode(charset or "utf-8", errors="replace"))
                else:
                    result.append(content)
            return "".join(result)
        except Exception:
            return str(header_value)

    def _decode_content(self, payload: bytes, part) -> str:
        """解码邮件内容。

        Args:
            payload: 邮件内容字节数据。
            part: 邮件部分对象。

        Returns:
            解码后的字符串。
        """
        charset = part.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except Exception:
            return payload.decode("utf-8", errors="replace")

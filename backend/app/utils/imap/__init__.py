"""IMAP工具模块。"""

from app.utils.imap.imap_config import (
    ImapConfig,
    ImapConfigFactory,
    QQ_IMAP_CONFIG,
    NETEASE_IMAP_CONFIG,
    DEFAULT_SCHOOL_CONFIG,
)
from app.utils.imap.imap_client import ImapClient, EmailMessage
from app.utils.imap.smtp_client import SmtpClient

__all__ = [
    "ImapConfig",
    "ImapConfigFactory",
    "QQ_IMAP_CONFIG",
    "NETEASE_IMAP_CONFIG",
    "DEFAULT_SCHOOL_CONFIG",
    "ImapClient",
    "EmailMessage",
    "SmtpClient",
]

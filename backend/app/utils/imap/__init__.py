"""IMAP工具模块。"""

from app.utils.imap.imap_config import (
    ImapConfig,
    ImapConfigFactory,
    QQ_IMAP_CONFIG,
    NETEASE_IMAP_CONFIG,
    DEFAULT_SCHOOL_CONFIG,
)
try:
    from app.utils.imap.imap_client import ImapClient
except ModuleNotFoundError:
    # 在测试环境中可缺少IMAP依赖，避免导入失败影响其他模块。
    ImapClient = None

from app.utils.imap.imap_models import (
    MailboxInfo,
    MailboxStatus,
    FetchedEmail,
    ParsedEmail,
)
from app.utils.imap.email_parser import EmailParser
try:
    from app.utils.imap.smtp_client import SmtpClient
except ModuleNotFoundError:
    # 测试环境下缺少SMTP依赖时降级处理。
    SmtpClient = None

__all__ = [
    "ImapConfig",
    "ImapConfigFactory",
    "QQ_IMAP_CONFIG",
    "NETEASE_IMAP_CONFIG",
    "DEFAULT_SCHOOL_CONFIG",
    "ImapClient",
    "MailboxInfo",
    "MailboxStatus",
    "FetchedEmail",
    "ParsedEmail",
    "EmailParser",
    "SmtpClient",
]

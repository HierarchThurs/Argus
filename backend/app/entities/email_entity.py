"""邮件实体定义。"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PhishingLevel(str, Enum):
    """钓鱼邮件危险等级枚举。

    Attributes:
        NORMAL: 正常邮件。
        SUSPICIOUS: 疑似钓鱼邮件。
        HIGH_RISK: 高危钓鱼邮件。
    """

    NORMAL = "NORMAL"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"


class EmailEntity(Base):
    """邮件实体ORM模型。

    映射到数据库的emails表，存储邮件内容和钓鱼检测结果。

    Attributes:
        id: 主键ID。
        email_account_id: 关联的邮箱账户ID。
        message_id: 邮件唯一标识（IMAP Message-ID）。
        subject: 邮件主题。
        sender: 发件人。
        recipients: 收件人（JSON格式）。
        content_text: 纯文本内容。
        content_html: HTML内容。
        received_at: 接收时间。
        is_read: 是否已读。
        is_sent: 是否为发送的邮件。
        phishing_level: 钓鱼危险等级。
        phishing_score: 钓鱼评分（0-1）。
        phishing_reason: 钓鱼判定原因。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="主键ID"
    )
    email_account_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("email_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="邮箱账户ID",
    )
    message_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, comment="邮件唯一标识"
    )
    subject: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="邮件主题"
    )
    sender: Mapped[str] = mapped_column(String(200), nullable=False, comment="发件人")
    recipients: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="收件人（JSON格式）"
    )
    content_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="纯文本内容"
    )
    content_html: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="HTML内容"
    )
    received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True, comment="接收时间"
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已读")
    is_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否为发送的邮件"
    )
    phishing_level: Mapped[PhishingLevel] = mapped_column(
        SQLEnum(PhishingLevel),
        default=PhishingLevel.NORMAL,
        comment="钓鱼危险等级",
    )
    phishing_score: Mapped[float] = mapped_column(default=0.0, comment="钓鱼评分")
    phishing_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="钓鱼判定原因"
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关联关系
    email_account = relationship("EmailAccountEntity", backref="emails")

    def __repr__(self) -> str:
        """返回邮件实体的字符串表示。

        Returns:
            邮件实体的调试字符串。
        """
        return f"<EmailEntity(id={self.id}, subject={self.subject})>"

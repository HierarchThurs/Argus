"""邮件特征提取器模块。

提供邮件特征提取功能，用于钓鱼检测机器学习模型的输入。
支持URL特征、文本特征、发件人特征等多维度提取。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


@dataclass
class UrlFeatures:
    """URL特征数据类。

    Attributes:
        total_count: URL总数。
        unique_domains: 唯一域名列表。
        suspicious_count: 可疑URL数量。
        has_ip_url: 是否包含IP地址URL。
        has_shortened_url: 是否包含短链接。
        domain_mismatches: 域名不匹配数量（显示文本与实际URL不同）。
    """

    total_count: int = 0
    unique_domains: List[str] = field(default_factory=list)
    suspicious_count: int = 0
    has_ip_url: bool = False
    has_shortened_url: bool = False
    domain_mismatches: int = 0


@dataclass
class TextFeatures:
    """文本特征数据类。

    Attributes:
        word_count: 单词数量。
        char_count: 字符数量。
        has_urgency_words: 是否包含紧急词汇。
        has_threat_words: 是否包含威胁词汇。
        has_reward_words: 是否包含奖励词汇。
        html_form_count: HTML表单数量。
        external_resource_count: 外部资源引用数量。
    """

    word_count: int = 0
    char_count: int = 0
    has_urgency_words: bool = False
    has_threat_words: bool = False
    has_reward_words: bool = False
    html_form_count: int = 0
    external_resource_count: int = 0


@dataclass
class SenderFeatures:
    """发件人特征数据类。

    Attributes:
        domain: 发件人域名。
        is_free_email: 是否为免费邮箱。
        domain_age_days: 域名年龄（预留）。
        has_display_name_mismatch: 显示名与地址是否不匹配。
    """

    domain: str = ""
    is_free_email: bool = False
    domain_age_days: Optional[int] = None
    has_display_name_mismatch: bool = False


@dataclass
class EmailFeatures:
    """邮件完整特征数据类。

    Attributes:
        url_features: URL特征。
        text_features: 文本特征。
        sender_features: 发件人特征。
        raw_features: 原始特征向量（供ML模型使用）。
    """

    url_features: UrlFeatures = field(default_factory=UrlFeatures)
    text_features: TextFeatures = field(default_factory=TextFeatures)
    sender_features: SenderFeatures = field(default_factory=SenderFeatures)
    raw_features: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。

        Returns:
            特征字典。
        """
        return {
            "url_features": {
                "total_count": self.url_features.total_count,
                "unique_domains": self.url_features.unique_domains,
                "suspicious_count": self.url_features.suspicious_count,
                "has_ip_url": self.url_features.has_ip_url,
                "has_shortened_url": self.url_features.has_shortened_url,
                "domain_mismatches": self.url_features.domain_mismatches,
            },
            "text_features": {
                "word_count": self.text_features.word_count,
                "char_count": self.text_features.char_count,
                "has_urgency_words": self.text_features.has_urgency_words,
                "has_threat_words": self.text_features.has_threat_words,
                "has_reward_words": self.text_features.has_reward_words,
                "html_form_count": self.text_features.html_form_count,
                "external_resource_count": self.text_features.external_resource_count,
            },
            "sender_features": {
                "domain": self.sender_features.domain,
                "is_free_email": self.sender_features.is_free_email,
                "has_display_name_mismatch": (
                    self.sender_features.has_display_name_mismatch
                ),
            },
        }


class FeatureExtractor:
    """邮件特征提取器。

    从邮件内容中提取多维度特征，供钓鱼检测模型使用。
    """

    # 常见短链接服务域名
    SHORTENED_URL_DOMAINS = frozenset([
        "bit.ly", "t.co", "goo.gl", "tinyurl.com", "ow.ly",
        "is.gd", "buff.ly", "adf.ly", "j.mp", "su.pr",
    ])

    # 常见免费邮箱域名
    FREE_EMAIL_DOMAINS = frozenset([
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
        "qq.com", "163.com", "126.com", "sina.com", "sohu.com",
    ])

    # 紧急词汇（中英文）
    URGENCY_WORDS = frozenset([
        "urgent", "immediately", "asap", "expire", "deadline",
        "紧急", "立即", "马上", "限时", "过期", "截止",
    ])

    # 威胁词汇（中英文）
    THREAT_WORDS = frozenset([
        "suspend", "terminate", "block", "freeze", "unauthorized",
        "暂停", "终止", "封禁", "冻结", "异常", "违规",
    ])

    # 奖励词汇（中英文）
    REWARD_WORDS = frozenset([
        "winner", "prize", "reward", "bonus", "free", "gift",
        "中奖", "奖励", "免费", "赠送", "红包", "优惠",
    ])

    # IP地址URL正则
    IP_URL_PATTERN = re.compile(
        r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    )

    # URL提取正则
    URL_PATTERN = re.compile(
        r"https?://[^\s<>\"']+",
        re.IGNORECASE
    )

    # HTML链接提取正则
    HTML_LINK_PATTERN = re.compile(
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>',
        re.IGNORECASE
    )

    # HTML表单正则
    HTML_FORM_PATTERN = re.compile(
        r"<form[^>]*>",
        re.IGNORECASE
    )

    # 外部资源正则
    EXTERNAL_RESOURCE_PATTERN = re.compile(
        r'(src|href)=["\']https?://[^"\']+["\']',
        re.IGNORECASE
    )

    def extract(
        self,
        subject: Optional[str],
        sender: str,
        content_text: Optional[str],
        content_html: Optional[str],
    ) -> EmailFeatures:
        """提取邮件特征。

        Args:
            subject: 邮件主题。
            sender: 发件人地址。
            content_text: 纯文本内容。
            content_html: HTML内容。

        Returns:
            邮件特征数据。
        """
        features = EmailFeatures()

        # 提取URL特征
        features.url_features = self._extract_url_features(
            content_text, content_html
        )

        # 提取文本特征
        features.text_features = self._extract_text_features(
            subject, content_text, content_html
        )

        # 提取发件人特征
        features.sender_features = self._extract_sender_features(sender)

        # 生成原始特征向量
        features.raw_features = self._generate_raw_features(features)

        return features

    def _extract_url_features(
        self,
        content_text: Optional[str],
        content_html: Optional[str],
    ) -> UrlFeatures:
        """提取URL特征。

        Args:
            content_text: 纯文本内容。
            content_html: HTML内容。

        Returns:
            URL特征数据。
        """
        features = UrlFeatures()
        all_urls = []
        domains = set()

        # 从HTML中提取链接
        if content_html:
            for match in self.HTML_LINK_PATTERN.finditer(content_html):
                href = match.group(1)
                display_text = match.group(2).strip()
                all_urls.append(href)

                # 检测域名不匹配
                if display_text and display_text.startswith("http"):
                    href_domain = self._get_domain(href)
                    display_domain = self._get_domain(display_text)
                    if href_domain and display_domain:
                        if href_domain != display_domain:
                            features.domain_mismatches += 1

        # 从文本中提取URL
        text_content = content_text or ""
        for match in self.URL_PATTERN.finditer(text_content):
            all_urls.append(match.group())

        # 统计URL特征
        features.total_count = len(all_urls)
        for url in all_urls:
            domain = self._get_domain(url)
            if domain:
                domains.add(domain)

                # 检测短链接
                if domain.lower() in self.SHORTENED_URL_DOMAINS:
                    features.has_shortened_url = True
                    features.suspicious_count += 1

            # 检测IP地址URL
            if self.IP_URL_PATTERN.match(url):
                features.has_ip_url = True
                features.suspicious_count += 1

        features.unique_domains = list(domains)
        return features

    def _extract_text_features(
        self,
        subject: Optional[str],
        content_text: Optional[str],
        content_html: Optional[str],
    ) -> TextFeatures:
        """提取文本特征。

        Args:
            subject: 邮件主题。
            content_text: 纯文本内容。
            content_html: HTML内容。

        Returns:
            文本特征数据。
        """
        features = TextFeatures()
        combined_text = f"{subject or ''} {content_text or ''}".lower()

        # 基础统计
        features.word_count = len(combined_text.split())
        features.char_count = len(combined_text)

        # 关键词检测
        features.has_urgency_words = any(
            word in combined_text for word in self.URGENCY_WORDS
        )
        features.has_threat_words = any(
            word in combined_text for word in self.THREAT_WORDS
        )
        features.has_reward_words = any(
            word in combined_text for word in self.REWARD_WORDS
        )

        # HTML特征
        if content_html:
            features.html_form_count = len(
                self.HTML_FORM_PATTERN.findall(content_html)
            )
            features.external_resource_count = len(
                self.EXTERNAL_RESOURCE_PATTERN.findall(content_html)
            )

        return features

    def _extract_sender_features(self, sender: str) -> SenderFeatures:
        """提取发件人特征。

        Args:
            sender: 发件人地址。

        Returns:
            发件人特征数据。
        """
        features = SenderFeatures()

        # 提取域名
        if "@" in sender:
            parts = sender.split("@")
            if len(parts) == 2:
                features.domain = parts[1].lower()
                features.is_free_email = (
                    features.domain in self.FREE_EMAIL_DOMAINS
                )

        return features

    def _get_domain(self, url: str) -> Optional[str]:
        """从URL中提取域名。

        Args:
            url: URL字符串。

        Returns:
            域名字符串或None。
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower() if parsed.netloc else None
        except Exception:
            return None

    def _generate_raw_features(self, features: EmailFeatures) -> List[float]:
        """生成原始特征向量。

        将结构化特征转换为数值向量，供ML模型使用。

        Args:
            features: 邮件特征数据。

        Returns:
            特征向量。
        """
        return [
            # URL特征
            float(features.url_features.total_count),
            float(len(features.url_features.unique_domains)),
            float(features.url_features.suspicious_count),
            float(features.url_features.has_ip_url),
            float(features.url_features.has_shortened_url),
            float(features.url_features.domain_mismatches),
            # 文本特征
            float(features.text_features.word_count),
            float(features.text_features.char_count),
            float(features.text_features.has_urgency_words),
            float(features.text_features.has_threat_words),
            float(features.text_features.has_reward_words),
            float(features.text_features.html_form_count),
            float(features.text_features.external_resource_count),
            # 发件人特征
            float(features.sender_features.is_free_email),
            float(features.sender_features.has_display_name_mismatch),
        ]

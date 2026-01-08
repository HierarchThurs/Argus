"""模拟钓鱼检测器模块。

用于开发阶段测试的模拟实现，后续替换为真实的机器学习模型。
"""

import random
import re
import logging
from typing import Any, Dict, List, Optional

from app.utils.phishing.phishing_detector_interface import (
    PhishingDetectorInterface,
    PhishingResult,
    PhishingLevel,
)
from app.utils.phishing.score_level_mapper import ScoreLevelMapper


class MockPhishingDetector(PhishingDetectorInterface):
    """模拟钓鱼检测器。

    使用简单规则和随机因素模拟钓鱼检测，用于开发测试。
    """

    # 可疑关键词列表
    SUSPICIOUS_KEYWORDS = [
        "紧急",
        "立即",
        "账号异常",
        "密码过期",
        "验证身份",
        "urgent",
        "immediately",
        "verify",
        "suspended",
        "confirm",
        "点击链接",
        "领取奖励",
        "中奖",
        "恭喜",
        "免费",
    ]

    # 高危关键词列表
    HIGH_RISK_KEYWORDS = [
        "银行卡",
        "支付密码",
        "转账",
        "汇款",
        "身份证",
        "bank",
        "password",
        "transfer",
        "ssn",
        "credit card",
    ]

    # 可疑发件人域名
    SUSPICIOUS_DOMAINS = [
        "mail.ru",
        "outlook.com",
        "163.com",
        "qq.com",
    ]

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        score_mapper: Optional[ScoreLevelMapper] = None,
    ):
        """初始化模拟检测器。

        Args:
            logger: 日志记录器。
            score_mapper: 置信度映射器。
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._score_mapper = score_mapper or ScoreLevelMapper()

    async def detect(
        self,
        subject: Optional[str],
        sender: str,
        content_text: Optional[str],
        content_html: Optional[str],
        headers: Optional[Dict[str, str]] = None,
    ) -> PhishingResult:
        """检测邮件是否为钓鱼邮件。

        Args:
            subject: 邮件主题。
            sender: 发件人。
            content_text: 纯文本内容。
            content_html: HTML内容。
            headers: 邮件头信息（预留）。

        Returns:
            钓鱼检测结果。
        """
        score = 0.0
        reasons = []

        # 合并内容进行分析
        full_text = " ".join(filter(None, [subject, content_text, content_html]))
        full_text_lower = full_text.lower()

        # 检查高危关键词
        high_risk_count = sum(
            1
            for keyword in self.HIGH_RISK_KEYWORDS
            if keyword.lower() in full_text_lower
        )
        if high_risk_count > 0:
            score += min(high_risk_count * 0.25, 0.5)
            reasons.append(f"检测到{high_risk_count}个高危关键词")

        # 检查可疑关键词
        suspicious_count = sum(
            1
            for keyword in self.SUSPICIOUS_KEYWORDS
            if keyword.lower() in full_text_lower
        )
        if suspicious_count > 0:
            score += min(suspicious_count * 0.1, 0.3)
            reasons.append(f"检测到{suspicious_count}个可疑关键词")

        # 检查链接数量（HTML中的链接）
        if content_html:
            link_count = len(re.findall(r'href=["\'"]http', content_html, re.I))
            if link_count > 5:
                score += 0.15
                reasons.append(f"邮件包含{link_count}个外部链接")

        # 检查发件人域名
        sender_lower = sender.lower()
        for domain in self.SUSPICIOUS_DOMAINS:
            if domain in sender_lower:
                score += 0.1
                reasons.append(f"来自可疑域名: {domain}")
                break

        # 添加随机因素（模拟ML模型的不确定性）
        random_factor = random.uniform(-0.1, 0.1)
        score = max(0.0, min(1.0, score + random_factor))

        # 确定危险等级
        level = self._score_mapper.get_level(score)

        reason = "; ".join(reasons) if reasons else "未检测到明显威胁特征"

        self._logger.debug(
            "钓鱼检测完成: level=%s, score=%.2f, reason=%s", level.value, score, reason
        )

        return PhishingResult(
            level=level,
            score=round(score, 4),
            reason=reason,
        )

    async def batch_detect(
        self,
        emails: List[Dict[str, Any]],
    ) -> List[PhishingResult]:
        """批量检测邮件。

        Args:
            emails: 邮件列表。

        Returns:
            钓鱼检测结果列表。
        """
        results = []
        for email_data in emails:
            result = await self.detect(
                subject=email_data.get("subject"),
                sender=email_data.get("sender", ""),
                content_text=email_data.get("content_text"),
                content_html=email_data.get("content_html"),
                headers=email_data.get("headers"),
            )
            results.append(result)
        return results

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息。

        Returns:
            模型信息字典。
        """
        return {
            "model_version": "mock-1.0.0",
            "model_path": None,
            "is_loaded": True,
            "mode": "mock_rule_based",
            "feature_count": 0,
        }

    async def reload_model(self) -> bool:
        """热加载模型（模拟实现）。

        Returns:
            始终返回True。
        """
        self._logger.info("模拟检测器无需重新加载模型")
        return True

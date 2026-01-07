"""机器学习钓鱼检测器模块。

提供基于机器学习的钓鱼邮件检测功能。
当前为模板实现，预留模型加载接口供后续训练模型对接。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils.phishing.feature_extractor import EmailFeatures, FeatureExtractor
from app.utils.phishing.phishing_detector_interface import (
    PhishingDetectorInterface,
    PhishingLevel,
    PhishingResult,
)


class MLPhishingDetector(PhishingDetectorInterface):
    """基于机器学习的钓鱼检测器。

    该类实现了钓鱼检测接口，使用机器学习模型进行检测。
    当前版本为模板实现，使用规则引擎模拟ML行为。
    后续可替换为真实的sklearn/pytorch模型。

    Attributes:
        _feature_extractor: 特征提取器实例。
        _model: 机器学习模型（预留）。
        _model_path: 模型文件路径。
        _model_version: 模型版本号。
        _logger: 日志记录器。
    """

    # 默认模型路径
    DEFAULT_MODEL_PATH = Path(__file__).parent / "models" / "phishing_model.pkl"

    def __init__(
        self,
        model_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """初始化ML钓鱼检测器。

        Args:
            model_path: 模型文件路径，None则使用默认路径。
            logger: 日志记录器。
        """
        self._feature_extractor = FeatureExtractor()
        self._model: Optional[Any] = None
        self._model_path = model_path or self.DEFAULT_MODEL_PATH
        self._model_version = "1.0.0-template"
        self._logger = logger or logging.getLogger(__name__)
        self._is_model_loaded = False

        # 尝试加载模型
        self._try_load_model()

    def _try_load_model(self) -> None:
        """尝试加载机器学习模型。

        如果模型文件存在则加载，否则使用规则引擎模式。
        """
        if self._model_path.exists():
            try:
                # TODO: 实现真实模型加载
                # import joblib
                # self._model = joblib.load(self._model_path)
                self._logger.info(
                    "模型文件存在，准备加载: %s", self._model_path
                )
                self._is_model_loaded = False  # 暂未实现
            except Exception as e:
                self._logger.warning("模型加载失败: %s", str(e))
                self._is_model_loaded = False
        else:
            self._logger.info(
                "模型文件不存在，使用规则引擎模式: %s", self._model_path
            )

    async def detect(
        self,
        subject: Optional[str],
        sender: str,
        content_text: Optional[str],
        content_html: Optional[str],
        headers: Optional[Dict[str, str]] = None,
    ) -> PhishingResult:
        """检测单封邮件是否为钓鱼邮件。

        Args:
            subject: 邮件主题。
            sender: 发件人地址。
            content_text: 纯文本内容。
            content_html: HTML内容。
            headers: 邮件头信息（可选）。

        Returns:
            钓鱼检测结果。
        """
        # 提取特征
        features = self._feature_extractor.extract(
            subject=subject,
            sender=sender,
            content_text=content_text,
            content_html=content_html,
        )

        # 使用模型或规则进行检测
        if self._is_model_loaded and self._model is not None:
            return await self._predict_with_model(features)
        else:
            return self._predict_with_rules(features)

    async def batch_detect(
        self,
        emails: List[Dict[str, Any]],
    ) -> List[PhishingResult]:
        """批量检测邮件。

        Args:
            emails: 邮件列表，每项包含subject、sender、content_text、content_html。

        Returns:
            钓鱼检测结果列表。
        """
        results = []
        for email in emails:
            result = await self.detect(
                subject=email.get("subject"),
                sender=email.get("sender", ""),
                content_text=email.get("content_text"),
                content_html=email.get("content_html"),
                headers=email.get("headers"),
            )
            results.append(result)
        return results

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息。

        Returns:
            模型信息字典。
        """
        return {
            "model_version": self._model_version,
            "model_path": str(self._model_path),
            "is_loaded": self._is_model_loaded,
            "mode": "ml" if self._is_model_loaded else "rule_based",
            "feature_count": 15,  # 特征向量维度
        }

    async def reload_model(self) -> bool:
        """热加载模型（无需重启服务）。

        Returns:
            加载是否成功。
        """
        self._logger.info("正在重新加载模型...")
        try:
            self._try_load_model()
            self._logger.info("模型重新加载完成")
            return True
        except Exception as e:
            self._logger.error("模型重新加载失败: %s", str(e))
            return False

    async def _predict_with_model(
        self,
        features: EmailFeatures,
    ) -> PhishingResult:
        """使用机器学习模型进行预测。

        Args:
            features: 邮件特征。

        Returns:
            钓鱼检测结果。
        """
        # TODO: 实现真实模型预测
        # raw_features = features.raw_features
        # prediction = self._model.predict_proba([raw_features])[0]
        # score = prediction[1]  # 钓鱼概率

        # 占位返回
        return self._predict_with_rules(features)

    def _predict_with_rules(
        self,
        features: EmailFeatures,
    ) -> PhishingResult:
        """使用规则引擎进行预测（ML模型未加载时的后备方案）。

        基于提取的特征使用加权评分进行判断。

        Args:
            features: 邮件特征。

        Returns:
            钓鱼检测结果。
        """
        score = 0.0
        reasons = []

        # URL特征评分
        url = features.url_features
        if url.has_ip_url:
            score += 0.3
            reasons.append("包含IP地址链接")
        if url.has_shortened_url:
            score += 0.15
            reasons.append("包含短链接")
        if url.domain_mismatches > 0:
            score += 0.25
            reasons.append("链接显示与实际不符")
        if url.suspicious_count > 2:
            score += 0.1
            reasons.append("可疑链接数量较多")

        # 文本特征评分
        text = features.text_features
        if text.has_urgency_words:
            score += 0.1
            reasons.append("包含紧急词汇")
        if text.has_threat_words:
            score += 0.15
            reasons.append("包含威胁词汇")
        if text.has_reward_words:
            score += 0.1
            reasons.append("包含奖励诱导词汇")
        if text.html_form_count > 0:
            score += 0.2
            reasons.append("包含表单提交")

        # 发件人特征评分
        sender = features.sender_features
        if sender.has_display_name_mismatch:
            score += 0.15
            reasons.append("发件人显示名与地址不匹配")

        # 限制分数范围
        score = min(score, 1.0)

        # 确定危险等级
        if score >= 0.6:
            level = PhishingLevel.HIGH_RISK
        elif score >= 0.3:
            level = PhishingLevel.SUSPICIOUS
        else:
            level = PhishingLevel.NORMAL

        # 生成原因说明
        if not reasons:
            reason = "未检测到明显钓鱼特征"
        else:
            reason = "；".join(reasons)

        return PhishingResult(
            level=level,
            score=score,
            reason=reason,
        )

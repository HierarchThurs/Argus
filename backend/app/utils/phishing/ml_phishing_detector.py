"""基于机器学习的钓鱼邮件检测器模块。

使用TF-IDF特征提取和Keras神经网络进行钓鱼邮件检测。
基于phishingDP项目的核心检测机制移植而来。

模型架构：
    - 输入层：5000维TF-IDF特征
    - 隐藏层1：128神经元 + ReLU + Dropout(0.2)
    - 隐藏层2：64神经元 + ReLU
    - 输出层：1神经元 + Sigmoid（输出钓鱼概率）
"""

from __future__ import annotations

import logging
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils.phishing.phishing_detector_interface import (
    PhishingDetectorInterface,
    PhishingResult,
    PhishingLevel,
)
from app.utils.phishing.ml_trainer import MLPhishingTrainer, MLTrainingConfig
from app.utils.phishing.score_level_mapper import ScoreLevelMapper, ScoreThresholds

# 基础目录（backend/app）
APP_BASE_DIR = Path(__file__).resolve().parents[2]

# 延迟导入ML依赖，避免未安装时启动失败
_ml_dependencies_checked = False
_ml_available = False
_load_model_func = None


def _check_ml_dependencies() -> bool:
    """检查ML依赖是否可用。"""
    global _ml_dependencies_checked, _ml_available, _load_model_func

    if _ml_dependencies_checked:
        return _ml_available

    _ml_dependencies_checked = True

    try:
        # 尝试导入所需依赖
        import numpy as np
        import pandas as pd
        from sklearn.feature_extraction.text import TfidfVectorizer
        from keras.models import load_model

        _ml_available = True
        _load_model_func = load_model
        return True
    except ImportError as e:
        _ml_available = False
        return False


class MLPhishingDetector(PhishingDetectorInterface):
    """基于机器学习的钓鱼邮件检测器。

    使用TF-IDF向量化和Keras神经网络模型进行检测。
    当ML依赖未安装时，自动降级到规则检测模式。
    """

    # 默认路径配置（基于 backend/app）
    DEFAULT_MODEL_PATH = APP_BASE_DIR / "utils/phishing/ml_models/phishing_model.h5"
    DEFAULT_DATASET_PATH = APP_BASE_DIR / "utils/phishing/datasets/spam_assassin.csv"
    DEFAULT_VECTORIZER_PATH = (
        APP_BASE_DIR / "utils/phishing/ml_models/tfidf_vectorizer.joblib"
    )
    DEFAULT_ARTIFACTS_DIR = (
        APP_BASE_DIR / "utils/phishing/ml_models/artifacts"
    )
    DEFAULT_MAX_FEATURES = 5000

    # 检测阈值
    HIGH_RISK_THRESHOLD = 0.8  # 高于此值判定为高危
    SUSPICIOUS_THRESHOLD = 0.6  # 高于此值判定为疑似

    def __init__(
        self,
        model_path: Optional[str | Path] = None,
        dataset_path: Optional[str | Path] = None,
        vectorizer_path: Optional[str | Path] = None,
        artifacts_dir: Optional[str | Path] = None,
        high_risk_threshold: float = HIGH_RISK_THRESHOLD,
        suspicious_threshold: float = SUSPICIOUS_THRESHOLD,
        auto_train_if_missing: bool = False,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """初始化ML检测器。

        Args:
            model_path: Keras模型文件路径（.h5格式）。
            dataset_path: 训练数据集路径（用于训练TF-IDF向量化器）。
            vectorizer_path: TF-IDF向量化器缓存路径。
            artifacts_dir: 训练产物输出目录。
            high_risk_threshold: 高危阈值。
            suspicious_threshold: 疑似阈值。
            auto_train_if_missing: 模型缺失时是否自动训练。
            logger: 日志记录器。
        """
        self._model_path = Path(model_path) if model_path else self.DEFAULT_MODEL_PATH
        self._dataset_path = (
            Path(dataset_path) if dataset_path else self.DEFAULT_DATASET_PATH
        )
        self._vectorizer_path = (
            Path(vectorizer_path) if vectorizer_path else self.DEFAULT_VECTORIZER_PATH
        )
        self._artifacts_dir = (
            Path(artifacts_dir) if artifacts_dir else self.DEFAULT_ARTIFACTS_DIR
        )
        self._high_risk_threshold = high_risk_threshold
        self._suspicious_threshold = suspicious_threshold
        self._auto_train_if_missing = auto_train_if_missing
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._score_mapper = ScoreLevelMapper(
            ScoreThresholds(
                suspicious_threshold=self._suspicious_threshold,
                high_risk_threshold=self._high_risk_threshold,
            )
        )

        self._model = None
        self._tfidf = None
        self._is_loaded = False
        self._load_error: Optional[str] = None

        # 尝试加载模型
        self._try_load_model()

    def _try_load_model(self) -> bool:
        """尝试加载模型和TF-IDF向量化器。

        Returns:
            是否加载成功。
        """
        if not _check_ml_dependencies():
            self._load_error = "ML依赖未安装（需要tensorflow, keras, pandas, scikit-learn）"
            self._logger.warning("ML检测器: %s", self._load_error)
            return False

        try:
            # 动态导入
            import pandas as pd
            from sklearn.feature_extraction.text import TfidfVectorizer

            # 检查模型文件，必要时自动训练
            if not self._model_path.exists():
                if not self._train_model_if_missing():
                    self._load_error = f"模型文件不存在: {self._model_path}"
                    self._logger.warning("ML检测器: %s", self._load_error)
                    return False

            self._logger.info("正在加载ML钓鱼检测模型...")

            # 加载Keras模型
            self._logger.info("加载Keras神经网络模型...")
            self._model = _load_model_func(str(self._model_path))
            self._logger.info("Keras模型加载成功")

            # 加载或训练TF-IDF向量化器
            if not self._load_vectorizer(pd, TfidfVectorizer):
                self._model = None
                return False

            self._is_loaded = True
            self._load_error = None
            self._logger.info("ML钓鱼检测模型初始化完成！")
            return True

        except Exception as e:
            self._load_error = f"模型加载失败: {str(e)}"
            self._logger.error("ML检测器: %s", self._load_error, exc_info=True)
            return False

    def _load_vectorizer(self, pd, TfidfVectorizer) -> bool:
        """加载或训练TF-IDF向量化器。

        Args:
            pd: pandas 模块引用。
            TfidfVectorizer: 向量化器类引用。

        Returns:
            是否加载成功。
        """
        if self._vectorizer_path and self._vectorizer_path.exists():
            try:
                import joblib

                self._tfidf = joblib.load(self._vectorizer_path)
                self._logger.info(
                    "TF-IDF向量化器加载成功: %s", self._vectorizer_path
                )
                return True
            except Exception as exc:
                self._logger.warning(
                    "TF-IDF向量化器加载失败，准备重新训练: %s", str(exc)
                )

        if not self._dataset_path.exists():
            self._load_error = f"数据集文件不存在: {self._dataset_path}"
            self._logger.warning("ML检测器: %s", self._load_error)
            return False

        self._logger.info("加载数据集并训练TF-IDF向量化器...")
        df = pd.read_csv(self._dataset_path)
        df["text"] = df["text"].fillna("")

        self._tfidf = TfidfVectorizer(
            stop_words="english",
            max_features=self.DEFAULT_MAX_FEATURES,
        )
        self._tfidf.fit(df["text"])
        self._logger.info(
            "TF-IDF向量化器训练完成，特征维度: %d",
            self.DEFAULT_MAX_FEATURES,
        )

        # 训练完成后缓存向量化器，提升后续加载速度
        try:
            import joblib

            self._vectorizer_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self._tfidf, self._vectorizer_path)
            self._logger.info(
                "TF-IDF向量化器已缓存: %s", self._vectorizer_path
            )
        except Exception as exc:
            self._logger.warning(
                "向量化器缓存失败（可忽略）: %s", str(exc)
            )

        return True

    def _train_model_if_missing(self) -> bool:
        """在模型缺失时自动训练。

        Returns:
            是否训练成功。
        """
        if not self._auto_train_if_missing:
            return False

        self._logger.warning("模型文件缺失，开始自动训练")
        try:
            trainer = MLPhishingTrainer(
                MLTrainingConfig(
                    dataset_path=self._dataset_path,
                    model_path=self._model_path,
                    artifacts_dir=self._artifacts_dir,
                    vectorizer_path=self._vectorizer_path,
                    max_features=self.DEFAULT_MAX_FEATURES,
                ),
                logger=self._logger,
            )
            trainer.train()
            return True
        except Exception as exc:
            self._load_error = f"模型训练失败: {str(exc)}"
            self._logger.error("ML检测器: %s", self._load_error, exc_info=True)
            return False

    async def detect(
        self,
        subject: Optional[str],
        sender: str,
        content_text: Optional[str],
        content_html: Optional[str],
        headers: Optional[Dict[str, str]] = None,
    ) -> PhishingResult:
        """使用ML模型检测邮件是否为钓鱼邮件。

        Args:
            subject: 邮件主题。
            sender: 发件人。
            content_text: 纯文本内容。
            content_html: HTML内容。
            headers: 邮件头信息（可选）。

        Returns:
            钓鱼检测结果。
        """
        if not self._is_loaded:
            # 模型未加载，返回正常（降级处理）
            return PhishingResult(
                level=PhishingLevel.NORMAL,
                score=0.0,
                reason=f"ML检测器未就绪: {self._load_error}"
            )

        # 合并邮件内容进行检测（主题 + 纯文本 + HTML）
        full_text = " ".join(filter(None, [subject, content_text, content_html]))
        if not full_text.strip():
            return PhishingResult(
                level=PhishingLevel.NORMAL,
                score=0.0,
                reason="邮件内容为空"
            )

        try:
            # 在线程池中执行ML预测（避免阻塞事件循环）
            loop = asyncio.get_running_loop()
            score = await loop.run_in_executor(
                None,
                self._predict_sync,
                full_text
            )

            # 根据置信度判定等级
            level = self._score_mapper.get_level(score)
            if level == PhishingLevel.HIGH_RISK:
                reason = f"[ML检测] 高危钓鱼邮件（置信度: {score:.1%}）"
            elif level == PhishingLevel.SUSPICIOUS:
                reason = f"[ML检测] 疑似钓鱼邮件（置信度: {score:.1%}）"
            else:
                reason = f"[ML检测] 正常邮件（钓鱼概率: {score:.1%}）"

            self._logger.debug(
                "ML检测完成: level=%s, score=%.4f",
                level.value, score
            )

            return PhishingResult(
                level=level,
                score=round(score, 4),
                reason=reason,
            )

        except Exception as e:
            self._logger.error("ML检测异常: %s", str(e), exc_info=True)
            return PhishingResult(
                level=PhishingLevel.NORMAL,
                score=0.0,
                reason=f"ML检测异常: {str(e)}"
            )

    def _predict_sync(self, text: str) -> float:
        """同步执行预测（在线程池中调用）。

        Args:
            text: 要检测的文本内容。

        Returns:
            钓鱼概率（0-1）。
        """
        # TF-IDF转换
        text_tfidf = self._tfidf.transform([text]).toarray()

        # 模型预测（verbose=0 禁止输出进度）
        prediction = self._model.predict(text_tfidf, verbose=0)

        return float(prediction[0][0])

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
            "model_version": "ml-keras-1.0.0",
            "model_path": str(self._model_path),
            "dataset_path": str(self._dataset_path),
            "vectorizer_path": str(self._vectorizer_path),
            "artifacts_dir": str(self._artifacts_dir),
            "is_loaded": self._is_loaded,
            "load_error": self._load_error,
            "mode": "ml_neural_network" if self._is_loaded else "disabled",
            "high_risk_threshold": self._high_risk_threshold,
            "suspicious_threshold": self._suspicious_threshold,
            "tfidf_max_features": self.DEFAULT_MAX_FEATURES,
            "model_architecture": "Input(5000)->Dense(128,relu)->Dropout(0.2)->Dense(64,relu)->Dense(1,sigmoid)",
        }

    async def reload_model(self) -> bool:
        """热加载模型（重新加载模型文件）。

        Returns:
            加载是否成功。
        """
        self._logger.info("重新加载ML模型...")
        self._is_loaded = False
        self._model = None
        self._tfidf = None

        # 在线程池中执行加载（避免阻塞）
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(None, self._try_load_model)

        if success:
            self._logger.info("ML模型重新加载成功")
        else:
            self._logger.error("ML模型重新加载失败: %s", self._load_error)

        return success

    @property
    def is_available(self) -> bool:
        """检查ML检测器是否可用。"""
        return self._is_loaded

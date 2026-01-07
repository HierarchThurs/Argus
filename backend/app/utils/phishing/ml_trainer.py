"""钓鱼邮件模型训练器模块。

基于 phishingDP 项目的训练流程封装训练器，提供模型训练、
评估指标计算与训练产物落盘能力，便于在后端独立完成模型更新。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import json
import logging


@dataclass(frozen=True)
class MLTrainingConfig:
    """模型训练配置。

    Attributes:
        dataset_path: 训练数据集路径（CSV）。
        model_path: 模型输出路径（.h5）。
        artifacts_dir: 训练产物输出目录。
        vectorizer_path: TF-IDF 向量化器输出路径。
        max_features: TF-IDF 最大特征数。
        test_size: 测试集占比。
        random_state: 数据集划分随机种子。
        epochs: 训练轮数。
        batch_size: 训练批次大小。
        enable_artifacts: 是否输出评估产物。
    """

    dataset_path: Path
    model_path: Path
    artifacts_dir: Path
    vectorizer_path: Path
    max_features: int = 5000
    test_size: float = 0.2
    random_state: int = 42
    epochs: int = 5
    batch_size: int = 32
    enable_artifacts: bool = True


class MLPhishingTrainer:
    """钓鱼邮件模型训练器。

    负责加载数据集、训练 TF-IDF 向量化器与 Keras 模型，
    并在训练完成后保存模型与评估产物。
    """

    def __init__(
        self,
        config: MLTrainingConfig,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """初始化训练器。

        Args:
            config: 训练配置。
            logger: 日志记录器。
        """
        self._config = config
        self._logger = logger or logging.getLogger(self.__class__.__name__)

    def train(self) -> Dict[str, float]:
        """训练模型并输出评估指标。

        Returns:
            训练完成后的评估指标字典。

        Raises:
            FileNotFoundError: 数据集文件不存在。
            ValueError: 数据集列缺失或格式不合法。
        """
        self._logger.info("开始训练钓鱼邮件检测模型")

        # 延迟导入依赖，避免在未安装时影响服务启动。
        import numpy as np
        import pandas as pd
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            confusion_matrix,
            roc_curve,
            precision_recall_curve,
            auc,
        )
        from keras.models import Sequential
        from keras.layers import Dense, Dropout
        import joblib

        dataset_path = self._config.dataset_path
        if not dataset_path.exists():
            raise FileNotFoundError(f"数据集文件不存在: {dataset_path}")

        self._logger.info("加载数据集: %s", dataset_path)
        df = pd.read_csv(dataset_path)
        if "text" not in df.columns or "target" not in df.columns:
            raise ValueError("数据集必须包含 text 和 target 列")

        df["text"] = df["text"].fillna("")

        self._logger.info("开始构建 TF-IDF 特征向量")
        tfidf = TfidfVectorizer(
            stop_words="english",
            max_features=self._config.max_features,
        )
        features = tfidf.fit_transform(df["text"]).toarray()
        labels = df["target"]

        X_train, X_test, y_train, y_test = train_test_split(
            features,
            labels,
            test_size=self._config.test_size,
            random_state=self._config.random_state,
        )

        self._logger.info("构建神经网络模型")
        model = Sequential(
            [
                Dense(128, activation="relu", input_dim=features.shape[1]),
                Dropout(0.2),
                Dense(64, activation="relu"),
                Dense(1, activation="sigmoid"),
            ]
        )
        model.compile(
            optimizer="adam",
            loss="binary_crossentropy",
            metrics=["accuracy"],
        )

        self._logger.info("开始训练模型，epochs=%d", self._config.epochs)
        history = model.fit(
            X_train,
            y_train,
            validation_data=(X_test, y_test),
            epochs=self._config.epochs,
            batch_size=self._config.batch_size,
            verbose=1,
        )

        self._ensure_output_dirs()
        model.save(self._config.model_path)
        joblib.dump(tfidf, self._config.vectorizer_path)

        self._logger.info("训练完成，开始评估模型")
        y_pred_proba = model.predict(X_test, verbose=0).ravel()
        y_pred = (y_pred_proba > 0.5).astype(int)
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
        roc_auc = float(auc(fpr, tpr))

        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        }

        if self._config.enable_artifacts:
            self._save_artifacts(
                history=history.history,
                metrics=metrics,
                confusion_matrix_data=confusion_matrix(y_test, y_pred),
                roc_fpr=fpr,
                roc_tpr=tpr,
                pr_precision=precision,
                pr_recall=recall,
                y_test=y_test.to_numpy(),
                y_pred=y_pred,
                y_pred_proba=y_pred_proba,
                roc_auc=roc_auc,
            )

        self._logger.info("模型训练与保存完成")
        return metrics

    def _ensure_output_dirs(self) -> None:
        """确保输出目录存在。"""
        self._config.model_path.parent.mkdir(parents=True, exist_ok=True)
        self._config.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._config.vectorizer_path.parent.mkdir(parents=True, exist_ok=True)

    def _save_artifacts(
        self,
        history: Dict[str, list],
        metrics: Dict[str, float],
        confusion_matrix_data,
        roc_fpr,
        roc_tpr,
        pr_precision,
        pr_recall,
        y_test,
        y_pred,
        y_pred_proba,
        roc_auc: float,
    ) -> None:
        """保存训练与评估产物。

        Args:
            history: 训练历史记录。
            metrics: 评估指标字典。
            confusion_matrix_data: 混淆矩阵数据。
            roc_fpr: ROC 曲线 FPR 数组。
            roc_tpr: ROC 曲线 TPR 数组。
            pr_precision: PR 曲线精确率数组。
            pr_recall: PR 曲线召回率数组。
            y_test: 测试集标签。
            y_pred: 预测标签。
            y_pred_proba: 预测概率。
            roc_auc: ROC AUC 值。
        """
        import numpy as np
        import pandas as pd

        artifacts_dir = self._config.artifacts_dir

        # 训练历史
        history_df = pd.DataFrame(history)
        history_path = artifacts_dir / "training_history.csv"
        history_df.to_csv(history_path, index=False)

        # 指标文本与 JSON
        metrics_path = artifacts_dir / "model_metrics.txt"
        with metrics_path.open("w", encoding="utf-8") as file:
            for key, value in metrics.items():
                file.write(f"{key}: {value:.4f}\n")

        metrics_json_path = artifacts_dir / "model_metrics.json"
        metrics_json_path.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 混淆矩阵
        np.save(artifacts_dir / "confusion_matrix.npy", confusion_matrix_data)

        # ROC 曲线数据
        np.savez(
            artifacts_dir / "roc_data.npz",
            fpr=roc_fpr,
            tpr=roc_tpr,
            auc=roc_auc,
        )

        # PR 曲线数据
        np.savez(
            artifacts_dir / "pr_data.npz",
            precision=pr_precision,
            recall=pr_recall,
        )

        # 测试预测结果
        np.savez(
            artifacts_dir / "test_predictions.npz",
            y_test=y_test,
            y_pred=y_pred,
            y_pred_proba=y_pred_proba,
        )

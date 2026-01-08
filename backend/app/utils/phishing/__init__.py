"""钓鱼检测工具模块。"""

from app.utils.phishing.phishing_detector_interface import (
    PhishingDetectorInterface,
    PhishingResult,
    PhishingLevel,
)
from app.utils.phishing.mock_phishing_detector import MockPhishingDetector
from app.utils.phishing.ml_phishing_detector import MLPhishingDetector
from app.utils.phishing.ml_trainer import MLPhishingTrainer, MLTrainingConfig
from app.utils.phishing.url_detector import LongUrlDetector
from app.utils.phishing.composite_detector import CompositePhishingDetector
from app.utils.phishing.dynamic_detector import DynamicPhishingDetector
from app.utils.phishing.score_level_mapper import ScoreLevelMapper, ScoreThresholds

__all__ = [
    "PhishingDetectorInterface",
    "PhishingResult",
    "PhishingLevel",
    "MockPhishingDetector",
    "MLPhishingDetector",
    "MLPhishingTrainer",
    "MLTrainingConfig",
    "ScoreLevelMapper",
    "ScoreThresholds",
    "LongUrlDetector",
    "CompositePhishingDetector",
    "DynamicPhishingDetector",
]

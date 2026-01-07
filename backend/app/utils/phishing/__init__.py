"""钓鱼检测工具模块。"""

from app.utils.phishing.phishing_detector_interface import (
    PhishingDetectorInterface,
    PhishingResult,
    PhishingLevel,
)
from app.utils.phishing.mock_phishing_detector import MockPhishingDetector

__all__ = [
    "PhishingDetectorInterface",
    "PhishingResult",
    "PhishingLevel",
    "MockPhishingDetector",
]

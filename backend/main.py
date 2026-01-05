"""应用入口模块（供 uvicorn CLI 使用）。"""

from app.main import app

__all__ = ["app"]

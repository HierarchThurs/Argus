"""钓鱼检测路由。"""

from fastapi import APIRouter, Depends, HTTPException

from app.middleware.jwt_auth import get_current_user, JWTPayload
from app.schemas.phishing_schema import (
    VerifyLinkRequest,
    VerifyLinkResponse,
    PhishingStatsResponse,
)


class PhishingRouter:
    """钓鱼检测路由。"""

    def __init__(self) -> None:
        """初始化路由。"""
        self.router = APIRouter(prefix="/api/phishing", tags=["phishing"])
        self._register_routes()

    def _register_routes(self) -> None:
        """注册路由。"""
        self.router.post("/verify-link")(self.verify_link)
        self.router.get("/stats")(self.get_stats)

    async def verify_link(
        self,
        request: VerifyLinkRequest,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> VerifyLinkResponse:
        """验证学号后返回链接。

        用户必须正确输入自己的学号才能获取高危链接内容。

        Args:
            request: 验证请求。
            current_user: 当前用户。

        Returns:
            验证结果。
        """
        if request.student_id != current_user.student_id:
            return VerifyLinkResponse(
                success=False,
                message="学号验证失败，请输入正确的学号。",
            )

        return VerifyLinkResponse(
            success=True,
            message="验证成功，请谨慎访问该链接。",
            link_url=request.link_url,
        )

    async def get_stats(
        self,
        current_user: JWTPayload = Depends(get_current_user),
    ) -> PhishingStatsResponse:
        """获取钓鱼检测统计。

        Args:
            current_user: 当前用户。

        Returns:
            统计数据。
        """
        # TODO: 从数据库获取真实统计数据
        return PhishingStatsResponse(
            total_emails=0,
            normal_count=0,
            suspicious_count=0,
            high_risk_count=0,
        )

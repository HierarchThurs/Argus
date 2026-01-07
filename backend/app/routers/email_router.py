"""邮件路由层。"""

import logging
from typing import Optional

from fastapi import APIRouter, Header, Query

from app.core.config import AppConfig
from app.schemas.email_schema import (
    EmailListResponse,
    EmailDetailResponse,
    SendEmailRequest,
    SendEmailResponse,
    MarkAsReadResponse,
)
from app.services.email_service import EmailService


class EmailRouter:
    """邮件路由类。

    负责注册邮件相关的 API 路由。
    """

    def __init__(
        self,
        email_service: EmailService,
        config: AppConfig,
        logger: logging.Logger,
    ) -> None:
        """初始化邮件路由。

        Args:
            email_service: 邮件服务。
            config: 应用配置。
            logger: 日志记录器。
        """
        self._email_service = email_service
        self._logger = logger
        self._router = APIRouter(prefix=config.api_prefix, tags=["emails"])
        self._register_routes()

    @property
    def router(self) -> APIRouter:
        """对外暴露 FastAPI 路由对象。"""
        return self._router

    def _register_routes(self) -> None:
        """注册路由方法。"""
        self._router.get(
            "/emails",
            response_model=EmailListResponse,
        )(self.get_emails)

        self._router.get(
            "/emails/{email_id}",
            response_model=EmailDetailResponse,
        )(self.get_email_detail)

        self._router.post(
            "/emails/send",
            response_model=SendEmailResponse,
        )(self.send_email)

        self._router.post(
            "/emails/{email_id}/read",
            response_model=MarkAsReadResponse,
        )(self.mark_as_read)

    async def get_emails(
        self,
        x_user_id: int = Header(..., alias="X-User-Id"),
        account_id: Optional[int] = Query(default=None, description="邮箱账户ID"),
        limit: int = Query(default=50, ge=1, le=100, description="返回数量"),
        offset: int = Query(default=0, ge=0, description="偏移量"),
    ) -> EmailListResponse:
        """获取邮件列表。

        Args:
            x_user_id: 用户ID（从请求头获取）。
            account_id: 邮箱账户ID（可选）。
            limit: 返回数量限制。
            offset: 偏移量。

        Returns:
            邮件列表响应。
        """
        self._logger.info(
            "获取邮件列表 user_id=%s, account_id=%s", x_user_id, account_id
        )
        return await self._email_service.get_emails(
            x_user_id, account_id, limit, offset
        )

    async def get_email_detail(
        self,
        email_id: int,
        x_user_id: int = Header(..., alias="X-User-Id"),
    ) -> EmailDetailResponse:
        """获取邮件详情。

        Args:
            email_id: 邮件ID。
            x_user_id: 用户ID（从请求头获取）。

        Returns:
            邮件详情响应。
        """
        self._logger.info("获取邮件详情 user_id=%s, email_id=%s", x_user_id, email_id)
        return await self._email_service.get_email_detail(x_user_id, email_id)

    async def send_email(
        self,
        request: SendEmailRequest,
        x_user_id: int = Header(..., alias="X-User-Id"),
    ) -> SendEmailResponse:
        """发送邮件。

        Args:
            request: 发送邮件请求。
            x_user_id: 用户ID（从请求头获取）。

        Returns:
            发送邮件响应。
        """
        self._logger.info("发送邮件 user_id=%s, to=%s", x_user_id, request.to_addresses)
        return await self._email_service.send_email(x_user_id, request)

    async def mark_as_read(
        self,
        email_id: int,
        x_user_id: int = Header(..., alias="X-User-Id"),
    ) -> MarkAsReadResponse:
        """标记邮件为已读。

        Args:
            email_id: 邮件ID。
            x_user_id: 用户ID（从请求头获取）。

        Returns:
            标记已读响应。
        """
        self._logger.info("标记邮件已读 user_id=%s, email_id=%s", x_user_id, email_id)
        return await self._email_service.mark_as_read(x_user_id, email_id)

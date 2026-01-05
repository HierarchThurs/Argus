"""认证相关的请求与响应模型。"""

from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求模型。"""

    student_id: str = Field(..., min_length=1, description="学号")
    password: str = Field(..., min_length=1, description="密码")


class LoginResponse(BaseModel):
    """登录响应模型。"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示信息")
    token: Optional[str] = Field(default=None, description="登录令牌")
    student_id: Optional[str] = Field(default=None, description="学号")
    display_name: Optional[str] = Field(default=None, description="显示名称")

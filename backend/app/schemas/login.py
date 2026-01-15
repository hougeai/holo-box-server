from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class CredentialsSchema(BaseModel):
    email: str = Field(..., description='邮箱', example='admin')
    password: str = Field(..., description='密码', example='123456')
    remember: Optional[bool] = False  # 是否记住登录状态


class JWTOut(BaseModel):
    access_token: str
    user_id: str


class JWTPayload(BaseModel):
    user_id: str
    exp: datetime


# 用户注册相关
class VerifyCodeRequest(BaseModel):
    email: EmailStr = Field(..., description='用户邮箱唯一', example='admin@example.com')


# 重置密码请求体
class ResetPasswordRequest(BaseModel):
    token: str  # 令牌
    new_password: str  # 新密码


class RegisterRequest(BaseModel):
    user_name: str = Field(..., description='用户名称', example='admin')
    password: str = Field(..., description='密码', example='123456')
    email: EmailStr = Field(..., description='用户邮箱', example='admin@example.com')
    verification_code: str = Field(..., description='验证码', example='123456')
    inviter_id: str = Field(None, description='邀请人ID', example='123456')


# 手机号注册登录相关
class PhoneRequest(BaseModel):
    phone: str = Field(None, description='手机号', example='13800138000')
    code: str = Field(None, description='验证码', example='123456')
    remember: Optional[bool] = False  # 是否记住登录状态
    inviter_id: str = Field(None, description='邀请人ID', example='123456')

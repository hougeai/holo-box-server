from tortoise import fields
from .base import BaseModel, TimestampMixin


# agent模板
class AgentTemplate(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, null=True, index=True, description='用户ID')
    agent_name = fields.CharField(max_length=64, null=True, index=True, description='智能体名称')
    system_prompt = fields.TextField(null=True, description='系统提示词')
    avatar = fields.TextField(null=True, description='头像')
    tags = fields.JSONField(null=True, description='标签, list')
    likes = fields.IntField(default=0, description='点赞数')


# agent表
class Agent(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, null=True, index=True, description='用户ID')
    agent_id = fields.CharField(max_length=64, unique=True, index=True, description='智能体ID')
    agent_name = fields.CharField(max_length=64, null=True, index=True, description='智能体名称')
    llm_model_id = fields.CharField(max_length=64, null=True, index=True, description='LLM模型ID')
    llm_model_name = fields.CharField(max_length=64, null=True, index=True, description='LLM模型名称')
    tts_voice_id = fields.CharField(max_length=64, null=True, index=True, description='TTS语音ID')
    tts_voice_name = fields.CharField(max_length=64, null=True, index=True, description='TTS语音名称')
    system_prompt = fields.TextField(null=True, description='系统提示词')
    device_count = fields.IntField(default=0, null=True, description='设备数量')
    avatar = fields.TextField(null=True, description='头像')


# TTS语音表
class Voice(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, null=True, index=True, description='用户ID')
    tts_voice_id = fields.CharField(max_length=64, unique=True, index=True, description='语音ID')
    tts_voice_name = fields.CharField(max_length=64, null=True, index=True, description='语音名称')
    demo = fields.TextField(null=True, description='语音示例')
    avatar = fields.TextField(null=True, description='头像')
    tags = fields.JSONField(null=True, description='标签, dict')
    public = fields.BooleanField(default=False, description='是否公开')
    ref_audio = fields.TextField(null=True, description='音频文件')
    status = fields.CharField(max_length=36, null=True, index=True, description='音色状态，Training/Success')

from tortoise import fields
from .base import BaseModel, TimestampMixin


# agent模板：和agent对齐，改造xiaozhi-api返回结果进行适配
class AgentTemplate(BaseModel, TimestampMixin):
    agent_id = fields.CharField(max_length=12, null=True, index=True, description='智能体模板ID')
    agent_name = fields.CharField(max_length=64, null=True, index=True, description='智能体模板名称')
    llm_model = fields.CharField(max_length=64, null=True, index=True, description='LLM模型')
    tts_voice = fields.CharField(max_length=64, null=True, index=True, description='TTS语音')
    assistant_name = fields.CharField(max_length=64, null=True, index=True, description='助手名称')
    user_name = fields.CharField(max_length=64, null=True, index=True, description='用户名称')
    character = fields.TextField(null=True, description='系统提示词')
    language = fields.CharField(max_length=64, null=True, index=True, description='语言')
    tts_speech_speed = fields.CharField(max_length=64, default='normal', null=True, description='TTS语速')
    asr_speed = fields.CharField(max_length=64, default='normal', null=True, description='ASR语速')
    tts_pitch = fields.IntField(default=0, null=True, description='TTS音调')


# agent表
class Agent(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, null=True, index=True, description='用户ID')
    agent_id = fields.CharField(max_length=64, unique=True, index=True, description='智能体ID')
    agent_name = fields.CharField(max_length=64, null=True, index=True, description='智能体名称')
    llm_model = fields.CharField(max_length=64, null=True, index=True, description='LLM模型')
    tts_voice = fields.CharField(max_length=64, null=True, index=True, description='TTS语音')
    assistant_name = fields.CharField(max_length=64, null=True, index=True, description='助手名称')
    user_name = fields.CharField(max_length=64, null=True, index=True, description='用户名称')
    character = fields.TextField(null=True, description='系统提示词')
    memory = fields.TextField(null=True, description='记忆')
    long_memory_switch = fields.BooleanField(default=False, null=True, description='长记忆开关')
    memory_type = fields.CharField(max_length=64, default='SHORT_TERM', null=True, index=True, description='记忆类型')
    language = fields.CharField(max_length=64, null=True, index=True, description='语言')
    tts_speech_speed = fields.CharField(max_length=64, default='normal', null=True, description='TTS语速')
    asr_speed = fields.CharField(max_length=64, default='normal', null=True, description='ASR语速')
    tts_pitch = fields.IntField(default=0, null=True, description='TTS音调')
    agent_template_id = fields.CharField(max_length=64, null=True, index=True, description='智能体模板ID')
    mcp_endpoints = fields.JSONField(null=True, description='MCP端点')
    device_count = fields.IntField(default=0, null=True, description='设备数量')
    source = fields.CharField(max_length=64, null=True, index=True, description='创建来源')
    avatar = fields.TextField(null=True, description='头像')


# LLM表
class LLM(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, null=True, index=True, description='用户ID')
    name = fields.CharField(max_length=64, null=True, index=True, description='LLM模型名称')
    description = fields.TextField(null=True, description='描述')


# TTS语音表
class Voice(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=12, null=True, index=True, description='用户ID')
    language = fields.CharField(max_length=64, null=True, index=True, description='语言')
    voice_id = fields.CharField(max_length=128, null=True, index=True, description='语音ID')
    voice_name = fields.CharField(max_length=128, null=True, index=True, description='语音名称')
    voice_demo = fields.TextField(null=True, description='语音示例')
    avatar = fields.TextField(null=True, description='头像')
    tags = fields.JSONField(null=True, description='标签')
    public = fields.BooleanField(default=False, description='是否公开')
    ref_audio = fields.TextField(null=True, description='参考音频文件')
    status = fields.CharField(max_length=36, null=True, index=True, description='音色状态')

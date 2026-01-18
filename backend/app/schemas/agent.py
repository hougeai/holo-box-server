from typing import Optional
from pydantic import BaseModel, Field


# ========== AgentTemplate ==========


class AgentTemplateCreate(BaseModel):
    agent_id: str = Field(description='智能体模板ID')
    agent_name: str = Field(description='智能体模板名称')
    tts_voices: Optional[list[str]] = Field(default=None, description='TTS语音列表')
    default_tts_voice: Optional[str] = Field(default=None, description='默认TTS语音')
    llm_model: Optional[str] = Field(default=None, description='LLM模型')
    assistant_name: Optional[str] = Field(default=None, description='助手名称')
    user_name: Optional[str] = Field(default=None, description='用户名称')
    character: Optional[str] = Field(default=None, description='系统提示词')
    tts_speech_speed: Optional[str] = Field(default=None, description='TTS语速')
    asr_speed: Optional[str] = Field(default=None, description='ASR语速')
    tts_pitch: Optional[int] = Field(default=None, description='TTS音调')
    tts_voice_name: Optional[str] = Field(default=None, description='TTS语音名称')


class AgentTemplateUpdate(AgentTemplateCreate):
    id: int = Field(description='ID')
    agent_id: Optional[str] = Field(default=None, description='智能体模板ID')
    agent_name: Optional[str] = Field(default=None, description='智能体名称')


# ========== Agent ==========


class AgentCreate(BaseModel):
    user_id: str = Field(description='用户ID')
    agent_id: str = Field(description='智能体ID')
    agent_name: Optional[str] = Field(default=None, description='智能体名称')
    llm_model: Optional[str] = Field(default=None, description='LLM模型')
    tts_voice: Optional[str] = Field(default=None, description='TTS语音')
    assistant_name: Optional[str] = Field(default=None, description='助手名称')
    user_name: Optional[str] = Field(default=None, description='用户名称')
    character: Optional[str] = Field(default=None, description='系统提示词')
    memory: Optional[str] = Field(default=None, description='记忆')
    long_memory_switch: Optional[bool] = Field(default=False, description='长记忆开关')
    memory_type: Optional[str] = Field(default='SHORT_TERM', description='记忆类型')
    language: Optional[str] = Field(default=None, description='语言')
    tts_speech_speed: Optional[str] = Field(default=None, description='TTS语速')
    asr_speed: Optional[str] = Field(default=None, description='ASR语速')
    tts_pitch: Optional[int] = Field(default=None, description='TTS音调')
    agent_template_id: Optional[int] = Field(default=None, description='模板ID')
    mcp_endpoints: Optional[dict] = Field(default=None, description='MCP端点')
    device_count: Optional[int] = Field(default=0, description='设备数量')
    avatar: Optional[str] = Field(default=None, description='头像')


class AgentUpdate(AgentCreate):
    id: int = Field(description='ID')
    user_id: Optional[str] = Field(default=None, description='用户ID')
    agent_id: Optional[str] = Field(default=None, description='智能体ID')


# ========== LLM ==========


class LLMCreate(BaseModel):
    user_id: str = Field(description='用户ID')
    name: Optional[str] = Field(default=None, description='LLM模型名称')
    description: Optional[str] = Field(default=None, description='描述')


class LLMUpdate(LLMCreate):
    id: int = Field(description='ID')
    user_id: Optional[str] = Field(default=None, description='用户ID')


# ========== Voice ==========


class VoiceCreate(BaseModel):
    user_id: str = Field(description='用户ID')
    language: Optional[str] = Field(default=None, description='语言')
    voice_id: str = Field(description='语音ID')
    voice_name: Optional[str] = Field(default=None, description='语音名称')
    voice_demo: Optional[str] = Field(default=None, description='语音示例')
    avatar: Optional[str] = Field(default=None, description='头像')
    tags: Optional[dict] = Field(default=None, description='标签')
    public: Optional[bool] = Field(default=False, description='是否公开')
    ref_audio: Optional[str] = Field(default=None, description='参考音频文件')
    status: Optional[str] = Field(default=None, description='音色状态')


class VoiceUpdate(VoiceCreate):
    id: int = Field(description='ID')
    user_id: Optional[str] = Field(default=None, description='用户ID')

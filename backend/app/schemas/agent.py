from typing import Optional
from pydantic import BaseModel, Field

# ========== AgentTemplate ==========


class AgentTemplateCreate(BaseModel):
    agent_name: str = Field(description='智能体模板名称')
    agent_id: Optional[str] = Field(default=None, description='智能体模板ID')
    llm_model: Optional[str] = Field(default=None, description='LLM模型')
    tts_voice: Optional[str] = Field(default=None, description='TTS语音')
    assistant_name: Optional[str] = Field(default=None, description='助手名称')
    user_name: Optional[str] = Field(default=None, description='用户名称')
    character: Optional[str] = Field(default=None, description='系统提示词')
    language: Optional[str] = Field(default=None, description='语言')
    tts_speech_speed: Optional[str] = Field(default=None, description='TTS语速')
    asr_speed: Optional[str] = Field(default=None, description='ASR语速')
    tts_pitch: Optional[int] = Field(default=None, description='TTS音调')
    avatar: Optional[str] = Field(default=None, description='头像')
    profile_id: Optional[int] = Field(default=None, description='形象ID')
    public: Optional[bool] = Field(default=False, description='是否公开')
    desc: Optional[str] = Field(default=None, description='智能体的功能特性描述')
    system_prompt: Optional[str] = Field(default=None, description='系统提示词-管理员添加')


class AgentTemplateUpdate(AgentTemplateCreate):
    id: int = Field(description='ID')
    agent_name: Optional[str] = Field(default=None, description='智能体名称')


# ========== Agent ==========


class AgentCreate(BaseModel):
    user_id: str = Field(description='用户ID')
    agent_id: Optional[str] = Field(default=None, description='智能体ID')
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
    agent_template_id: Optional[str] = Field(default=None, description='模板ID')
    mcp_endpoints: Optional[list] = Field(default=None, description='MCP端点')
    device_count: Optional[int] = Field(default=0, description='设备数量')
    source: Optional[str] = Field(default=None, description='创建来源')
    avatar: Optional[str] = Field(default=None, description='头像')
    profile_id: Optional[int] = Field(default=None, description='形象ID')
    system_prompt: Optional[str] = Field(default=None, description='系统提示词-管理员添加')


class AgentUpdate(AgentCreate):
    id: int = Field(description='ID')
    user_id: Optional[str] = Field(default=None, description='用户ID')


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
    voice_id: Optional[str] = Field(default=None, description='语音ID')
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


# ========== Profile ==========


class ProfileCreate(BaseModel):
    id: int = Field(description='形象ID')
    name: Optional[str] = Field(default=None, description='形象名称')
    ori_img: Optional[str] = Field(default=None, description='原始上传图片')
    gen_img: Optional[str] = Field(default=None, description='生成形象图片')
    gen_vids: Optional[dict] = Field(default=None, description='生成形象视频，emotion-url 字典')
    public: Optional[bool] = Field(default=None, description='是否公开')
    method: Optional[str] = Field(default=None, description='生成方式，支持 bailian')
    status: Optional[str] = Field(default=None, description='形象状态')


class ProfileUpdate(ProfileCreate): ...


class ProfileVidGen(BaseModel):
    id: int = Field(description='形象ID')
    method: str = Field(description='生成方式，支持 bailian')
    emotion: Optional[str] = Field(default=None, description='表情')


# ========== SystemPrompt ==========
class SystemPromptCreate(BaseModel):
    user_id: str = Field(description='用户ID')
    name: str = Field(description='系统提示词名称')
    content: Optional[str] = Field(default=None, description='系统提示词内容')


class SystemPromptUpdate(SystemPromptCreate):
    id: int = Field(description='ID')
    user_id: Optional[str] = Field(default=None, description='用户ID')
    name: Optional[str] = Field(default=None, description='系统提示词名称')


# ========== McpTool ==========
class McpToolCreate(BaseModel):
    user_id: str = Field(description='用户ID')
    name: str = Field(description='MCP名称')
    description: Optional[str] = Field(default=None, description='MCP描述')
    source: Optional[str] = Field(default=None, description='创建来源')
    enabled: Optional[bool] = Field(default=True, description='是否启用')
    endpoint_id: Optional[str] = Field(default=None, description='MCP端点ID')
    token: Optional[str] = Field(default=None, description='MCP密钥')
    public: Optional[bool] = Field(default=False, description='是否公开')
    protocol: Optional[str] = Field(default=None, description='协议类型')
    config: Optional[dict] = Field(default=None, description='配置文件')


class McpToolUpdate(McpToolCreate):
    id: int = Field(description='ID')
    user_id: Optional[str] = Field(default=None, description='用户ID')
    name: Optional[str] = Field(default=None, description='MCP名称')

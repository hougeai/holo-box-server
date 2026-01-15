from typing import Optional
from pydantic import BaseModel


class AgentTemplateCreate(BaseModel):
    user_id: str
    agent_name: str
    system_prompt: Optional[str] = None
    avatar: Optional[str] = None
    tags: Optional[list[str]] = None
    likes: Optional[int] = 0


class AgentTemplateUpdate(AgentTemplateCreate):
    id: int
    user_id: Optional[str] = None
    agent_name: Optional[str] = None


class AgentCreate(BaseModel):
    agent_name: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    llm_model_id: Optional[str] = None
    llm_model_name: Optional[str] = None
    tts_voice_id: Optional[str] = None
    tts_voice_name: Optional[str] = None
    system_prompt: Optional[str] = None
    device_count: Optional[int] = 0
    avatar: Optional[str] = None


class AgentUpdate(AgentCreate):
    id: int
    agent_name: Optional[str] = None

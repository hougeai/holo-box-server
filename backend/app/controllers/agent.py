from datetime import datetime
from models.agent import Agent, AgentTemplate, Voice, Profile, SystemPrompt, McpTool
from schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentTemplateCreate,
    AgentTemplateUpdate,
    VoiceCreate,
    VoiceUpdate,
    ProfileCreate,
    ProfileUpdate,
    SystemPromptCreate,
    SystemPromptUpdate,
    McpToolCreate,
    McpToolUpdate,
)

from .crud import CRUDBase


class AgentTemplateController(CRUDBase[AgentTemplate, AgentTemplateCreate, AgentTemplateUpdate]):
    def __init__(self):
        super().__init__(model=AgentTemplate)


agent_template_controller = AgentTemplateController()


class AgentController(CRUDBase[Agent, AgentCreate, AgentUpdate]):
    def __init__(self):
        super().__init__(model=Agent)


agent_controller = AgentController()


class VoiceController(CRUDBase[Voice, VoiceCreate, VoiceUpdate]):
    def __init__(self):
        super().__init__(model=Voice)


voice_controller = VoiceController()


class ProfileController(CRUDBase[Profile, ProfileCreate, ProfileUpdate]):
    def __init__(self):
        super().__init__(model=Profile)

    async def soft_delete(self, id: int) -> bool:
        """软删除形象"""
        await self.model.filter(id=id).update(deleted_at=datetime.now())
        return True

    async def restore(self, id: int) -> bool:
        """恢复已删除的形象"""
        await self.model.filter(id=id).update(deleted_at=None)
        return True


profile_controller = ProfileController()


class SystemPromptController(CRUDBase[SystemPrompt, SystemPromptCreate, SystemPromptUpdate]):
    def __init__(self):
        super().__init__(model=SystemPrompt)


system_prompt_controller = SystemPromptController()


class McpToolController(CRUDBase[McpTool, McpToolCreate, McpToolUpdate]):
    def __init__(self):
        super().__init__(model=McpTool)


mcp_tool_controller = McpToolController()

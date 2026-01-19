from models import Agent, AgentTemplate, Voice
from schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentTemplateCreate,
    AgentTemplateUpdate,
    VoiceCreate,
    VoiceUpdate,
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

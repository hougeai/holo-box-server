from models.agent import Agent, AgentTemplate, Voice, Profile
from schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentTemplateCreate,
    AgentTemplateUpdate,
    VoiceCreate,
    VoiceUpdate,
    ProfileCreate,
    ProfileUpdate,
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


profile_controller = ProfileController()

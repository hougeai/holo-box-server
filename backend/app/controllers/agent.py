from models import Agent, AgentTemplate
from schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentTemplateCreate,
    AgentTemplateUpdate,
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

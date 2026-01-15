from typing import Optional
from tortoise.expressions import Q

from models import Ota
from schemas.resource import (
    OtaCreate,
    OtaUpdate,
)
from .crud import CRUDBase


# OTA
class OtaController(CRUDBase[Ota, OtaCreate, OtaUpdate]):
    def __init__(self):
        super().__init__(model=Ota)

    async def get_by_name(self, app_version: str, device_model: str) -> Optional[Ota]:
        return await self.model.filter(Q(app_version=app_version) & Q(device_model=device_model)).first()


ota_controller = OtaController()

from typing import Optional

from models import Device
from schemas.device import (
    DeviceCreate,
    DeviceUpdate,
)

from .crud import CRUDBase


class DeviceController(CRUDBase[Device, DeviceCreate, DeviceUpdate]):
    def __init__(self):
        super().__init__(model=Device)

    async def get_by_mac(self, device_id: str) -> Optional[Device]:
        return await self.model.filter(device_id=device_id).first()


device_controller = DeviceController()

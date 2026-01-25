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

    async def get_by_mac(self, mac_address: str) -> Optional[Device]:
        return await self.model.filter(mac_address=mac_address).first()


device_controller = DeviceController()

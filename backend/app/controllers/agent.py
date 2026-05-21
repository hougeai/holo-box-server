from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from models.agent import Agent, AgentTemplate, Voice, Profile, SystemPrompt, McpTool, Alarm
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
    AlarmCreate,
    AlarmUpdate,
)

from core.celery_app import push_alarm
from core.log import logger
from core.xz_api import xz_service
from croniter import croniter
from .crud import CRUDBase

_SHANGHAI_TZ = ZoneInfo('Asia/Shanghai')


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


class AlarmController(CRUDBase[Alarm, AlarmCreate, AlarmUpdate]):
    """闹钟业务逻辑：一次性 countdown，周期性触发后自动自调度"""

    def __init__(self):
        super().__init__(model=Alarm)

    async def create(self, obj_in: AlarmCreate) -> Alarm:
        existing = await self.model.filter(serial_number=obj_in.serial_number, name=obj_in.name).first()
        if existing:
            raise ValueError('该设备已有同名闹钟')
        alarm = await super().create(obj_in)
        delay = self._calc_delay(alarm)
        if delay is not None:
            alarm.next_trigger_time = datetime.now(timezone.utc) + timedelta(seconds=delay)
            await alarm.save(update_fields=['next_trigger_time'])
            push_alarm.apply_async(args=[alarm.id], countdown=delay)
            logger.info(f'闹钟 {alarm.id} 已注册，{delay}秒后触发')
        return alarm

    async def update(self, id: int, obj_in: AlarmUpdate) -> Optional[Alarm]:
        need_reschedule = any(
            getattr(obj_in, k, None) is not None for k in ('enabled', 'cron_expr', 'delay_seconds')
        )
        alarm = await super().update(id, obj_in)
        if alarm and need_reschedule and alarm.enabled:
            delay = self._calc_delay(alarm)
            if delay is not None:
                alarm.next_trigger_time = datetime.now(timezone.utc) + timedelta(seconds=delay)
                await alarm.save(update_fields=['next_trigger_time'])
                push_alarm.apply_async(args=[alarm.id], countdown=delay)
        return alarm

    @staticmethod
    async def trigger_alarm(alarm_id: int):
        """推送提醒 + 周期性闹钟自动重新调度"""
        alarm = await Alarm.get_or_none(id=alarm_id)
        if not alarm or not alarm.enabled:
            return

        # 幂等：60 秒内已触发过则跳过（防止重复投递导致重复推送）
        if alarm.last_triggered and (datetime.now(timezone.utc) - alarm.last_triggered).total_seconds() < 60:
            logger.info(f'闹钟 {alarm_id} 60秒内已触发，跳过')
            return

        if alarm.serial_number:
            try:
                await xz_service.push_message(
                    serial_number=alarm.serial_number,
                    message={'name': 'self.wake_up', 'arguments': {'reason': f'{alarm.name} 闹钟提醒时间到了，请播放相关提醒信息'}},
                )
            except Exception as e:
                logger.error(f'闹钟 {alarm_id} 推送失败: {e}')

        alarm.trigger_count += 1
        alarm.last_triggered = datetime.now(timezone.utc)

        if alarm.alarm_type == 'once':
            alarm.status = 'triggered'
            alarm.enabled = False
            await alarm.save()
        else:
            delay = AlarmController._calc_delay(alarm)
            if delay is not None:
                alarm.next_trigger_time = datetime.now(timezone.utc) + timedelta(seconds=delay)
                await alarm.save()
                push_alarm.apply_async(args=[alarm.id], countdown=delay)

    @staticmethod
    def _calc_delay(alarm: Alarm) -> Optional[int]:
        """计算距下次触发还剩多少秒（cron 按 Asia/Shanghai 时区解析）"""
        if alarm.alarm_type == 'once':
            return alarm.delay_seconds if alarm.delay_seconds > 0 else None
        if alarm.alarm_type == 'recurring' and alarm.cron_expr:
            try:
                now = datetime.now(_SHANGHAI_TZ).replace(tzinfo=None)
                cron = croniter(alarm.cron_expr, now)
                return int((cron.get_next(datetime) - now).total_seconds())
            except Exception:
                return None
        return None

    @staticmethod
    async def restore_schedules():
        """服务重启后恢复所有未过期闹钟"""
        alarms = await Alarm.filter(enabled=True, status='active').all()
        count = 0
        for alarm in alarms:
            if alarm.alarm_type == 'once':
                if alarm.next_trigger_time and alarm.next_trigger_time > datetime.now(timezone.utc):
                    remaining = int((alarm.next_trigger_time - datetime.now(timezone.utc)).total_seconds())
                    push_alarm.apply_async(args=[alarm.id], countdown=remaining)
                    count += 1
                else:
                    alarm.status = 'expired'
                    alarm.enabled = False
                    await alarm.save()
            else:
                delay = AlarmController._calc_delay(alarm)
                if delay is not None:
                    alarm.next_trigger_time = datetime.now(timezone.utc) + timedelta(seconds=delay)
                    await alarm.save()
                    push_alarm.apply_async(args=[alarm.id], countdown=delay)
                    count += 1
        logger.info(f'已恢复 {count} 个闹钟调度')


alarm_controller = AlarmController()

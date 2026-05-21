from fastmcp import FastMCP
from typing import Optional
from datetime import datetime, timedelta
import time

# 创建 FastMCP 服务器实例
server = FastMCP('Alarm Server')

# 模拟闹钟数据存储（后续改为调用后端 REST API）
alarms_db = {}
alarm_id_counter = int(time.time() * 1000)

# 后端 API 地址（MCP 服务器通过 HTTP 调用后端持久化）
BACKEND_API_BASE = 'http://localhost:3000/api/v1'


# ─── Cron 表达式解析 ─────────────────────────────────────────────────


def parse_cron_expression(expr: str) -> dict:
    """解析 cron 表达式，返回配置字典"""
    if expr == '@hourly':
        return {
            'type': 'recurring',
            'minute': '0',
            'hour': '*',
            'day': '*',
            'month': '*',
            'weekday': '*',
            'interval': 'hourly',
        }
    elif expr == '@daily':
        return {
            'type': 'recurring',
            'minute': '0',
            'hour': '0',
            'day': '*',
            'month': '*',
            'weekday': '*',
            'interval': 'daily',
        }
    elif expr == '@weekly':
        return {
            'type': 'recurring',
            'minute': '0',
            'hour': '0',
            'day': '*',
            'month': '*',
            'weekday': '0',
            'interval': 'weekly',
        }
    elif expr == '@monthly':
        return {
            'type': 'recurring',
            'minute': '0',
            'hour': '0',
            'day': '1',
            'month': '*',
            'weekday': '*',
            'interval': 'monthly',
        }
    else:
        parts = expr.strip().split()
        if len(parts) != 5:
            raise ValueError(f'无效的 cron 表达式: "{expr}"，需要 5 个字段')
        return {
            'type': 'recurring',
            'minute': parts[0],
            'hour': parts[1],
            'day': parts[2],
            'month': parts[3],
            'weekday': parts[4],
            'interval': 'cron',
            'raw': expr,
        }


# ─── Cron 字段匹配 ───────────────────────────────────────────────────


def _match_field(pattern: str, value: int, max_val: int) -> bool:
    """判断 value 是否匹配 cron 字段模式（支持 *、*/N、N-M、逗号列表、单值）"""
    pattern = pattern.strip()
    if pattern == '*':
        return True
    # */N 步进
    if '/' in pattern:
        parts = pattern.split('/')
        base = parts[0].strip()
        step = int(parts[1])
        if base == '*':
            return value % step == 0
        return value >= int(base) and (value - int(base)) % step == 0
    # 逗号列表: 1,3,5
    if ',' in pattern:
        values = set(int(x) for x in pattern.split(',') if x)
        return value in values
    # 范围: 1-5
    if '-' in pattern:
        lo, hi = pattern.split('-')
        return int(lo) <= value <= int(hi)
    # 单值
    return int(pattern) == value


def _find_next_cron_match(cron_config: dict, now: datetime = None) -> Optional[datetime]:
    """暴力查找下一个匹配 cron 的时间（最多查 30 天）"""
    if now is None:
        now = datetime.now()
    dt = now.replace(second=0, microsecond=0)
    limit = 30 * 24 * 60  # 30 分钟步长
    for _ in range(limit):
        if (
            _match_field(cron_config['minute'], dt.minute, 59)
            and _match_field(cron_config['hour'], dt.hour, 23)
            and _match_field(cron_config['day'], dt.day, 31)
            and _match_field(cron_config['month'], dt.month, 12)
            and _match_field(cron_config['weekday'], dt.weekday(), 6)
        ):
            if dt > now:
                return dt
        dt += timedelta(minutes=1)
    return None


# ─── 触发时间计算 ────────────────────────────────────────────────────


def calculate_once_trigger(delay_seconds: int) -> datetime:
    """一次性闹钟：当前时间 + 延迟秒数"""
    return datetime.now() + timedelta(seconds=delay_seconds)


def calculate_recurring_trigger(cron_config: dict) -> Optional[datetime]:
    """周期性闹钟：计算 cron 的下一次触发时间"""
    interval = cron_config.get('interval', 'cron')
    now = datetime.now()
    minute = int(cron_config.get('minute', 0))

    if interval == 'hourly':
        # 下一小时的第 minute 分钟
        dt = now.replace(minute=minute, second=0, microsecond=0)
        if dt <= now:
            dt += timedelta(hours=1)
        return dt

    hour = int(cron_config.get('hour', 0))
    if interval == 'daily':
        dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if dt <= now:
            dt += timedelta(days=1)
        return dt

    if interval == 'weekly':
        wd = int(cron_config.get('weekday', 0))
        days_ahead = wd - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        dt = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        return dt

    if interval == 'monthly':
        day = int(cron_config.get('day', 1))
        try:
            dt = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            # 如果当前月没有这一天（如 31 日在 2 月），推到下月
            import calendar

            _, last_day = calendar.monthrange(now.year, now.month)
            dt = now.replace(day=min(day, last_day), hour=hour, minute=minute, second=0, microsecond=0)
        if dt <= now:
            month = now.month + 1
            year = now.year
            if month > 12:
                month = 1
                year += 1
            dt = dt.replace(year=year, month=month)
        return dt

    # 标准 cron：暴力查找
    return _find_next_cron_match(cron_config, now)


# ─── 工具函数 ────────────────────────────────────────────────────────


def generate_alarm_id() -> int:
    global alarm_id_counter
    alarm_id_counter += 1
    return alarm_id_counter


def _call_backend(method: str, path: str, body: dict = None) -> dict:
    """调用后端 REST API（暂未启用，后续替换本地 dict）"""
    # TODO: 后续改为调用后端 API
    # import json
    # data = json.dumps(body).encode('utf-8') if body else None
    # req = urllib.request.Request(f'{BACKEND_API_BASE}{path}',
    #                              data=data,
    #                              headers={'Content-Type': 'application/json'},
    #                              method=method)
    # try:
    #     with urllib.request.urlopen(req, timeout=5) as resp:
    #         return json.loads(resp.read().decode('utf-8'))
    # except urllib.error.HTTPError as e:
    #     return {'success': False, 'message': f'HTTP {e.code}: {e.reason}'}
    # except Exception as e:
    #     return {'success': False, 'message': f'请求失败: {str(e)}'}
    return None


def format_cron_description(cron_config: dict, name: str) -> str:
    """生成人类可读的闹钟描述"""
    interval = cron_config.get('interval', 'cron')
    if interval == 'hourly':
        return f'每小时提醒: {name}'
    h = int(cron_config.get('hour', 0))
    m = int(cron_config.get('minute', 0))
    if interval == 'daily':
        return f'每天 {h:02d}:{m:02d} 提醒: {name}'
    if interval == 'weekly':
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        wd = int(cron_config.get('weekday', 0))
        day_name = weekday_names[wd] if 0 <= wd <= 6 else f'周{wd}'
        return f'每周{day_name} {h:02d}:{m:02d} 提醒: {name}'
    if interval == 'monthly':
        d = int(cron_config.get('day', 1))
        return f'每月{d}日 {h:02d}:{m:02d} 提醒: {name}'
    raw = cron_config.get('raw', '')
    return f'周期性提醒 ({raw}): {name}'


# ─── MCP Tools ───────────────────────────────────────────────────────


@server.tool()
def alarm_set(
    name: str,
    delay_seconds: int = 0,
    cron_expr: str = '',
) -> dict:
    """为用户添加各种闹钟提醒功能

    示例：
    - 一次性提醒（5分钟后）→ delay_seconds=300, name="出发"
    - 每天下午2点提醒刷牙 → cron_expr="0 14 * * *", name="刷牙"
    - 每小时提醒喝水      → cron_expr="@hourly", name="喝水"
    - 工作日早上9点开会    → cron_expr="0 9 * * 1-5", name="开会"

    Args:
        name: 提醒内容（必填），LLM 从用户语义中提取
        delay_seconds: 一次性提醒，多少秒后触发（二选一）
        cron_expr: 周期性提醒，cron 表达式（二选一）
            - "@hourly" / "@daily" / "@weekly" / "@monthly"
            - 标准 5 段式: "分 时 日 月 周"，如 "0 14 * * *","0 9 * * 1-5"
    """
    try:
        # ── 参数校验 ──
        name = name.strip()
        if not name:
            return {'success': False, 'message': '提醒名称不能为空'}

        # 判断闹钟类型
        if delay_seconds > 0 and cron_expr:
            return {'success': False, 'message': 'delay_seconds 和 cron_expr 不能同时设置'}
        if delay_seconds <= 0 and not cron_expr:
            return {'success': False, 'message': '请设置 delay_seconds（一次性）或 cron_expr（周期性）'}

        is_once = delay_seconds > 0

        # ── 计算触发时间 ──
        if is_once:
            alarm_type = 'once'
            cron_config = None
            next_trigger = calculate_once_trigger(delay_seconds)
            friendly_desc = f'{delay_seconds} 秒后提醒: {name}'
        else:
            alarm_type = 'recurring'
            try:
                cron_config = parse_cron_expression(cron_expr)
            except ValueError as e:
                return {'success': False, 'message': str(e)}

            next_trigger = calculate_recurring_trigger(cron_config)
            if next_trigger is None:
                return {'success': False, 'message': '无法计算触发时间，请检查 cron 表达式'}
            friendly_desc = format_cron_description(cron_config, name)

        # ── 生成记录 ──
        alarm_id = generate_alarm_id()
        alarm_data = {
            'id': alarm_id,
            'name': name,
            'alarm_type': alarm_type,
            'delay_seconds': delay_seconds if is_once else 0,
            'cron_expr': '' if is_once else cron_expr,
            'cron_config': cron_config,
            'next_trigger_time': next_trigger.isoformat(),
            'tts_message': name,  # 默认用 name 作为 TTS 内容
            'enabled': True,
            'status': 'active',
            'trigger_count': 0,
            'created_at': datetime.now().isoformat(),
            'last_triggered': None,
        }

        # ── 存储（本地 dict，后续改为调用后端 API） ──
        alarms_db[alarm_id] = alarm_data

        time_str = next_trigger.strftime('%Y-%m-%d %H:%M:%S')
        message = f'✅ {friendly_desc}\n📅 下次触发: {time_str}'

        return {
            'success': True,
            'message': message,
            'alarm_id': alarm_id,
            'alarm': {
                'id': alarm_id,
                'name': name,
                'alarm_type': alarm_type,
                'next_trigger_time': next_trigger.isoformat(),
            },
        }

    except Exception as e:
        return {'success': False, 'message': f'设置闹钟失败: {str(e)}'}


@server.tool()
def alarm_del(id: int) -> dict:
    """根据 id 删除一个闹钟提醒

    首先用 alarm_queryall 查询所有闹钟，然后基于用户意图给出闹钟列表中的一个 id，删除前需要和用户确认

    Args:
        id: 闹钟 ID
    """
    try:
        if id not in alarms_db:
            return {'success': False, 'message': f'未找到 ID 为 {id} 的闹钟'}

        deleted = alarms_db.pop(id)
        return {
            'success': True,
            'message': f'已删除闹钟: {deleted["name"]}',
            'deleted_alarm': {
                'id': deleted['id'],
                'name': deleted['name'],
                'alarm_type': deleted['alarm_type'],
            },
        }
    except Exception as e:
        return {'success': False, 'message': f'删除闹钟失败: {str(e)}'}


@server.tool()
def alarm_cleanup() -> dict:
    """清空所有的提醒和闹钟

    比如：我想清空/关闭所有的提醒和闹钟
    """
    try:
        count = len(alarms_db)
        alarms_db.clear()
        return {
            'success': True,
            'message': f'已清空所有 {count} 个闹钟',
            'cleared_count': count,
        }
    except Exception as e:
        return {'success': False, 'message': f'清空闹钟失败: {str(e)}'}


@server.tool()
def alarm_queryall() -> dict:
    """查询所有的提醒和闹钟"""
    try:
        alarms = []
        for alarm in alarms_db.values():
            alarms.append(
                {
                    'id': alarm['id'],
                    'name': alarm['name'],
                    'alarm_type': alarm['alarm_type'],
                    'cron_expr': alarm.get('cron_expr', ''),
                    'delay_seconds': alarm.get('delay_seconds', 0),
                    'next_trigger_time': alarm['next_trigger_time'],
                    'tts_message': alarm.get('tts_message', alarm['name']),
                    'enabled': alarm['enabled'],
                    'status': alarm['status'],
                    'trigger_count': alarm['trigger_count'],
                    'created_at': alarm['created_at'],
                }
            )

        return {
            'success': True,
            'alarms': alarms,
            'total': len(alarms),
        }
    except Exception as e:
        return {'success': False, 'message': f'查询闹钟失败: {str(e)}'}


@server.tool()
def alarm_toggle(id: int, enabled: bool) -> dict:
    """启用或禁用闹钟

    Args:
        id: 闹钟 ID
        enabled: True 启用，False 禁用
    """
    try:
        if id not in alarms_db:
            return {'success': False, 'message': f'未找到 ID 为 {id} 的闹钟'}

        alarm = alarms_db[id]
        alarm['enabled'] = enabled
        alarm['status'] = 'active' if enabled else 'disabled'

        action = '启用' if enabled else '禁用'
        return {
            'success': True,
            'message': f'已{action}闹钟: {alarm["name"]}',
            'alarm': {
                'id': alarm['id'],
                'name': alarm['name'],
                'enabled': alarm['enabled'],
                'status': alarm['status'],
            },
        }
    except Exception as e:
        return {'success': False, 'message': f'操作失败: {str(e)}'}


if __name__ == '__main__':
    server.run()
